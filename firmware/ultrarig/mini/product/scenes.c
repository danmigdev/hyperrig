/* Eight scenes for each preset, where the application has four.
 *
 * The records of the scenes and their names are eight each, in arrays of HyperRig's own (scene_memory.S); the application's code finds
 * them there under MINI_PRODUCT. Its working preset (L01c24790, 1490 bytes, the form of version 5) keeps the first four as ever;
 * the other four are beside it, in "more", in the same form: for each effect of the preset, not for each slot.
 *
 * A preset that uses four scenes at most is stored as before, byte for byte, and an older HyperRig reads it. One that uses more is
 * stored in version 6, packed: only the effects that a scene covers, and of each only the parameters that differ from the preset's.
 * It is padded over the 1490 bytes that an older HyperRig accepts, which then takes its place as empty instead of reading it wrong.
 * In the worst case 11 effects fit with eight scenes, 12 with seven, 14 with six and 16 with five.
 *
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

enum { OLD = 4, SCENES = 8, RECORD = 260, NAME = 16, EFFECTS = 16, PARAMETERS = 7, VALUES = 6 };
enum { WORKING = 1490, LIMIT = 1880, PADDED = 1492, VERSION_PACKED = 6, NO_ROOM = -90, DAMAGED = -4, REFUSED = -1 };
enum { AT_COUNT = 1, AT_MASK = 7, AT_EFFECTS = 12, EFFECT = 18, AT_FLAG_A = 1345, AT_TAIL = 1340, TAIL = WORKING - AT_TAIL };
enum { REC_THERE = 0, REC_FLAG_A = 1, REC_MASK = 2, REC_LEVELS = 4, REC_ON = 6, REC_PARAMETERS = 22, REC_VALUES = 246, REC_FLAG_B = 258 };
enum { ONLY_ON = 0x80 };                          /* in REC_ON of a block that is not in the mask: the scene knows its switch, and no knob */

extern uint8_t L01c24790[];                       /* the working preset */
extern uint8_t hyperrig_scenes[], hyperrig_scene_names[];
extern void scene_import_clean_name(uint8_t *to, const uint8_t *from);
extern void link_and_print_print(const char *format, ...);
extern void command_services_effect_snapshot(unsigned scene);
extern void status_snapshot_status_snapshot(unsigned preset);
extern int preset_application_effect_type(unsigned slot);
extern int preset_application_effect_enabled(unsigned slot);
extern int preset_application_parameter(unsigned slot, unsigned parameter);

/* scenes 4 to 7 of the working preset */
static struct {
    uint8_t block[SCENES - OLD][RECORD];          /* mask 2, levels 2, then 16 for each effect: on, unused, seven halfwords */
    uint8_t name[SCENES - OLD][NAME];
    uint8_t values[SCENES - OLD][2 * VALUES];
    uint8_t flag_b;
} more;
static uint8_t kept[RECORD], kept_name[NAME];     /* of a scene that is tried for room */
static int packed_length;                         /* of hyperrig_packed, 0 when the working preset is stored as it is, NO_ROOM */
uint8_t hyperrig_packed[LIMIT] __attribute__((aligned(4)));
const char hyperrig_no_room[] = "no room for these scenes: take a block or a scene away";

static void copy(void *to, const void *from, unsigned n)
{
    uint8_t *a = to;
    const uint8_t *b = from;
    while (n--)
        *a++ = *b++;
}

static void clear(void *to, unsigned n)
{
    uint8_t *a = to;
    while (n--)
        *a++ = 0;
}

static unsigned half(const uint8_t *p)
{
    return p[0] | p[1] << 8;
}

static unsigned effects(void)
{
    unsigned n = L01c24790[AT_COUNT];
    return n < EFFECTS ? n : EFFECTS;
}

/* The block of a scene in the working preset. */
__attribute__((noinline)) uint8_t *hyperrig_scene_block(unsigned scene)
{
    return scene < OLD ? L01c24790 + 300 + RECORD * scene : more.block[scene - OLD];
}

