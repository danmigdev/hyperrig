/* HYF1: one RAM plugin for the MINI's ROM download mode. 4 KiB reads, CRC32 of any range computed on the chip, and
 * whole-sector writes confined to the application area. It never writes outside [0x4000, 0x82000) and never changes
 * the flash's protection bits, and it refuses to erase before the host has shown that it holds a backup of the whole
 * flash (ARM). See README.md for the protocol and for what is, and is not, proven on hardware. */
#ifndef HYPERRIG_MINI_FAST_H
#define HYPERRIG_MINI_FAST_H
#include <stddef.h>
#include <stdint.h>

#define HYF_START UINT32_C(0x4000)
#define HYF_END UINT32_C(0x82000)
#define HYF_CAPACITY UINT32_C(0x100000)
#define HYF_SECTOR 4096u
#define HYF_PAGE 256u
#define HYF_MAX_SECTORS 126u
#define HYF_ARM_MAGIC 0x4152u
#define HYF_JEDEC UINT32_C(0xeb6014)

enum { HYF_IDLE, HYF_READY, HYF_ARMED, HYF_DONE, HYF_FAILED };
/* Errors up to HYF_LAST_NOTE change nothing on the flash and leave the session usable; the rest end it. */
enum { HYF_OK, HYF_FRAME, HYF_RANGE, HYF_STATE, HYF_CRC, HYF_SLOW, HYF_BACKUP, HYF_LAST_NOTE = HYF_BACKUP,
       HYF_LOCKED, HYF_JEDEC_ERROR, HYF_PROTECTED, HYF_BUSY, HYF_WEL, HYF_IO, HYF_TIMEOUT, HYF_PREIMAGE,
       HYF_READBACK, HYF_GUARD, HYF_TRANSPORT, HYF_STACK };

typedef int (*hyf_handler)(const uint8_t *, uint8_t *);
typedef struct {
    int (*send)(const void *, uint32_t);
    int (*receive)(void *, uint32_t);
    hyf_handler *handler_slot;
} hyf_services;

/* Every call returns 0 only after its bounded transaction ended with the chip select released. */
typedef struct {
    void *user;
    int (*initialize)(void *, uint32_t *jedec, int *fast, uint8_t *scratch_a, uint8_t *scratch_b);
    int (*status)(void *, uint8_t *sr1, uint8_t *sr2);
    int (*read)(void *, uint32_t address, uint8_t *, unsigned length);
    int (*write_enable)(void *);
    int (*erase4k)(void *, uint32_t address);
    int (*program256)(void *, uint32_t address, const uint8_t *);
    void (*poll_delay)(void *);
    unsigned wip_poll_limit;
} hyf_nor;

typedef struct {
    void *user;
    uint32_t (*read32)(void *, uintptr_t);
    void (*write32)(void *, uintptr_t, uint32_t);
    void (*sync)(void *);
    void (*settle)(void *, unsigned);
    unsigned byte_poll_limit, dma_poll_limit;
} hyf_io;
typedef struct {
    hyf_io io;
    uint32_t sys_div, clk_con2;
    unsigned failed, initialized, fast;
} hyf_pio;

extern const uint32_t hyperrig_fast_mutations_enabled;
int hyf_range(uint32_t address, uint32_t length);
uint32_t hyf_crc32(const uint8_t *, unsigned);
void hyf_pio_bind(hyf_pio *, const hyf_io *, hyf_nor *, unsigned wip_poll_limit);
int hyperrig_fast_initialize(const hyf_services *, const hyf_nor *, uint32_t base);
int hyperrig_fast_dispatch(const uint8_t *cbw, uint8_t *answer);
#endif
