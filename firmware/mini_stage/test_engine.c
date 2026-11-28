/* Host tests of the loader's engine: a simulated NOR with faults, a host that installs, power cut at every flash operation.
 * Build and run with tools/build_mini_stage.py (sanitizers on). */
#include "engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { printf("line %d: %s\n", __LINE__, #x); exit(1); } } while (0)

static uint8_t flash[HRS_CAPACITY], before[HRS_CAPACITY], target[HRS_CAPACITY];
static unsigned wel, busy, operations, cut_at, erases, programs, idles;
static int cut, fail_status, fail_read, fail_erase, fail_program, stuck_busy, no_wel, protect, bad_erase, bad_program, lazy_program;

/* One erase or program is one operation; at the chosen one the power goes: the sector or page is left half done. */
static int power(uint32_t a, unsigned n, uint8_t fill, const uint8_t *data)
{
    unsigned i;
    ++operations;
    if (cut) return -1;
    if (operations == cut_at) {
        for (i = 0; i < n / 2; ++i) flash[a + i] = data ? (uint8_t)(flash[a + i] & data[i]) : fill;
        cut = 1;
        return -1;
    }
    return 0;
}
static int nor_status(void *u, uint8_t *a, uint8_t *b)
{
    (void)u;
    if (cut || fail_status) return -1;
    *a = (uint8_t)((busy ? 1 : 0) | (wel ? 2 : 0) | (protect ? 0x1c : 0));
    *b = 0;
    if (busy && !stuck_busy && !--busy) wel = 0;
    return 0;
}
static int nor_read(void *u, uint32_t a, uint8_t *o, unsigned n)
{
    (void)u;
    CHECK(n && n <= HRS_SECTOR && a < HRS_CAPACITY && n <= HRS_CAPACITY - a);
    if (cut || fail_read) return -1;
    memcpy(o, flash + a, n);
    return 0;
}
static int nor_enable(void *u) { (void)u; if (cut) return -1; if (!no_wel) wel = 1; return 0; }
static int nor_erase(void *u, uint32_t a)
{
    (void)u;
    CHECK(wel && !busy && !(a % HRS_SECTOR) && hrs_writable(a, HRS_SECTOR));
    if (power(a, HRS_SECTOR, 0xff, 0)) return -1;
    if (fail_erase) return -1;
    memset(flash + a, 0xff, HRS_SECTOR);
    if (bad_erase) flash[a + 100] = 0x7f;
    busy = 2;
    ++erases;
    return 0;
}
static int nor_program(void *u, uint32_t a, const uint8_t *p)
{
    unsigned i;
    (void)u;
    CHECK(wel && !busy && !(a % HRS_PAGE) && hrs_permits(a, HRS_PAGE) && !hrs_permits(a, HRS_PAGE + 1) == !hrs_writable(a, HRS_PAGE + 1));
    if (power(a, HRS_PAGE, 0, p)) return -1;
    if (fail_program) return -1;
    if (!lazy_program) for (i = 0; i < HRS_PAGE; ++i) flash[a + i] &= p[i];
    if (bad_program) flash[a + 7] ^= 1;
    busy = 1;
    ++programs;
    return 0;
}
static void nor_delay(void *u) { (void)u; }
static void nor_idle(void *u) { (void)u; ++idles; }
static const hrs_nor nor = {0, nor_status, nor_read, nor_enable, nor_erase, nor_program, nor_delay, nor_idle, 50};

/* The host; end is where it takes the application's window to end (HRS_APP_END: the old BEGIN, as old hosts send it). */
static uint32_t end = HRS_APP_END;
static uint16_t seq;
static uint8_t reply[HRS_FRAME];
static uint32_t reply_length;
static uint32_t build(uint8_t *f, unsigned op, const uint8_t *body, unsigned n)
{
    uint32_t c;
    unsigned i;
    f[0] = 'H'; f[1] = 'R'; f[2] = 1; f[3] = (uint8_t)op; f[4] = (uint8_t)seq; f[5] = (uint8_t)(seq >> 8);
    f[6] = (uint8_t)n; f[7] = (uint8_t)(n >> 8);
    if (n) memcpy(f + 8, body, n);
    c = hrs_crc32(f, 8 + n);
    for (i = 0; i < 4; ++i) f[8 + n + i] = (uint8_t)(c >> (8 * i));
    return 12 + n;
}
static unsigned ask(unsigned op, const uint8_t *body, unsigned n)
{
    uint8_t f[HRS_FRAME];
    uint32_t c, length;
    ++seq;
    length = build(f, op, body, n);
    reply_length = hrs_message(f, length, reply);
    CHECK(reply_length >= 14 && reply[3] == (op | HRS_REPLY) && reply[4] == f[4] && reply[5] == f[5]);
    c = hrs_crc32(reply, reply_length - 4);
    CHECK(c == ((uint32_t)reply[reply_length - 4] | (uint32_t)reply[reply_length - 3] << 8 | (uint32_t)reply[reply_length - 2] << 16 |
                (uint32_t)reply[reply_length - 1] << 24));
    return reply[8];
}
static void le(uint8_t *p, uint32_t v, unsigned n) { while (n--) { *p++ = (uint8_t)v; v >>= 8; } }
static unsigned begin_to(const uint8_t *now, const uint8_t *want, unsigned sectors, unsigned windows, uint32_t to, int wide)
{
    uint8_t b[19];
    le(b, hrs_crc32(now, HRS_CAPACITY), 4);
    le(b + 4, hrs_crc32(want, HRS_CAPACITY), 4);
    le(b + 8, sectors, 2);
    b[10] = (uint8_t)windows;
    le(b + 11, HRS_MAGIC, 4);
    le(b + 15, to, 4);
    return ask(HRS_BEGIN, b, wide ? 19 : 15);
}
/* The old BEGIN of 15 bytes while the window is the old one; with its end when it is wider. */
static unsigned begin(const uint8_t *now, const uint8_t *want, unsigned sectors, unsigned windows)
{ return begin_to(now, want, sectors, windows, end, end != HRS_APP_END); }
static unsigned open_app(const uint8_t *now) { uint8_t b[4]; le(b, hrs_crc32(now + HRS_APP, HRS_SECTOR), 4); return ask(HRS_OPEN, b, 4); }
static unsigned send(const uint8_t *sector)
{
    uint8_t b[2 + HRS_CHUNK];
    unsigned at, e;
    for (at = 0; at < HRS_SECTOR; at += HRS_CHUNK) {
        le(b, at, 2);
        memcpy(b + 2, sector + at, HRS_CHUNK);
        if ((e = ask(HRS_DATA, b, 2 + HRS_CHUNK))) return e;
    }
    return 0;
}
static unsigned write(uint32_t a, const uint8_t *now, const uint8_t *want)
{
    uint8_t b[12];
    unsigned e;
    if ((e = send(want + a))) return e;
    le(b, a, 4);
    le(b + 4, hrs_crc32(now + a, HRS_SECTOR), 4);
    le(b + 8, hrs_crc32(want + a, HRS_SECTOR), 4);
    return ask(HRS_WRITE, b, 12);
}
static unsigned leave(unsigned mode) { uint8_t b = (uint8_t)mode; return ask(HRS_LEAVE, &b, 1); }
static unsigned hello(void) { return ask(HRS_HELLO, 0, 0); }
static unsigned phase(void) { return reply[9]; }

