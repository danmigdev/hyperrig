/* Fixed ABI addresses are checked against pinned G instructions by the audit.
 * These functions execute MMIO and ORIGINAL G code when called on target.
 * They must never be called from the ROM plugin or a host executable. */
#include "audio_port.h"

typedef void (*gpio_value_fn)(unsigned pin, unsigned value);
typedef void (*gpio_input_fn)(unsigned pin);
typedef void (*start_channels_fn)(void);
typedef uint32_t (*clock_mhz_fn)(void);

#define G_OUTPUT ((gpio_value_fn)(uintptr_t)0x02004998u)
#define G_INPUT ((gpio_input_fn)(uintptr_t)0x02004ad6u)
#define G_DIGITAL ((gpio_value_fn)(uintptr_t)0x0200187cu)
#define G_PULL_DOWN ((gpio_value_fn)(uintptr_t)0x02004bacu)
#define G_PULL_UP ((gpio_value_fn)(uintptr_t)0x02004c9au)
#define G_START ((start_channels_fn)(uintptr_t)0x02005194u)
#define G_CPU_MHZ ((clock_mhz_fn)(uintptr_t)0x020057c6u)
#define PORTA_OUT (*(volatile const uint32_t *)(uintptr_t)0x00050000u)
#define PORTA_IN (*(volatile const uint32_t *)(uintptr_t)0x00050004u)
#define DELAY_MODE (*(volatile const uint32_t *)(uintptr_t)0x00040200u)
#define G_DRIVER_STATE (*(volatile const uint8_t *)(uintptr_t)0x01c278dcu)
#define G_RATE (*(volatile const uint32_t *)(uintptr_t)0x01c278e4u)

typedef struct { uint32_t nominal_sys_hz; } g_bus_context;

static void g_gpio(void *unused, unsigned op, unsigned pin, unsigned value)
{
    (void)unused;
    /* All original helpers serialize their PORTA read/modify/write through
     * G's critical-section and bank-lock protocol. Do not add an outer bank
     * lock: the helpers would deadlock while trying to acquire it again. */
    switch (op) {
    case HYPERRIG_MINI_CODEC_OUTPUT: G_OUTPUT(pin, value); break;
    case HYPERRIG_MINI_CODEC_DIRECTION:
        if (value) G_INPUT(pin);
        /* G has an input-only direction helper. Its output helper sets the
         * latch then DIR=0; replaying the current latch preserves its level.
         * No other task may own PA1/2 during this sequence. */
        else G_OUTPUT(pin, (PORTA_OUT >> pin) & 1u);
        break;
    case HYPERRIG_MINI_CODEC_DIGITAL: G_DIGITAL(pin, value); break;
    case HYPERRIG_MINI_CODEC_PULL_UP: G_PULL_UP(pin, value); break;
    case HYPERRIG_MINI_CODEC_PULL_DOWN: G_PULL_DOWN(pin, value); break;
    default: break;
    }
}

static int g_sample(void *unused, unsigned pin)
{
    (void)unused;
    return (int)((PORTA_IN >> pin) & 1u);
}

static int g_delay(void *user, unsigned units)
{
    const g_bus_context *ctx = user;
    uint32_t iterations;
    int status = hyperrig_mini_codec_delay_iterations(ctx->nominal_sys_hz,
                                                    DELAY_MODE, units, &iterations);
    if (status) return status;
    hyperrig_mini_codec_spin_pi32v2(0, iterations);
    return 0;
}

static void g_pa9(void *unused, unsigned value)
{
    (void)unused;
    G_OUTPUT(9, value);
}

static void g_spin(void *unused, uint32_t iterations)
{
    (void)unused;
    hyperrig_mini_codec_spin_pi32v2(0, iterations);
}

static int g_start(void *unused)
{
    (void)unused;
    /* 02004D36 sets driver state1; 02005148 stores rate48000;
     * 02005194 ends by setting state2. These are software-path checks only. */
    if (G_DRIVER_STATE != 1 || G_RATE != 48000)
        return HYPERRIG_MINI_CODEC_ESTATE;
    G_START();
    return G_DRIVER_STATE == 2 ? 0 : HYPERRIG_MINI_CODEC_ESTATE;
}

static const hyperrig_mini_audio_port_io g_io = {g_pa9, g_spin, g_start, 0};

int hyperrig_mini_g_audio_pre(uint32_t nominal_sys_hz)
{
    g_bus_context ctx;
    hyperrig_mini_codec_bus bus;
    ctx.nominal_sys_hz = nominal_sys_hz;
    bus.gpio = g_gpio;
    bus.sample = g_sample;
    bus.delay = g_delay;
    bus.user = &ctx;
    bus.initialized = 0;
    return hyperrig_mini_audio_port_pre(&bus, &g_io, 0);
}

int hyperrig_mini_g_audio_post(void)
{
    return hyperrig_mini_audio_port_post(&g_io);
}

int hyperrig_mini_g_audio_pre_current_clock(void)
{
    uint32_t mhz = G_CPU_MHZ();
    /* Codec delay arithmetic accepts only positive signed Hertz. The getter
     * returns zero for an unsupported mux; do not guess a fallback clock. */
    if (!mhz || mhz > 2147u) {
        g_pa9(0, 0);
        return HYPERRIG_MINI_CODEC_ECLOCK;
    }
    return hyperrig_mini_g_audio_pre(mhz * 1000000u);
}
