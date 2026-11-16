/* Reconstructed UltraRig M5.71 DSP initialization, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_INITIALIZATION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_DSP_INITIALIZATION_H
#define HYPERRIG_DSP_INITIALIZATION_H

#include "hyperrig_biquad_generator.h"

typedef struct {
    uint8_t configuration[68]; /* 0x01c1f7d4: gain word, divisor at +36. */
    uint8_t guard[4];          /* 0x01c2249c: only byte zero is inspected. */
    uint8_t slots[16 * 480];   /* 0x01c2c220: initializer clears each byte +2. */
    uint8_t routes[8 * 448];   /* 0x01c2e5a0: reset clears matched routes. */
    uint8_t control[640];     /* 0x01c32db0: includes five signed parameters. */
    hyperrig_biquad_section filters[4]; /* 0x01c33030, separate from five-section chain. */
    uint8_t callbacks[768];   /* 0x01c34190: tokens, counters and preserved bytes. */
} hyperrig_dsp_initialization_runtime;

enum {
    HYPERRIG_DSP_PLATFORM_INPUT = 0x01c010a6,
    HYPERRIG_DSP_DYNAMICS_CONFIGURE = 0x02030f8e
};
/* Explicit unrecovered startup dependencies. The first supplies the word
 * stored at control+48. The second receives (1, -3 as uint32, 100); its return
 * is ignored. Tokens are identifiers, never host function pointers.
 * Synchronous in-domain runtime mutation is allowed. No retained pointers,
 * concurrent mutation, re-entry or changes to IO itself are supported. */
typedef uint32_t (*hyperrig_dsp_initialization_service)(void *opaque,
    uint32_t service, uint32_t a, uint32_t b, uint32_t c);
typedef struct {
    hyperrig_dsp_initialization_service call;
    void *opaque;
} hyperrig_dsp_initialization_io;

/* Original 0x01c0539c conversion, including binary32 rounding and saturation.
 * Accepts every raw binary32 bit pattern; no host float/libm is used. */
int32_t hyperrig_dsp_initialization_q16(uint32_t value);
/* Original 0x02028968 gain helper. Parameter is bounded here to +/-1280,
 * keeping the reused scaled-exponential argument within its verified domain. */
int hyperrig_dsp_initialization_gain(int32_t parameter, uint32_t *output);
/* Original 0x0202898e setup for indices 1..4, using the second fixed table.
 * Parameter is bounded to +/-1280. History/residue/reserved bytes survive. */
int hyperrig_dsp_initialization_setup(hyperrig_biquad_section *destination,
    uint32_t index, int32_t parameter, uint32_t divisor);
/* Original 0x020290cc slot reset, including byte counter wrap. Any uint32
 * slot is accepted; only matching route IDs and slot flags below 16 change. */
int hyperrig_dsp_initialization_reset_slot(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t slot);
/* Original 0x020289d4 regenerates four sections and clears their histories.
 * The five signed halfwords at control+218..+226 must each be in +/-1280. */
int hyperrig_dsp_initialization_reset_filters(hyperrig_dsp_initialization_runtime *runtime);
/* Complete 0x02029112 initializer. Divisor and input_word accept all uint32
 * values. The same five stored-parameter bounds apply before any writes. */
int hyperrig_dsp_initialization_initialize(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t divisor, uint32_t input_word);
/* Original 0x020291f8 writes two opaque callback words at control+52/+56. */
int hyperrig_dsp_initialization_bind(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t first, uint32_t second);
/* Complete guarded 0x020024ec startup helper. A nonzero guard is a no-op and
 * requires no IO or parameter validation. Otherwise set the guard, obtain the
 * platform word, initialize with divisor 48077, call dynamics configuration,
 * then install the original callback tokens. IO/runtime must be distinct.
 * All status APIs return new 0/-1 success/invalid-API values, not native ABI
 * return-register values. Invalid calls leave buffers and callbacks untouched. */
int hyperrig_dsp_initialization_startup(hyperrig_dsp_initialization_runtime *runtime,
    const hyperrig_dsp_initialization_io *io);

#endif
