/* HyperRig MINI ROM plugin: bounded NOR reads, no NVM write operations. */
#ifndef HYPERRIG_MINI_RECOVERY_READER_H
#define HYPERRIG_MINI_RECOVERY_READER_H
#include <stddef.h>
#include <stdint.h>

typedef int (*hyperrig_reader_handler)(const uint8_t *, uint8_t *);
typedef struct {
    int (*send)(const void *, uint32_t);
    int (*receive)(void *, uint32_t);
    hyperrig_reader_handler *handler_slot;
} hyperrig_reader_services;

typedef struct {
    void *user;
    uint32_t (*read32)(void *, uintptr_t);
    void (*write32)(void *, uintptr_t, uint32_t);
    void (*sync)(void *);
    void (*settle)(void *, unsigned);
    uint32_t poll_limit;
} hyperrig_reader_io;

enum {
    HYPERRIG_READER_OK = 0,
    HYPERRIG_READER_CLOCK = 1,
    HYPERRIG_READER_TIMEOUT = 2,
    HYPERRIG_READER_JEDEC = 3,
    HYPERRIG_READER_FRAME = 4,
    HYPERRIG_READER_RANGE = 5,
    HYPERRIG_READER_NOT_READY = 6,
    HYPERRIG_READER_TRANSPORT = 7,
    HYPERRIG_READER_FORBIDDEN = 8
};

/* Initialization only resets private RAM and registers the callback.
 * It makes NO MMIO access. FC72 explicitly performs the SPI initialization.
 * The callback runs synchronously on the ROM's existing stack. */
int hyperrig_reader_initialize(const hyperrig_reader_services *,
                              const hyperrig_reader_io *, uint32_t slot);
int hyperrig_reader_dispatch(const uint8_t *cbw, uint8_t *answer);
#endif
