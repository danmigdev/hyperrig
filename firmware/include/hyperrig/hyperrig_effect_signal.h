/* Reconstructed M5.71 signal kernels, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/EFFECT_SIGNAL_RECONSTRUCTION.md. */
#ifndef HYPERRIG_EFFECT_SIGNAL_H
#define HYPERRIG_EFFECT_SIGNAL_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    /* Shared per API invocation: one unit per native 16-sample all-pass/gate
     * block or 4-sample state-variable-filter block. Zero is a valid budget. */
    uint32_t block_budget;
} hyperrig_effect_signal_io;

/* New entries 0x01c1958e/0x01c19a8a/0x01c1ee40 take samples, count and state
 * in arguments 0..2. Words, counts and address increments are modulo 2^32.
 * All-pass/gate always enter a 16-sample block; the filter always enters a
 * four-sample block. No zero-count no-op is invented. A finite block budget
 * bounds long or unreachable-endpoint walks and returns -203 on exhaustion.
 * Errors -200/-201/-202 mean invalid API, missing mapping or invalid access.
 * Errors retain preceding writes and are not resumable observations.
 * map is pure/consistent and exposes little-endian bytes at original tokens.
 * Native sample/state overlap is supported. Distinct original bytes cannot
 * alias host storage; API/IO/result/control storage is disjoint from all maps.
 * The original private stack 0x30000000..0x30001020 is reserved and cannot be
 * supplied as ordinary sample/state storage. Missing maps retain preceding
 * writes; only block-budget stops are compared as exact instruction prefixes.
 * Callbacks obey the unchanged processing contracts. See the scoped document.
 * Other entries delegate to the unchanged processing API with these three
 * numerical boundaries replaced by actual reconstructed execution. */
int hyperrig_effect_signal_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t *result,const hyperrig_effect_signal_io *io);
int hyperrig_effect_signal_stage(uint32_t stage,uint32_t samples,uint32_t count,
    const hyperrig_effect_signal_io *io);
int hyperrig_effect_signal_audio_resume(hyperrig_audio_task *task,
    uint32_t wait_budget,uint32_t frame_budget,const hyperrig_effect_signal_io *io);
#endif
