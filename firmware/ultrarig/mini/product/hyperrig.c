/* What HyperRig adds to the MINI application in a product build (tools/build_hyperrig_mini_image.py --product):
 * - the console words HRID, which says which build this is, HRST, the state of the parts below, STAGE, the way into
 *   HyperRig's loader (loader_entry.c), FXC, a block in the place of another (replace.c), AMPK (parametric.c), MIDI
 *   (midi.c) and HRLV, the measure of loudness (loudness.c). PING keeps the original answer, the same for every build;
 * - the volume wheel, and the battery.
 * The application calls these by name, under .if MINI_PRODUCT. HyperRig code; the names of the application are those of
 * firmware/ultrarig.
 *
 * The wheel and the battery are read as the stock TANK-MINI application reads them (facts from its code, none of which is
 * here): the wheel on PC9, converter channel 8, every 10 ms, a 1/16 low pass, the level 124 less the value / 8 (the wheel
 * counts down as it is turned up), the gain the square of the level; the battery on PC0, channel 6, empty at 558 and full at
 * 636. No hardware test of this code has been made. */
#include <stdint.h>

#ifndef HYPERRIG_VERSION
#error "the builder gives HYPERRIG_VERSION and HYPERRIG_BUILD"
#endif

extern uint8_t L01c26890[];                               /* the application's state */
extern uint8_t L01c1f180[];                               /* its settings, which GSAVE keeps */
extern void bond_records_and_prints_print_b(const char *format, ...);
extern int footswitch_events_adc_read(unsigned channel, unsigned wait, unsigned limit, uint32_t *value);
extern void phase3_p5_gpio_set_die(unsigned pin, unsigned value);
extern void L02004ad6(unsigned pin);                      /* makes the pin an input */
extern void phase3_p5_gpio_set_pull_up(unsigned pin, unsigned value);
extern void phase3_p5_gpio_set_pull_down(unsigned pin, unsigned value);
int hyperrig_stage(const char *rest);
int hyperrig_replace(const char *rest);
int hyperrig_level(const char *rest);
void hyperrig_level_turn(void);
void hyperrig_pairs_turn(uint32_t now);
void hyperrig_parametric_turn(void);
void hyperrig_amp_knobs(void);
void hyperrig_midi_turn(uint32_t now);
int hyperrig_midi_console(const char *rest);
uint32_t hyperrig_midi_volume(uint32_t gain);

enum { STATE_FLASH_GOOD = 49, STATE_FLASH_TIME = 920 };
enum { SETTING_FLASH_SWITCH = 13, SETTING_VOLUME_ON = 14, SETTING_VOLUME_SHOWN = 15, SETTING_VOLUME = 36, SETTING_PRESET = 92 };
enum { WHEEL_PIN = 41, WHEEL_CHANNEL = 8, BATTERY_PIN = 32, BATTERY_CHANNEL = 6, CONVERTER_WAIT = 15, CONVERTER_LIMIT = 20000 };
enum { UNITY = 0x10000, LEVEL_MAX = 124, WHEEL_STEP = 6, NEVER = 0xffff };
enum { BATTERY_EMPTY = 558, BATTERY_FULL = 636, BATTERY_SAMPLES = 32, BATTERY_TURNS = 25, BATTERY_LOW = 10, LOW_FLASH_MS = 8000 };

static struct {
    uint32_t low_flash;                  /* when the light last flashed for an empty battery */
    uint32_t battery_sum;
    uint32_t gain;                       /* what the wheel asks for, UNITY at most */
    uint16_t wheel, wheel_used;          /* filtered, 16 times the value; the value the gain was made of */
    uint16_t battery_raw;                /* the last mean, 0 before the first */
    uint8_t ready, turns, samples, wheel_seen, battery_percent, level;
} panel;

static int same(const char *a, const char *b)
{
    while (*a && *a == *b)
        ++a, ++b;
    return *a == *b;
}

static uint32_t setting_word(unsigned at)
{
    return *(volatile uint32_t *)(L01c1f180 + at);
}

/* The word of a console line and the rest of it; nonzero when the word was one of these. */
int hyperrig_console(const char *word, const char *rest)
{
    if (same(word, "STAGE"))
        return hyperrig_stage(rest);
    if (same(word, "FXC"))
        return hyperrig_replace(rest);
    if (same(word, "AMPK")) {
        hyperrig_amp_knobs();
        return 1;
    }
    if (same(word, "MIDI"))
        return hyperrig_midi_console(rest);
    if (same(word, "HRLV"))
        return hyperrig_level(rest);
    if (same(word, "HRID")) {
        bond_records_and_prints_print_b("HRID 1 %s %s banks=3\n", HYPERRIG_VERSION, HYPERRIG_BUILD);
        return 1;
    }
    if (same(word, "HRST")) {
        bond_records_and_prints_print_b("HRST wheel=%d level=%d volume=%d battery=%d raw=%d\n",
                                        panel.wheel_seen ? panel.wheel >> 4 : -1, panel.wheel_seen ? panel.level : -1,
                                        (int)setting_word(SETTING_VOLUME), panel.battery_raw ? panel.battery_percent : -1,
                                        panel.battery_raw);
        return 1;
    }
    return 0;
}

