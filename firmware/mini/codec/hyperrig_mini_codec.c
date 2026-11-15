#include "hyperrig_mini_codec.h"

#define SDA HYPERRIG_MINI_CODEC_SDA
#define SCL HYPERRIG_MINI_CODEC_SCL
#define OUT HYPERRIG_MINI_CODEC_OUTPUT
#define DIR HYPERRIG_MINI_CODEC_DIRECTION
#define DIE HYPERRIG_MINI_CODEC_DIGITAL
#define PU HYPERRIG_MINI_CODEC_PULL_UP
#define PD HYPERRIG_MINI_CODEC_PULL_DOWN

static const uint8_t stock_records[HYPERRIG_MINI_CODEC_RECORDS][4] = {
    {0x00,0x00,0xff,0xff}, {0x00,0x66,0x00,0x60},
    {0x00,0x01,0x0f,0xd0}, {0x00,0x03,0x00,0x00},
    {0x00,0x1d,0x00,0x02}, {0x00,0x1c,0x00,0x0e},
    {0x00,0x72,0x01,0x70}, {0x00,0x2b,0x00,0x03},
    {0x00,0x2c,0x00,0x81}, {0x00,0x73,0x33,0x0c},
    {0x00,0x76,0x71,0x40}, {0x00,0x34,0xcf,0xcf},
    {0x00,0x35,0xcf,0xcf}, {0x00,0x4b,0x20,0x07},
    {0x00,0x6a,0x10,0x03}, {0x00,0x77,0x00,0x00},
    {0x00,0x7e,0x0a,0x0a}, {0x00,0x7f,0xc0,0x3f},
    {0x00,0x32,0x00,0x00}, {0x00,0x80,0x07,0x20},
    {0x00,0x0d,0xc0,0x00}, {0x00,0x31,0x10,0x04}
};

static int valid_bus(const hyperrig_mini_codec_bus *bus)
{
    return bus && bus->gpio && bus->sample && bus->delay;
}

static void gpio(hyperrig_mini_codec_bus *bus, unsigned op,
                 unsigned pin, unsigned value)
{
    bus->gpio(bus->user, op, pin, value);
}

static int delay(hyperrig_mini_codec_bus *bus, unsigned units)
{
    int status = bus->delay(bus->user, units);
    return status <= 0 ? status : HYPERRIG_MINI_CODEC_EIO;
}

int hyperrig_mini_codec_bus_init(hyperrig_mini_codec_bus *bus)
{
    if (!valid_bus(bus)) return HYPERRIG_MINI_CODEC_EINVAL;
    bus->initialized = 0;
    gpio(bus, DIR, SCL, 0);
    gpio(bus, PD, SCL, 0);
    gpio(bus, DIE, SCL, 1);
    gpio(bus, OUT, SCL, 0);
    gpio(bus, DIR, SDA, 0);
    gpio(bus, PD, SDA, 0);
    gpio(bus, DIE, SDA, 1);
    gpio(bus, OUT, SDA, 1);
    gpio(bus, OUT, SCL, 1);
    gpio(bus, PU, SCL, 1);
    gpio(bus, PU, SDA, 1);
    bus->initialized = 1;
    return 0;
}

static int start(hyperrig_mini_codec_bus *bus)
{
    int status;
    gpio(bus, OUT, SDA, 1);
    if ((status = delay(bus, 3))) return status;
    gpio(bus, OUT, SCL, 1);
    if ((status = delay(bus, 6))) return status;
    gpio(bus, OUT, SDA, 0);
    if ((status = delay(bus, 3))) return status;
    gpio(bus, OUT, SCL, 0);
    return delay(bus, 3);
}

/* On a failed delay still restore both output latches high. This is only
 * best-effort line cleanup; a failed timing callback cannot promise STOP. */
static int stop(hyperrig_mini_codec_bus *bus)
{
    int status, later;
    gpio(bus, OUT, SDA, 0);
    status = delay(bus, 3);
    gpio(bus, OUT, SCL, 1);
    later = delay(bus, 6);
    if (!status) status = later;
    gpio(bus, OUT, SDA, 1);
    later = delay(bus, 3);
    return status ? status : later;
}

