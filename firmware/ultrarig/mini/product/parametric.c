/* NAM captures that keep some knobs of what they were made of (docs/PARAMETRIC_NAM.md). The engine is the application's own, unchanged: with the
 * knobs at rest such a network is a plain A2-Lite whose numbers were made for that place of the knobs. A stored capture is the plain one at the
 * middle of the knobs and, behind it, how its numbers move: along at most eight directions, and how far along each one, a small hidden layer says.
 *
 * The knobs are the amp's own controls (AMPEQ: Gain, Bass, Mid, Treble, Presence): what the preset and its scenes keep of them, and what moves
 * them, is as ever. A control that has a knob of the capture leaves its filter, or the gain, flat and moves the knob: -120 is one end of it,
 * 0 its usual place and 120 the other end. At 0 the capture plays exactly as it was stored.
 *
 * Two sides. The application's tasks read the extension, and say for each number where it goes and in which steps (hyperrig_tone). The sound task
 * takes the steps, half of the numbers in each half block, where the second core waits and nobody reads them (hyperrig_capture_turn). The flash is
 * short: this is written for size. HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code
 * has been made. */
#include <stdint.h>

/* What runs for every block of sound is in the RAM, as the sound code of the application is. */
#define SOUND __attribute__((section(".ram_text")))
#define ONCE __attribute__((noinline))
/* What was written is there for the sound task before what follows. */
#define SETTLED __asm__ volatile("csync" : : : "memory")

enum { MAGIC = 0x31503241, TAIL = 0x5041, VERSION = 1, HEADER = 12, KNOB = 26, GROUPS = 71, NUMBERS = 388, TAIL_BYTES = 8 };
enum { AT_VERSION = 4, AT_KNOBS = 5, AT_UNITS = 6, AT_DIRECTIONS = 7, AT_SLOPE = 8 };
enum { LAYERS = 23, CHANNELS = 3, TAPS = 16, KNOBS = 5, UNITS = 24, DIRECTIONS = 8, TONES = 6, FIRST_HALF = 12 };
enum { SMALLEST = 44, END = 120, DRIVE = 5, TONE_AT = 218, SOURCE_AT = 60, SHAPE = 0x10032010 };
enum { CTX_LAYERS = 8, CTX_RECH = 60, CTX_HEAD = 68, CTX_BIAS = 72, CTX_TABLE = 92, ENGINE = 76 };
enum { D_KERNEL = 0, D_MATRIX = 32, D_PACKED = 44, D_BIAS = 52, D_SIZE = 80 };

extern uint8_t L01c1f180[];                               /* the application's settings: what plays, and its length */
extern uint8_t L01c1f7e0[];                               /* how long a change of the amp's controls takes, in blocks */
extern uint8_t L01c2bff0[];                               /* the engine: its context is at 76 */
extern uint8_t L01c32db0[];                               /* the amp's controls, six halfwords at 218 */
extern uint8_t L01c3446c[];                               /* who hears of the amp's gain */
extern void *L0203c15c(uint32_t bytes);                   /* gives memory, or 0 */
extern void L0203d218(void *memory);                      /* takes it back */
extern int dsp_transition_request(const int16_t *tones, int blocks);
extern void link_and_print_print(const char *format, ...);

/* A number of the engine: as it was loaded, where it goes, where it is, its step. */
struct number {
    int32_t base, goal, now, step;
};

static struct {
    struct number *number, *next;                         /* those that move, in the order of the form, or 0; the one that is next */
    const uint8_t *shift, *b;                             /* what is next in the extension */
    int32_t c[DIRECTIONS];                                /* how far along each direction */
    uint32_t identity, parsed;                            /* the last word of the capture in the engine, and of the one that was read last; 0 without knobs */
    int32_t blocks;
    int16_t drive;                                        /* the gain that was last told */
    volatile uint8_t live, left;                          /* the sound task may look at what is here; steps still to take */
    uint8_t directions, part;                             /* the half of the numbers that is next */
} move;
uint8_t hyperrig_tone_due;                                /* dsp_transition_request goes through although the six tones are as they were */

ONCE static unsigned half(const uint8_t *p)
{
    return p[0] | p[1] << 8;
}

ONCE static int signed_half(const uint8_t *p)
{
    return (int16_t)half(p);
}

ONCE static uint32_t word(const uint8_t *p)
{
    return half(p) | half(p + 2) << 16;
}

