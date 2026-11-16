/* Reconstructed UltraRig M5.71 preset validation, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_STORAGE_RECONSTRUCTION.md. */
#ifndef HYPERRIG_PRESET_STORAGE_H
#define HYPERRIG_PRESET_STORAGE_H

#include "hyperrig_selection.h"

enum {
    HYPERRIG_PRESET_HEADER_BYTES = 40,
    HYPERRIG_PRESET_PAYLOAD_MAX = 1490,
    HYPERRIG_PRESET_SCRATCH_BYTES = 256,
    HYPERRIG_STORAGE_PREPARE = 0x020031d4,
    HYPERRIG_STORAGE_PRIORITY = 0x020054a8,
    HYPERRIG_STORAGE_POLL = 0x020027e4
};

/* Original state+3476 maps sixteen pairs of presets to signed block indices.
 * Original state+5812 is the 256-byte validation scratch area. */
typedef struct {
    hyperrig_selection_runtime selection;
    uint8_t pair_block[16];
    uint8_t scratch[HYPERRIG_PRESET_SCRATCH_BYTES];
} hyperrig_preset_storage;

/* Boundary of original 0x02002810. Return 0 only after writing all requested
 * bytes. A nonzero return may leave a partially written destination. Preserve
 * unwritten bytes. The pointer is borrowed for this call only, including size 0.
 * The callback supplies the original read wrapper's range/error behavior;
 * this component performs no physical I/O and does not implement that wrapper. */
typedef uint32_t (*hyperrig_storage_read)(void *opaque, uint32_t address,
                                        uint8_t *destination, uint32_t size);

typedef struct {
    hyperrig_control_service_call call;
    hyperrig_storage_read read;
    void *opaque;
} hyperrig_storage_io;

/* PREPARE(), PRIORITY(1/0), POLL() remain external services. They may mutate
 * caller-owned state synchronously, preserving the selection API domain and
 * buffer bounds. A record's length is read again after the payload read;
 * callbacks must keep it within capacity and the 1490-byte API domain.
 * No re-entry, IRQ concurrency, retained buffer pointers or overlapping
 * header/payload/runtime storage are supported. */
uint32_t hyperrig_storage_block_address(uint32_t block);
uint32_t hyperrig_storage_preset_address(const hyperrig_preset_storage *storage,
                                       uint32_t preset);

/* Header: 0/1 for rejected/accepted, -1 for invalid API. Availability: 0/1 for
 * unavailable/available, -1 for invalid API. Out-of-range preset IDs return 0
 * without external calls. The availability cache is updated even on I/O failure. */
int hyperrig_storage_header(uint32_t address, uint32_t tag, uint32_t maximum,
                            uint8_t header[HYPERRIG_PRESET_HEADER_BYTES],
                            const hyperrig_storage_io *io);
int hyperrig_storage_available(hyperrig_preset_storage *storage, uint32_t preset,
                               const hyperrig_storage_io *io);

/* Incremental CRC retains the caller's initial state without final XOR.
 * Checksum starts at UINT32_MAX, finishes with XOR UINT32_MAX and calls POLL
 * between 256-byte chunks. These bounded APIs accept sizes 0..1490; data may
 * be NULL only at size 0. Return 0, or -1 before writes/calls on invalid API. */
int hyperrig_storage_crc_update(uint32_t initial, const uint8_t *data, uint32_t size,
                                uint32_t *result);
int hyperrig_storage_checksum(const uint8_t *data, uint32_t size, uint32_t *result,
                              const hyperrig_storage_io *io);

/* Original record-reader statuses: 0 success, -1 header/read rejection,
 * -2 payload read failure, -3 CRC mismatch. -4 is new invalid-API rejection.
 * maximum <=1490 and capacity >= maximum are required before any I/O. Output
 * retains header and payload writes on error; this is validation, not loading. */
int hyperrig_storage_record(uint32_t address, uint32_t tag, uint32_t maximum,
                            uint8_t header[HYPERRIG_PRESET_HEADER_BYTES],
                            uint8_t *payload, uint32_t capacity, const hyperrig_storage_io *io);

/* Integrate actual availability validation into the unchanged selection model.
 * The preset loader, DSP application and remaining services stay external. */
int hyperrig_storage_step_preset(hyperrig_preset_storage *storage, uint32_t step,
                                 const hyperrig_storage_io *io);
int hyperrig_storage_action(hyperrig_preset_storage *storage, unsigned logical,
                            unsigned event, const hyperrig_storage_io *io);
int hyperrig_storage_tick(hyperrig_preset_storage *storage, uint32_t delta,
                          const hyperrig_storage_io *io);
int hyperrig_storage_edge(hyperrig_preset_storage *storage, unsigned physical,
                          unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                          const hyperrig_storage_io *io);

#endif
