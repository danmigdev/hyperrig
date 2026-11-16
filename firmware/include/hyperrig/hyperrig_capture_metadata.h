/* Reconstructed UltraRig M5.71 capture metadata, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_METADATA_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_METADATA_H
#define HYPERRIG_CAPTURE_METADATA_H
#include "hyperrig_preset_storage.h"

enum { HYPERRIG_CAPTURE_METADATA_CACHE_BYTES = 300 };
typedef struct {
    /* Original 0x01c2422c: fifteen 20-byte entries, including preserved padding. */
    uint8_t cache[HYPERRIG_CAPTURE_METADATA_CACHE_BYTES];
} hyperrig_capture_metadata_runtime;

/* Original arithmetic for every uint32 input; lengths above 8152 return zero. */
uint32_t hyperrig_capture_metadata_capacity(uint32_t size);
/* Bounded helper APIs accept 0..256 bytes. NULL data is valid only at size zero.
 * Erased returns 0/1; CRC writes the finalized checksum and returns zero.
 * Invalid API returns new -200 before writes. */
int hyperrig_capture_metadata_erased(const uint8_t *data, uint32_t size);
int hyperrig_capture_metadata_crc(const uint8_t *data, uint32_t size, uint32_t *crc);

/* Scan result is four LE words: metadata, selected index (or UINT32_MAX),
 * scan cursor, capacity. The cursor starts at zero; only non-erased records
 * replace it with index+1. No packed-metadata validation.
 * Returns original 0/-1; new -200 rejects invalid pointers/callbacks first.
 * Reads use wrapping base+offset via the original adapter, in chunks <=256.
 * Callbacks may synchronously mutate caller-owned header, cache and result;
 * result capacity must stay 0..255. Private read buffers/contexts are borrowed
 * only for a read and may not be inspected beyond size, retained or aliased.
 * No overlapping buffers, re-entry, concurrent mutation or physical I/O. */
int hyperrig_capture_metadata_scan(uint32_t base, const uint8_t header[40],
    uint32_t identity, uint8_t result[16], const hyperrig_storage_io *io);

/* Non-NULL details forces a scan; NULL permits cache reuse for unsigned slots
 * 0..14. Scan failure is deliberately ignored and its fallback gets cached.
 * Original metadata return is written to value; API status is new 0/-200.
 * The IO call member is unused. Only read is required; no flash write occurs. */
int hyperrig_capture_metadata_lookup(hyperrig_capture_metadata_runtime *runtime,
    uint32_t slot, const uint8_t header[40], uint32_t identity,
    uint8_t details[16], uint32_t *value, const hyperrig_storage_io *io);
#endif
