#include "read16.h"

#define SDA HYPERRIG_MINI_CODEC_SDA
#define SCL HYPERRIG_MINI_CODEC_SCL
#define OUT HYPERRIG_MINI_CODEC_OUTPUT
#define DIR HYPERRIG_MINI_CODEC_DIRECTION

static void gpio(hyperrig_mini_codec_bus *b, unsigned op,
                 unsigned pin, unsigned value)
{
    b->gpio(b->user, op, pin, value);
}

static int delay(hyperrig_mini_codec_bus *b, unsigned units)
{
    int status = b->delay(b->user, units);
    if (status) b->initialized = 0;
    return status <= 0 ? status : HYPERRIG_MINI_CODEC_EIO;
}

static int sample(hyperrig_mini_codec_bus *b,
                  hyperrig_mini_codec_read_result *r)
{
    int level;
    ++r->samples;
    level = b->sample(b->user, SDA);
    if (level == 0 || level == 1) return level;
    b->initialized = 0;
    return level < 0 ? level : HYPERRIG_MINI_CODEC_EIO;
}

static int start(hyperrig_mini_codec_bus *b)
{
    int status;
    gpio(b, OUT, SDA, 1);
    if ((status = delay(b, 3))) return status;
    gpio(b, OUT, SCL, 1);
    if ((status = delay(b, 6))) return status;
    gpio(b, OUT, SDA, 0);
    if ((status = delay(b, 3))) return status;
    gpio(b, OUT, SCL, 0);
    return delay(b, 3);
}

static int stop(hyperrig_mini_codec_bus *b)
{
    int status, later;
    /* Lower SCL before taking SDA ownership, including an interrupted read.
     * Always attempt all three waits and leave both OUT latches high.
     * Failed callbacks cannot establish an electrically valid STOP. */
    gpio(b, OUT, SCL, 0);
    gpio(b, OUT, SDA, 0);
    status = delay(b, 3);
    gpio(b, OUT, SCL, 1);
    later = delay(b, 6);
    if (!status) status = later;
    gpio(b, OUT, SDA, 1);
    later = delay(b, 3);
    return status ? status : later;
}

static int write_byte(hyperrig_mini_codec_bus *b, uint8_t byte,
                      hyperrig_mini_codec_read_result *r)
{
    unsigned mask;
    int status, level;
    gpio(b, OUT, SCL, 0);
    for (mask = 0x80; mask; mask >>= 1) {
        gpio(b, OUT, SDA, (byte & mask) != 0);
        if ((status = delay(b, 3))) return status;
        gpio(b, OUT, SCL, 1);
        if ((status = delay(b, 6))) return status;
        gpio(b, OUT, SCL, 0);
        if ((status = delay(b, 3))) return status;
    }
    gpio(b, DIR, SDA, 1);
    if ((status = delay(b, 3))) return status;
    gpio(b, OUT, SCL, 1);
    if ((status = delay(b, 3))) return status;
    level = sample(b, r);
    if (level < 0) return level;
    if ((status = delay(b, 3))) return status;
    gpio(b, OUT, SCL, 0);
    if ((status = delay(b, 3))) return status;
    /* Keep SDA released after ACK. The codec owns it immediately after the
     * read-address ACK; driving it low here would contend with read data. */
    return level ? HYPERRIG_MINI_CODEC_NACK : 0;
}

static int read_byte(hyperrig_mini_codec_bus *b, uint8_t *byte, unsigned last,
                     hyperrig_mini_codec_read_result *r)
{
    unsigned bit, value = 0;
    int status, level;
    gpio(b, DIR, SDA, 1);
    for (bit = 0; bit < 8; ++bit) {
        if ((status = delay(b, 3))) return status;
        gpio(b, OUT, SCL, 1);
        if ((status = delay(b, 3))) return status;
        level = sample(b, r);
        if (level < 0) return level;
        value = (value << 1) | (unsigned)level;
        if ((status = delay(b, 3))) return status;
        gpio(b, OUT, SCL, 0);
        if ((status = delay(b, 3))) return status;
    }
    if (!last) gpio(b, OUT, SDA, 0); /* ACK high byte */
    /* Last byte NACK: release SDA instead of actively driving a high. */
    else gpio(b, DIR, SDA, 1);
    if ((status = delay(b, 3))) return status;
    gpio(b, OUT, SCL, 1);
    if ((status = delay(b, 6))) return status;
    gpio(b, OUT, SCL, 0);
    if ((status = delay(b, 3))) return status;
    gpio(b, DIR, SDA, 1);
    *byte = (uint8_t)value;
    return 0;
}

int hyperrig_mini_codec_probe_register_allowed(uint16_t reg)
{
    switch (reg) {
    case 0x01: case 0x03: case 0x1c: case 0x1d: case 0x2b:
    case 0x2c: case 0x31: case 0x32: case 0x58: case 0x59:
        return 1;
    default:
        return 0;
    }
}

int hyperrig_mini_codec_read16(hyperrig_mini_codec_bus *b, uint16_t reg,
    uint16_t *value, hyperrig_mini_codec_read_result *result)
{
    hyperrig_mini_codec_read_result r = {0, 0, 0, 0, 0, 0};
    uint8_t bytes[2] = {0, 0};
    unsigned index;
    if (!b || !b->gpio || !b->sample || !b->delay || !value ||
        !hyperrig_mini_codec_probe_register_allowed(reg)) {
        r.status = HYPERRIG_MINI_CODEC_EINVAL;
    } else if (!b->initialized) {
        r.status = HYPERRIG_MINI_CODEC_ESTATE;
    } else {
        r.status = start(b);
        for (index = 0; !r.status && index < 4; ++index) {
            uint8_t byte = index == 0 ? 0x36 : index == 1 ?
                (uint8_t)(reg >> 8) : index == 2 ? (uint8_t)reg : 0x37;
            if (index == 3) r.status = start(b);
            if (!r.status) r.status = write_byte(b, byte, &r);
            if (!r.status) ++r.acknowledged;
        }
        for (index = 0; !r.status && index < 2; ++index) {
            r.status = read_byte(b, &bytes[index], index == 1, &r);
            if (!r.status) ++r.received;
        }
        r.stop_attempted = 1;
        r.cleanup_status = stop(b);
        if (!r.status) r.status = r.cleanup_status;
        if (!r.status) *value = (uint16_t)((unsigned)bytes[0] << 8 | bytes[1]);
    }
    if (result) {
        result->acknowledged = r.acknowledged;
        result->received = r.received;
        result->samples = r.samples;
        result->stop_attempted = r.stop_attempted;
        result->status = r.status;
        result->cleanup_status = r.cleanup_status;
    }
    return r.status;
}