static void restart(int app_valid)
{
    hrs_unit u = {HRS_JEDEC, 0x980f, 1, (uint8_t)app_valid, "test"};
    wel = busy = 0;
    cut = 0;
    hrs_start(&nor, &u);
}
static void clear_faults(void)
{ fail_status = fail_read = fail_erase = fail_program = stuck_busy = no_wel = protect = bad_erase = bad_program = lazy_program = 0; cut_at = 0; operations = 0; }
static void fresh(void)
{
    clear_faults();
    memcpy(flash, before, sizeof(flash));
    erases = programs = 0;
    restart(1);
}
/* The sectors of want that differ from now in the windows (the application's up to end), the header last. */
static unsigned plan(const uint8_t *now, const uint8_t *want, uint32_t *list, unsigned *windows, int force_header)
{
    uint32_t a;
    unsigned n = 0, app = 0;
    *windows = 0;
    for (a = HRS_APP + HRS_SECTOR; a < HRS_USER_END; a += HRS_SECTOR) {
        if (!(a < end || (a >= HRS_USER && a < HRS_USER_END)) || !memcmp(now + a, want + a, HRS_SECTOR)) continue;
        list[n++] = a;
        if (a < end) app = 1; else *windows |= HRS_WINDOW_USER;
    }
    if (app || force_header || memcmp(now + HRS_APP, want + HRS_APP, HRS_SECTOR)) { list[n++] = HRS_APP; *windows |= HRS_WINDOW_APP; }
    return n;
}
/* A whole installation, as the host does it: read, plan, begin, open, write, finish. 0 when it ended well. */
static unsigned install(const uint8_t *want)
{
    static uint8_t now[HRS_CAPACITY];
    uint32_t list[HRS_MAX_SECTORS + 1];
    unsigned n, i, windows, e;
    memcpy(now, flash, sizeof(now));
    n = plan(now, want, list, &windows, 0);
    if (!n) return 0;
    if ((e = begin(now, want, n, windows))) return e;
    if (windows & HRS_WINDOW_APP && (e = open_app(now))) return e;
    for (i = 0; i < n; ++i) if ((e = write(list[i], now, want))) return e;
    return ask(HRS_FINISH, 0, 0);
}
static int header_looks_valid(void) { return flash[HRS_APP] == 0x11 && !memcmp(flash + HRS_APP, before + HRS_APP, 256); }
static int new_header(void) { return !memcmp(flash + HRS_APP, target + HRS_APP, 256); }
static int outside_same(void)
{
    return !memcmp(flash, before, HRS_APP) && !memcmp(flash + end, before + end, HRS_USER - end) &&
        !memcmp(flash + HRS_USER_END, before + HRS_USER_END, HRS_CAPACITY - HRS_USER_END);
}

/* What the stock firmware stores for its bootloader: the update record, and at the place it names a file record and the
 * compression header of a loader. */
#define RECORD 0xbcf00u
#define PLACE 0xb7000u
static unsigned crc16(const uint8_t *p, unsigned n)
{
    unsigned c = 0, i;
    while (n--) { c ^= (unsigned)*p++ << 8; for (i = 0; i < 8; ++i) c = c & 0x8000 ? (c << 1 ^ 0x1021) & 0xffff : c << 1; }
    return c;
}
static void seal(uint8_t *f, uint32_t a, unsigned n) { le(f + a, crc16(f + a + 2, n - 2), 2); }
static void plant(uint8_t *f, uint32_t record, uint32_t place, unsigned code_crc)
{
    memset(f + record, 0, 80);
    le(f + record + 2, 0x5a0d, 2); le(f + record + 4, 0x5a01, 2); le(f + record + 6, HRS_RECORD_MARK, 2);
    memcpy(f + record + 8, "ota-TANK MINI_011", 17);
    le(f + record + 72, place, 4);
    seal(f, record, 80);
    memset(f + place, 0, 64);
    le(f + place + 4, place, 4); le(f + place + 8, 19990, 4);
    memcpy(f + place + 16, "LOADER.BIN", 10);
    seal(f, place, 32);
    le(f + place + 34, code_crc, 2); le(f + place + 36, 0x4abc, 4); le(f + place + 40, HRS_LOADER_AT, 4);
    memcpy(f + place + 48, "usb_hid_ota.bin", 15);
    seal(f, place + 32, 32);
}
static unsigned returns(void) { CHECK(!hello()); return reply[10 + 42]; }
static uint32_t first_record(void)
{ return (uint32_t)reply[53] | (uint32_t)reply[54] << 8 | (uint32_t)reply[55] << 16 | (uint32_t)reply[56] << 24; }
static uint32_t window(void)
{
    CHECK(!hello() && reply_length == 14 + 51);
    return (uint32_t)reply[57] | (uint32_t)reply[58] << 8 | (uint32_t)reply[59] << 16 | (uint32_t)reply[60] << 24;
}

