#include "reader.h"

#define SYS_DIV UINT32_C(0x10008)
#define CLK_CON2 UINT32_C(0x10014)
#define SPI_CON UINT32_C(0x11c00)
#define SPI_BAUD UINT32_C(0x11c04)
#define SPI_BUF UINT32_C(0x11c08)
#define PORTD UINT32_C(0x500c0)
#define CAPACITY UINT32_C(0x100000)
#define MAX_READ 512u
#define SPI_DIVIDER 15u

static struct {
    hyperrig_reader_services services;
    hyperrig_reader_io io;
    uint32_t slot, sys_div, clk_con2, jedec, capacity, bytes_read;
    uint8_t error, initialized;
    uint8_t buffer[MAX_READ] __attribute__((aligned(4)));
} state;

static uint32_t getle32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint32_t getbe32(const uint8_t *p)
{
    return (uint32_t)p[3] | (uint32_t)p[2] << 8 | (uint32_t)p[1] << 16 | (uint32_t)p[0] << 24;
}

static void putbe32(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (24 - i * 8));
}

static uint32_t read32(uintptr_t address)
{
    return state.io.read32(state.io.user, address);
}

static void write32(uintptr_t address, uint32_t value)
{
    state.io.write32(state.io.user, address, value);
}

static void sync_cpu(void)
{
    state.io.sync(state.io.user);
}

static int fail(unsigned error)
{
    if (!state.error) state.error = (uint8_t)error;
    return -1;
}

static void update(uintptr_t address, uint32_t clear, uint32_t set)
{
    write32(address, (read32(address) & ~clear) | set);
}

static void chip_select(int high)
{
    update(PORTD, 1, high ? 1 : 0);
    state.io.settle(state.io.user, 40);
}

static int byte_transfer(uint8_t value, int receive, uint8_t *out)
{
    uint32_t attempts;
    if (state.error) return -1;
    update(SPI_CON, UINT32_C(1) << 12, receive ? UINT32_C(1) << 12 : 0);
    write32(SPI_BUF, value);
    sync_cpu();
    for (attempts = 0; attempts < state.io.poll_limit; ++attempts) {
        if (read32(SPI_CON) & (UINT32_C(1) << 15)) {
            if (out) *out = (uint8_t)read32(SPI_BUF);
            update(SPI_CON, 0, UINT32_C(1) << 14);
            return 0;
        }
    }
    return fail(HYPERRIG_READER_TIMEOUT);
}

/* No generic command entrypoint exists. The only transmitted command bytes
 * below are FF (exit continuous read), 9F (JEDEC), and 03 (NOR read). */
static int identify(void)
{
    uint8_t value;
    uint32_t id = 0;
    unsigned i;
    chip_select(0);
    if (byte_transfer(0x9f, 0, 0)) goto failed;
    for (i = 0; i < 3; ++i) {
        if (byte_transfer(0xff, 1, &value)) goto failed;
        id = (id << 8) | value;
    }
    chip_select(1);
    state.jedec = id;
    /* This reader is deliberately confined to the MINI's 1 MiB target.
     * The actual physical JEDEC response, not the FWSC size, must agree. */
    if ((id >> 16) == 0 || (id >> 16) == 255 || (id & 255) != 20)
        return fail(HYPERRIG_READER_JEDEC);
    state.capacity = CAPACITY;
    state.initialized = 1;
    return 0;
failed:
    chip_select(1);
    return -1;
}

static int clock_guard(int initial)
{
    uint32_t div = read32(SYS_DIV), clk = read32(CLK_CON2);
    uint32_t fields = div & UINT32_C(0x30700), low = clk & 255;
    int known = (low == 0x80 && fields == 0) || (low == 0x40 && fields == 0x100);
    if (initial) {
        state.sys_div = div;
        state.clk_con2 = clk;
    }
    if (!known || (fields != (state.sys_div & UINT32_C(0x30700))) ||
        (low != (state.clk_con2 & 255))) return fail(HYPERRIG_READER_CLOCK);
    return 0;
}

static int initialize_spi(void)
{
    if (state.error) return -1;
    if (state.initialized) return 0;
    if (clock_guard(1)) return -1;
    /* These are the WL82 flash pins corroborated by MINI uboot.boot.
     * SFC is disabled only because every plugin instruction resides in RAM.
     * No PLL/divider/timer/P33/cache/MMU register is modified. */
    write32(0x40200, 0);
    write32(0x13000, 0);
    update(0x51020, 2, 0);
    update(0x5101c, 32, 0);
    update(PORTD, UINT32_C(0x30), UINT32_C(0x0d));
    update(PORTD + 8, UINT32_C(0x3d), 2);
    update(PORTD + 0x1c, 0, 16);
    update(PORTD + 0x0c, 0, 2);
    update(PORTD + 0x10, 2, 0);
    update(PORTD + 0x14, 2, 0);
    write32(SPI_CON, 0x28);
    write32(SPI_BAUD, SPI_DIVIDER);
    update(SPI_CON, 0, UINT32_C(0x4001));
    chip_select(1);
    chip_select(0);
    if (byte_transfer(0xff, 0, 0) || byte_transfer(0xff, 0, 0)) {
        chip_select(1);
        return -1;
    }
    chip_select(1);
    return identify();
}

