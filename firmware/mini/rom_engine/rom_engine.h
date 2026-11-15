/* Synthetic three-layer A2L engine diagnostic, AC791N ROM callback ABI. */
#ifndef HYPERRIG_ROM_ENGINE_H
#define HYPERRIG_ROM_ENGINE_H
#include <stddef.h>
#include <stdint.h>

typedef int (*hyperrig_rom_engine_send)(const void *, uint32_t);
typedef int (*hyperrig_rom_engine_handler)(const uint8_t *, uint8_t *);
typedef struct {
    hyperrig_rom_engine_send send;
    int (*receive)(void *, uint32_t);
    hyperrig_rom_engine_handler *handler_slot;
} hyperrig_rom_engine_services;

enum {
    HYPERRIG_ENGINE_RECORD_BYTES = 128,
    HYPERRIG_ENGINE_SLOT_BYTES = 32768,
    HYPERRIG_ENGINE_STACK_BYTES = 4096,
    HYPERRIG_ENGINE_MODEL_ARENA_BYTES = 1024,
    HYPERRIG_ENGINE_RUNTIME_ARENA_BYTES = 9216,
    HYPERRIG_ENGINE_FAIL_LOAD = 1,
    HYPERRIG_ENGINE_FAIL_SIZE = 2,
    HYPERRIG_ENGINE_FAIL_INIT = 4,
    HYPERRIG_ENGINE_FAIL_PROCESS = 8,
    HYPERRIG_ENGINE_FAIL_OUTPUT = 16,
    HYPERRIG_ENGINE_FAIL_SUM = 32,
    HYPERRIG_ENGINE_FAIL_HISTORY = 64,
    HYPERRIG_ENGINE_FAIL_REPLAY = 128,
    HYPERRIG_ENGINE_FAIL_ARENA = 256,
    HYPERRIG_ENGINE_FAIL_STACK = 512,
    HYPERRIG_ENGINE_FAIL_DIMENSIONS = 1024
};

/* Little-endian words unless marked ASCII. CRC covers bytes [0,120).
 * 0 HYE1; 4 version; 8 base; 12 span; 16 runs; 20 failure bits;
 * 24 frames; 28 blocks; 32 layers; 36 output CRC; 40 sum CRC;
 * 44 history/positions CRC; 48 replay output CRC; 52 model size query;
 * 56 engine size query; 60 model used; 64 engine used; 68 record address;
 * 72 record bytes; 76 build tag; 80 fixture CRC; 84 private stack bytes;
 * 88 observed stack bytes; 92 stack guards OK; 96 replay history CRC;
 * 100 replay blocks; 104 replay frames; 108 flags (bit0 target private stack);
 * 112 last C API result; 116 arena guards OK; 120 record CRC; 124 DONE.
 * Observed stack bytes count changed fill bytes, not a proven worst case.
 */
extern uint8_t hyperrig_rom_engine_record[HYPERRIG_ENGINE_RECORD_BYTES];
int hyperrig_rom_engine_initialize(const hyperrig_rom_engine_services *,
                                  uint32_t, uint32_t, const uint8_t *);
int hyperrig_rom_engine_dispatch(const uint8_t *, uint8_t *);
int hyperrig_mini_rom_run_on_stack(int (*)(void *), void *, void *);

#endif