static void images(void)
{
    uint32_t i, x = 12345;
    for (i = 0; i < HRS_CAPACITY; ++i) { x = x * 1664525u + 1013904223u; before[i] = (uint8_t)(x >> 24); }
    before[HRS_APP] = 0x11;
    plant(before, RECORD, PLACE, HRS_LOADER_CRC);
    memcpy(target, before, sizeof(target));
    target[HRS_APP] = 0x22;
    for (i = 0; i < 9; ++i) target[HRS_APP + 0x1234 * (i + 1) * 3] ^= 0x5a;
    target[HRS_APP_END - 1] ^= 3;
    target[HRS_USER + 5] ^= 1;
    target[HRS_USER_END - 1] ^= 1;
    memset(target + 0x60000, 0xff, HRS_SECTOR);            /* a sector that becomes blank */
    memset(before + 0x70000, 0xff, HRS_SECTOR);            /* one that was blank */
}

static void good_path(void)
{
    uint8_t b[8];
    unsigned i;
    fresh();
    CHECK(!hello() && !memcmp(reply + 10, "HRS1", 4) && reply[10 + 19] == 1 && phase() == HRS_READY && hrs_untouched());
    le(b, 0xff00, 4); le(b + 4, 1024, 2);
    CHECK(!ask(HRS_READ, b, 6) && reply_length == 14 + 1024 && !memcmp(reply + 10, flash + 0xff00, 1024));
    le(b, 0x1234, 4); le(b + 4, 0x7654, 4);
    CHECK(!ask(HRS_CRC, b, 8));
    le(b, hrs_crc32(flash + 0x1234, 0x7654), 4);
    CHECK(!memcmp(reply + 10, b, 4));
    CHECK(!leave(HRS_START_APP) && hrs_leaving() == HRS_START_APP);
    fresh();
    i = idles;
    CHECK(!install(target) && phase() == HRS_DONE && idles > i + 500);
    CHECK(!memcmp(flash, target, sizeof(flash)) && outside_same() && !hrs_untouched());
    CHECK(!leave(HRS_START_APP) && hrs_leaving() == HRS_START_APP);
    /* and again: nothing differs */
    restart(1);
    CHECK(!install(target));
    CHECK(hrs_untouched());
    /* and back */
    CHECK(!install(before) && !memcmp(flash, before, sizeof(flash)));
    /* only the user area: the application is never opened */
    fresh();
    memcpy(target + HRS_APP, before + HRS_APP, HRS_APP_END - HRS_APP);
    CHECK(!install(target) && !memcmp(flash, target, sizeof(flash)) && !leave(HRS_START_APP));
    images();
}

