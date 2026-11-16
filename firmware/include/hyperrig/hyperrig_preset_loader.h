/* Reconstructed UltraRig M5.71 preset loader, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_LOADER_RECONSTRUCTION.md. */
#ifndef HYPERRIG_PRESET_LOADER_H
#define HYPERRIG_PRESET_LOADER_H

#include "hyperrig_preset_preflight.h"

typedef struct {
    hyperrig_preset_runtime preset;
    uint8_t saved_actions[36]; /* Original state+4012. */
    uint8_t report_counter[4]; /* Original state+4092, little-endian. */
} hyperrig_loader_runtime;

/* Boundary of original 0x020092fa. Output pointers are distinct borrowed words;
 * this caller does not consume their values. The callback may update runtime
 * state synchronously. Its uint32 result is reported, not used to reject a load. */
typedef uint32_t (*hyperrig_preset_apply)(void *opaque, uint32_t preset,
                                         uint32_t *first, uint32_t *second);
typedef struct {
    hyperrig_storage_io storage;
    hyperrig_preset_apply apply;
} hyperrig_loader_io;

/* Wrapped uint32 multiplication by 1000, then unsigned division by 6. */
uint32_t hyperrig_loader_rate(uint32_t calibration);

/* Snapshot and rebind return -1 on invalid API, otherwise 0 / rewritten count.
 * Snapshot output may be saved_actions, but must not overlap the action source.
 * Rebind requires the selection domain (chain counts <=10; scene <=3 or negative). */
int hyperrig_loader_snapshot(const hyperrig_loader_runtime *runtime, uint8_t output[36]);
int hyperrig_loader_rebind(hyperrig_loader_runtime *runtime);

/* types[0] is count <=16, followed by types. Output pointers must be distinct
 * and not overlap types. Negative/out-of-range positions clear both outputs.
 * Return 0, or -1 without writes for invalid API. */
int hyperrig_loader_binding(const uint8_t types[17], uint32_t position,
                             uint8_t *type, uint8_t *occurrence);

/* Bounded original memcmp: size <=36, null pointers allowed only for size zero.
 * Returns first unsigned-byte difference, or new API error -256. */
int hyperrig_loader_compare(const uint8_t *first, const uint8_t *second, uint32_t size);

/* Elapsed/report wrappers return 0 or -2 for invalid API before calls/writes.
 * Global+44 supplies calibration; elapsed/report require a nonzero rate.
 * A clock callback making the divisor zero returns -3 after that callback.
 * These are arithmetic ratios, without a claim about physical time units. */
int hyperrig_loader_elapsed(hyperrig_loader_runtime *runtime, uint32_t start,
                             uint32_t *result, const hyperrig_loader_io *io);
int hyperrig_loader_report(hyperrig_loader_runtime *runtime, uint32_t preset,
                            uint32_t preflight_time, uint32_t start, uint32_t previous_counter,
                            const hyperrig_loader_io *io);

/* 0 completes the original loader sequence; -1 collapses all preflight errors.
 * New -2 rejects invalid API/selection domain or initial rate <1000 before
 * calls/writes. New -3 catches a callback invalidating timing calibration;
 * earlier writes/calls remain. A completed load commits the preset ID even
 * when the application callback returns nonzero. No persistence is implied.
 * Callbacks must preserve the selection/storage domains and timing divisors.
 * No re-entry, IRQ concurrency or retained output pointers are supported. */
int hyperrig_loader_load(hyperrig_loader_runtime *runtime, uint32_t preset,
                          const hyperrig_loader_io *io);
int hyperrig_loader_step_preset(hyperrig_loader_runtime *runtime, uint32_t step,
                                 const hyperrig_loader_io *io);
int hyperrig_loader_action(hyperrig_loader_runtime *runtime, unsigned logical,
                            unsigned event, const hyperrig_loader_io *io);
int hyperrig_loader_tick(hyperrig_loader_runtime *runtime, uint32_t delta,
                          const hyperrig_loader_io *io);
int hyperrig_loader_edge(hyperrig_loader_runtime *runtime, unsigned physical,
                          unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                          const hyperrig_loader_io *io);

#endif
