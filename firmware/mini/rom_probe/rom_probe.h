/* RAM-only diagnostic plug-in for the AC791N mask-ROM callback ABI.
 * No firmware install, flash, SPI, clock, GPIO or audio peripheral operations. */
#ifndef HYPERRIG_ROM_PROBE_H
#define HYPERRIG_ROM_PROBE_H
#include <stdint.h>
#include <stddef.h>

typedef int (*hyperrig_rom_send)(const void *, uint32_t);
typedef int (*hyperrig_rom_handler)(const uint8_t *, uint8_t *);
typedef struct {
    hyperrig_rom_send send;
    int (*receive)(void *, uint32_t);
    hyperrig_rom_handler *handler_slot;
} hyperrig_rom_services;

extern uint8_t hyperrig_rom_record[64];
int hyperrig_rom_initialize(const hyperrig_rom_services *, uint32_t base,
                            uint32_t span, const uint8_t *memory);
int hyperrig_rom_dispatch(const uint8_t *cbw, uint8_t *answer);
#endif