static int read_flash(uint32_t address, uint32_t length)
{
    uint32_t i;
    if (state.error) return -1;
    if (!state.initialized) return fail(HYPERRIG_READER_NOT_READY);
    if (!length || length > MAX_READ || address >= state.capacity || length > state.capacity - address)
        return fail(HYPERRIG_READER_RANGE);
    if (clock_guard(0)) return -1;
    chip_select(0);
    if (byte_transfer(0x03, 0, 0) || byte_transfer((uint8_t)(address >> 16), 0, 0) ||
        byte_transfer((uint8_t)(address >> 8), 0, 0) || byte_transfer((uint8_t)address, 0, 0)) goto failed;
    for (i = 0; i < length; ++i)
        if (byte_transfer(0xff, 1, state.buffer + i)) goto failed;
    chip_select(1);
    return 0;
failed:
    chip_select(1);
    return -1;
}

static int send(const void *bytes, uint32_t count)
{
    if (count && state.services.send(bytes, count) < 0) return fail(HYPERRIG_READER_TRANSPORT);
    return 0;
}

static void rejected_phase(const uint8_t *cbw, uint32_t count)
{
    unsigned i;
    /* Never loop on an unbounded malformed OUT count. A client must only use
     * the reviewed IN protocol; a larger malformed transfer can stall BOT. */
    if (count > MAX_READ) count = MAX_READ;
    if (cbw[12] & 128) {
        for (i = 0; i < count; ++i) state.buffer[i] = 0xff;
        (void)send(state.buffer, count);
    } else if (count && state.services.receive) {
        if (state.services.receive(state.buffer, count) < 0) (void)fail(HYPERRIG_READER_TRANSPORT);
    }
}

int hyperrig_reader_dispatch(const uint8_t *cbw, uint8_t *answer)
{
    uint32_t count, address, length;
    unsigned op, i;
    int status;
    if (!cbw || !answer || !state.services.send) return 0;
    op = (unsigned)cbw[15] << 8 | cbw[16];
    /* Leave standard SCSI and the ROM's RAM-only upload/read/call operations
     * with ROM. Consume other private commands, including legacy NOR writes,
     * so rejecting a command does not delegate that write to the ROM. */
    if (cbw[15] < 0xf0 || op == 0xfb06 || op == 0xfd07 || op == 0xfb08) return 0;
    count = getle32(cbw + 8);
    for (i = 0; i < 16; ++i) answer[i] = 0;
    answer[0] = cbw[15]; answer[1] = cbw[16];
    if (op != 0xfc70 && op != 0xfd71 && op != 0xfc72 && op != 0xfc73) {
        (void)fail(HYPERRIG_READER_FORBIDDEN);
        rejected_phase(cbw, count);
        return 1;
    }
    if (getle32(cbw) != UINT32_C(0x43425355) || cbw[12] != 128 || cbw[13] != 0 || cbw[14] != 16 ||
        (op != 0xfd71 && count != 16)) {
        (void)fail(HYPERRIG_READER_FRAME);
        rejected_phase(cbw, count);
        return 1;
    }
    if (op == 0xfc70) {
        answer[2] = 'H'; answer[3] = 'Y'; answer[4] = 'R'; answer[5] = 'N';
        answer[6] = 1; answer[7] = 3; /* protocol v1, RO | PIO */
        putbe32(answer + 8, state.slot);
        putbe32(answer + 12, 0x8000);
    } else if (op == 0xfc72) {
        (void)initialize_spi();
        answer[2] = state.error; answer[3] = state.initialized;
        answer[4] = (uint8_t)(state.jedec >> 16);
        answer[5] = (uint8_t)(state.jedec >> 8);
        answer[6] = (uint8_t)state.jedec;
        answer[7] = SPI_DIVIDER;
        putbe32(answer + 8, state.capacity);
    } else if (op == 0xfc73) {
        answer[2] = state.error; answer[3] = state.initialized;
        putbe32(answer + 4, state.sys_div);
        putbe32(answer + 8, state.clk_con2);
        putbe32(answer + 12, state.bytes_read);
    } else {
        address = getbe32(cbw + 17);
        length = (uint32_t)cbw[21] << 8 | cbw[22];
        if (!count || count > MAX_READ || count != length) {
            (void)fail(HYPERRIG_READER_FRAME);
            rejected_phase(cbw, count);
            return 1;
        }
        status = read_flash(address, length);
        if (status) for (i = 0; i < count; ++i) state.buffer[i] = 0xff;
        if (!send(state.buffer, count) && !status) state.bytes_read += count;
        return 1;
    }
    (void)send(answer, 16);
    return 1;
}

int hyperrig_reader_initialize(const hyperrig_reader_services *services,
                              const hyperrig_reader_io *io, uint32_t slot)
{
    hyperrig_reader_services services_copy;
    hyperrig_reader_io io_copy;
    size_t i;
    if (!services || !services->send || !services->receive || !services->handler_slot || !io ||
        !io->read32 || !io->write32 || !io->sync || !io->settle || !io->poll_limit || io->poll_limit > 1000000 ||
        (slot != UINT32_C(0x01c20000) && slot != UINT32_C(0x01c28000))) return -1;
    services_copy = *services;
    io_copy = *io;
    for (i = 0; i < sizeof(state); ++i) ((uint8_t *)&state)[i] = 0;
    state.services = services_copy;
    state.io = io_copy;
    state.slot = slot;
    /* target entry supplies a csync callback: this is not peripheral MMIO. */
    sync_cpu();
    *state.services.handler_slot = hyperrig_reader_dispatch;
    sync_cpu();
    return 0;
}
