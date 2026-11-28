/* See engine.h. The way a sector is written (checks, erase, read back, program, read back, header page last) is that of
 * firmware/mini_fast/fast.c, which ran on a TANK-MINI; the messages and the order around it are new here. */
#include "engine.h"

static struct {
    hrs_nor nor;
    hrs_unit unit;
    uint32_t full_crc, target_crc, sectors, done, frame_crc, reply_length, retiring;
    uint32_t app_end, loader_at;              /* the application's window ends here; where the last record looked at leads */
    unsigned phase, error, windows, leaving, touched, have_last;
    uint8_t sr1, sr2;
    uint8_t sector[HRS_SECTOR] __attribute__((aligned(4)));    /* what the host sends */
    uint8_t work[HRS_SECTOR] __attribute__((aligned(4)));      /* what the flash holds */
    uint8_t reply[HRS_FRAME];
    uint32_t table[256];
} s;

static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | p[1] << 8); }
static uint32_t get32(const uint8_t *p)
{ return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }
static void put16(uint8_t *p, unsigned v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put32(uint8_t *p, uint32_t v) { unsigned i; for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8 * i)); }

static void make_table(void)
{
    unsigned i, j;
    for (i = 0; i < 256; ++i) {
        uint32_t c = i;
        for (j = 0; j < 8; ++j) c = (c >> 1) ^ ((c & 1) ? UINT32_C(0xedb88320) : 0);
        s.table[i] = c;
    }
}
/* A function of its own also in the compiled loader: tools/check_mini_stage_target.py steps over it. */
__attribute__((noinline)) static uint32_t update(uint32_t c, const uint8_t *p, unsigned n)
{ while (n--) c = (c >> 8) ^ s.table[(c ^ *p++) & 255]; return c; }
uint32_t hrs_crc32(const uint8_t *p, unsigned n) { return ~update(UINT32_MAX, p, n); }

static int inside(uint32_t a, uint32_t n, uint32_t from, uint32_t to) { return a >= from && a < to && n && n <= to - a; }
int hrs_writable(uint32_t a, uint32_t n)
{
    return inside(a, n, HRS_APP, s.app_end) || inside(a, n, HRS_USER, HRS_USER_END);
}
int hrs_permits(uint32_t a, uint32_t n) { return hrs_writable(a, n) || (s.retiring && a == s.retiring && n == HRS_PAGE); }
static int is_app(uint32_t a) { return inside(a, HRS_SECTOR, HRS_APP, s.app_end); }

static unsigned fail(unsigned error) { s.error = error; s.phase = HRS_FAILED; return error; }

static unsigned look(void)
{
    if (s.nor.status(s.nor.user, &s.sr1, &s.sr2)) return fail(HRS_E_IO);
    if ((s.sr1 & 0x7c) || (s.sr2 & 0x40)) return fail(HRS_E_PROTECTED);
    return HRS_OK;
}
static unsigned quiet(void)
{
    unsigned e = look();
    if (e) return e;
    if (s.sr1 & 1) return fail(HRS_E_BUSY);
    if (s.sr1 & 2) return fail(HRS_E_WEL);
    return HRS_OK;
}
static unsigned enable(void)
{
    unsigned e = quiet();
    if (e) return e;
    if (s.nor.write_enable(s.nor.user)) return fail(HRS_E_IO);
    if ((e = look())) return e;
    return (s.sr1 & 3) == 2 ? HRS_OK : fail(HRS_E_WEL);
}
static unsigned wait_done(void)
{
    unsigned i, e;
    for (i = 0; i < s.nor.wip_poll_limit; ++i) {
        if ((e = look())) return e;
        if (!(s.sr1 & 1)) return s.sr1 & 2 ? fail(HRS_E_WEL) : HRS_OK;
        s.nor.poll_delay(s.nor.user);
    }
    return fail(HRS_E_TIMEOUT);
}
static unsigned load(uint32_t a) { return s.nor.read(s.nor.user, a, s.work, HRS_SECTOR) ? fail(HRS_E_IO) : HRS_OK; }
static int blank(void) { unsigned i; for (i = 0; i < HRS_SECTOR; ++i) if (s.work[i] != 0xff) return 0; return 1; }
static int equal(void) { unsigned i; for (i = 0; i < HRS_SECTOR; ++i) if (s.work[i] != s.sector[i]) return 0; return 1; }
static unsigned erase(uint32_t a)
{
    unsigned e;
    if (!hrs_writable(a, HRS_SECTOR) || (a & (HRS_SECTOR - 1))) return fail(HRS_E_RANGE);
    if ((e = enable())) return e;
    s.touched = 1;
    if (s.nor.erase4k(s.nor.user, a)) return fail(HRS_E_IO);
    if ((e = wait_done()) || (e = load(a))) return e;
    return blank() ? HRS_OK : fail(HRS_E_READBACK);
}
static unsigned whole_crc(uint32_t a, uint32_t n, uint32_t *out)
{
    uint32_t c = UINT32_MAX;
    while (n) {
        unsigned k = n > HRS_SECTOR ? HRS_SECTOR : (unsigned)n;
        if (s.nor.read(s.nor.user, a, s.work, k)) return fail(HRS_E_IO);
        c = update(c, s.work, k);
        a += k;
        n -= k;
        s.nor.idle(s.nor.user);
    }
    *out = ~c;
    return HRS_OK;
}