static void refusals(void)
{
    uint8_t b[16], f[HRS_FRAME];
    uint32_t a, n;
    unsigned i;
    static const uint32_t wrong[] = {0, 0x3000, 0x3fff, 0x4001, HRS_APP_END, 0xb7000, 0xbc000, 0xbd000, 0xbe000, HRS_USER_END, 0xfffff, 0x100000, 0xfffff000u};
    fresh();
    /* before BEGIN, and in the wrong order */
    CHECK(send(target + HRS_APP) == HRS_E_STATE && open_app(flash) == HRS_E_STATE && ask(HRS_FINISH, 0, 0) == HRS_E_STATE);
    CHECK(begin(target, target, 3, 1) == HRS_E_BACKUP && phase() == HRS_READY);
    CHECK(begin(flash, target, 0, 1) == HRS_E_RANGE && begin(flash, target, HRS_MAX_SECTORS + 1, 1) == HRS_E_RANGE);
    CHECK(begin(flash, target, 3, 0) == HRS_E_RANGE && begin(flash, target, 3, 4) == HRS_E_RANGE);
    for (i = 0; i < 4; ++i) {
        uint8_t m[15];
        le(m, hrs_crc32(flash, HRS_CAPACITY), 4); le(m + 4, 1, 4); le(m + 8, 3, 2); m[10] = 3; le(m + 11, HRS_MAGIC ^ (1u << (8 * i)), 4);
        CHECK(ask(HRS_BEGIN, m, 15) == HRS_E_FRAME && phase() == HRS_READY);
    }
    CHECK(!begin(flash, target, 3, 3) && begin(flash, target, 3, 3) == HRS_E_STATE);
    le(b, 0x5000, 4); le(b + 4, 0, 4); le(b + 8, 0, 4);
    CHECK(ask(HRS_WRITE, b, 12) == HRS_E_STATE);                         /* not opened */
    CHECK(send(target + HRS_APP) == HRS_E_STATE);                        /* not opened */
    CHECK(open_app(target) == HRS_E_PREIMAGE && phase() == HRS_ARMED && !memcmp(flash, before, sizeof(flash)));
    CHECK(!open_app(before) && phase() == HRS_OPENED && open_app(before) == HRS_E_STATE && erases == 1);
    CHECK(leave(HRS_START_APP) == HRS_E_NO_APP && hrs_leaving() == HRS_STAY);
    for (i = 0; i < sizeof(wrong) / sizeof(*wrong); ++i) {
        CHECK(!send(target + HRS_APP));
        le(b, wrong[i], 4); le(b + 4, 0, 4); le(b + 8, hrs_crc32(target + HRS_APP, HRS_SECTOR), 4);
        CHECK(ask(HRS_WRITE, b, 12) == HRS_E_RANGE);
    }
    CHECK(write(HRS_APP, before, target) == HRS_E_STATE);                 /* the header is not the last one */
    CHECK(!send(target + 0x5000));
    le(b, 0x5000, 4); le(b + 4, hrs_crc32(before + 0x5000, HRS_SECTOR), 4); le(b + 8, 1, 4);
    CHECK(ask(HRS_WRITE, b, 12) == HRS_E_CRC);                            /* what was sent is not what was meant */
    CHECK(write(0x5000, target, target) == HRS_E_PREIMAGE || !memcmp(before + 0x5000, target + 0x5000, HRS_SECTOR));
    target[0x5001] ^= 1;
    CHECK(write(0x5000, target, target) == HRS_E_PREIMAGE && erases == 1);
    target[0x5001] ^= 1;
    CHECK(ask(HRS_FINISH, 0, 0) == HRS_E_STATE && phase() == HRS_OPENED);
    /* malformed bodies */
    for (n = 0; n < 16; ++n) {
        if (n != 6) CHECK(ask(HRS_READ, b, n) == HRS_E_FRAME);
        if (n != 8) CHECK(ask(HRS_CRC, b, n) == HRS_E_FRAME);
        if (n != 12) CHECK(ask(HRS_WRITE, b, n) == HRS_E_FRAME);
        if (n != 4) CHECK(ask(HRS_OPEN, b, n) == HRS_E_FRAME);
        if (n != 15) CHECK(ask(HRS_BEGIN, b, n) == HRS_E_FRAME);
        if (n != 1) CHECK(ask(HRS_LEAVE, b, n) == HRS_E_FRAME);
        if (n < 3) CHECK(ask(HRS_DATA, b, n) == HRS_E_FRAME);
        if (n) CHECK(ask(HRS_HELLO, b, n) == HRS_E_FRAME && ask(HRS_FINISH, b, n) == HRS_E_FRAME);
    }
    for (i = 0; i < 256; ++i)
        if (i != HRS_HELLO && i != HRS_READ && i != HRS_CRC && i != HRS_BEGIN && i != HRS_DATA && i != HRS_WRITE && i != HRS_OPEN &&
            i != HRS_FINISH && i != HRS_LEAVE && i != HRS_RETIRE) { if (!(i & HRS_REPLY)) CHECK(ask(i, 0, 0) == HRS_E_FRAME); }
    for (i = 0; i < 4; ++i) { b[0] = (uint8_t)(i == 3 ? 255 : i == 2 ? 4 : 0); CHECK(ask(HRS_LEAVE, b, 1) == HRS_E_FRAME); }
    le(b, 0xfffff, 4); le(b + 4, 2, 2); CHECK(ask(HRS_READ, b, 6) == HRS_E_RANGE);
    le(b, 0, 4); le(b + 4, HRS_CHUNK + 1, 2); CHECK(ask(HRS_READ, b, 6) == HRS_E_RANGE);
    le(b, 0, 4); le(b + 4, 0, 2); CHECK(ask(HRS_READ, b, 6) == HRS_E_RANGE);
    le(b, 0xff000, 4); le(b + 4, 0x1001, 4); CHECK(ask(HRS_CRC, b, 8) == HRS_E_RANGE);
    le(b, 0x100000, 4); le(b + 4, 1, 4); CHECK(ask(HRS_CRC, b, 8) == HRS_E_RANGE);
    le(b, 0, 4); le(b + 4, 0, 4); CHECK(ask(HRS_CRC, b, 8) == HRS_E_RANGE);
    le(b, 4095, 2); b[2] = b[3] = 1; CHECK(ask(HRS_DATA, b, 4) == HRS_E_RANGE);
    le(b, 4096, 2); CHECK(ask(HRS_DATA, b, 3) == HRS_E_RANGE);
    /* a message damaged anywhere, cut short or too long is not answered */
    ++seq;
    le(b, 0x4000, 4); le(b + 4, 16, 2);
    n = build(f, HRS_READ, b, 6);
    for (a = 0; a < n; ++a) { f[a] ^= 0x10; CHECK(!hrs_message(f, n, reply)); f[a] ^= 0x10; }
    for (a = 0; a < n; ++a) CHECK(!hrs_message(f, a, reply));
    CHECK(!hrs_message(f, n + 1, reply) && !hrs_message(f, HRS_FRAME + 1, reply));
    f[6] ^= 1;
    le(f + n - 4, hrs_crc32(f, n - 4), 4);
    CHECK(!hrs_message(f, n, reply));                                     /* its own length says otherwise */
    CHECK(outside_same() && erases == 1);
}

/* Only the windows BEGIN named; and a user sector that was blank is programmed without an erase. */
static void windows(void)
{
    static uint8_t want[HRS_CAPACITY];
    uint8_t b[12];
    fresh();
    CHECK(!begin(flash, target, 3, HRS_WINDOW_USER) && open_app(before) == HRS_E_STATE && !send(target + HRS_APP));
    le(b, 0x5000, 4); le(b + 4, hrs_crc32(flash + 0x5000, HRS_SECTOR), 4); le(b + 8, hrs_crc32(target + HRS_APP, HRS_SECTOR), 4);
    CHECK(ask(HRS_WRITE, b, 12) == HRS_E_RANGE && !erases && !programs);
    fresh();
    CHECK(!begin(flash, target, 3, HRS_WINDOW_APP) && !open_app(before));
    CHECK(write(HRS_USER, before, target) == HRS_E_RANGE && erases == 1 && !programs);
    fresh();
    memset(flash + 0xc5000, 0xff, HRS_SECTOR);
    memcpy(want, flash, sizeof(want));
    want[0xc5010] = 0x12;
    memcpy(target + 0xc5000, want + 0xc5000, HRS_SECTOR);
    CHECK(!begin(flash, want, 2, HRS_WINDOW_USER) && hrs_untouched());
    CHECK(!write(0xc5000, flash, want) && !erases && programs == 16 && !hrs_untouched());
    CHECK(leave(HRS_START_APP) == HRS_E_NO_APP);
    images();
}