/* A block that a scene does not know is in it as it plays now. The application leaves such a block alone when the scene is chosen, so a
 * scene that was kept before the block was added sounded as the one before it had left the block. Called before a scene is applied and
 * before the working preset is made from what plays; a block that is removed leaves every scene, so its slot starts anew. Of a block that took
 * the place of another (replace.c) the scene knows whether it is on. */
void hyperrig_scene_fill(void)
{
    unsigned slot, scene, k;
    for (slot = 0; slot < EFFECTS; ++slot) {
        if (!preset_application_effect_type(slot))
            continue;
        for (scene = 0; scene < SCENES; ++scene) {
            uint8_t *record = hyperrig_scenes + RECORD * scene;
            if (!record[REC_THERE] || half(record + REC_MASK) >> slot & 1)
                continue;
            record[REC_ON + slot] = record[REC_ON + slot] & ONLY_ON ? record[REC_ON + slot] & 1 : preset_application_effect_enabled(slot);
            for (k = 0; k < PARAMETERS; ++k) {
                int value = preset_application_parameter(slot, k);
                record[REC_PARAMETERS + 14 * slot + 2 * k] = value;
                record[REC_PARAMETERS + 14 * slot + 2 * k + 1] = value >> 8;
            }
            record[REC_MASK + (slot >> 3)] |= 1 << (slot & 7);
        }
    }
}

/* A slot with another block, or without one: no scene knows it. In place of the body of the application's bank_bit_clear. */
void hyperrig_scene_forget(unsigned slot)
{
    unsigned scene;
    if (slot >= EFFECTS)
        return;
    for (scene = 0; scene < SCENES; ++scene) {
        uint8_t *record = hyperrig_scenes + RECORD * scene;
        record[REC_MASK + (slot >> 3)] &= ~(1 << (slot & 7));
        record[REC_ON + slot] = 0;
    }
}

/* The block of slot to is in the place of the one of slot from, which may be the same slot: in each scene it has the switch that one had there. */
void hyperrig_scene_replace(unsigned from, unsigned to)
{
    unsigned scene;
    for (scene = 0; scene < SCENES; ++scene) {
        uint8_t *record = hyperrig_scenes + RECORD * scene, on = record[REC_ON + from];
        if (half(record + REC_MASK) >> from & 1)
            on = ONLY_ON | !!on;
        else if (!(on & ONLY_ON))
            on = 0;                                /* it did not know that one either */
        record[REC_MASK + (from >> 3)] &= ~(1 << (from & 7));
        record[REC_MASK + (to >> 3)] &= ~(1 << (to & 7));
        record[REC_ON + from] = 0;
        record[REC_ON + to] = on;
    }
}

/* From the working preset to the records of scenes 4 to 7 and their names; map: the slot of each effect, or negative. */
void hyperrig_import_more(const int8_t *map)
{
    unsigned n = effects(), scene, i;
    for (scene = OLD; scene < SCENES; ++scene) {
        uint8_t *record = hyperrig_scenes + RECORD * scene, text[NAME + 1];
        const uint8_t *from = hyperrig_scene_block(scene);
        copy(text, more.name[scene - OLD], NAME);
        text[NAME - 1] = text[NAME] = 0;
        scene_import_clean_name(hyperrig_scene_names + NAME * scene, text);
        if (!(L01c24790[AT_MASK] >> scene & 1))
            continue;
        record[REC_THERE] = 1;
        record[REC_FLAG_A] = !(L01c24790[AT_FLAG_A] >> scene & 1);
        copy(record + REC_LEVELS, from + 2, 2);
        copy(record + REC_VALUES, more.values[scene - OLD], 2 * VALUES);
        record[REC_FLAG_B] = more.flag_b >> (scene - OLD) & 1;
        for (i = 0; i < n; ++i) {
            int slot = map[i];
            if (slot < 0 || slot >= EFFECTS || !(half(from) >> i & 1))
                continue;
            record[REC_MASK + (slot >> 3)] |= 1 << (slot & 7);
            record[REC_ON + slot] = from[4 + 16 * i];
            copy(record + REC_PARAMETERS + 14 * slot, from + 6 + 16 * i, 14);
        }
    }
}

