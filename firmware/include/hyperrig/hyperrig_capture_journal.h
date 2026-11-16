/* Reconstructed UltraRig M5.71 journal writes, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_JOURNAL_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_JOURNAL_H
#define HYPERRIG_CAPTURE_JOURNAL_H
#include "hyperrig_capture_metadata.h"

typedef struct {
    hyperrig_control_runtime controls;
    hyperrig_capture_metadata_runtime metadata;
    uint8_t scratch[256]; /* Original 0x01c24420 verification buffer. */
} hyperrig_capture_journal_runtime;
enum {
    HYPERRIG_JOURNAL_CLOCK = 0x01c04862,
    HYPERRIG_JOURNAL_ELAPSED = 0x020031be,
    HYPERRIG_JOURNAL_PREPARE = 0x02002772,
    HYPERRIG_JOURNAL_MODE = 0x02002bcc,
    HYPERRIG_JOURNAL_ACTIVITY = 0x02002786,
    HYPERRIG_JOURNAL_GATE = 0x02002d06,
    HYPERRIG_JOURNAL_EVENT = 0x02002d70,
    HYPERRIG_JOURNAL_NOTIFY = 0x02002d10,
    HYPERRIG_JOURNAL_WAIT_READY = 0x02002920,
    HYPERRIG_JOURNAL_YIELD = 0x0203feb8,
    HYPERRIG_JOURNAL_ERASE_SECTOR = 0x02002b80,
    HYPERRIG_JOURNAL_RAW_READ = 0x02002806,
    HYPERRIG_JOURNAL_WRAPPED_READ = 0x02002810
};
/* Services use original tokens, never host function addresses. Erase receives
 * (0,200,address); its original return is ignored. The callback is synthetic. */
typedef uint32_t (*hyperrig_capture_journal_service)(void *opaque, uint32_t service,
    uint32_t a, uint32_t b, uint32_t c);
/* Original 0x02002ef2 boundary; return the programmed byte count, not status.
 * Source is borrowed read-only for size bytes. No physical driver is supplied. */
typedef uint32_t (*hyperrig_capture_journal_program)(void *opaque, uint32_t address,
    const uint8_t *source, uint32_t size);
/* Raw reads reject negative results; wrapped reads reject any nonzero result.
 * Non-rejected reads must initialize the entire destination. Failed reads can
 * initialize only a prefix. The service argument distinguishes both contracts. */
typedef uint32_t (*hyperrig_capture_journal_read)(void *opaque, uint32_t service,
    uint32_t address, uint8_t *destination, uint32_t size);
typedef struct {
    hyperrig_capture_journal_service call;
    hyperrig_capture_journal_program program;
    hyperrig_capture_journal_read read;
    void *opaque;
} hyperrig_capture_journal_io;

/* All APIs require disjoint buffers and exclude re-entry, concurrency and
 * retained private pointers. Callbacks may synchronously mutate caller-owned
 * runtime/header/data/details while retaining their documented sizes/domains.
 * IO itself and borrowed program sources must not be changed by a callback.
 * New -200 rejects invalid API before calls/writes. No physical I/O is provided. */
int hyperrig_capture_journal_invalidate(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, uint32_t size);
/* These wrappers retain original 0/-1/-3 statuses and uint32 range arithmetic.
 * Bounded write API: size <=8192, NULL source allowed only for size zero.
 * Bounded erase API: pages <=64. A raw erase's result is not checked. */
int hyperrig_capture_journal_write(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, const uint8_t *source, uint32_t size, const hyperrig_capture_journal_io *io);
int hyperrig_capture_journal_write_offset(hyperrig_capture_journal_runtime *runtime,
    uint32_t base, uint32_t offset, const uint8_t *source, uint32_t size, const hyperrig_capture_journal_io *io);
int hyperrig_capture_journal_erase(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, uint32_t pages, const hyperrig_capture_journal_io *io);
/* Bytewise memcmp result, written as its uint32 bit pattern. Size <=256. */
int hyperrig_capture_journal_compare(const uint8_t *left, const uint8_t *right,
    uint32_t size, uint32_t *result);
/* Complete original 0x0200a622 helper: erase, payload then header writes, header
 * readback, and payload readback in <=256-byte chunks. Payload size <=8152.
 * Header bytes are written verbatim; no CRC or identity is generated here.
 * Returns original 0/-1/-3, or new -200 for invalid API. */
int hyperrig_capture_journal_rewrite(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, uint32_t reservation, const uint8_t header[40],
    const uint8_t *payload, uint32_t size, const hyperrig_capture_journal_io *io);
/* Bounded command continuation 0x0200ab96: append at most two journal records.
 * Details holds the scanner's four LE words; cursor/capacity must be <=255,
 * header payload length <=8152. Identity and metadata are already computed.
 * Return 1 after matching readback; return 0 at the allocation/compaction
 * boundary and write its allocation request (at least four bytes). Allocation
 * output stays unchanged on success. Clock stamp is the caller's prior value.
 * Does not run the command parser, allocate, reload payload or perform fallback. */
int hyperrig_capture_journal_append(hyperrig_capture_journal_runtime *runtime,
    uint32_t base, const uint8_t header[40], uint32_t identity, uint32_t metadata,
    uint8_t details[16], uint32_t stamp, uint32_t *allocation,
    const hyperrig_capture_journal_io *io);
#endif
