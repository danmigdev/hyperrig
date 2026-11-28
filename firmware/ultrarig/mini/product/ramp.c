/* Hold to ramp: while a switch is held, a knob of a block goes from where the preset has it to a target, in a rise time; let go,
 * it goes back in a fall time, from wherever it got to.
 *
 * A switch has a ramp when the hold of its actions (the table at G_ACTIONS: tap, hold and double press, three bytes each) is
 * ACTION_RAMP, in the layouts with actions (Stomp, Scenes, Custom). The application does nothing with that action. A press of
 * such a switch, alone, is kept from the application (and from pairs.c) for DELAY_MS, or for QUICK_MS, a pair's wait, when its tap
 * and its double press do nothing. Let go sooner, the press goes on with its own time and then its release: a tap, a double press,
 * as before, also for a switch that fires on the press. Held, it is the ramp's, and the application never sees it: no tap, no
 * hold. Another switch pressed meanwhile lets the kept press go on first, so two together are a pair as before. With the tuner
 * on, a press is not kept: it closes the tuner.
 *
 * A tap that is ACTION_LATCH is the same ramp on and off: a press, alone, after QUICK_MS or let go sooner, sends it to its target,
 * where it stays; the next sends it back. Every press of that switch is the ramp's; with the tuner on, it closes the tuner, which the
 * application, knowing no such action, would not.
 *
 * The block is the first of its kind in the chain, so one setting serves every preset; a preset without one has nothing to ramp.
 * A preset or a scene that changes ends the ramp: its own values stand. The knob is set as MIDI's controllers set it, with a short
 * glide, in each turn of the control scan; the editor hears of it every TELL_MS and at the end.
 *
 * The settings, one ramp for each switch, are kept by GSAVE behind MIDI's in the record TKGX (midi.c).
 *
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

enum { SWITCHES = 3, PLACES = 16, DELAY_MS = 200, QUICK_MS = 45, STEP_MS = 50, FULL = 4096, TELL_MS = 100, GLIDE = 4 };
enum { S_TUNER = 52, S_LAYOUT = 74, G_SCENE = 88, G_PRESET = 92, G_ACTIONS = 236, ACTION_RAMP = 11, ACTION_LATCH = 12, EVENT_PARAMETER = 112 };
enum { HOLD = 1, LATCH = 2 };
enum { BYTES = 6 };

extern uint8_t L01c26890[], L01c1f180[];
extern void bond_records_and_prints_print_b(const char *format, ...);
extern void selection_effect_flatten(uint8_t *count_and_types, uint8_t *slots);
extern int preset_application_effect_type(unsigned slot);
extern const int16_t *preset_application_metadata(unsigned type, unsigned parameter);      /* the lowest, the highest, ... */
extern int preset_application_parameter(unsigned slot, unsigned parameter);
extern int dispatch_helpers_parameter_apply(unsigned slot, unsigned parameter, int value, unsigned glide);
extern void panel_inputs_event_queue(unsigned kind, unsigned a, unsigned b);

void hyperrig_pairs_transition(unsigned raw, unsigned level, unsigned tick, unsigned ms);       /* pairs.c */
int hyperrig_ramp_transition(unsigned f, unsigned raw, unsigned level, unsigned tick, uint32_t ms);
void hyperrig_ramp_turn(uint32_t now);
int hyperrig_ramp_console(const char *rest);
void hyperrig_ramp_export(uint8_t *to);
void hyperrig_ramp_import(const uint8_t *from);

/* The kind of block (as the application numbers them), the knob from 0, where it goes, and the times in steps of STEP_MS. */
static struct setting {
    uint8_t kind, knob;
    uint8_t target[2];                                    /* little end first */
    uint8_t rise, fall;
} set[SWITCHES];
_Static_assert(sizeof set == SWITCHES * BYTES, "the stored form");
_Static_assert(FULL == 1 << 12, "the shift in step");

static struct run {
    uint32_t since, tick, at, told;                       /* the press, in ms and ticks; the last step; when the editor last heard */
    int32_t preset, scene;                                /* when the ramp began */
    int32_t from, target, last;
    int32_t way;                                          /* how far it is, of FULL */
    uint8_t slot, knob, raw;
    uint8_t down;                                         /* the switch is held */
    uint8_t kept;                                         /* its press is kept from the application, for now */
    uint8_t owned;                                        /* this press is the ramp's */
    uint8_t latched;                                      /* a ramp on and off that is on */
    uint8_t active, untold;
} run[SWITCHES];
static uint8_t down;                                      /* a bit for each switch that is held */