/* From the records of scenes 4 to 7 to the working preset that status_snapshot has just filled. */
void hyperrig_snapshot_more(const uint8_t *map)
{
    unsigned n = effects(), scene, i;
    clear(&more, sizeof more);
    for (scene = OLD; scene < SCENES; ++scene) {
        const uint8_t *record = hyperrig_scenes + RECORD * scene;
        uint8_t *to = hyperrig_scene_block(scene);
        if (!record[REC_THERE])
            continue;
        L01c24790[AT_MASK] |= 1 << scene;
        if (!record[REC_FLAG_A])
            L01c24790[AT_FLAG_A] |= 1 << scene;
        copy(to + 2, record + REC_LEVELS, 2);
        copy(more.name[scene - OLD], hyperrig_scene_names + NAME * scene, NAME);
        if (record[REC_FLAG_B]) {
            more.flag_b |= 1 << (scene - OLD);
            copy(more.values[scene - OLD], record + REC_VALUES, 2 * VALUES);
        }
        for (i = 0; i < n; ++i) {
            unsigned slot = map[i];
            if (slot >= EFFECTS || !(half(record + REC_MASK) >> slot & 1))
                continue;
            to[i >> 3] |= 1 << (i & 7);
            to[4 + 16 * i] = record[REC_ON + slot];
            copy(to + 6 + 16 * i, record + REC_PARAMETERS + 14 * slot, 14);
        }
    }
}

/* The names of scenes 4 to 7 for a working preset that was read from the flash, when only names are written. */
void hyperrig_names_more(void)
{
    copy(more.name, hyperrig_scene_names + NAME * OLD, sizeof more.name);
}

static int uses_more(void)
{
    return L01c24790[AT_MASK] >> OLD != 0;
}

/* The working preset into hyperrig_packed; the length, or NO_ROOM. */
static int pack(void)
{
    uint8_t *p = hyperrig_packed, *end = hyperrig_packed + LIMIT;
    unsigned n = effects(), scene, i, k;
    unsigned fixed = AT_EFFECTS + EFFECT * n + TAIL + 1 + sizeof more.name + sizeof more.values;
    copy(p, L01c24790, AT_EFFECTS + EFFECT * n);
    p[0] = VERSION_PACKED;
    p[AT_COUNT] = n;
    p += AT_EFFECTS + EFFECT * n;
    copy(p, L01c24790 + AT_TAIL, TAIL);
    p += TAIL;
    *p++ = more.flag_b;
    copy(p, more.name, sizeof more.name);
    p += sizeof more.name;
    copy(p, more.values, sizeof more.values);
    p = hyperrig_packed + fixed;
    for (scene = 0; scene < SCENES; ++scene) {
        const uint8_t *from = hyperrig_scene_block(scene);
        if (!(L01c24790[AT_MASK] >> scene & 1))
            continue;
        if (p + 4 > end)
            return NO_ROOM;
        copy(p, from, 4);
        p += 4;
        for (i = 0; i < n; ++i) {
            const uint8_t *item = from + 4 + 16 * i, *own = L01c24790 + AT_EFFECTS + EFFECT * i + 4;
            uint8_t *head = p;
            if (!(half(from) >> i & 1))
                continue;
            if (p + 1 + 2 * PARAMETERS > end)
                return NO_ROOM;
            *p++ = item[0] ? 0x80 : 0;
            for (k = 0; k < PARAMETERS; ++k)
                if (half(item + 2 + 2 * k) != half(own + 2 * k)) {
                    *head |= 1 << k;
                    copy(p, item + 2 + 2 * k, 2);
                    p += 2;
                }
        }
    }
    while (p < hyperrig_packed + PADDED)
        *p++ = 0;
    return (int)(p - hyperrig_packed);
}