/* The checksum of the bootloader's records (CRC-16, 0x1021, from 0). */
static uint16_t crc16(const uint8_t *p, unsigned n)
{
    uint16_t c = 0;
    unsigned i;
    while (n--) {
        c = (uint16_t)(c ^ *p++ << 8);
        for (i = 0; i < 8; ++i) c = (uint16_t)(c << 1 ^ (c & 0x8000 ? 0x1021 : 0));
    }
    return c;
}
/* The update record the bootloader finds when there is no application: from the top down, 256 bytes before each sector
 * boundary, the first with its mark and checksum. Its bytes stay in s.work; *at is 0 when there is none. */
static unsigned find_record(uint32_t boundary, uint32_t *at)
{
    for (*at = 0; boundary > HRS_SECTOR; boundary -= HRS_SECTOR) {
        if (s.nor.read(s.nor.user, boundary - HRS_PAGE, s.work, HRS_RECORD)) return fail(HRS_E_IO);
        if (get16(s.work + 6) == HRS_RECORD_MARK && crc16(s.work + 2, HRS_RECORD - 2) == get16(s.work)) {
            *at = boundary - HRS_PAGE;
            return HRS_OK;
        }
    }
    return HRS_OK;
}
/* Does the record in s.work lead to a HyperRig loader, as the bootloader reads it: its file record, then the compression
 * header, with the checksum of the code it will check after unpacking. */
static unsigned leads_here(int *ours)
{
    uint32_t a = get32(s.work + 72);
    *ours = 0;
    s.loader_at = a;
    if (!get16(s.work) || !get16(s.work + 2) || !inside(a, 64, HRS_APP_END, HRS_USER)) return HRS_OK;
    if (s.nor.read(s.nor.user, a, s.work, 64)) return fail(HRS_E_IO);
    *ours = get32(s.work + 4) == a && get32(s.work + 8) > 64 && inside(a, get32(s.work + 8), HRS_APP_END, HRS_USER) &&
        crc16(s.work + 34, 30) == get16(s.work + 32) && get16(s.work + 34) == HRS_LOADER_CRC &&
        get32(s.work + 36) && get32(s.work + 36) <= HRS_LOADER_MAX && get32(s.work + 40) == HRS_LOADER_AT;
    return HRS_OK;
}
static unsigned look_back(uint32_t *at, int *ours)
{
    unsigned e = find_record(HRS_CAPACITY - HRS_SECTOR, at);
    *ours = 0;
    return e || !*at ? e : leads_here(ours);
}
/* An update record of another loader, which the bootloader would find before ours: its mark is cleared. */
static unsigned retire(const uint8_t *b, unsigned n)
{
    uint32_t at, next;
    int ours;
    unsigned e, i;
    if (n != 4) return HRS_E_FRAME;
    if (s.phase != HRS_READY) return HRS_E_STATE;
    if ((e = quiet()) || (e = look_back(&at, &ours))) return e;
    if (!at || at != get32(b) || ours || !inside(at, HRS_PAGE, HRS_APP_END, HRS_USER)) return HRS_E_RANGE;
    if ((e = find_record(at + HRS_PAGE - HRS_SECTOR, &next))) return e;
    if (!next) return HRS_E_NO_RETURN;
    if ((e = leads_here(&ours))) return e;
    if (!ours) return HRS_E_NO_RETURN;
    for (i = 0; i < HRS_PAGE; ++i) s.sector[i] = i == 6 || i == 7 ? 0 : 0xff;
    if ((e = enable())) return e;
    s.retiring = at;
    e = s.nor.program256(s.nor.user, at, s.sector) ? fail(HRS_E_IO) : wait_done();
    s.retiring = 0;
    if (e || (e = look_back(&at, &ours))) return e;
    return at == next && ours ? HRS_OK : fail(HRS_E_READBACK);
}
/* The pedal's own partitions, in the directory at the head of its application (JieLi's encoding with the chip's key, the
 * records' own CRC-16): a VM record must start at end and reach HRS_VM_END, a PRCT record must run from 0 to end. A header
 * whose first page holds no record (blank, or an installation cut while it was erased) says nothing: then the bounds and the
 * way back decide. Without the chip's key nothing can be read, and an unread header is not taken for an empty one. */
