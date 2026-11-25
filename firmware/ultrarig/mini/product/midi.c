/* What MIDI does on the pedal. In: presets, scenes, blocks, the amp, bypass, the tuner, the tempo by taps or by MIDI clock, the
 * volume, and up to four controllers that turn a knob of a block. Out: what the player changes on the pedal, with the same numbers.
 *
 * Everything happens in the main task, in the turn of the control scan, and through the functions that the footswitches and the
 * console call. A turn does one preset, scene or bypass, or eight smaller things, and leaves the rest of what came in for the next; of
 * several presets in a row it does the last. So a flood costs no more than that.
 *
 * Out is found by looking: the preset, the scene, the blocks, bypass, the amp and the tuner, as they were in the turn before and as
 * they are now. What a message did is looked at behind it and not told; and a message that was sent and comes straight back is not
 * taken. A preset or a scene that changes takes its blocks with it: they are not told one by one.
 *
 * The settings are kept by GSAVE, behind the 32 bytes of the lights in the record TKGX: a letter, the port, and the settings as they
 * are here. An older HyperRig reads the 32 bytes and leaves the rest.
 *
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

extern uint8_t L01c26890[], L01c1f180[], L01c1f7e0[];
#include "midi_usb.h"

enum { PLACES = 16, KNOBS = 4, SCENES = 8, PRESETS = 32, SLOTS = 16, OFF = 255, EVENTS = PACKET / 4 };
enum { S_TUNER = 52, S_LAYOUT = 74, S_BYPASS = 77, S_ENGINE = 280, S_SCANNED = 776, S_KEPT = 780, S_ALL_OFF = 872, S_STEPS = 956 };
enum { G_SCENE = 88, G_PRESET = 92 };
enum { QUIET_MS = 300, BACK_MS = 500, STOPPED_MS = 500, A_TURN = 8 };
enum { UNITY = 0x10000, LIGHTS = 32, HEAD = 40, ITEM = 'M', SETTINGS = 30, KEPT = LIGHTS + 2 + SETTINGS };
enum { EVENT_ENABLE = 101, EVENT_PARAMETER = 112 };
enum { EVENT_BYTES = 0x7affe7e0 };                        /* how many bytes the event of each code has, two bits each */

extern void bond_records_and_prints_print_b(const char *format, ...);
extern int preset_storage_available(unsigned preset);
extern int preset_loader_load(unsigned preset);
extern void scene_application_select(unsigned scene);
extern void scene_application_flush(void);
extern int slot_commands_enable_command(unsigned slot, unsigned on);
extern unsigned slot_commands_requested(void);
extern int preset_band_controls_request_reserve(unsigned on);
extern void footswitch_events_reload_preset(void);
extern void selection_effect_flatten(uint8_t *count_and_types, uint8_t *slots);
extern int preset_application_effect_type(unsigned slot);
extern unsigned preset_application_effect_enabled(unsigned slot);
extern const int16_t *preset_application_metadata(unsigned type, unsigned parameter);      /* the lowest, the highest, ... */
extern int preset_application_parameter(unsigned slot, unsigned parameter);
extern int dispatch_helpers_parameter_apply(unsigned slot, unsigned parameter, int value, unsigned glide);
extern void panel_inputs_event_queue(unsigned kind, unsigned a, unsigned b);               /* for the editor */
extern void tap_tempo_tap_tempo(uint32_t clock, uint32_t ms);
extern int tempo_slot_services_tempo_command(unsigned tenths);
extern unsigned preset_application_services_tempo(void);
extern uint32_t preset_application_rate(void);
extern void mode_and_settings_block_export(void *to);
extern void mode_and_settings_record_scan(void);
extern uint32_t capture_metadata_crc(const void *data, unsigned length);
extern void record_helpers_copy_name(void *header, const char *name);
extern int settings_store_record_store(const void *record, unsigned length);
void hyperrig_settings_import(const uint8_t *page);
int hyperrig_settings_keep(void);
void hyperrig_midi_turn(uint32_t ms);
int hyperrig_midi_console(const char *rest);
uint32_t hyperrig_midi_volume(uint32_t gain);

