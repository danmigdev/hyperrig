/* HYC1: bounded codec register reads in ROM; no codec data writes. */
#ifndef HYPERRIG_ROM_CODEC_H
#define HYPERRIG_ROM_CODEC_H
#include <stddef.h>
#include <stdint.h>

typedef int (*hyperrig_rom_codec_send)(const void *, uint32_t);
typedef int (*hyperrig_rom_codec_handler)(const uint8_t *, uint8_t *);
typedef struct {
    hyperrig_rom_codec_send send;
    int (*receive)(void *, uint32_t);
    hyperrig_rom_codec_handler *handler_slot;
} hyperrig_rom_codec_services;

/* PORTA word indices: OUT0 IN1 DIR2 DIE3 PU4 PD5. Bind performs no IO.
 * read/write/spin must be bounded; caller owns PA1/2 for each command.
 * No lock/IRQ/clock register is changed by this diagnostic. */
typedef struct {
    uint32_t (*read)(unsigned);
    void (*write)(unsigned, uint32_t);
    void (*spin)(uint32_t);
} hyperrig_rom_codec_hardware;

/* Record: LE32 words except ASCII signatures.
 * 0 HYC1,4 version1,8 base,12 buildtag,16 seq,20 register,24 status,
 * 28 value (0xffff on error),32 ACKs,36 received bytes,40 SDA samples,
 * 44 STOP attempted,48 cleanup status,52 GPIO restore OK,
 * 56 IN before,60 IN after,
 * 64..80 OUT/DIR/DIE/PU/PD before,84..100 same after,
 * 104 delay callbacks,108 read16 status,112 stack bytes observed,
 * 116 stack guards OK,120 CRC32 of [0,120),124 DONE.
 * Negative status -6 = GPIO restore mismatch, -7 = stack guards damaged.
 * Success requires ACKs4, received2, samples20, STOP1, clean0, restore1.
 * Fixed spin iterations=units*1024; NOT calibrated microseconds. */
extern uint8_t hyperrig_rom_codec_record[128];
int hyperrig_rom_codec_initialize(const hyperrig_rom_codec_services *,
                                 uint32_t, const hyperrig_rom_codec_hardware *);
int hyperrig_rom_codec_dispatch(const uint8_t *, uint8_t *);
#endif
