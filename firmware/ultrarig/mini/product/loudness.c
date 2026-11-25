/* The measure of loudness: what the editor needs to give every preset and scene the same volume (docs/MINI_LOUDNESS.md).
 *
 * The same stroke of a guitar is played into the input of each preset while the output is silent, and the loudness at the end of the
 * chain is measured: after the second section and the global equalizer, before the output gain, the wheel and the limiter. The weighting
 * is that of BS.1770; what comes out are the energies of slices of 512 samples, and the editor makes the loudest 400 ms of them. The
 * strokes are the player's own: recorded here, at a quarter of the rate and in four bits a sample, kept by the editor, and played again.
 *
 * It is small because the editor does what it can, with the firmware's own diagnostic words: REC 4 takes the memory that everything here
 * is in and RECD reads it, INJBEGIN takes the memory of a stroke and INJB fills it. What it does is the stage of REC (S + 25): its own are
 * 1 to 4, these are 5 to 7. The word HRLV has one operation, in hexadecimal bytes, and answers "HRLV <result> <codes or slices there>";
 * without one it only says that the editor is there:
 *
 *   01                                                       ends it
 *   02 <preset> <gain> <gain of scene 1> ... <of scene 8>    writes output gains into a stored preset, 7f for one that stays
 *   05                                                       records the input
 *   06 <blocks of a play> <plays> <blocks before> <slices>   plays the stroke and measures
 *
 * A press of a footswitch and four seconds without a word end it as well. Then the preset and the scene of the beginning come back, and
 * the sound. HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

/* What runs for every block of sound is in the RAM, with its numbers: a flash that is being written has nothing to give. */
#define SOUND __attribute__((section(".ram_text")))
#define TABLE __attribute__((section(".data")))
#include "loudness_tables.h"

enum { BLOCK = 128, SMALL = BLOCK / 4, SLICE_BLOCKS = 4, UP = 2 * PAIRS - 1, DOWN = 4 * PAIRS - 2 };
enum { HEAD = 32, RING = 1024, CODES = 8 * RING };           /* words before the energies or the codes; words of codes, and codes */
enum { NOTHING, END, GAINS, RECORD = 5, MEASURE, SILENT };   /* MEASURE and SILENT: the output gain is 0 (in the application's audio task) */
enum { TURNS = 400, KEEP = 127, SCENES = 8, AT_OUT = 5, SCENE_OUT = 3, LAST_STEP = 87, LARGEST = 30000 };
enum { S_STAGE = 25, S_STROKE = 312, S_MEMORY = 456, G_SCENE = 88, G_PRESET = 92 };

extern uint8_t L01c26890[], L01c1f180[], L01c24790[];         /* the application's state, its settings, and its working preset */
extern int32_t L01c23f68[];                                   /* the second channel: 48 words of history, then the block */
extern void bond_records_and_prints_print_b(const char *format, ...);
extern int bond_records_and_prints_hex_value(int c);
extern void effect_enable_memset(void *to, int value, uint32_t bytes);
extern void dispatch_helpers_buffer_release(void);            /* REC free: the stage is 0, then it waits for the audio, then the memory */
extern void dispatch_helpers_scope_buffer(int halfwords);     /* INJBEGIN, or INJ free */
extern void L0203feb8(unsigned turns);                        /* waits, ten milliseconds a turn */
extern int preset_loader_load(unsigned preset);
extern int scene_application_apply(unsigned scene);
extern int command_services_save_word(unsigned preset, unsigned colour);
uint8_t *hyperrig_scene_block(unsigned scene);
int hyperrig_level(const char *rest);
int hyperrig_level_end(void);
void hyperrig_level_turn(void);
int hyperrig_gains(void);
void hyperrig_level_input(int32_t *block);
void hyperrig_level_output(const int32_t *block, unsigned stereo);

/* In the memory of REC, as RECD shows it: the editor looks at the first three words. */
struct session {
    volatile uint32_t done;              /* slices, or codes */
    int32_t peak;
    volatile uint32_t running;
    uint8_t length, plays, before, total;             /* the operation: blocks, times, blocks, slices */
    uint32_t block, part;                /* of the run; of the slice */
    int32_t guess, step;                 /* of the codes */
    float sum, weight[2][4];
    int32_t past[UP], unused[4];         /* the last samples of a stroke, for the way up */
    union {
        float energy[1];
        uint8_t codes[CODES / 2];
        int32_t word[RING + DOWN + 2 * SMALL];       /* RECORD: after the ring, the last samples of the input and the block */
    } u;
};
_Static_assert(__builtin_offsetof(struct session, u) == 4 * HEAD, "the editor counts on it");