/* Every message twice, as after a lost reply: the same answer, and nothing done twice. */
static void repeats(void)
{
    static uint8_t now[HRS_CAPACITY];
    uint8_t f[HRS_FRAME], again[HRS_FRAME], b[2 + HRS_CHUNK];
    uint32_t list[HRS_MAX_SECTORS + 1], n, first;
    unsigned count, windows, i, at, e;
    fresh();
    memcpy(now, flash, sizeof(now));
    count = plan(now, target, list, &windows, 0);
    CHECK(!begin(now, target, count, windows) && !open_app(now));
    for (i = 0; i < count; ++i) {
        for (at = 0; at < HRS_SECTOR; at += HRS_CHUNK) {
            le(b, at, 2);
            memcpy(b + 2, target + list[i] + at, HRS_CHUNK);
            ++seq;
            n = build(f, HRS_DATA, b, 2 + HRS_CHUNK);
            CHECK(hrs_message(f, n, reply) == 14 && hrs_message(f, n, again) == 14 && !memcmp(reply, again, 14) && !reply[8]);
        }
        le(b, list[i], 4); le(b + 4, hrs_crc32(now + list[i], HRS_SECTOR), 4); le(b + 8, hrs_crc32(target + list[i], HRS_SECTOR), 4);
        ++seq;
        n = build(f, HRS_WRITE, b, 12);
        first = hrs_message(f, n, reply);
        e = erases * 1000 + programs;
        for (at = 0; at < 3; ++at) CHECK(hrs_message(f, n, again) == first && !memcmp(reply, again, first) && !reply[8]);
        CHECK(e == erases * 1000 + programs);
    }
    CHECK(!ask(HRS_FINISH, 0, 0) && !memcmp(flash, target, sizeof(flash)));
}

/* Power gone at each operation in turn, then a new session finishes; the same for going back. */
static void power_cuts(void)
{
    unsigned total, k, e, valid_old, valid_new, opened;
    fresh();
    CHECK(!install(target));
    total = operations;
    CHECK(total > 100);
    for (k = 1; k <= total; ++k) {
        fresh();
        cut_at = k;
        e = install(target);
        CHECK(e && cut);
        CHECK(outside_same());
        opened = flash[HRS_APP] != 0x11 || memcmp(flash + HRS_APP, before + HRS_APP, HRS_SECTOR);
        valid_old = (unsigned)header_looks_valid();
        valid_new = (unsigned)new_header();
        /* From the first erase on, no header that could start a half-written application; the new one only as the very
         * last page. The half-erased old header has lost its first page, where the bootloader looks. */
        CHECK(!(opened && valid_old));
        CHECK(!valid_new || k >= total);
        /* the pedal comes back in the loader, with no application; a new session completes the same installation */
        clear_faults();
        restart(0);
        CHECK(returns() == 1 && first_record() == RECORD);
        CHECK(leave(HRS_START_APP) == HRS_E_NO_APP);
        CHECK(!install(target) && !memcmp(flash, target, sizeof(flash)) && !leave(HRS_START_APP));
        /* or goes back instead */
        fresh();
        cut_at = k;
        CHECK(install(target));
        clear_faults();
        restart(0);
        CHECK(!install(before) && !memcmp(flash, before, sizeof(flash)) && !leave(HRS_START_APP));
    }
    printf("power cut at each of %u flash operations, forwards and back\n", total);
}

static void faults(void)
{
    int *const fault[] = {&fail_erase, &fail_program, &stuck_busy, &no_wel, &protect, &bad_erase, &bad_program};
    static const unsigned code[] = {HRS_E_IO, HRS_E_IO, HRS_E_TIMEOUT, HRS_E_WEL, HRS_E_PROTECTED, HRS_E_READBACK, HRS_E_READBACK};
    unsigned i, e;
    for (i = 0; i < sizeof(fault) / sizeof(*fault); ++i) {
        fresh();
        CHECK(!begin(flash, target, 4, 3));
        *fault[i] = 1;
        e = open_app(before);
        CHECK(!e == (fault[i] == &fail_program || fault[i] == &bad_program));      /* OPEN only erases, and sees the rest */
        if (!e) e = write(0x7000, before, target) ? reply[8] : write(0x60000, before, target);
        CHECK(e == code[i] && phase() == HRS_FAILED);
        CHECK(ask(HRS_FINISH, 0, 0) == e && send(target) == e);
        /* a fault before the first erase leaves the old application whole, and it may be started */
        CHECK(hrs_untouched() == !memcmp(flash, before, sizeof(flash)) || hrs_untouched() == 0);
        CHECK(leave(HRS_START_APP) == (hrs_untouched() ? HRS_OK : HRS_E_NO_APP));
        CHECK(!hello() && phase() == HRS_FAILED);
        CHECK(!leave(HRS_RESTART) && hrs_leaving() == HRS_RESTART);
        CHECK(outside_same());
        clear_faults();
        restart(0);
        CHECK(!install(target) && !memcmp(flash, target, sizeof(flash)));
    }
    /* left busy, or with its write enable on, by whoever was here before */
    fresh();
    busy = stuck_busy = 1;
    CHECK(begin(flash, target, 4, 3) == HRS_E_BUSY && phase() == HRS_FAILED);
    fresh();
    wel = 1;
    CHECK(begin(flash, target, 4, 3) == HRS_E_WEL && phase() == HRS_FAILED);
    /* a flash that does not answer, or is another one */
    fresh();
    fail_read = 1;
    CHECK(begin(flash, target, 4, 3) == HRS_E_IO && phase() == HRS_FAILED);
    fresh();
    fail_status = 1;
    CHECK(begin(flash, target, 4, 3) == HRS_E_IO);
    {
        hrs_unit u = {0x856014, 0x980f, 1, 1, "other"};
        fresh();
        hrs_start(&nor, &u);
        CHECK(begin(flash, target, 4, 3) == HRS_E_JEDEC && hello() == HRS_OK && phase() == HRS_FAILED && leave(HRS_START_APP) == HRS_OK);
    }
    /* a wrong result found by FINISH: the application is not started */
    fresh();
    CHECK(!begin(flash, before, 1, 3) && !open_app(before) && !write(HRS_APP, before, target));
    CHECK(ask(HRS_FINISH, 0, 0) == HRS_E_READBACK && leave(HRS_START_APP) == HRS_E_NO_APP);
    CHECK(!leave(HRS_DOWNLOAD) && hrs_leaving() == HRS_DOWNLOAD);
}

