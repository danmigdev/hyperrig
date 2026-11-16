/* Reconstructed UltraRig M5.71 preset preflight, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_PREFLIGHT_RECONSTRUCTION.md. */
#ifndef HYPERRIG_PRESET_PREFLIGHT_H
#define HYPERRIG_PRESET_PREFLIGHT_H

#include "hyperrig_preset_storage.h"

typedef struct {
    hyperrig_preset_storage storage;
    /* Original scratch preset at 0x01c24790. This is not live DSP state. */
    uint8_t working[HYPERRIG_PRESET_PAYLOAD_MAX];
} hyperrig_preset_runtime;

/* Original predicates/conversion accept any uint32 ID. A non-null parameters
 * pointer must reference fourteen writable bytes. NULL maps the ID only.
 * Conversion returns 27 for ID 6, 29 for ID 24, or the unchanged input ID. */
int hyperrig_preset_needs_conversion(uint32_t type);
uint32_t hyperrig_preset_convert_effect(uint32_t type, uint8_t parameters[14]);

/* Clear the working buffer, read a record, then migrate supported old layouts.
 * Returns 0 success, -1 invalid preset/header, -2 payload read failure,
 * -3 CRC mismatch, -4 old format with length >1200. New API error -5 rejects
 * missing runtime/header/I/O callbacks before any write or external call.
 * Failed preflight retains all completed/partial writes, including clearing
 * the working buffer before an out-of-range preset ID is rejected.
 * Header and runtime must not overlap. The storage callback domain applies;
 * callbacks may synchronously mutate these caller-owned buffers within bounds.
 * No re-entry/concurrency, live preset application or flash writes are provided. */
int hyperrig_preset_preflight(hyperrig_preset_runtime *runtime, uint32_t preset,
                              uint8_t header[HYPERRIG_PRESET_HEADER_BYTES],
                              const hyperrig_storage_io *io);

#endif