#define STAGE (*(volatile uint8_t *)(L01c26890 + S_STAGE))
#define SETTING(at) (*(volatile int32_t *)(L01c1f180 + (at)))
#define LIMIT (*(volatile uint32_t *)(L01c26890 + S_MEMORY + 8))
#define SESSION (*(struct session *volatile *)(L01c26890 + S_MEMORY))
#define STROKE (*(const uint8_t *volatile *)(L01c26890 + S_STROKE))

static struct {
    int32_t preset, scene;               /* of the beginning */
    const int8_t *gains;                 /* that a preset gets */
    uint32_t left;                       /* turns until it ends by itself; 0 when it is not used */
} kept;

TABLE static const uint8_t steps[8] = { 16, 17, 19, 21, 23, 25, 27, 29 };
TABLE static const int8_t moves[8] = { -1, -1, -1, -1, 2, 4, 6, 8 };

/* A sample is the one before and a difference in steps; the step follows the size of the differences. With code < 0: the code of v. */
SOUND static int step_on(struct session *s, int code, int v)
{
    int size = steps[s->step & 7] << (s->step >> 3), d = v - s->guess;
    if (code < 0) {
        code = (d < 0 ? -d : d) * 4 / size;
        code = (code > 7 ? 7 : code) | (d < 0 ? 8 : 0);
    }
    d = size * (2 * (code & 7) + 1) >> 3;
    v = s->guess + (code & 8 ? -d : d);
    s->guess = v > LARGEST ? LARGEST : v < -LARGEST ? -LARGEST : v;
    d = s->step + moves[code & 7];
    s->step = d < 0 ? 0 : d > LAST_STEP ? LAST_STEP : d;
    return code;
}

/* The half-band: what the pairs around a place make. */
SOUND __attribute__((noinline)) static int32_t half(const int32_t *p, const int32_t *q, int step)
{
    int32_t sum = 0;
    for (int k = 0; k < PAIRS; ++k, p -= step, q += step)
        sum += halfband[k] * (*p + *q);
    return sum;
}

/* Every block of the input, before anything else looks at it, in one of the three stages. */
SOUND void hyperrig_level_input(int32_t *x)
{
    struct session *s = SESSION;
    int32_t w[UP + SMALL], *v = w;
    const uint8_t *from;
    uint32_t n, at;
    if (STAGE == RECORD) {
        /* to a quarter of the rate, the mean of two samples and the half-band, into the ring of codes */
        v = s->u.word + RING;
        for (n = 0; n < DOWN + 2 * SMALL; ++n)
            if (n < DOWN)
                v[n] = v[n + 2 * SMALL];
            else {
                v[n] = (x[0] >> 16) + (x[1] >> 16);
                x += 2;
            }
        for (n = 0; n < SMALL; ++n, v += 2) {
            uint8_t *to = s->u.codes + (s->done % CODES + n) / 2;
            int code = step_on(s, -1, ((v[DOWN / 2] << 15) + half(v + DOWN / 2 - 1, v + DOWN / 2 + 1, 2)) >> 16);
            *to = n & 1 ? *to | code << 4 : code;
        }
        s->done += SMALL;
        return;
    }
    /* a block of the stroke, or of silence, in place of the input: the half-band, and a straight line between two samples */
    at = s->block - s->before;
    n = s->running && at < s->length * s->plays;
    s->block += s->running;
    from = STROKE;
    if (!n)
        from = 0;
    if (from) {
        at %= s->length;
        if (!at)
            s->guess = s->step = 0;
        from += at * (SMALL / 2);
    }
    for (n = 0; n < UP + SMALL; ++n) {
        if (n < UP)
            w[n] = s->past[n];
        else {
            w[n] = 0;
            if (from) {
                step_on(s, from[(n - UP) / 2] >> (n - UP & 1 ? 4 : 0) & 15, 0);
                w[n] = s->guess;
            }
        }
        if (n >= SMALL)
            s->past[n - SMALL] = w[n];
    }
    for (n = 0; n < SMALL; ++n, ++v) {
        int32_t here = v[PAIRS - 1] << 14, next = v[PAIRS] << 14, between = half(v + PAIRS - 1, v + PAIRS, 1) >> 1;
        *x++ = here << 1;
        *x++ = here + between;
        *x++ = between << 1;
        *x++ = between + next;
    }
}