static struct {
    uint8_t clock, in, out;                               /* in: 0 all channels, 1 to 16, OFF; out: 1 to 16, OFF */
    uint8_t scene, bypass, tuner, tap, amp, volume, blocks;      /* controllers, or OFF; blocks: the first of sixteen */
    struct knob { uint8_t cc, place, knob, from, to; } knob[KNOBS];      /* the place in the chain and the knob from 0, percent of its way */
} set = {
    1, 0, 1, 20, 21, 22, 23, 24, 7, 102, {{OFF, 0, 0, 0, 100}, {OFF, 0, 0, 0, 100}, {OFF, 0, 0, 0, 100}, {OFF, 0, 0, 0, 100}}
};
_Static_assert(sizeof set == SETTINGS, "the stored form");

struct view {
    int32_t preset, scene;
    uint16_t on;                                          /* one bit for each place of the chain */
    uint8_t bypass, tuner, amp, count;
    uint8_t slot[PLACES];
};

static struct {
    uint32_t ms;                                          /* of this turn */
    uint32_t quiet, sent;                                 /* when what a message did was looked at; when the last packet was sent */
    uint32_t in, out;                                     /* counts */
    struct view seen;
    uint8_t looked, behind, free, build, last;            /* of the buffer: it is free, how many events are put, were sent last */
    uint8_t at;                                           /* where the oldest packet is */
    uint8_t message[3], have;                             /* the stream that comes in */
    uint8_t preset;                                       /* asked for, from 1 */
    int8_t budget, acted;
} now;
static uint32_t volume = UNITY;

static struct {
    uint32_t last, ms, ticks;
    uint32_t kept, length;                                /* how many beats the length is of, in tenths of a millisecond */
    uint32_t odd;                                         /* the last beat was longer, 1, or shorter, 2 */
} beat;

static void copy(void *to, const void *from, unsigned n)
{
    uint8_t *a = to;
    const uint8_t *b = from;
    while (n--)
        *a++ = *b++;
}

static void look(struct view *v)
{
    uint8_t types[PLACES + 1];
    unsigned i;
    selection_effect_flatten(types, v->slot);
    v->count = types[0];
    for (v->on = i = 0; i < types[0]; ++i)
        v->on |= preset_application_effect_enabled(v->slot[i]) << i;
    v->amp = slot_commands_requested();
    /* The application does this in the factory layout only: something that is on again is no bypass. */
    if (L01c26890[S_LAYOUT] && (v->on || v->amp))
        L01c26890[S_BYPASS] = 0;
    v->preset = *(volatile int32_t *)(L01c1f180 + G_PRESET);
    v->scene = *(volatile int32_t *)(L01c1f180 + G_SCENE);
    v->bypass = L01c26890[S_BYPASS];
    v->tuner = L01c26890[S_TUNER];
}

/* Behind what messages did: known, and not told. */
static void known(void)
{
    look(&now.seen);
    now.quiet = now.ms;
}

/* --- out --- */

/* A controller that is OFF is none of these numbers. */
static void put(unsigned status, unsigned a, unsigned b)
{
    uint8_t *e = sending + 4 * now.build;
    if (a > 127 || set.out == OFF || now.build == EVENTS)
        return;
    if (!now.free) {
        now.behind = 1;
        return;
    }
    ++now.build;
    e[0] = status >> 4;
    e[1] = status | ((set.out - 1) & 15);
    e[2] = a;
    e[3] = b;
}

static void put_switch(unsigned cc, unsigned on)
{
    put(0xb0, cc, on ? 127 : 0);
}

static void put_state(const struct view *v)
{
    if (v->preset < 0)
        return;
    put(0xc0, v->preset, 0);
    if (v->scene >= 0)
        put(0xb0, set.scene, v->scene);
}