static unsigned partitions(uint32_t end)
{
    uint32_t o, key;
    unsigned e, i, said = 1;
    uint8_t *r;
    if ((e = load(HRS_APP))) return e;
    for (i = 0; i < HRS_PAGE && s.work[i] == 0xff; ++i)
        ;
    if (i == HRS_PAGE) return HRS_OK;
    if (!s.unit.key) return HRS_E_RANGE;
    for (o = 0; o < HRS_PAGE; o += 32)
        for (key = s.unit.key ^ (o >> 2), i = 0; i < 32; ++i) {
            s.work[o + i] ^= (uint8_t)key;
            key = (key << 1 ^ (key & 0x8000 ? 0x1021 : 0)) & 0xffff;
        }
    for (o = 0; o < HRS_PAGE; o += 32) {
        r = s.work + o;
        if (crc16(r + 2, 30) != get16(r)) continue;
        if (r[16] == 'V' && r[17] == 'M' && !r[18]) said &= get32(r + 4) == end && get32(r + 8) == HRS_VM_END - end;
        if (r[16] == 'P' && r[17] == 'R' && r[18] == 'C' && r[19] == 'T' && !r[20]) said &= !get32(r + 4) && get32(r + 8) == end;
    }
    return said ? HRS_OK : HRS_E_RANGE;
}
/* BEGIN may widen the application's window, up to where the pedal's VM begins: only to whole sectors between HRS_APP_END and
 * HRS_APP_END_MAX, only as the pedal's directory says, and only with the way back above it, the record that the bootloader
 * finds first and the HyperRig loader it leads to. */
