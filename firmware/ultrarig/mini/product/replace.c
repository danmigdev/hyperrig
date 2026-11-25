/* Another block in the place of one that is there, in one console word.
 *
 *     FXC <preset> <id> <its type> <new type>  ->  FXC id=<the new one's> <new type>, and the line of the processor
 *
 * The preset is the one the editor knows (p in LVL, -1 without one). With another on the pedal, or another type at the id, nothing is done: a
 * footswitch that was pressed meanwhile does not put the block elsewhere. Switches and console are turns of the same task, so nothing comes
 * between. The new block has the place of the old one, its section, its branch and its switch; in each scene it has the switch that the old one
 * had there, and the knobs of a block that was added (hyperrig_scene_fill). The sound pauses once.
 *
 * What does not fit leaves the old block as it was, in every scene. Whether an IR is loaded, and whether the processor is enough, is known before
 * anything of the old block is touched, the second from the application's own sums with the old block out of its route. Then the old one's memory
 * is given back before the new one asks for its own, so both need not fit at once; when the new one gets none, the old one gets its memory again
 * as a block does that is switched on, and only what still rang in it is lost. With sixteen blocks the new one is made in the old one's slot, and
 * a copy of the record is put back if it cannot be. A block that is off needs neither processor nor memory, as in a preset that is loaded.
 *
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

enum { BLOCKS = 16, BLOCK = 480, METER = 88, TYPES = 39, TYPE_IR = 7, NAME = 24 };
enum { ON = 1, THERE = 2, LANE = 4, MODE = 6, RING = 8, IR_SAMPLES = 48, MEMORY = 84, OBJECT = 288 };            /* in a block */
enum { STEREO_OFF = 3, BUDGET = 48, GIVE = 56, IR = 60, IR_LENGTH = 64, IR_STORED = 72 };                        /* in the state of the chain */
enum { SETTING_PRESET = 92 };
enum { NO_MEMORY = -3, NO_PROCESSOR = -4 };             /* of the application; below zero is always no */

extern const void *hyperrig_effect_rows(unsigned type);                       /* effects.c: 0 for an id it does not have; its ids follow the application's */
extern uint8_t L01c2c220[];                             /* the blocks */
extern uint8_t L01c32db0[];                             /* the chain */
extern uint8_t L01c2e074[];                             /* 88 bytes for each block */
extern uint32_t L01c343d8[];                            /* what each block was measured to take */
extern uint8_t L01c1f180[];                             /* the settings */
extern uint8_t L01c1f7f0[], L01c3441c[];
extern int preset_application_effect_type(unsigned slot);
extern const char *console_reports_type_name(unsigned type);
extern const char *dispatch_helpers_error_text(int code);
extern void dispatch_helpers_cpu_line(const char *word);
extern void link_and_print_print(const char *format, ...);
extern void audio_pause_pause_audio(void);
extern void audio_pause_resume_audio(void);
extern int effect_ownership_lookup(unsigned slot, unsigned *at);
extern void effect_ownership_detach(unsigned slot);
extern void effect_ownership_release(uint8_t *block);
extern void effect_ownership_capture(uint8_t *block);
extern int effect_ownership_remove(unsigned slot);
extern void effect_ownership_refresh(void);
extern int enable_resources_make_resource(uint8_t *block);
extern void effect_construction_construct(uint8_t *block);
extern void effect_parameter_lifecycle_resource_flush(void);
extern int effect_setup_create(unsigned section, unsigned at, unsigned type);
extern int effect_setup_create_disabled(unsigned section, unsigned at, unsigned type);
extern void effect_setup_route_insert(unsigned section, unsigned at, unsigned slot);
extern unsigned effect_setup_route_cost(unsigned section);
extern unsigned effect_setup_total_cost(void);
extern unsigned effect_setup_insertion_cost(unsigned section, unsigned at, unsigned type, int mode);
extern unsigned effect_setup_base_cost(unsigned type);
extern int slot_queries_slot_set_mode(unsigned slot, int mode);
extern int preset_band_controls_set_group_quiet(unsigned slot, unsigned lane);
void hyperrig_scene_replace(unsigned from, unsigned to);
/* These are in the RAM, too far for a call from here: through their address. */
extern unsigned effect_setup_stereo_extra_cost(unsigned type);
extern int effect_setup_default_mode(unsigned type);
extern int effect_setup_next_mode(int mode);
extern int effect_setup_has_mode(unsigned type);
#define FAR(function) ({ __typeof__(&function) at_ = function; __asm__("" : "+r" (at_)); at_; })