static void tell(void)
{
    struct view v;
    const struct view *was = &now.seen;
    unsigned i, moved;
    look(&v);
    now.free = is_free();
    now.build = 0;
    moved = v.preset != was->preset || v.scene != was->scene || v.bypass != was->bypass;
    if (moved)
        now.quiet = now.ms;
    if (now.behind && now.free) {
        now.behind = 0;                                   /* nobody has read for a while: the state of now, for the old packet that is gone at last */
        put_state(&v);
    } else if (now.looked) {
        if (v.preset != was->preset)
            put_state(&v);
        else if (v.scene != was->scene && v.scene >= 0)
            put(0xb0, set.scene, v.scene);
        if (v.bypass != was->bypass)
            put_switch(set.bypass, v.bypass);
        if (now.ms - now.quiet >= QUIET_MS && v.count == was->count) {
            for (i = 0; i < v.count && v.slot[i] == was->slot[i]; ++i)
                if ((v.on ^ was->on) >> i & 1)
                    put_switch(set.blocks + i, v.on >> i & 1);
            if (v.amp != was->amp)
                put_switch(set.amp, v.amp);
        }
        if (v.tuner != was->tuner)
            put_switch(set.tuner, v.tuner);
    }
    copy(&now.seen, &v, sizeof v);
    now.looked = 1;
    if (now.build) {
        now.last = now.build;
        now.out += now.build;
        now.sent = now.ms;
        transmit(4 * now.build);
    }
}

/* --- in --- */

static void done(unsigned cost)
{
    now.budget -= cost;
    now.acted = 1;
}

/* One tick of MIDI clock, 24 to a beat. The tempo is of the last beats, the newest one to a quarter, so that a late packet does not
 * move it. One beat of another length is waited out: with the next of the same side it is another tempo, with one of the other side it
 * was a packet that came late, and with none the clock had stopped for a moment. Whole beats a minute when it is as good as that. */
static void tick(uint32_t clock)
{
    uint32_t d, side;
    int tempo, apart;
    if (now.ms - beat.ms > STOPPED_MS)
        beat.ticks = beat.kept = 0;
    beat.ms = now.ms;
    if (beat.ticks++ % 24)
        return;
    d = (clock - beat.last) / (preset_application_rate() / 10000);
    beat.last = clock;
    if (beat.ticks == 1 || d < 1900 || d > 15200 || !set.clock) {       /* 300 to 40 beats a minute, as the editor has them */
        beat.kept = beat.odd = 0;
        return;
    }
    side = d > beat.length + beat.length / 32 ? 1 : beat.length > d + d / 32 ? 2 : 0;
    if (beat.kept && side && side != beat.odd) {
        beat.odd = beat.odd ? 0 : side;
        return;
    }
    if (side)
        beat.kept = 0;
    beat.odd = 0;
    if (beat.kept < 4)
        ++beat.kept;
    beat.length += (int)(d - beat.length) / (int)beat.kept;
    tempo = 6000000 / beat.length;
    apart = (tempo + 5) / 10 * 10;
    if (tempo - apart <= 2 && apart - tempo <= 2)
        tempo = apart;
    apart = tempo - (int)preset_application_services_tempo();
    if (apart > 3 || apart < -3)
        tempo_slot_services_tempo_command(tempo);
}

static void bypass(unsigned on)
{
    unsigned slot;
    if (on == L01c26890[S_BYPASS])
        return;
    done(A_TURN);
    L01c26890[S_BYPASS] = on;
    if (!on) {
        footswitch_events_reload_preset();
        return;
    }
    for (slot = 0; slot < SLOTS; ++slot)
        if (preset_application_effect_type(slot) && preset_application_effect_enabled(slot))
            slot_commands_enable_command(slot, 0);
    if (slot_commands_requested())
        preset_band_controls_request_reserve(0);
    L01c26890[S_ALL_OFF] = 1;
}