/* Before the header of a record is made: the length of what is stored when it is the packed form, 0 when it is the working preset. */
int hyperrig_pack(void)
{
    packed_length = uses_more() ? pack() : 0;
    return packed_length;
}

/* What is stored in place of the working preset; 0 when it does not fit. */
const uint8_t *hyperrig_payload(const uint8_t *payload)
{
    if (payload != L01c24790 || !packed_length)
        return payload;
    return packed_length < 0 ? 0 : hyperrig_packed;
}

static int unpack(unsigned length)
{
    const uint8_t *p = hyperrig_packed, *end = hyperrig_packed + length;
    unsigned n = p[AT_COUNT], scene, i, k;
    unsigned fixed = AT_EFFECTS + EFFECT * n + TAIL + 1 + sizeof more.name + sizeof more.values;
    if (n > EFFECTS || length > LIMIT || fixed > length)
        return DAMAGED;
    copy(L01c24790, p, AT_EFFECTS + EFFECT * n);
    L01c24790[0] = VERSION_PACKED - 1;
    p += AT_EFFECTS + EFFECT * n;
    copy(L01c24790 + AT_TAIL, p, TAIL);
    p += TAIL;
    more.flag_b = *p++;
    copy(more.name, p, sizeof more.name);
    p += sizeof more.name;
    copy(more.values, p, sizeof more.values);
    p += sizeof more.values;
    for (scene = 0; scene < SCENES; ++scene) {
        uint8_t *to = hyperrig_scene_block(scene);
        if (!(L01c24790[AT_MASK] >> scene & 1))
            continue;
        if (p + 4 > end)
            return DAMAGED;
        copy(to, p, 4);
        p += 4;
        for (i = 0; i < n; ++i) {
            uint8_t *item = to + 4 + 16 * i, head;
            if (!(half(to) >> i & 1))
                continue;
            if (p + 1 > end)
                return DAMAGED;
            head = *p++;
            item[0] = head >> 7;
            copy(item + 2, L01c24790 + AT_EFFECTS + EFFECT * i + 4, 2 * PARAMETERS);
            for (k = 0; k < PARAMETERS; ++k)
                if (head >> k & 1) {
                    if (p + 2 > end)
                        return DAMAGED;
                    copy(item + 2 + 2 * k, p, 2);
                    p += 2;
                }
        }
    }
    return 0;
}

/* A record was read into hyperrig_packed: to the working preset, which is clear, and "more". header[1] is its length. */
int hyperrig_unpack(uint32_t *header)
{
    unsigned length = header[1];
    clear(&more, sizeof more);
    if (length && hyperrig_packed[0] == VERSION_PACKED) {
        int result = unpack(length);
        header[1] = WORKING;
        return result;
    }
    if (length > WORKING)
        return REFUSED;
    copy(L01c24790, hyperrig_packed, length);
    return 0;
}

/* Whether the preset that plays fits in its place when this scene is saved; the scene is as before afterwards. */
int hyperrig_scene_fits(unsigned scene, int preset)
{
    uint8_t *record = hyperrig_scenes + RECORD * scene;
    int fits;
    copy(kept, record, RECORD);
    copy(kept_name, hyperrig_scene_names + NAME * scene, NAME);
    command_services_effect_snapshot(scene);
    status_snapshot_status_snapshot(preset < 0 ? 0 : preset);
    fits = hyperrig_pack() >= 0;
    copy(record, kept, RECORD);
    copy(hyperrig_scene_names + NAME * scene, kept_name, NAME);
    if (!fits)
        link_and_print_print("ERR SNAPSAVE %s\n", hyperrig_no_room);
    return fits;
}

/* SNAPS */
void hyperrig_snaps(int current)
{
    char there[SCENES + 1];
    unsigned scene;
    for (scene = 0; scene < SCENES; ++scene)
        there[scene] = hyperrig_scenes[RECORD * scene] ? '1' : '0';
    there[SCENES] = 0;
    link_and_print_print("SNAPS %s current=%d\n", there, current);
}