/* The bytes of the extension behind a capture, 0 when it has none that this firmware knows. */
static uint32_t extension(const uint8_t *source, uint32_t length)
{
    if (length < SMALLEST + HEADER + TAIL_BYTES || half(source + length - 6) != TAIL)
        return 0;
    uint32_t size = half(source + length - 8);
    const uint8_t *e = source + length - size;
    if (size > length - SMALLEST || word(e) != MAGIC || e[AT_VERSION] != VERSION)
        return 0;
    unsigned knobs = e[AT_KNOBS], units = e[AT_UNITS], directions = e[AT_DIRECTIONS];
    if (knobs - 1 >= KNOBS || units > UNITS || directions - 1 >= DIRECTIONS ||
        size != HEADER + KNOB * knobs + GROUPS + units * (3 + 2 * knobs) + directions * (3 + 2 * units + NUMBERS) + TAIL_BYTES)
        return 0;
    for (e += HEADER; knobs; --knobs, e += KNOB)
        if (e[0] - 1u >= DRIVE)
            return 0;
    return size;
}

/* When the application reads a capture: the length of the plain one, the only part it knows. */
uint32_t hyperrig_capture_length(const uint8_t *source, uint32_t length)
{
    uint32_t size = extension(source, length);
    move.parsed = size ? word(source + length - 4) : 0;
    return length - size;
}

/* A capture is in the engine, as it was stored. The sound is stopped here, and the application has not yet said which capture plays. */
void hyperrig_capture_loaded(void)
{
    hyperrig_tone_due = move.live || move.parsed;
    move.live = 0;
    SETTLED;
    if (move.number)
        L0203d218(move.number);
    move.number = 0;
    move.identity = move.parsed;
}

/* The numbers of the engine, in the order in which they are stored: for each layer its biases, what it takes of the dry sound and its matrix (what the
 * last one gives goes nowhere), then the way in, the head and the bias of the head. many numbers of wide bytes are at one place. */
typedef void action(void *at, unsigned wide, unsigned many);

SOUND static void walk(unsigned from, unsigned end, action *act)
{
    uint8_t *context = L01c2bff0 + ENGINE, *d = *(uint8_t **)(context + CTX_TABLE) + D_SIZE * from;
    for (; from < end; ++from, d += D_SIZE) {
        act(d + D_BIAS, 4, CHANNELS);
        act(*(int16_t **)(d + D_PACKED) + CHANNELS * CHANNELS * d[D_KERNEL], 2, CHANNELS);
        if (from < LAYERS - 1)
            act(*(void **)(d + D_MATRIX), 2, CHANNELS * CHANNELS);
    }
    if (end < LAYERS)
        return;
    act(*(void **)(context + CTX_RECH), 2, CHANNELS);
    act(*(void **)(context + CTX_HEAD), 2, TAPS * CHANNELS);
    act(context + CTX_BIAS, 8, 1);
}

/* From the flash, which is too far for a plain call. */
ONCE static void walk_all(action *act)
{
    void (*far)(unsigned, unsigned, action *) = walk;
    __asm__("" : "+r"(far));
    move.next = move.number;
    far(0, LAYERS, act);
}

SOUND static void take(void *at, unsigned wide, unsigned many)
{
    struct number *n = move.next;
    unsigned last = move.left == 1;
    int32_t *words = at, v;
    int16_t *halves = at;
    do {
        n->now = v = last ? n->goal : n->now + n->step;
        ++n;
        if (wide == 2)
            *halves++ = (int16_t)v;
        else
            *words++ = v;
    } while (--many);
    if (wide == 8)
        *words = v >> 31;
    move.next = n;
}

/* In each half block of sound, after the wait for the second core and before its next work: nobody reads the numbers now. */
SOUND void hyperrig_capture_turn(void)
{
    if (!move.live || !move.left)
        return;
    if (!move.part) {
        move.next = move.number;
        walk(0, FIRST_HALF, take);
    } else {
        walk(FIRST_HALF, LAYERS, take);
        --move.left;
    }
    move.part ^= 1;
}

/* The numbers as they were loaded. */
static void load(void *at, unsigned wide, unsigned many)
{
    struct number *n = move.next;
    int32_t *words = at;
    int16_t *halves = at;
    do {
        n->base = n->now = wide == 2 ? *halves++ : *words++;
        ++n;
    } while (--many);
    move.next = n;
}

/* Where the numbers go, and in which steps. */
static void aim(void *at, unsigned wide, unsigned many)
{
    struct number *n = move.next;
    int s = (int8_t)*move.shift++;
    do {
        int32_t sum = 0;
        for (unsigned k = 0; k < move.directions; ++k)
            sum += move.c[k] * (int8_t)*move.b++;
        n->goal = n->base + (s > 0 ? sum >> s : sum * (1 << -s));
        n->step = (n->goal - n->now) / move.blocks;
        ++n;
    } while (--many);
    move.next = n;
    (void)at, (void)wide;
}