/* The energy of a block after the weighting. */
SOUND static float weigh(struct session *s, float *z, const int32_t *x)
{
    float a = z[0], b = z[1], c = z[2], d = z[3], sum = 0.0f;
    int32_t n = BLOCK;
    do {
        int32_t i = *x++;
        float v = (float)i, y = v + a;
        i = i < 0 ? -i : i;
        if (i > s->peak)
            s->peak = i;
        a = SHELF_B1 * v - SHELF_A1 * y + b;
        b = SHELF_B2 * v - SHELF_A2 * y;
        v = y + c;
        c = d - (y + y) - HIGH_A1 * v;
        d = y - HIGH_A2 * v;
        sum += v * v;
    } while (--n);
    z[0] = a, z[1] = b, z[2] = c, z[3] = d;
    return sum;
}

/* Every block at the end of the chain, while the output is silent; with a second channel the mean of the two. */
SOUND void hyperrig_level_output(const int32_t *block, unsigned stereo)
{
    struct session *s = SESSION;
    if (!s->running)
        return;
    float energy = weigh(s, s->weight[0], block);
    if (stereo)
        energy = 0.5f * (energy + weigh(s, s->weight[1], L01c23f68 + 48));
    s->sum += energy;
    if (++s->part < SLICE_BLOCKS)
        return;
    s->u.energy[s->done] = s->sum * (ENERGY / (SLICE_BLOCKS * BLOCK));
    s->sum = 0.0f;
    s->part = 0;
    if (++s->done == s->total)
        s->running = 0;
}

/* The rest is not for the audio. */

/* Ends it, when it is used: nonzero. The preset and the scene of the beginning come back while the output is still silent, if they are not the
 * ones that play; its memory is given back. */
int hyperrig_level_end(void)
{
    struct session *s = SESSION;
    if (!kept.left)
        return 0;
    kept.left = 0;
    if (s) {
        s->running = 0;
        if (STAGE == MEASURE)
            STAGE = SILENT;
    }
    if (STROKE)
        dispatch_helpers_scope_buffer(0);
    if (SETTING(G_PRESET) != kept.preset || SETTING(G_SCENE) != kept.scene)
        preset_loader_load(kept.preset);
    if (kept.scene >= 0 && SETTING(G_PRESET) == kept.preset && SETTING(G_SCENE) != kept.scene)
        scene_application_apply(kept.scene);
    dispatch_helpers_buffer_release();
    return 1;
}

/* Once in each turn of the control scan, ten milliseconds or more. */
void hyperrig_level_turn(void)
{
    if (kept.left == 1)
        hyperrig_level_end();
    else if (kept.left)
        --kept.left;
}

/* Output gains into the working preset that a stored one was read into, before it is written back: the one it starts with, and those of
 * its scenes. 0 when it is the colour that changes. */
int hyperrig_gains(void)
{
    const int8_t *g = kept.gains;
    if (!g)
        return 0;
    for (int k = -1; k < SCENES; ++k, ++g)
        if (*g != KEEP)
            *(k < 0 ? L01c24790 + AT_OUT : hyperrig_scene_block(k) + SCENE_OUT) = *g;
    return 1;
}

/* The console word HRLV and the rest of its line. The result is 0, or of the saving, or the operation that was not done: a byte of a line
 * can be lost on the way, and the memory may not be there, or not any more. */
int hyperrig_level(const char *p)
{
    struct session *s = SESSION;
    uint32_t words[4];
    uint8_t *a = (uint8_t *)words + 3, *to = a;
    int result;
    *a = NOTHING;
    for (; p[0] && p[1] && to < a + 13; p += 2)
        *to++ = bond_records_and_prints_hex_value(p[0]) << 4 | bond_records_and_prints_hex_value(p[1]);
    result = *a;
    if (result == END) {
        hyperrig_level_end();
        result = 0;
    } else if (result == GAINS) {
        if (to == a + 11) {
            kept.gains = (const int8_t *)a + 2;
            result = command_services_save_word(a[1], 0);
            kept.gains = 0;
        }
    } else {
        if (!kept.left)
            kept.preset = SETTING(G_PRESET), kept.scene = SETTING(G_SCENE);
        kept.left = TURNS;
        if (result >= RECORD && s && LIMIT >= (result == RECORD ? sizeof(struct session) / 4 : HEAD + a[4])) {
            s->running = 0;
            STAGE = SILENT;
            L0203feb8(2);                        /* the audio is done with the block it was in */
            effect_enable_memset(s, 0, 4 * HEAD);
            *(uint32_t *)&s->length = words[1];
            __asm__ volatile("csync" ::: "memory");
            s->running = 1;
            STAGE = result;
            result = 0;
        }
    }
    s = SESSION;
    bond_records_and_prints_print_b("HRLV %d %d\n", result, s ? s->done : -1);
    return 1;
}
