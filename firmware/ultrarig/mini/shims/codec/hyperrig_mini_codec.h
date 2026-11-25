/* MINI_009 bus control.
 * No physical address is dereferenced until the caller explicitly invokes
 * bus_init/write on a bus bound to its own MMIO context. */
#ifndef HYPERRIG_MINI_CODEC_H
#define HYPERRIG_MINI_CODEC_H
#include <stddef.h>
#include <stdint.h>

enum {
    HYPERRIG_MINI_CODEC_SDA = 1,
    HYPERRIG_MINI_CODEC_SCL = 2,
    HYPERRIG_MINI_CODEC_ADDRESS_BYTE = 0x36,
    HYPERRIG_MINI_CODEC_RECORDS = 22,
    HYPERRIG_MINI_CODEC_OK = 0,
    HYPERRIG_MINI_CODEC_EINVAL = -1,
    HYPERRIG_MINI_CODEC_NACK = -2,
    HYPERRIG_MINI_CODEC_ECLOCK = -3,
    HYPERRIG_MINI_CODEC_ESTATE = -4,
    HYPERRIG_MINI_CODEC_EIO = -5
};

/* These operations correspond to the stock GPIO helper calls. OUTPUT sets
 * the OUT latch and then selects output direction (DIR=0). It drives highs;
 * this is the observed private bus, not a general open-drain I2C driver. */
enum hyperrig_mini_codec_gpio_op {
    HYPERRIG_MINI_CODEC_OUTPUT,
    HYPERRIG_MINI_CODEC_DIRECTION,
    HYPERRIG_MINI_CODEC_DIGITAL,
    HYPERRIG_MINI_CODEC_PULL_UP,
    HYPERRIG_MINI_CODEC_PULL_DOWN
};

typedef struct {
    void (*gpio)(void *user, unsigned operation, unsigned pin, unsigned value);
    int (*sample)(void *user, unsigned pin); /* 0/1 or a negative error */
    int (*delay)(void *user, unsigned units); /* units are 3 or 6, NOT us */
    void *user;
    unsigned initialized;
} hyperrig_mini_codec_bus;

typedef struct {
    unsigned acknowledged; /* 0..5: address plus four payload bytes */
    unsigned stop_attempted;
    int status;           /* first transaction error, otherwise STOP error */
    int cleanup_status;   /* STOP failure is retained even after a NACK */
} hyperrig_mini_codec_result;

/* Caller owns PA1/PA2 and serializes GPIO/clock changes for the entire call.
 * Hardware voltages, reset/power sequence and delay calibration are external.
 * Neither function enables interrupts or configures PLLs. */
int hyperrig_mini_codec_bus_init(hyperrig_mini_codec_bus *bus);
int hyperrig_mini_codec_write(hyperrig_mini_codec_bus *bus,
    const uint8_t record[4], hyperrig_mini_codec_result *result);
/* Signature matches hyperrig_mini_codec_replay_stock() in the audio module. */
int hyperrig_mini_codec_write_adapter(void *user, uint8_t address_byte,
    const uint8_t record[4]);
const uint8_t *hyperrig_mini_codec_stock_record(unsigned index);
int hyperrig_mini_codec_apply_stock(hyperrig_mini_codec_bus *bus,
    unsigned *records_completed);

/* 16-bit register and value, both MSB first; no implicit bus operation. */
void hyperrig_mini_codec_encode(uint16_t reg, uint16_t value, uint8_t record[4]);

enum hyperrig_mini_codec_map {
    HYPERRIG_MINI_CODEC_OPAQUE = 0,
    HYPERRIG_MINI_CODEC_NAU88L21 = 1
};
typedef struct {
    hyperrig_mini_codec_bus *bus;
    unsigned map; /* caller-selected interpretation, NOT hardware detection */
    unsigned mute_known;
    uint16_t mute_shadow;
} hyperrig_mini_codec_control;

int hyperrig_mini_codec_control_init(hyperrig_mini_codec_control *control,
    hyperrig_mini_codec_bus *bus, unsigned map);
int hyperrig_mini_codec_control_apply_stock(hyperrig_mini_codec_control *control,
    unsigned *records_completed);
/* Requires the selected NAU88L21 map and an ACKed register-0x31 shadow.
 * Only ADC/DAC digital mute bits change. Not analog-output mute readiness.
 * All writes to this codec must be serialized through this owner; external
 * writes/reset invalidate mute_known and require reinitialization. */
int hyperrig_mini_codec_soft_mute(hyperrig_mini_codec_control *control,
    unsigned adc_mute, unsigned dac_mute);

typedef struct {
    uint32_t sample_rate, mclk_hz, bclk_hz, converter_clock_hz;
    unsigned osr;
    uint8_t records[3][4];
} hyperrig_mini_codec_clock_plan;
/* Pure planning only: a derived OSR128 candidate for the NAU88L21 map.
 * Does not send records, enable clocks or claim a measured target rate.
 * Stock OSR256 exceeds the published 6.144 MHz converter-clock limit at
 * both 44100 and 48000, so stock replay is not rate validation. */
int hyperrig_mini_codec_plan_128(uint32_t sample_rate,
    hyperrig_mini_codec_clock_plan *plan);

typedef struct {
    volatile uint32_t out, in, direction, digital_enable, pull_up, pull_down;
} hyperrig_mini_codec_porta;

typedef struct {
    hyperrig_mini_codec_porta *porta;             /* physical 0x50000 */
    const volatile uint32_t *delay_mode;         /* physical 0x40200 */
    const volatile uint32_t *system_clock_hz;    /* new board-owned value */
    void (*spin)(void *user, uint32_t iterations);
    void *spin_user;
} hyperrig_mini_codec_mmio;

/* Exactly the stock loop-count arithmetic for positive signed clock values,
 * rejecting zero-trip/invalid clocks instead of silently losing all waits. */
int hyperrig_mini_codec_delay_iterations(uint32_t system_clock_hz,
    uint32_t delay_mode, unsigned units, uint32_t *iterations);
/* Binding itself performs no peripheral reads or writes. */
int hyperrig_mini_codec_bind_mmio(hyperrig_mini_codec_bus *bus,
    hyperrig_mini_codec_mmio *mmio);
/* Optional native callback, built from spin_pi32v2.S; no timing-us claim.
 * r0=user (unused), r1=iterations, leaf function with no stack use. */
void hyperrig_mini_codec_spin_pi32v2(void *user, uint32_t iterations);

#endif