static int write_byte(hyperrig_mini_codec_bus *bus, uint8_t byte)
{
    unsigned mask;
    int status, level;
    gpio(bus, OUT, SCL, 0);
    for (mask = 0x80; mask; mask >>= 1) {
        gpio(bus, OUT, SDA, (byte & mask) != 0);
        if ((status = delay(bus, 3))) return status;
        gpio(bus, OUT, SCL, 1);
        if ((status = delay(bus, 6))) return status;
        gpio(bus, OUT, SCL, 0);
        if ((status = delay(bus, 3))) return status;
    }
    gpio(bus, DIR, SDA, 1);
    gpio(bus, OUT, SCL, 0);
    if ((status = delay(bus, 3))) return status;
    gpio(bus, OUT, SCL, 1);
    if ((status = delay(bus, 3))) return status;
    level = bus->sample(bus->user, SDA);
    if ((status = delay(bus, 3))) return status;
    gpio(bus, OUT, SCL, 0);
    if ((status = delay(bus, 3))) return status;
    gpio(bus, DIR, SDA, 0);
    gpio(bus, OUT, SDA, 0);
    if (level == 0) return 0;
    if (level == 1) return HYPERRIG_MINI_CODEC_NACK;
    return level < 0 ? level : HYPERRIG_MINI_CODEC_EIO;
}

int hyperrig_mini_codec_write(hyperrig_mini_codec_bus *bus,
    const uint8_t record[4], hyperrig_mini_codec_result *result)
{
    unsigned acknowledged = 0, stopped = 0;
    int status, cleanup = 0;
    if (!valid_bus(bus) || !record) {
        status = HYPERRIG_MINI_CODEC_EINVAL;
    } else if (!bus->initialized) {
        status = HYPERRIG_MINI_CODEC_ESTATE;
    } else {
        status = start(bus);
        while (!status && acknowledged < 5) {
            uint8_t byte = acknowledged ? record[acknowledged - 1] :
                                         HYPERRIG_MINI_CODEC_ADDRESS_BYTE;
            status = write_byte(bus, byte);
            if (!status) ++acknowledged;
        }
        /* HyperRig policy: STOP on every attempted transaction, including
         * NACK. Stock 0x02006DCE emits STOP only after all five ACKs. */
        stopped = 1;
        cleanup = stop(bus);
        if (!status) status = cleanup;
        if (cleanup || (status && status != HYPERRIG_MINI_CODEC_NACK))
            bus->initialized = 0;
    }
    if (result) {
        result->acknowledged = acknowledged;
        result->stop_attempted = stopped;
        result->status = status;
        result->cleanup_status = cleanup;
    }
    return status;
}

int hyperrig_mini_codec_write_adapter(void *user, uint8_t address_byte,
    const uint8_t record[4])
{
    if (address_byte != HYPERRIG_MINI_CODEC_ADDRESS_BYTE)
        return HYPERRIG_MINI_CODEC_EINVAL;
    return hyperrig_mini_codec_write((hyperrig_mini_codec_bus *)user, record, 0);
}

const uint8_t *hyperrig_mini_codec_stock_record(unsigned index)
{
    return index < HYPERRIG_MINI_CODEC_RECORDS ? stock_records[index] : 0;
}

int hyperrig_mini_codec_apply_stock(hyperrig_mini_codec_bus *bus,
    unsigned *records_completed)
{
    unsigned count;
    int status;
    if (records_completed) *records_completed = 0;
    for (count = 0; count < HYPERRIG_MINI_CODEC_RECORDS; ++count) {
        status = hyperrig_mini_codec_write(bus, stock_records[count], 0);
        if (status) return status;
        if (records_completed) *records_completed = count + 1;
    }
    return 0;
}

void hyperrig_mini_codec_encode(uint16_t reg, uint16_t value, uint8_t record[4])
{
    if (!record) return;
    record[0] = (uint8_t)(reg >> 8);
    record[1] = (uint8_t)reg;
    record[2] = (uint8_t)(value >> 8);
    record[3] = (uint8_t)value;
}

int hyperrig_mini_codec_control_init(hyperrig_mini_codec_control *control,
    hyperrig_mini_codec_bus *bus, unsigned map)
{
    if (!control || !valid_bus(bus) || map > HYPERRIG_MINI_CODEC_NAU88L21)
        return HYPERRIG_MINI_CODEC_EINVAL;
    control->bus = bus;
    control->map = map;
    control->mute_known = 0;
    control->mute_shadow = 0;
    return 0;
}

int hyperrig_mini_codec_control_apply_stock(hyperrig_mini_codec_control *control,
    unsigned *records_completed)
{
    int status;
    if (records_completed) *records_completed = 0;
    if (!control) return HYPERRIG_MINI_CODEC_EINVAL;
    control->mute_known = 0;
    status = hyperrig_mini_codec_apply_stock(control->bus, records_completed);
    if (!status && control->map == HYPERRIG_MINI_CODEC_NAU88L21) {
        control->mute_shadow = 0x1004;
        control->mute_known = 1;
    }
    return status;
}