/* A whole application is opened only when the bootloader would come back to a HyperRig loader without it. */
static unsigned try_open(void)
{
    static uint8_t now[HRS_CAPACITY];
    memcpy(now, flash, sizeof(now));
    CHECK(!begin(now, target, 4, 3));
    return open_app(now);
}
static uint8_t keep[HRS_CAPACITY];
/* A record whose checksum is zero, which the bootloader takes for none. */
static void zero_checksum(void)
{
    unsigned v = 0;
    do le(flash + RECORD + 40, v, 2); while (crc16(flash + RECORD + 2, 78) && ++v < 65536);
    CHECK(v < 65536);
    seal(flash, RECORD, 80);
}
#define SPOIL(change) do { fresh(); change; memcpy(keep, flash, sizeof(keep)); CHECK(returns() == 0); CHECK(try_open() == HRS_E_NO_RETURN && \
    phase() == HRS_ARMED && !erases && !programs && !memcmp(flash, keep, sizeof(keep)) && !leave(HRS_START_APP)); } while (0)
static void way_back(void)
{
    uint32_t a;
    fresh();
    CHECK(returns() == 1 && first_record() == RECORD && !try_open());
    /* each thing the bootloader or the loader looks at, spoiled in turn */
    SPOIL(flash[RECORD + 6] ^= 1);
    SPOIL((flash[RECORD + 6] ^= 1, seal(flash, RECORD, 80)));
    SPOIL(zero_checksum());
    SPOIL(flash[RECORD + 20] ^= 1);
    SPOIL((le(flash + RECORD + 2, 0, 2), seal(flash, RECORD, 80)));
    SPOIL((memset(flash + RECORD, 0, 80), le(flash + RECORD + 6, HRS_RECORD_MARK, 2)));
    SPOIL((le(flash + RECORD + 72, HRS_APP, 4), seal(flash, RECORD, 80)));
    SPOIL((le(flash + RECORD + 72, 0xfffff0, 4), seal(flash, RECORD, 80)));
    SPOIL((le(flash + RECORD + 72, HRS_USER - 32, 4), seal(flash, RECORD, 80)));
    SPOIL((le(flash + RECORD + 72, PLACE + 32, 4), seal(flash, RECORD, 80)));
    SPOIL(le(flash + PLACE + 8, 64, 4));
    SPOIL(le(flash + PLACE + 8, 0x100000, 4));
    SPOIL(flash[PLACE + 50] ^= 1);
    SPOIL(le(flash + PLACE + 4, PLACE + 32, 4));
    SPOIL((le(flash + PLACE + 34, 0x4853, 2), seal(flash, PLACE + 32, 32)));
    SPOIL((le(flash + PLACE + 36, 0, 4), seal(flash, PLACE + 32, 32)));
    SPOIL((le(flash + PLACE + 36, HRS_LOADER_MAX + 1, 4), seal(flash, PLACE + 32, 32)));
    SPOIL((le(flash + PLACE + 40, HRS_LOADER_AT + 4, 4), seal(flash, PLACE + 32, 32)));
    SPOIL(memset(flash + RECORD, 0xff, 80));
    /* with a record below ours it is still ours that is found; above ours, the other one */
    fresh();
    plant(flash, 0xb9f00, 0x90000, 0x1234);
    CHECK(returns() == 1 && first_record() == RECORD);
    SPOIL(plant(flash, 0xbdf00, 0x90000, 0x1234));
    /* that one can be made void, and only that one */
    fresh();
    plant(flash, 0xbdf00, 0x90000, 0x1234);
    memcpy(keep, flash, sizeof(keep));
    CHECK(returns() == 0 && first_record() == 0xbdf00);
    {
        uint8_t b[4];
        for (a = 0; a < HRS_CAPACITY; a += 0x1f00) if (a != 0xbdf00) { le(b, a, 4); CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_RANGE); }
        le(b, RECORD, 4);
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_RANGE && ask(HRS_RETIRE, b, 3) == HRS_E_FRAME && !programs);
        le(b, 0xbdf00, 4);
        CHECK(!ask(HRS_RETIRE, b, 4) && programs == 1 && !erases && hrs_untouched() && !hrs_permits(0xbdf00, HRS_PAGE));
        keep[0xbdf06] = keep[0xbdf07] = 0;
        CHECK(!memcmp(flash, keep, sizeof(flash)) && returns() == 1 && first_record() == RECORD);
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_RANGE && programs == 1);
        le(b, RECORD, 4);
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_RANGE && programs == 1);         /* never ours */
        CHECK(!leave(HRS_START_APP));
        restart(1);
        CHECK(!try_open() && ask(HRS_RETIRE, b, 4) == HRS_E_STATE);
        /* not when ours is not the next one, nor one that is not in the VM, nor with a fault */
        fresh();
        plant(flash, 0xbdf00, 0x90000, 0x1234);
        plant(flash, RECORD, PLACE, 0x1234);
        le(b, 0xbdf00, 4);
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_NO_RETURN && !programs);
        fresh();
        memset(flash + RECORD, 0xff, 80);
        plant(flash, 0xbdf00, 0x90000, 0x1234);
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_NO_RETURN && !programs);
        fresh();
        plant(flash, 0xc7f00, 0x90000, 0x1234);
        le(b, 0xc7f00, 4);
        CHECK(returns() == 0 && first_record() == 0xc7f00 && ask(HRS_RETIRE, b, 4) == HRS_E_RANGE && !programs);
        fresh();
        plant(flash, 0xbdf00, 0x90000, 0x1234);
        le(b, 0xbdf00, 4);
        lazy_program = 1;
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_READBACK && phase() == HRS_FAILED && hrs_untouched() && !leave(HRS_START_APP));
        clear_faults();
        fresh();
        plant(flash, 0xbdf00, 0x90000, 0x1234);
        fail_program = 1;
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_IO && phase() == HRS_FAILED && !hrs_permits(0xbdf00, HRS_PAGE));
        fresh();
        plant(flash, 0xbdf00, 0x90000, 0x1234);
        fail_read = 1;
        CHECK(ask(HRS_RETIRE, b, 4) == HRS_E_IO);
        clear_faults();
    }
    /* nothing to lose: without a whole application it may be opened all the same */
    fresh();
    memset(flash + RECORD, 0xff, 80);
    restart(0);
    CHECK(returns() == 0 && !try_open());
    images();
}

