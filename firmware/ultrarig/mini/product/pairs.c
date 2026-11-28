/* Two switches together, outside the factory layout: the application looks at pairs only in that one.
 *
 * It is for the two sets of actions that the editor makes (Scenes and Stomp): the taps of A, B and C are the scenes 1, 2 and 3, or a block each.
 * A press waits for its neighbour; alone, the application gets it as it is, a moment later. A+B and B+C:
 *   Scenes  the group of three scenes before and after, of those that have one: the taps are the scenes of the group
 *   Stomp   the preset before and after
 * B+C held for a second is the tuner, in both; a tap closes it. With any other actions nothing waits and nothing changes.
 *
 * The level of a switch (S + 1567) is kept for a pair as well: the Bluetooth gesture reads it. The group stands in the byte of the bank (S + 76),
 * which the application shows in LVL and FSMODE and uses in the factory layout only, where it is the bank of the preset again.
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

enum { SWITCHES = 3, WAIT_MS = 45, HOLD_MS = 1000, SCENES = 8, RECORD = 260 };
enum { S_TUNER = 52, S_LAYOUT = 74, S_BANK = 76, S_HOLD_DONE = 932, S_LEVEL = 1567 };
enum { G_SCENE = 88, G_PRESET = 92, G_RAW = 116, G_ACTIONS = 236, ACTION_SCENE = 1, ACTION_BLOCK = 8 };
enum { NONE, SCENE_SET, BLOCK_SET };
enum { HELD = 3 };                                /* its hold is done: the release is nothing */

extern uint8_t L01c26890[], L01c1f180[], hyperrig_scenes[];
extern uint8_t L01c26888[];                       /* what the factory layout has seen of each switch */
extern void controls_transition(unsigned raw, unsigned level, unsigned tick, unsigned ms);
extern void selection_preset_step(int step);
int hyperrig_level_end(void);
int hyperrig_ramp_transition(unsigned f, unsigned raw, unsigned level, unsigned tick, uint32_t ms);
void hyperrig_pairs_transition(unsigned raw, unsigned level, unsigned tick, unsigned ms);

static struct {
    uint32_t tick, ms;                  /* of the press that waits */
    uint32_t since;                     /* when the pair was made */
    int8_t waits;                       /* the switch whose press waits, or -1 */
    int8_t pair;                        /* 0: A+B, 1: B+C, or -1 */
    uint8_t done;                       /* the pair has done what it does */
    uint8_t swallow;                    /* one bit for each switch whose release is not the application's */
    uint8_t group, layout;
    int8_t scene;                       /* the current scene of the last turn */
    uint8_t started;
} two;

static int current(unsigned at)
{
    return *(volatile int32_t *)(L01c1f180 + at);
}

/* Which of the two sets the switches have. */
static int set(void)
{
    const uint8_t *a = L01c1f180 + G_ACTIONS;
    unsigned f, scenes = 0, blocks = 0;
    if (!L01c26890[S_LAYOUT])
        return NONE;
    for (f = 0; f < SWITCHES; ++f, a += 9) {
        scenes += a[0] == ACTION_SCENE && a[1] == f;
        blocks += a[0] == ACTION_BLOCK;
    }
    return scenes == SWITCHES ? SCENE_SET : blocks == SWITCHES ? BLOCK_SET : NONE;
}

static unsigned raw_of(unsigned f)
{
    return L01c1f180[G_RAW + f];
}

static void start(void)
{
    if (two.started)
        return;
    two.started = 1;
    two.waits = two.pair = two.scene = -1;
}

/* The press that waited is the application's. */
static void give(void)
{
    unsigned f = two.waits;
    if (two.waits < 0)
        return;
    two.waits = -1;
    controls_transition(raw_of(f), 1, two.tick, two.ms);
}

/* A press that is not the application's: the level is kept, and no hold is counted. */
static void take(unsigned f)
{
    two.swallow |= 1 << f;
    L01c26890[S_LEVEL + raw_of(f)] = 1;
    L01c26890[S_HOLD_DONE + f] = 1;
}