static unsigned widen(uint32_t end)
{
    uint32_t at;
    unsigned e;
    int ours;
    if ((end & (HRS_SECTOR - 1)) || end < HRS_APP_END || end > HRS_APP_END_MAX) return HRS_E_RANGE;
    if (end == HRS_APP_END) return HRS_OK;
    if ((e = quiet()) || (e = look_back(&at, &ours))) return e;
    if (!ours || at < end || s.loader_at < end) return HRS_E_NO_RETURN;
    return partitions(end);
}
static unsigned begin(const uint8_t *b, unsigned n)
{
    uint32_t crc, end;
    unsigned e, windows;
    if ((n != 15 && n != 19) || get32(b + 11) != HRS_MAGIC) return HRS_E_FRAME;
    end = n == 19 ? get32(b + 15) : HRS_APP_END;
    windows = b[10];
    if (s.phase != HRS_READY) return HRS_E_STATE;
    if (!windows || windows > 3 || !get16(b + 8) || get16(b + 8) > HRS_MAX_SECTORS) return HRS_E_RANGE;
    if ((e = widen(end))) return e;
    if ((e = quiet()) || (e = whole_crc(0, HRS_CAPACITY, &crc))) return e;
    if (crc != get32(b)) return HRS_E_BACKUP;
    s.app_end = end;
    s.full_crc = crc;
    s.target_crc = get32(b + 4);
    s.sectors = get16(b + 8);
    s.windows = windows;
    s.done = 0;
    s.phase = HRS_ARMED;
    return HRS_OK;
}
/* The header sector goes first: from here on the bootloader finds no application and starts the stored loader. */
static unsigned open_app(const uint8_t *b, unsigned n)
{
    uint32_t at;
    unsigned e;
    int ours;
    if (n != 4) return HRS_E_FRAME;
    if (s.phase != HRS_ARMED || s.done || !(s.windows & HRS_WINDOW_APP)) return HRS_E_STATE;
    if ((e = quiet()) || (e = look_back(&at, &ours))) return e;
    if (s.unit.app_valid && !ours) return HRS_E_NO_RETURN;
    if ((e = load(HRS_APP))) return e;
    if (!blank()) {
        if (hrs_crc32(s.work, HRS_SECTOR) != get32(b)) return HRS_E_PREIMAGE;
        if ((e = erase(HRS_APP))) return e;
    }
    s.phase = HRS_OPENED;
    return HRS_OK;
}
static unsigned data(const uint8_t *b, unsigned n)
{
    unsigned i, offset;
    if (n < 3 || s.phase != (s.windows & HRS_WINDOW_APP ? HRS_OPENED : HRS_ARMED)) return n < 3 ? HRS_E_FRAME : HRS_E_STATE;
    offset = get16(b);
    n -= 2;
    if (offset >= HRS_SECTOR || n > HRS_SECTOR - offset || n > HRS_CHUNK) return HRS_E_RANGE;
    for (i = 0; i < n; ++i) s.sector[offset + i] = b[2 + i];
    return HRS_OK;
}
static unsigned write(const uint8_t *b, unsigned n)
{
    uint32_t a;
    unsigned e, i, page, was_blank;
    if (n != 12) return HRS_E_FRAME;
    a = get32(b);
    if (s.phase != (s.windows & HRS_WINDOW_APP ? HRS_OPENED : HRS_ARMED)) return HRS_E_STATE;
    if ((a & (HRS_SECTOR - 1)) || !hrs_writable(a, HRS_SECTOR) ||
        !(s.windows & (is_app(a) ? HRS_WINDOW_APP : HRS_WINDOW_USER))) return HRS_E_RANGE;
    /* The header is the last sector of all, and nothing but it is. */
    if (s.windows & HRS_WINDOW_APP ? (a == HRS_APP) != (s.done + 1 == s.sectors) : s.done >= s.sectors) return HRS_E_STATE;
    if (hrs_crc32(s.sector, HRS_SECTOR) != get32(b + 8)) return HRS_E_CRC;
    if ((e = quiet()) || (e = load(a))) return e;
    if (!equal()) {
        was_blank = (unsigned)blank();
        /* The sector still holds what the host read, or it is the header that was opened. */
        if (hrs_crc32(s.work, HRS_SECTOR) != get32(b + 4) && !(was_blank && a == HRS_APP)) return HRS_E_PREIMAGE;
        if (!was_blank && (e = erase(a))) return e;
        for (i = 0; i < HRS_SECTOR / HRS_PAGE; ++i) {
            page = a == HRS_APP ? (i + 1) % (HRS_SECTOR / HRS_PAGE) : i;
            if ((e = enable())) return e;
            s.touched = 1;
            if (s.nor.program256(s.nor.user, a + page * HRS_PAGE, s.sector + page * HRS_PAGE)) return fail(HRS_E_IO);
            if ((e = wait_done())) return e;
        }
        if ((e = load(a))) return e;
        if (!equal()) return fail(HRS_E_READBACK);
    }
    ++s.done;
    return HRS_OK;
}
static unsigned finish(unsigned n)
{
    uint32_t crc;
    unsigned e;
    if (n) return HRS_E_FRAME;
    if (s.phase != (s.windows & HRS_WINDOW_APP ? HRS_OPENED : HRS_ARMED) || s.done != s.sectors) return HRS_E_STATE;
    if ((e = quiet()) || (e = whole_crc(0, HRS_CAPACITY, &crc))) return e;
    if (crc != s.target_crc) return fail(HRS_E_READBACK);
    if (s.windows & HRS_WINDOW_APP) s.unit.app_valid = 1;
    s.phase = HRS_DONE;
    return HRS_OK;
}
static unsigned leave(const uint8_t *b, unsigned n)
{
    if (n != 1 || b[0] < HRS_START_APP || b[0] > HRS_RESTART) return HRS_E_FRAME;
    /* The application is started only when it is whole: untouched and found by the bootloader, or written and checked. */
    if (b[0] == HRS_START_APP && !(s.phase == HRS_DONE ? s.unit.app_valid : s.unit.app_valid && !s.touched)) return HRS_E_NO_APP;
    s.leaving = b[0];
    return HRS_OK;
}

static unsigned hello(uint8_t *o)
{
    uint32_t at = 0;
    unsigned i;
    int ours = 0;
    if (s.phase != HRS_FAILED && !look()) (void)look_back(&at, &ours);
    o[0] = 'H'; o[1] = 'R'; o[2] = 'S'; o[3] = '1';
    put16(o + 4, HRS_CHUNK);
    put32(o + 6, HRS_CAPACITY);
    put32(o + 10, s.unit.jedec);
    put16(o + 14, s.unit.key);
    o[16] = s.sr1;
    o[17] = s.sr2;
    o[18] = s.unit.fast;
    o[19] = s.unit.app_valid;
    put16(o + 20, s.done);
    put16(o + 22, s.sectors);
    o[24] = (uint8_t)s.touched;
    o[25] = (uint8_t)s.windows;
    for (i = 0; i < HRS_BUILD_TEXT; ++i) o[26 + i] = (uint8_t)s.unit.build[i];
    o[26 + HRS_BUILD_TEXT] = (uint8_t)ours;
    put32(o + 27 + HRS_BUILD_TEXT, at);
    put32(o + 31 + HRS_BUILD_TEXT, s.app_end);        /* a loader that can widen its window says how wide it is now */
    return 35 + HRS_BUILD_TEXT;
}