/* The old block while the new one is made; in_its_slot: when there is no other slot for that. */
static struct {
    uint32_t cost, meter;
    unsigned section, at;
    uint8_t *block;
    uint8_t slot, on, ring[2], had_memory, in_its_slot, flags[4];
} old;
/* Then the record of the old one is here: the room for a preset that is stored or read (scenes.c), free in a console word. */
extern uint8_t hyperrig_packed[];
static const uint16_t FLAGS[4] = {268, 284, 300, 316};  /* one byte for each block, in the state of the chain */

static uint32_t word(const uint8_t *p)
{
    return *(const volatile uint32_t *)p;
}

static void set_word(uint8_t *p, uint32_t value)
{
    *(volatile uint32_t *)p = value;
}

static uint8_t *block_of(unsigned slot)
{
    return L01c2c220 + BLOCK * slot;
}

static void copy(uint8_t *to, const uint8_t *from)
{
    unsigned k;
    for (k = 0; k < BLOCK; ++k)
        to[k] = from[k];
}

static int same(const char *a, const char *b)
{
    while (*a && *a == *b)
        ++a, ++b;
    return *a == *b;
}

static const char *number(const char *p, int *value)
{
    int sign = *p == '-' ? -1 : 1, n = 0;
    const char *start = p += sign < 0;
    while (*p >= '0' && *p <= '9' && p - start < 3)
        n = 10 * n + *p++ - '0';
    if (p == start || *p != ' ')
        return 0;
    *value = sign * n;
    return p + 1;
}

/* A name up to the end or the next space. */
static const char *name(const char *p, char *to)
{
    unsigned n = 0;
    while (*p && *p != ' ' && n < NAME - 1)
        to[n++] = *p++;
    to[n] = 0;
    return n && (!*p || *p == ' ') ? p + (*p == ' ') : 0;
}

static unsigned type_of(const char *text)
{
    unsigned type;
    for (type = 1; type <= TYPES || hyperrig_effect_rows(type); ++type)
        if (same(text, console_reports_type_name(type)))
            return type;
    return 0;
}

static int slot_left(void)
{
    unsigned slot;
    for (slot = 0; slot < BLOCKS; ++slot)
        if (!block_of(slot)[THERE])
            return 1;
    return 0;
}

static int ir_there(void)
{
    return word(L01c32db0 + IR_LENGTH) && (word(L01c32db0 + IR) || (word(L01c32db0 + IR_STORED) && word(L01c3441c)));
}

/* Out of its route and of the sums; everything else of it stays. */
static void take_out(void)
{
    effect_ownership_detach(old.slot);
    old.on = old.block[ON];
    old.ring[0] = old.block[RING];
    old.ring[1] = old.block[RING + 1];
    old.block[ON] = old.block[RING] = old.block[RING + 1] = 0;
}

/* As it was; with its memory again when it was given back. */
static void put_back(int given)
{
    unsigned k;
    if (old.in_its_slot) {
        copy(old.block, hyperrig_packed);
        L01c343d8[old.slot] = old.cost;
        set_word(L01c2e074 + METER * old.slot, old.meter);
        for (k = 0; k < 4; ++k)
            L01c32db0[FLAGS[k] + old.slot] = old.flags[k];
        old.block[THERE] = 1;
    }
    effect_setup_route_insert(old.section, old.at, old.slot);
    old.block[ON] = old.on;
    if (!given) {
        old.block[RING] = old.ring[0];
        old.block[RING + 1] = old.ring[1];
    } else if (old.on && enable_resources_make_resource(old.block))
        old.block[ON] = 0;                              /* its memory is somebody else's now: it stays, off */
    else if (old.in_its_slot && !old.had_memory)
        effect_construction_construct(old.block);       /* a knob that was on its way is where it was going */
}

/* The memory of the old block, and its slot when there is no other. */
static void give_back(void)
{
    unsigned k;
    old.had_memory = word(old.block + MEMORY) != 0;
    effect_ownership_release(old.block);
    effect_ownership_capture(old.block);
    if (old.block[0] == TYPE_IR)
        set_word(old.block + OBJECT, 0);
    if (!slot_left())
        effect_parameter_lifecycle_resource_flush();
    old.in_its_slot = !slot_left();
    if (!old.in_its_slot)
        return;
    copy(hyperrig_packed, old.block);
    old.cost = L01c343d8[old.slot];
    old.meter = word(L01c2e074 + METER * old.slot);
    for (k = 0; k < 4; ++k)
        old.flags[k] = L01c32db0[FLAGS[k] + old.slot];
    old.block[THERE] = 0;
}