static int has_scene(unsigned group)
{
    unsigned k;
    for (k = 3 * group; k < 3 * group + 3 && k < SCENES; ++k)
        if (hyperrig_scenes[RECORD * k])
            return 1;
    return 0;
}

static void act(void)
{
    int step = two.pair ? 1 : -1, i;
    unsigned group = two.group;
    two.done = 1;
    if (set() == BLOCK_SET) {
        selection_preset_step(step);
        return;
    }
    for (i = 0; i < 3; ++i) {
        group = (group + 3 + step) % 3;
        if (has_scene(group)) {
            two.group = group;
            return;
        }
    }
}

/* In place of controls_transition in the control scan: a switch whose hold is a ramp first (ramp.c), then pairs. */
void hyperrig_transition(unsigned raw, unsigned level, unsigned tick, unsigned ms)
{
    unsigned f;
    for (f = 0; f < SWITCHES && raw_of(f) != raw; ++f)
        ;
    if (!hyperrig_ramp_transition(f, raw, level, tick, ms))
        hyperrig_pairs_transition(raw, level, tick, ms);
}

/* Pairs, and what is not a pair to the application. */
void hyperrig_pairs_transition(unsigned raw, unsigned level, unsigned tick, unsigned ms)
{
    unsigned f;
    start();
    for (f = 0; f < SWITCHES && raw_of(f) != raw; ++f)
        ;
    if (level && f < SWITCHES && hyperrig_level_end()) {      /* it stops a measure of loudness, and does nothing else */
        take(f);
        L01c26888[f] = HELD;
        return;
    }
    if (f == SWITCHES || (set() == NONE && !(two.swallow >> f & 1))) {
        give();
        controls_transition(raw, level, tick, ms);
        return;
    }
    if (two.swallow >> f & 1) {
        if (level)
            return;
        two.swallow &= ~(1 << f);
        L01c26890[S_LEVEL + raw] = 0;
        if (two.pair >= 0 && (f == (unsigned)two.pair || f == (unsigned)two.pair + 1)) {
            if (!two.done && ms - two.since < HOLD_MS)
                act();
            two.pair = -1;
        }
        return;
    }
    if (level) {
        if (L01c26890[S_TUNER]) {
            give();
            L01c26890[S_TUNER] = 0;
            take(f);
            return;
        }
        if (two.waits >= 0 && (two.waits - (int)f == 1 || two.waits - (int)f == -1)) {
            two.pair = two.waits < (int)f ? two.waits : (int)f;
            take(two.waits);
            take(f);
            two.waits = -1;
            two.since = ms;
            two.done = 0;
            return;
        }
        give();
        two.waits = f;
        two.tick = tick;
        two.ms = ms;
        return;
    }
    if (two.waits == (int)f)
        give();
    controls_transition(raw, level, tick, ms);
}

/* Every turn of the control scan. */
void hyperrig_pairs_turn(uint32_t now)
{
    int scene = current(G_SCENE), kind = set();
    start();
    if (two.waits >= 0 && (int32_t)(now - two.ms) >= WAIT_MS)
        give();
    if (two.pair >= 0 && !two.done && (int32_t)(now - two.since) >= HOLD_MS) {
        two.done = 1;
        if (two.pair == 1)
            L01c26890[S_TUNER] = 1;
    }
    if (scene != two.scene) {
        two.scene = scene;
        if (scene >= 0)
            two.group = scene / 3;
    }
    if (kind == SCENE_SET)
        L01c26890[S_BANK] = two.group;
    else if (!L01c26890[S_LAYOUT] && two.layout && current(G_PRESET) >= 0)
        L01c26890[S_BANK] = current(G_PRESET) / 3;
    two.layout = L01c26890[S_LAYOUT];
}

/* The scene that a tap of the set Scenes chooses; gesture 0 is the tap. */
unsigned hyperrig_scene_of(unsigned scene, unsigned f, unsigned gesture)
{
    return f < SWITCHES && !gesture && set() == SCENE_SET ? scene + 3 * two.group : scene;
}

/* The scene whose light a switch shows. */
unsigned hyperrig_shown_scene(unsigned scene)
{
    return scene < SWITCHES && set() == SCENE_SET ? scene + 3 * two.group : scene;
}