uint32_t hrs_message(const uint8_t *in, uint32_t length, uint8_t *out)
{
    const uint8_t *b;
    uint8_t *o;
    uint32_t crc, i, a, n;
    unsigned op, size, status, extra = 0;
    if (length < HRS_HEAD + 4 || length > HRS_FRAME || in[0] != 'H' || in[1] != 'R' || in[2] != 1) return 0;
    op = in[3];
    size = get16(in + 6);
    if (size != length - HRS_HEAD - 4) return 0;
    crc = hrs_crc32(in, HRS_HEAD + size);
    if (crc != get32(in + HRS_HEAD + size)) return 0;                   /* a damaged message is not answered: it is sent again */
    if (s.have_last && crc == s.frame_crc) {
        for (i = 0; i < s.reply_length; ++i) out[i] = s.reply[i];
        return s.reply_length;
    }
    b = in + HRS_HEAD;
    o = s.reply + HRS_HEAD + 2;
    status = HRS_OK;
    if (op == HRS_HELLO) {
        if (size) status = HRS_E_FRAME; else extra = hello(o);
    } else if (op == HRS_READ) {
        a = size == 6 ? get32(b) : 0;
        n = size == 6 ? get16(b + 4) : 0;
        if (size != 6) status = HRS_E_FRAME;
        else if (!inside(a, n, 0, HRS_CAPACITY) || n > HRS_CHUNK) status = HRS_E_RANGE;
        else if (s.nor.read(s.nor.user, a, s.work, n)) status = fail(HRS_E_IO);
        else { for (i = 0; i < n; ++i) o[i] = s.work[i]; extra = (unsigned)n; }
    } else if (op == HRS_CRC) {
        if (size != 8) status = HRS_E_FRAME;
        else if (!inside(get32(b), get32(b + 4), 0, HRS_CAPACITY)) status = HRS_E_RANGE;
        else if (!(status = whole_crc(get32(b), get32(b + 4), &crc))) { put32(o, crc); extra = 4; crc = get32(in + HRS_HEAD + size); }
        else crc = get32(in + HRS_HEAD + size);
    } else if (op == HRS_LEAVE) status = leave(b, size);
    else if (s.phase == HRS_FAILED) status = s.error;
    else if (op == HRS_BEGIN) status = begin(b, size);
    else if (op == HRS_DATA) status = data(b, size);
    else if (op == HRS_WRITE) status = write(b, size);
    else if (op == HRS_OPEN) status = open_app(b, size);
    else if (op == HRS_FINISH) status = finish(size);
    else if (op == HRS_RETIRE) status = retire(b, size);
    else status = HRS_E_FRAME;
    s.reply[0] = 'H';
    s.reply[1] = 'R';
    s.reply[2] = 1;
    s.reply[3] = (uint8_t)(op | HRS_REPLY);
    s.reply[4] = in[4];
    s.reply[5] = in[5];
    put16(s.reply + 6, 2 + extra);
    s.reply[HRS_HEAD] = (uint8_t)status;
    s.reply[HRS_HEAD + 1] = (uint8_t)s.phase;
    put32(s.reply + HRS_HEAD + 2 + extra, hrs_crc32(s.reply, HRS_HEAD + 2 + extra));
    s.reply_length = HRS_HEAD + 2 + extra + 4;
    s.frame_crc = crc;
    s.have_last = 1;
    for (i = 0; i < s.reply_length; ++i) out[i] = s.reply[i];
    return s.reply_length;
}
unsigned hrs_leaving(void) { return s.leaving; }
int hrs_untouched(void) { return !s.touched; }
void hrs_start(const hrs_nor *nor, const hrs_unit *unit)
{
    unsigned i;
    hrs_nor n = *nor;
    hrs_unit u = *unit;
    for (i = 0; i < sizeof(s); ++i) ((uint8_t *)&s)[i] = 0;
    s.nor = n;
    s.unit = u;
    s.app_end = HRS_APP_END;
    make_table();
    if (u.jedec != HRS_JEDEC) (void)fail(HRS_E_JEDEC);
}