static void turn_knob(const struct knob *k, unsigned value)
{
    const int16_t *range;
    unsigned slot;
    int to;
    if (k->place >= now.seen.count)
        return;
    slot = now.seen.slot[k->place];
    range = preset_application_metadata(preset_application_effect_type(slot), k->knob);
    if (!range)
        return;
    to = range[0] + ((range[1] - range[0]) * (k->from * 127 + (k->to - k->from) * (int)value) + 6350) / 12700;
    if (to == preset_application_parameter(slot, k->knob))
        return;
    dispatch_helpers_parameter_apply(slot, k->knob, to, L01c1f7e0[0]);
    panel_inputs_event_queue(EVENT_PARAMETER, slot, k->knob);
    --now.budget;
}

static void control(unsigned cc, unsigned value, uint32_t clock)
{
    unsigned on = value >> 6, i;
    if (cc == set.scene && value < SCENES + 2) {
        if (value < SCENES)
            scene_application_select(value);
        else {
            *(volatile int32_t *)(L01c26890 + S_STEPS) += value == SCENES ? 1 : -1;
            scene_application_flush();
        }
        done(A_TURN);
    }
    if (cc == set.bypass)
        bypass(on);
    if (cc == set.tuner) {
        L01c26890[S_TUNER] = on;
        done(1);
    }
    if (cc == set.tap && on)
        tap_tempo_tap_tempo(clock, now.ms);
    if (cc == set.amp && on != slot_commands_requested()) {
        preset_band_controls_request_reserve(on);
        done(1);
    }
    if (cc == set.volume)
        volume = value == 127 ? UNITY : value * value * UNITY / (127 * 127);
    i = cc - set.blocks;
    if (i < now.seen.count && preset_application_effect_enabled(now.seen.slot[i]) != on) {
        slot_commands_enable_command(now.seen.slot[i], on);
        panel_inputs_event_queue(EVENT_ENABLE, now.seen.slot[i], 0);
        done(1);
    }
    for (i = 0; i < KNOBS; ++i)
        if (cc == set.knob[i].cc)
            turn_knob(&set.knob[i], value);
}

/* The preset that was asked for last: before the next message that is not one, and at the end of what came in. */
static void load(void)
{
    unsigned preset = now.preset;
    now.preset = 0;
    if (preset && preset <= PRESETS && preset_storage_available(preset - 1)) {
        preset_loader_load(preset - 1);
        done(A_TURN);
    }
}

static void message(uint32_t clock)
{
    const uint8_t *m = now.message, *e;
    ++now.in;
    if (set.in && set.in != (m[0] & 15) + 1)
        return;
    for (e = sending; e < sending + 4 * now.last; e += 4)
        if (e[1] == m[0] && e[2] == m[1] && e[3] == m[2] && now.ms - now.sent < BACK_MS)
            return;                                       /* its own, come back */
    if (m[0] >> 4 == 0xc)
        now.preset = m[1] + 1;
    else if (m[0] >> 4 == 0xb) {
        load();
        control(m[1], m[2], clock);
    }
}

/* One byte of a stream of MIDI. Real time may stand anywhere; a status byte stays in force for the data bytes that follow; what
 * belongs to SysEx, or to a message that is not for one channel, or to one whose beginning was not seen, is passed over. */
static void byte_in(unsigned b, uint32_t clock)
{
    if (b >= 0xf8) {
        if (b == 0xf8)
            tick(clock);
    } else if (b & 0x80) {
        now.message[0] = b < 0xf0 ? b : 0;
        now.message[2] = now.have = 0;
    } else if (now.message[0]) {
        now.message[++now.have] = b;
        if (now.have == ((now.message[0] & 0xe0) == 0xc0 ? 1 : 2)) {
            now.have = 0;
            message(clock);
        }
    }
}

/* Once in each turn of the control scan. */
void hyperrig_midi_turn(uint32_t ms)
{
    now.ms = ms;
    port_turn(ms);
    if (state() != PORT_ON) {
        now.looked = 0;                                   /* nobody to tell, and nothing to look for */
        return;
    }
    tell();                                               /* before what came in is done: the player's own change of this turn is the player's */
    if (!*(volatile uint32_t *)(L01c26890 + S_ENGINE))
        return;                                           /* the engine is off: it waits, as the switches do */
    now.budget = A_TURN;
    now.acted = 0;
    while (now.budget > 0 && row.in != row.out) {
        const uint8_t *e = row.packet[row.out % ROW].events + now.at;
        unsigned k, n = e[0] < 16 ? EVENT_BYTES >> 2 * e[0] & 3 : 0;       /* another cable: the port has one */
        for (k = 1; k <= n; ++k)
            byte_in(e[k], row.packet[row.out % ROW].clock);
        now.at = (now.at + 4) % PACKET;
        if (!now.at)
            ++row.out;
    }
    load();
    if (now.acted)
        known();
    take();                                               /* one that waited for room */
}