/* A directory at the head of the application, as a TANK-MINI with 011 has it: the VM at vm, vm_size long, PRCT from prct_from,
 * prct long. JieLi's encoding with the chip's key, the records' own CRC-16. */
static void records(uint8_t *f, uint32_t vm, uint32_t vm_size, uint32_t prct_from, uint32_t prct)
{
    static const char *const names[] = {"app_area_head", "app.bin", "cfg_tool.bin", "VM", "PRCT", "BTIF", "USR"};
    uint8_t page[HRS_PAGE];
    uint32_t o, key;
    unsigned i, k;
    memset(page, 0xff, sizeof(page));
    for (k = 0; k < 7; ++k) {
        uint8_t *r = page + 32 * k;
        memset(r, 0, 16);
        le(r + 2, 0xffff, 2);
        le(r + 4, k == 3 ? vm : k == 4 ? prct_from : k == 5 ? HRS_VM_END : k == 6 ? HRS_USER : 0x120 * k, 4);
        le(r + 8, k == 3 ? vm_size : k == 4 ? prct : k == 5 ? HRS_SECTOR : k == 6 ? HRS_USER_END - HRS_USER : 0x1000, 4);
        r[12] = 0x92;
        memset(r + 16, 0xff, 16);
        memcpy(r + 16, names[k], strlen(names[k]) + 1);
        seal(page, 32 * k, 32);
    }
    for (o = 0; o < HRS_PAGE; o += 32)
        for (key = 0x980f ^ (o >> 2), i = 0; i < 32; ++i) {
            f[HRS_APP + o + i] = (uint8_t)(page[o + i] ^ key);
            key = (key << 1 ^ (key & 0x8000 ? 0x1021 : 0)) & 0xffff;
        }
}
/* The application's partition up to vm (PRCT up to prct), the VM from vm to HRS_VM_END. */
static void directory(uint8_t *f, uint32_t vm, uint32_t prct) { records(f, vm, HRS_VM_END - vm, 0, prct); }
static unsigned wide_install(const uint8_t *want, uint32_t to) { uint32_t was = end; unsigned e; end = to; e = install(want); end = was; return e; }
/* The window widened up to the pedal's VM (0x95000, as on a TANK-MINI with 011), and every way it is refused. */
static void wide(void)
{
    unsigned total, k, e;
    directory(before, 0x95000, 0x95000);
    memcpy(target, before, sizeof(target));
    target[HRS_APP + HRS_PAGE] ^= 0x22;                    /* the header changes past its directory */
    target[HRS_APP_END] ^= 1;                              /* the first sector the old window did not have ... */
    target[0x94000 + 77] ^= 0x40;                          /* ... and the last one of the wide window */
    target[0x88000 + 5] ^= 0x10;
    target[0x30000] ^= 2;
    target[HRS_USER + 9] ^= 4;
    /* an old loader's window, unless BEGIN says */
    fresh();
    CHECK(window() == HRS_APP_END && !hrs_writable(HRS_APP_END, HRS_SECTOR));
    {
        static uint8_t now[HRS_CAPACITY];
        uint32_t list[HRS_MAX_SECTORS + 1];
        unsigned windows, n;
        memcpy(now, flash, sizeof(now));
        end = 0x95000;
        n = plan(now, target, list, &windows, 0);
        end = HRS_APP_END;
        CHECK(!begin_to(now, target, n, windows, HRS_APP_END, 0) && !open_app(now));      /* the old BEGIN: 0x82000 is not in it */
        CHECK(write(HRS_APP_END, now, target) == HRS_E_RANGE && write(0x94000, now, target) == HRS_E_RANGE && erases == 1);
    }
    /* widened as the directory says: written, checked, reported */
    fresh();
    CHECK(!wide_install(target, 0x95000) && !memcmp(flash, target, sizeof(flash)) && window() == 0x95000);
    CHECK(hrs_writable(0x94000, HRS_SECTOR) && !hrs_writable(0x95000, HRS_SECTOR) && !hrs_writable(0x94000, HRS_SECTOR + 1));
    CHECK(!leave(HRS_START_APP));
    restart(1);
    CHECK(!wide_install(before, 0x95000) && !memcmp(flash, before, sizeof(flash)));          /* and back */
    /* the application alone, the wide part with it: BEGIN names the application's window only */
    {
        static uint8_t app_only[HRS_CAPACITY];
        memcpy(app_only, target, sizeof(app_only));
        memcpy(app_only + HRS_USER, before + HRS_USER, HRS_USER_END - HRS_USER);
        fresh();
        CHECK(!wide_install(app_only, 0x95000) && !memcmp(flash, app_only, sizeof(flash)));
    }
    /* refused before anything is read or written: a BEGIN of another length, not whole sectors, too narrow, too wide, not what
     * the directory says */
    {
        uint8_t m[24];
        memset(m, 0, sizeof(m));
        le(m + 11, HRS_MAGIC, 4);
        le(m + 15, 0x95000, 4);
        fresh();
        for (k = 16; k <= 24; ++k) if (k != 19) CHECK(ask(HRS_BEGIN, m, k) == HRS_E_FRAME && phase() == HRS_READY);
        le(m + 11, HRS_MAGIC ^ 1, 4);
        CHECK(ask(HRS_BEGIN, m, 19) == HRS_E_FRAME);
    }
    {
        static const uint32_t bad[] = {0x95001, 0x94fff, 0x81000, 0x4000, 0, 0xa1000, 0xbe000, 0xffffffffu};
        static const uint32_t other[] = {0x96000, 0x94000, 0xa0000, 0x83000};
        for (k = 0; k < sizeof(bad) / sizeof(*bad); ++k) {
            fresh();
            CHECK(begin_to(flash, target, 4, 3, bad[k], 1) == HRS_E_RANGE && phase() == HRS_READY && window() == HRS_APP_END);
        }
        for (k = 0; k < sizeof(other) / sizeof(*other); ++k) {
            fresh();
            CHECK(begin_to(flash, target, 4, 3, other[k], 1) == HRS_E_RANGE && phase() == HRS_READY && !erases && !programs);
        }
    }
    /* a 009 pedal: its VM starts at 0x82000, widening would write into its settings; the old window is still fine */
    fresh();
    directory(flash, HRS_APP_END, HRS_APP_END);
    CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_RANGE && !begin_to(flash, flash, 1, 3, HRS_APP_END, 1));
    /* a PRCT record that says otherwise; a VM record whose CRC is wrong is no record (PRCT still decides) */
    fresh();
    directory(flash, 0x95000, 0x96000);
    CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_RANGE);
    fresh();
    directory(flash, 0x96000, 0x95000);
    flash[HRS_APP + 96 + 20] ^= 1;
    CHECK(!begin_to(flash, target, 4, 3, 0x95000, 1));
    fresh();
    directory(flash, 0x96000, 0x95000);
    CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_RANGE);
    fresh();
    records(flash, 0x96000, HRS_VM_END - 0x95000, 0, 0x95000);          /* the VM's place says otherwise, its length does not */
    CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_RANGE);
    fresh();
    records(flash, 0x95000, HRS_VM_END - 0x96000, 0, 0x95000);          /* its length says otherwise */
    CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_RANGE);
    fresh();
    records(flash, 0x95000, HRS_VM_END - 0x95000, HRS_SECTOR, 0x95000); /* PRCT does not start at 0 */
    CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_RANGE);
    /* without the chip's key the directory cannot be read: not widened */
    {
        hrs_unit u = {HRS_JEDEC, 0, 1, 1, "nokey"};
        fresh();
        hrs_start(&nor, &u);
        CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_RANGE && !begin_to(flash, target, 4, 3, HRS_APP_END, 1));
        fresh();
        memset(flash + HRS_APP, 0xff, HRS_SECTOR);
        hrs_start(&nor, &u);
        CHECK(!begin_to(flash, target, 4, 3, 0x95000, 1));                 /* a blank header needs no key */
    }
    /* a blank header says nothing: then the bounds alone decide */
    {
        static const uint32_t bad[] = {0x95001, 0x81000, 0xa1000, 0xbe000};
        for (k = 0; k < sizeof(bad) / sizeof(*bad); ++k) {
            fresh();
            memset(flash + HRS_APP, 0xff, HRS_SECTOR);
            restart(0);
            CHECK(begin_to(flash, target, 4, 3, bad[k], 1) == HRS_E_RANGE && phase() == HRS_READY);
        }
        fresh();
        memset(flash + HRS_APP, 0xff, HRS_SECTOR);
        restart(0);
        CHECK(!begin_to(flash, target, 4, 3, HRS_APP_END_MAX, 1));
    }
    /* the way back must lie above the window: the record the bootloader finds first, and the loader it leads to */
    fresh();
    memset(flash + PLACE, 0xff, 64);
    plant(flash, RECORD, 0x90000, HRS_LOADER_CRC);
    CHECK(returns() == 1 && begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_NO_RETURN && phase() == HRS_READY);
    fresh();
    memset(flash + RECORD, 0xff, 80);
    CHECK(begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_NO_RETURN);
    fresh();
    plant(flash, 0xbdf00, 0xb9000, 0x1234);                                /* another loader's record, found first */
    CHECK(returns() == 0 && begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_NO_RETURN);
    fresh();
    memset(flash + RECORD, 0xff, 80);
    plant(flash, 0x93f00, PLACE, HRS_LOADER_CRC);
    CHECK(returns() == 1 && first_record() == 0x93f00 && begin_to(flash, target, 4, 3, 0x95000, 1) == HRS_E_NO_RETURN);
    /* a header with no directory (blank, or an installation cut while it was erased): the bounds and the way back decide */
    fresh();
    memset(flash + HRS_APP, 0xff, HRS_SECTOR);
    restart(0);
    CHECK(!wide_install(target, 0x95000) && !memcmp(flash, target, sizeof(flash)));
    /* power gone at each operation of a wide installation; a new session with the same window finishes it, or goes back */
    end = 0x95000;
    fresh();
    CHECK(!install(target));
    total = operations;
    for (k = 1; k <= total; ++k) {
        fresh();
        cut_at = k;
        e = install(target);
        CHECK(e && cut && outside_same());
        clear_faults();
        restart(0);
        CHECK(returns() == 1 && leave(HRS_START_APP) == HRS_E_NO_APP);
        CHECK(!install(target) && !memcmp(flash, target, sizeof(flash)) && window() == 0x95000 && !leave(HRS_START_APP));
        fresh();
        cut_at = k;
        CHECK(install(target));
        clear_faults();
        restart(0);
        CHECK(!install(before) && !memcmp(flash, before, sizeof(flash)) && !leave(HRS_START_APP));
    }
    end = HRS_APP_END;
    printf("wide window: power cut at each of %u flash operations, forwards and back\n", total);
    images();
}

int main(void)
{
    images();
    good_path();
    way_back();
    refusals();
    images();
    windows();
    repeats();
    power_cuts();
    faults();
    wide();
    printf("engine tests passed\n");
    return 0;
}
