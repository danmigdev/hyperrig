/* Finite diagnostic reads for the MINI private codec bus.
 * Register protocol: Nuvoton NAU88L21/NAU88L21C, not hardware identification.
 * This API never writes codec data, resets the codec or changes audio clocks. */
#ifndef HYPERRIG_MINI_CODEC_READ16_H
#define HYPERRIG_MINI_CODEC_READ16_H
#include "../codec/hyperrig_mini_codec.h"

typedef struct {
    unsigned acknowledged; /* slave ACKs: write-address, reg-hi, reg-lo, read-address */
    unsigned received;     /* complete data bytes, including their master ACK/NACK */
    unsigned samples;      /* SDA samples attempted, at most 20 */
    unsigned stop_attempted;
    int status;
    int cleanup_status;
} hyperrig_mini_codec_read_result;

/* Exact allowlist: 0x01,0x03,0x1c,0x1d,0x2b,0x2c,0x31,0x32,0x58,0x59.
 * Excludes IRQ-clear, reset, test, OTP and fuse registers. */
int hyperrig_mini_codec_probe_register_allowed(uint16_t reg);

/* Caller serializes ownership of PA1/PA2 and supplies an initialized bus with
 * bounded callbacks. Values are published only after two bytes AND STOP pass.
 * No retry, bus-clear, clock stretching, IRQ control or time-us calibration.
 * A NACK does not prove codec absence: power/reset/MCLK state is external.
 * Result may be null; value must be valid and must not overlap bus/result. */
int hyperrig_mini_codec_read16(hyperrig_mini_codec_bus *bus, uint16_t reg,
    uint16_t *value, hyperrig_mini_codec_read_result *result);
#endif