/* What the wheel gives, less what the controller of the volume takes. */
uint32_t hyperrig_midi_volume(uint32_t gain)
{
    return volume == UNITY ? gain : gain * volume >> 16;
}

/* --- kept --- */

/* The page of the record TKGX as it was read at the start, whole and right. */
void hyperrig_settings_import(const uint8_t *page)
{
    if (page[4] >= KEPT && page[HEAD + LIGHTS] == ITEM) {
        port.wanted = page[HEAD + LIGHTS + 1] & 1;
        copy(&set, page + HEAD + LIGHTS + 2, SETTINGS);
    }
}

/* In place of the store of the record TKGX in GSAVE. 0, or the application's error. A trial of the port is not kept. */
int hyperrig_settings_keep(void)
{
    uint32_t record[(HEAD + KEPT) / 4];
    uint8_t *item = (uint8_t *)record + HEAD + LIGHTS;
    int result;
    mode_and_settings_block_export(record + HEAD / 4);
    item[0] = ITEM;
    item[1] = port.wanted > port.trial;
    copy(item + 2, &set, SETTINGS);
    record[0] = 0x58474b54;                               /* TKGX */
    record[1] = KEPT;
    record[2] = capture_metadata_crc(record + HEAD / 4, KEPT);
    record[3] = 0;
    if (record[2] == *(volatile uint32_t *)(L01c26890 + S_KEPT))
        return 0;
    record_helpers_copy_name(record, "leds");
    if (!L01c26890[S_SCANNED]) {
        mode_and_settings_record_scan();
        L01c26890[S_SCANNED] = 1;
    }
    result = settings_store_record_store(record, HEAD + KEPT);
    if (!result)
        *(volatile uint32_t *)(L01c26890 + S_KEPT) = record[2];
    return result;
}

/* --- console --- */

static int hex(unsigned c)
{
    return c - '0' < 10 ? (int)(c - '0') : c - 'a' < 6 ? (int)(c - 'a' + 10) : -1;
}

/* MIDI: what it is; MIDI on, MIDI off: the port; MIDI =<60 digits>: the settings; MIDI ><digits>: as if these bytes had come in. The answer is
 * always MIDI <port> <kept on> <the settings> <messages in> <messages out>. The editor gives the settings their words. */
int hyperrig_midi_console(const char *rest)
{
    uint8_t bytes[SETTINGS], *b = (uint8_t *)&set;
    char text[2 * SETTINGS + 1];
    unsigned n = 0;
    if (*rest == 'o')
        port_ask(rest[1] == 'n');
    else if (*rest == '=' || *rest == '>') {
        int high, low;
        look(&now.seen);
        for (; (high = hex(rest[1 + 2 * n])) >= 0 && (low = hex(rest[2 + 2 * n])) >= 0; ++n) {
            if (*rest == '>')
                byte_in(high << 4 | low, clock_now());
            else if (n < SETTINGS)
                bytes[n] = high << 4 | low;
        }
        load();
        known();
        if (*rest == '=' && n == SETTINGS)
            copy(b, bytes, SETTINGS);
    }
    for (n = 0; n < 2 * SETTINGS; ++n) {
        unsigned digit = n & 1 ? b[n >> 1] & 15 : b[n >> 1] >> 4;
        text[n] = digit + (digit < 10 ? '0' : 'a' - 10);
    }
    text[n] = 0;
    bond_records_and_prints_print_b("MIDI %d %d %s %d %d\n", state(), port.wanted > port.trial, text, now.in, now.out);
    return 1;
}