/* The antialiasing with which the block fits, as effect_setup_create looks for it; more is what its branch takes. Negative: none. */
static int mode_that_fits(unsigned type, unsigned more)
{
    unsigned total = effect_setup_total_cost() + more, budget = word(L01c32db0 + BUDGET), cost;
    int mode = FAR(effect_setup_default_mode)(type);
    while (mode > 0 && total + effect_setup_insertion_cost(old.section, old.at, type, mode) > budget)
        mode = FAR(effect_setup_next_mode)(mode);
    if (FAR(effect_setup_has_mode)(type))
        cost = effect_setup_insertion_cost(old.section, old.at, type, mode);
    else
        cost = effect_setup_base_cost(type) +
            (old.section == 1 && !L01c32db0[STEREO_OFF] && L01c1f7f0[0] ? FAR(effect_setup_stereo_extra_cost)(type) : 0);
    return total + cost <= budget ? mode : NO_PROCESSOR;
}

static int make(unsigned type)
{
    int slot = effect_setup_create(old.section, old.at, type);
    if (slot == NO_MEMORY) {
        effect_parameter_lifecycle_resource_flush();
        slot = effect_setup_create(old.section, old.at, type);
    }
    if (!old.on && (slot == NO_MEMORY || slot == NO_PROCESSOR))
        slot = effect_setup_create_disabled(old.section, old.at, type);
    return slot;
}

/* The slot of the new block, or why there is none. */
static int replace(unsigned type)
{
    unsigned route = effect_setup_route_cost(old.section), lane = old.block[LANE];
    uint32_t samples;
    int mode = 0, slot;
    take_out();
    if (old.on)
        mode = mode_that_fits(type, route - effect_setup_route_cost(old.section));
    if (mode < 0) {
        put_back(0);
        return mode;
    }
    give_back();
    slot = make(type);
    if (slot < 0) {
        put_back(1);
        return slot;
    }
    block_of(slot)[ON] = old.on;
    preset_band_controls_set_group_quiet(slot, lane);
    if (old.on && FAR(effect_setup_has_mode)(type) && mode < block_of(slot)[MODE])
        slot_queries_slot_set_mode(slot, mode);
    hyperrig_scene_replace(old.slot, slot);
    if (!old.in_its_slot)
        effect_ownership_remove(old.slot);
    else if ((samples = word(hyperrig_packed + IR_SAMPLES)) && word(L01c32db0 + GIVE))
        ((void (*)(uint32_t))word(L01c32db0 + GIVE))(samples);
    effect_ownership_refresh();
    return slot;
}

int hyperrig_replace(const char *rest)
{
    char now[NAME], wanted[NAME];
    int preset, slot, section;
    unsigned type, was;
    if (!(rest = number(rest, &preset)) || !(rest = number(rest, &slot)) || !(rest = name(rest, now)) || !(rest = name(rest, wanted)) || *rest) {
        link_and_print_print("ERR FXC <preset> <id> <type> <new type>\n");
        return 1;
    }
    type = type_of(wanted);
    was = preset_application_effect_type(slot);
    section = effect_ownership_lookup(slot, &old.at);
    if (preset != (int)word(L01c1f180 + SETTING_PRESET))
        link_and_print_print("ERR FXC another preset\n");
    else if (!was || was != type_of(now) || section < 0)
        link_and_print_print("ERR FXC another block\n");
    else if (!type)
        link_and_print_print("ERR FXC unknown effect\n");
    else if (type == TYPE_IR && !ir_there())
        link_and_print_print("ERR FXC no IR loaded\n");
    else {
        old.slot = slot;
        old.block = block_of(slot);
        old.section = section;
        old.in_its_slot = 0;
        audio_pause_pause_audio();
        slot = replace(type);
        audio_pause_resume_audio();
        if (slot < 0)
            link_and_print_print("ERR FXC %s\n", dispatch_helpers_error_text(slot));
        else {
            link_and_print_print("FXC id=%d %s\n", slot, console_reports_type_name(preset_application_effect_type(slot)));
            dispatch_helpers_cpu_line("FX");
        }
    }
    return 1;
}
