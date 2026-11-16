/* Reconstructed UltraRig M5.71 five-section filter caller, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_CHAIN_RECONSTRUCTION.md. */
#ifndef HYPERRIG_BIQUAD_CHAIN_H
#define HYPERRIG_BIQUAD_CHAIN_H

#include "hyperrig_biquad.h"

typedef struct {
    hyperrig_biquad_q28 filter;
    uint8_t enabled;
    uint8_t residual;
    uint8_t reserved[2];
} hyperrig_biquad_section;

typedef struct {
    hyperrig_biquad_section staged[5];
    hyperrig_biquad_section active[5];
    uint32_t clock_token; /* Original function pointer, represented as an opaque token. */
    uint32_t elapsed_average;
    uint32_t elapsed_total;
    uint8_t pending[5];
    uint8_t activity;
    uint8_t reserved[2];
} hyperrig_biquad_chain;

/* Optional original indirect clock boundary. Nonzero tokens are opaque here.
 * The callback can synchronously change runtime/sample memory within the API
 * domain; mutations are observed at the original subsequent read points. */
typedef uint32_t (*hyperrig_biquad_clock)(void *opaque, uint32_t token);
typedef struct {
    hyperrig_biquad_clock clock;
    void *opaque;
} hyperrig_biquad_chain_io;

/* Copy five coefficients and two flags for section 0..4, retaining active
 * history, residue and reserved bytes. Clear that section's pending byte.
 * Return new status 0, or -1 before writes for an invalid runtime/index. */
int hyperrig_biquad_chain_update(hyperrig_biquad_chain *runtime, unsigned section);

/* Apply pending sections, then run enabled Q28 sections in order, in place.
 * Frames are bounded here to 0..128. A valid runtime is always required;
 * samples may be null only for zero frames. Nonzero clock_token requires IO
 * with a clock callback, even when the filters will all be disabled.
 * Return new status 0, or -1 before calls/writes for invalid API.
 * Runtime/sample/IO storage must not overlap. No re-entry, concurrent mutation,
 * retained pointers or physical time-unit/sample-rate claim is supported. */
int hyperrig_biquad_chain_process(hyperrig_biquad_chain *runtime,
                                 int32_t *samples, uint32_t frames,
                                 const hyperrig_biquad_chain_io *io);

#endif