static int32_t word(unsigned at)
{
    return *(volatile int32_t *)(L01c1f180 + at);
}

/* HOLD, LATCH or 0: the latch takes the whole switch. */
static unsigned ramp_of(unsigned f)
{
    const uint8_t *a = L01c1f180 + G_ACTIONS + 9 * f;
    return !L01c26890[S_LAYOUT] ? 0 : a[0] == ACTION_LATCH ? LATCH : a[3] == ACTION_RAMP ? HOLD : 0;
}

/* How long a press is kept: a pair's wait when nothing else may come of it, longer when a tap or a double press may. */
static uint32_t wait_of(unsigned f)
{
    const uint8_t *a = L01c1f180 + G_ACTIONS + 9 * f;
    return ramp_of(f) == LATCH || (!a[0] && !a[6]) ? QUICK_MS : DELAY_MS;
}

static void begin(unsigned f, uint32_t now);

/* A ramp on and off: to its target, or back. Without its block here it stays off, and the next press tries again. */
static void toggle(unsigned f, uint32_t now)
{
    run[f].latched ^= 1;
    if (run[f].latched) {
        begin(f, now);
        run[f].latched = run[f].active;
    }
}

/* A kept press goes on to pairs.c and the application, with the time it came. */
static void let_go(unsigned f)
{
    if (!run[f].kept)
        return;
    run[f].kept = 0;
    hyperrig_pairs_transition(run[f].raw, 1, run[f].tick, run[f].since);
}

/* From the control scan, for each press and release, before pairs.c: 1 when it is kept from the application, or is the release of a
 * ramp's hold. f is the switch, SWITCHES for another input. */
int hyperrig_ramp_transition(unsigned f, unsigned raw, unsigned level, unsigned tick, uint32_t ms)
{
    struct run *r;
    unsigned k, alone = !down, mine;
    if (f >= SWITCHES)
        return 0;
    r = run + f;
    if (!level) {
        if (r->kept && ramp_of(f) == LATCH && !L01c26890[S_TUNER]) {
            r->kept = 0;                                  /* a short press of a latch is the ramp's as well */
            r->owned = 1;
            toggle(f, ms);
        }
        mine = r->owned;
        let_go(f);                                        /* let go before the ramp: the press, then this release */
        r->down = r->owned = 0;
        down &= ~(1u << f);
        return mine;
    }
    for (k = 0; k < SWITCHES; ++k)
        let_go(k);                                        /* with another switch: those presses go on as they came */
    r->down = 1;
    r->since = ms;
    r->tick = tick;
    r->raw = raw;
    down |= 1u << f;
    if (alone && L01c26890[S_TUNER] && ramp_of(f) == LATCH) {
        L01c26890[S_TUNER] = 0;
        r->owned = 1;
        return 1;
    }
    r->kept = alone && ramp_of(f) && !L01c26890[S_TUNER];
    return r->kept;
}

/* The press is the ramp's now: the block, and where the knob is. Pressed again on the way back, it goes on from there. */
static void begin(unsigned f, uint32_t now)
{
    struct run *r = run + f;
    const struct setting *s = set + f;
    uint8_t types[PLACES + 1], slots[PLACES];
    const int16_t *range;
    int32_t preset = word(G_PRESET), scene = word(G_SCENE), target = (int16_t)(s->target[0] | s->target[1] << 8);
    unsigned i;
    r->at = r->told = now;
    if (r->active && r->preset == preset && r->scene == scene && r->knob == s->knob && preset_application_effect_type(r->slot) == s->kind)
        return;
    r->active = 0;
    if (!s->kind)
        return;
    selection_effect_flatten(types, slots);
    for (i = 0; i < types[0] && i < PLACES && preset_application_effect_type(slots[i]) != s->kind; ++i)
        ;
    if (i == types[0] || i == PLACES || !(range = preset_application_metadata(s->kind, s->knob)))
        return;                                           /* no such block here: the hold does nothing */
    r->slot = slots[i];
    r->knob = s->knob;
    r->from = r->last = preset_application_parameter(r->slot, r->knob);
    r->target = target < range[0] ? range[0] : target > range[1] ? range[1] : target;
    r->way = 0;
    r->preset = preset;
    r->scene = scene;
    r->untold = 0;
    r->active = 1;
}