/* In place of the volume of the G's expression pedal: the output volume is what the wheel asks for, and full before the
 * wheel was read or when KNOB turned it off; less what MIDI takes. The application smooths the step. */
void hyperrig_volume(void)
{
    uint32_t gain = hyperrig_midi_volume(panel.wheel_seen && L01c1f180[SETTING_VOLUME_ON] ? panel.gain : UNITY);
    L01c1f180[SETTING_VOLUME_SHOWN] = (uint8_t)(gain * 127 >> 16);
    *(volatile uint32_t *)(L01c1f180 + SETTING_VOLUME) = gain;
}

static void analog_input(unsigned pin)
{
    phase3_p5_gpio_set_die(pin, 0);
    L02004ad6(pin);
    phase3_p5_gpio_set_pull_up(pin, 0);
    phase3_p5_gpio_set_pull_down(pin, 0);
}

static void read_wheel(void)
{
    uint32_t value;
    if (!footswitch_events_adc_read(WHEEL_CHANNEL, CONVERTER_WAIT, CONVERTER_LIMIT, &value))
        return;
    value &= 1023;
    if (!panel.wheel_seen)
        panel.wheel = (uint16_t)(value << 4), panel.wheel_used = NEVER;
    else
        panel.wheel = (uint16_t)(panel.wheel - (panel.wheel >> 4) + value);
    panel.wheel_seen = 1;
    unsigned now = panel.wheel >> 4, used = panel.wheel_used;
    if (used == NEVER || now >= used + WHEEL_STEP || now + WHEEL_STEP <= used || (now != used && (now < 2 || now > 1021))) {
        unsigned down = now >> 3, level = down < LEVEL_MAX ? LEVEL_MAX - down : 0;
        panel.wheel_used = (uint16_t)now;
        panel.level = (uint8_t)level;
        panel.gain = level * level * UNITY / (LEVEL_MAX * LEVEL_MAX);
    }
}

static void read_battery(uint32_t now)
{
    uint32_t value;
    if (++panel.turns < BATTERY_TURNS)
        return;
    panel.turns = 0;
    if (footswitch_events_adc_read(BATTERY_CHANNEL, CONVERTER_WAIT, CONVERTER_LIMIT, &value)) {
        panel.battery_sum += value & 1023;
        if (++panel.samples == BATTERY_SAMPLES) {
            unsigned raw = panel.battery_sum / BATTERY_SAMPLES;
            panel.battery_raw = (uint16_t)raw;
            panel.battery_percent = raw <= BATTERY_EMPTY ? 0 : raw >= BATTERY_FULL ? 100 :
                (uint8_t)((raw - BATTERY_EMPTY) * 100 / (BATTERY_FULL - BATTERY_EMPTY));
            panel.battery_sum = panel.samples = 0;
        }
    }
    /* A reading near zero is a pin that is not the battery, not an empty one. */
    if (panel.battery_raw > BATTERY_EMPTY / 2 && panel.battery_percent < BATTERY_LOW && now - panel.low_flash >= LOW_FLASH_MS) {
        uint32_t preset = setting_word(SETTING_PRESET);
        panel.low_flash = now;
        L01c26890[STATE_FLASH_GOOD] = 0;
        L01c1f180[SETTING_FLASH_SWITCH] = (uint8_t)(preset < 32 ? preset % 3 : 1);
        *(volatile uint32_t *)(L01c26890 + STATE_FLASH_TIME) = now;
    }
}

/* Once in each turn of the control scan, every 10 ms or more; now in milliseconds. */
void hyperrig_panel_turn(uint32_t now)
{
    hyperrig_pairs_turn(now);
    hyperrig_parametric_turn();
    hyperrig_midi_turn(now);
    hyperrig_level_turn();
    if (!panel.ready) {
        analog_input(WHEEL_PIN);
        analog_input(BATTERY_PIN);
        panel.low_flash = now;
        panel.ready = 1;
        return;                          /* the pins settle until the next turn */
    }
    read_wheel();
    read_battery(now);
    hyperrig_volume();
}
