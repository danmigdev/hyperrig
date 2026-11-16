/* Reconstructed UltraRig M5.71 capture loading, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_LOADER_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_LOADER_H
#define HYPERRIG_CAPTURE_LOADER_H
#include "hyperrig_preset_assets.h"

typedef uint32_t (*hyperrig_capture_metadata)(void *opaque, uint32_t slot,
    const uint8_t header[40], uint32_t identity);
/* Original 0x02008586 boundary. Request has exactly 17 initialized bytes:
 * slot, length, header identity, resolved identity (four LE words), valid byte.
 * The callback can update these bytes synchronously. It may not retain the
 * pointer or inspect adjacent private stack storage. Loader is an opaque token. */
typedef uint32_t (*hyperrig_capture_install)(void *opaque, uint32_t source,
    uint32_t size, uint32_t loader, uint8_t request[17]);
typedef struct {
    hyperrig_storage_io storage;
    hyperrig_capture_metadata metadata;
    hyperrig_capture_install install;
} hyperrig_capture_io;

int hyperrig_capture_valid(uint32_t metadata);
int hyperrig_capture_gain_value(uint32_t metadata);
/* Auxiliary output is written only for valid version-one metadata. New -200
 * rejects a null output; otherwise return original 0/1 and preserve old output
 * on rejection. Output signed values use their uint32 bit patterns. */
int hyperrig_capture_aux(uint32_t metadata, uint32_t *output);
int hyperrig_capture_clamp(uint32_t value);
uint32_t hyperrig_capture_scale(uint32_t value);
/* New status 0/-200. Gain lookup retains original table values and uint32 state;
 * physical gain units and live audio application are not established here. */
int hyperrig_capture_mix(hyperrig_control_runtime *runtime, uint32_t flag);
int hyperrig_capture_set_gain(hyperrig_control_runtime *runtime, uint32_t value, uint32_t flag);
int hyperrig_capture_apply_metadata(hyperrig_control_runtime *runtime, uint32_t metadata, uint32_t flag);

/* Original signature gate reads four bytes before checking header length.
 * Return 0/1; new -200 rejects invalid API before calls/writes. */
int hyperrig_capture_signature(uint32_t slot, const uint8_t header[40], const hyperrig_storage_io *io);

/* Header rejection -1; unsupported signature -111; installation status passes
 * through unchanged. Reuse returns 0 even after an extended-identity read error.
 * New -200 rejects invalid API before calls/writes. Callback mutation is limited
 * to caller-owned runtime and the documented request output. No re-entry,
 * concurrent mutation, overlapping buffers or retained callback pointers.
 * Metadata journal scan and container/DSP installation remain external. */
int hyperrig_capture_load(hyperrig_control_runtime *runtime, uint32_t slot, const hyperrig_capture_io *io);
#endif