static void tell(struct run *r, uint32_t now)
{
    panel_inputs_event_queue(EVENT_PARAMETER, r->slot, r->knob);
    r->told = now;
    r->untold = 0;
}

static void step(unsigned f, uint32_t now)
{
    struct run *r = run + f;
    unsigned up = r->latched || (r->owned && ramp_of(f) == HOLD), steps = up ? set[f].rise : set[f].fall;
    int32_t move, value;
    if (word(G_PRESET) != r->preset || word(G_SCENE) != r->scene || preset_application_effect_type(r->slot) != set[f].kind) {
        r->active = r->latched = 0;                       /* another preset or scene: its own values stand */
        return;
    }
    move = steps ? (int32_t)((now - r->at) * FULL / (steps * STEP_MS)) : FULL;
    if (move < 1)
        move = 1;
    r->at = now;
    r->way += up ? move : -move;
    r->way = r->way < 0 ? 0 : r->way > FULL ? FULL : r->way;
    value = r->from + (((r->target - r->from) * r->way + FULL / 2) >> 12);
    if (value != r->last) {
        dispatch_helpers_parameter_apply(r->slot, r->knob, value, GLIDE);
        r->last = value;
        r->untold = 1;
    }
    if (!r->way && !up)
        r->active = 0;                                    /* back where the preset has it */
    if (r->untold && (!r->active || (int32_t)(now - r->told) >= TELL_MS))
        tell(r, now);
}

/* Once in each turn of the control scan, after the switches; now in milliseconds. */
void hyperrig_ramp_turn(uint32_t now)
{
    unsigned f;
    for (f = 0; f < SWITCHES; ++f) {
        struct run *r = run + f;
        if (r->kept && (int32_t)(now - r->since) >= (int32_t)wait_of(f)) {
            unsigned kind = L01c26890[S_TUNER] ? 0 : ramp_of(f);
            if (kind) {
                r->kept = 0;
                r->owned = 1;                             /* the application never sees this press */
                if (kind == LATCH)
                    toggle(f, now);
                else
                    begin(f, now);
            } else
                let_go(f);
        }
        if (r->active)
            step(f, now);
    }
}

/* --- kept --- */

static void copy(void *to, const void *from, unsigned n)
{
    uint8_t *a = to;
    const uint8_t *b = from;
    while (n--)
        *a++ = *b++;
}

/* The settings as they are stored (BYTES for each switch), for midi.c's record. */
void hyperrig_ramp_export(uint8_t *to)
{
    copy(to, set, sizeof set);
}

void hyperrig_ramp_import(const uint8_t *from)
{
    copy(set, from, sizeof set);
}

/* --- console --- */

static int hex(unsigned c)
{
    return c - '0' < 10 ? (int)(c - '0') : c - 'a' < 6 ? (int)(c - 'a' + 10) : -1;
}

/* RAMP: the settings; RAMP =<36 digits>: all of them. The answer is always RAMP <the settings> <the switches whose ramp is up or
 * on its way back, a bit each>. For each switch: kind, knob, target (two bytes, the low first), rise and fall in steps of 50 ms. */
int hyperrig_ramp_console(const char *rest)
{
    uint8_t bytes[sizeof set], *b = (uint8_t *)set;
    char text[2 * sizeof set + 1];
    unsigned n, moving = 0;
    if (*rest == '=') {
        int high, low;
        for (n = 0; n < sizeof set && (high = hex(rest[1 + 2 * n])) >= 0 && (low = hex(rest[2 + 2 * n])) >= 0; ++n)
            bytes[n] = high << 4 | low;
        if (n == sizeof set && !rest[1 + 2 * n])
            copy(b, bytes, sizeof set);
    }
    for (n = 0; n < 2 * sizeof set; ++n) {
        unsigned digit = n & 1 ? b[n >> 1] & 15 : b[n >> 1] >> 4;
        text[n] = digit + (digit < 10 ? '0' : 'a' - 10);
    }
    text[n] = 0;
    for (n = 0; n < SWITCHES; ++n)
        moving |= run[n].active << n;
    bond_records_and_prints_print_b("RAMP %s %d\n", text, moving);
    return 1;
}