/* Rows of a shift, a bias (of 16384) and weights, one after the other. Whole numbers: the editor makes the same of them. */
static const uint8_t *rows(const uint8_t *w, unsigned many, const int32_t *in, unsigned ins, int32_t *out)
{
    for (; many; --many) {
        unsigned shift = *w++, k;
        int64_t sum = (int64_t)signed_half(w) << 14;
        for (k = 0; k < ins; ++k)
            sum += (int64_t)signed_half(w += 2) * in[k];
        w += 2;
        *out++ = (int32_t)((sum + ((int64_t)1 << (shift - 1))) >> shift);
    }
    return w;
}

/* The extension of the capture that plays, when it is the one in the engine; 0 else. */
static const uint8_t *playing(void)
{
    const uint8_t *source = *(const uint8_t **)(L01c1f180 + SOURCE_AT);
    uint32_t length = *(uint32_t *)(L01c1f180 + SOURCE_AT + 4), size = move.identity ? extension(source, length) : 0;
    return size && word(source + length - 4) == move.identity ? source + length - size : 0;
}

/* In place of the part of dsp_transition_request that keeps the six tones and tells the gain. tones: as they are asked; afterwards as the filters and
 * the gain take them, flat where a knob of the capture is moved instead. */
void hyperrig_tone(int16_t *tones, int blocks)
{
    uint8_t *context = L01c2bff0 + ENGINE;
    int16_t *kept = (int16_t *)(L01c32db0 + TONE_AT);
    uint32_t tell = *(uint32_t *)L01c3446c;
    const uint8_t *e = playing(), *q;
    int32_t x[KNOBS], phi[UNITS];
    unsigned k;
    for (k = 0; k < TONES; ++k)
        kept[k] = tones[k];
    if (hyperrig_tone_due && (e || !move.identity)) {     /* not before the application says what plays */
        hyperrig_tone_due = 0;
        if (e && *(uint32_t *)context == SHAPE && *(uint16_t *)(context + CTX_LAYERS) == LAYERS) {
            move.number = L0203c15c(NUMBERS * sizeof(struct number));
            if (move.number) {                            /* without memory it plays as it was stored, and its controls are the amp's own */
                walk_all(load);
                move.left = 0;
                move.live = 1;
            }
        }
    }
    if (move.live && e) {
        for (q = e + HEADER, k = 0; k < e[AT_KNOBS]; ++k, q += KNOB) {
            int mid = signed_half(q + 22), v = tones[q[0]];
            tones[q[0]] = 0;
            v = v < -END ? -END : v > END ? END : v;
            x[k] = mid + (v < 0 ? mid - signed_half(q + 20) : signed_half(q + 24) - mid) * v / END;
        }
        move.shift = q;
        q = rows(q + GROUPS, e[AT_UNITS], x, k, phi);
        for (k = 0; k < e[AT_UNITS]; ++k)
            if (phi[k] < 0)
                phi[k] = phi[k] * (int)half(e + AT_SLOPE) >> 10;
        move.left = 0;                                    /* the sound task does not look at the numbers now */
        SETTLED;
        move.directions = e[AT_DIRECTIONS];
        move.b = rows(q, move.directions, phi, k, move.c);
        move.blocks = blocks < 1 ? 1 : blocks > 255 ? 255 : blocks;
        walk_all(aim);
        move.part = 0;
        SETTLED;
        move.left = (uint8_t)move.blocks;
    }
    if (tones[DRIVE] != move.drive) {
        move.drive = tones[DRIVE];
        if (tell)
            ((void (*)(int))tell)(move.drive);
    }
}

/* Once in each turn of the control scan: a capture came or went, and its controls are to be taken over or given back. */
void hyperrig_parametric_turn(void)
{
    if (hyperrig_tone_due)
        dsp_transition_request((const int16_t *)(L01c32db0 + TONE_AT), L01c1f7e0[0]);
}

/* AMPK: the knobs of the capture that plays, each as it is stored, in hexadecimal digits. */
void hyperrig_amp_knobs(void)
{
    const uint8_t *e = move.live ? playing() : 0, *q = e + HEADER;
    char line[2 * KNOB + 1];
    for (unsigned i = e ? e[AT_KNOBS] : 0, k; i; --i) {
        for (k = 0; k < 2 * KNOB; ++k) {
            unsigned digit = k & 1 ? *q++ & 15 : *q >> 4;
            line[k] = (char)(digit + (digit > 9 ? 'a' - 10 : '0'));
        }
        line[k] = 0;
        link_and_print_print("AMPK %s\n", line);
    }
    link_and_print_print("AMPK end\n");
}