int hyperrig_mini_codec_soft_mute(hyperrig_mini_codec_control *control,
    unsigned adc_mute, unsigned dac_mute)
{
    uint8_t record[4];
    uint16_t value;
    int status;
    if (!control || adc_mute > 1 || dac_mute > 1)
        return HYPERRIG_MINI_CODEC_EINVAL;
    if (control->map != HYPERRIG_MINI_CODEC_NAU88L21 || !control->mute_known)
        return HYPERRIG_MINI_CODEC_ESTATE;
    value = (uint16_t)((control->mute_shadow & ~0x0202u) |
                      (adc_mute << 1) | (dac_mute << 9));
    hyperrig_mini_codec_encode(0x31, value, record);
    status = hyperrig_mini_codec_write(control->bus, record, 0);
    if (status) control->mute_known = 0;
    else control->mute_shadow = value;
    return status;
}

int hyperrig_mini_codec_plan_128(uint32_t sample_rate,
    hyperrig_mini_codec_clock_plan *plan)
{
    if (!plan || (sample_rate != 44100 && sample_rate != 48000))
        return HYPERRIG_MINI_CODEC_EINVAL;
    plan->sample_rate = sample_rate;
    plan->mclk_hz = sample_rate * 256;
    plan->bclk_hz = sample_rate * 64;
    plan->converter_clock_hz = sample_rate * 128;
    plan->osr = 128;
    hyperrig_mini_codec_encode(0x03, 0x0050, plan->records[0]);
    hyperrig_mini_codec_encode(0x2b, 0x0002, plan->records[1]);
    hyperrig_mini_codec_encode(0x2c, 0x0082, plan->records[2]);
    return 0;
}

int hyperrig_mini_codec_delay_iterations(uint32_t system_clock_hz,
    uint32_t delay_mode, unsigned units, uint32_t *iterations)
{
    uint32_t divisor = (delay_mode & 1) ? 8000000u : 4000000u;
    if (!iterations || (units != 3 && units != 6) ||
        system_clock_hz > 0x7fffffffu || system_clock_hz < divisor)
        return HYPERRIG_MINI_CODEC_ECLOCK;
    *iterations = (system_clock_hz / divisor) * units;
    return 0;
}

typedef char porta_layout_check[(offsetof(hyperrig_mini_codec_porta, in) == 4 &&
    offsetof(hyperrig_mini_codec_porta, direction) == 8 &&
    offsetof(hyperrig_mini_codec_porta, digital_enable) == 12 &&
    offsetof(hyperrig_mini_codec_porta, pull_up) == 16 &&
    offsetof(hyperrig_mini_codec_porta, pull_down) == 20) ? 1 : -1];

static void mmio_gpio(void *user, unsigned op, unsigned pin, unsigned value)
{
    hyperrig_mini_codec_mmio *mmio = (hyperrig_mini_codec_mmio *)user;
    volatile uint32_t *reg;
    uint32_t mask = 1u << pin;
    switch (op) {
    case OUT: reg = &mmio->porta->out; break;
    case DIR: reg = &mmio->porta->direction; break;
    case DIE: reg = &mmio->porta->digital_enable; break;
    case PU: reg = &mmio->porta->pull_up; break;
    case PD: reg = &mmio->porta->pull_down; break;
    default: return;
    }
    *reg = (*reg & ~mask) | (value ? mask : 0);
    if (op == OUT) mmio->porta->direction &= ~mask;
}

static int mmio_sample(void *user, unsigned pin)
{
    hyperrig_mini_codec_mmio *mmio = (hyperrig_mini_codec_mmio *)user;
    return (int)((mmio->porta->in >> pin) & 1);
}

static int mmio_delay(void *user, unsigned units)
{
    hyperrig_mini_codec_mmio *mmio = (hyperrig_mini_codec_mmio *)user;
    uint32_t iterations, mode = *mmio->delay_mode;
    int status = hyperrig_mini_codec_delay_iterations(*mmio->system_clock_hz,
                                                    mode, units, &iterations);
    if (status) return status;
    mmio->spin(mmio->spin_user, iterations);
    return 0;
}

int hyperrig_mini_codec_bind_mmio(hyperrig_mini_codec_bus *bus,
    hyperrig_mini_codec_mmio *mmio)
{
    if (!bus || !mmio || !mmio->porta || !mmio->delay_mode ||
        !mmio->system_clock_hz || !mmio->spin)
        return HYPERRIG_MINI_CODEC_EINVAL;
    bus->gpio = mmio_gpio;
    bus->sample = mmio_sample;
    bus->delay = mmio_delay;
    bus->user = mmio;
    bus->initialized = 0;
    return 0;
}
