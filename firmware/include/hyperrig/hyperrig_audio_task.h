/* Reconstructed M5.71 audio task, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/AUDIO_TASK_RECONSTRUCTION.md. */
#ifndef HYPERRIG_AUDIO_TASK_H
#define HYPERRIG_AUDIO_TASK_H
#include <stdint.h>

typedef uint8_t *(*hyperrig_audio_task_map)(void *opaque, uint32_t address,
    uint32_t bytes, int writable);
typedef uint32_t (*hyperrig_audio_task_service)(void *opaque, uint32_t target,
    const uint32_t arguments[5], uint32_t count);
typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_audio_task_service call;
    void *opaque;
} hyperrig_audio_task_io;

/* Portable control for the nonreturning original task. Initialize to zero.
 * phase 0 starts its entry, 1 resumes after a completed wait, 2 resumes at
 * queue polling, and 3 preserves an original fatal spin. Counters describe
 * this adapter's observation boundaries, not native task return values. */
typedef struct {
    uint32_t phase, waits, frames, fatal_site;
} hyperrig_audio_task;

/* Run complete original task flow until wait_budget waits or frame_budget
 * completed frames have occurred, or an original fatal spin is reached.
 * Both budgets must be nonzero. Return 0 at a wait, 1 at queue polling and 2
 * at a fatal spin. The original task never returns at these boundaries.
 * New -200 rejects invalid API; -201 reports a missing mapping after possible
 * partial writes; -202 reports a dependency outside its reviewed domain.
 * Mapping is pure, consistent and writable where requested. Returned pointers
 * must provide at least the token's natural alignment, up to four bytes; the
 * adapter checks this before access. Sample and filter objects require
 * compatible int32_t and hyperrig_biquad_section storage on a little-endian
 * host. Services can
 * synchronously mutate mapped memory within the documented domain, but cannot
 * re-enter this task or retain pointers. Task, IO and output argument objects
 * must be disjoint from mapped storage. Guard errors may leave partial writes
 * and are not resumable observation states.
 * The service targets and numerical domains are listed in the module doc. */
int hyperrig_audio_task_resume(hyperrig_audio_task *task,
    uint32_t wait_budget, uint32_t frame_budget, const hyperrig_audio_task_io *io);

/* Complete direct helpers, using original address tokens and the same map.
 * FIR is bounded to the actual task's 9/19 taps and 15/31 ring masks. */
int hyperrig_audio_task_fir(uint32_t coefficients, uint32_t taps, uint32_t ring,
    uint32_t position, uint32_t mask, uint32_t *result, const hyperrig_audio_task_io *io);
int hyperrig_audio_task_tap(uint32_t stage, uint32_t samples, const hyperrig_audio_task_io *io);
int hyperrig_audio_task_warmup(const hyperrig_audio_task_io *io);
int hyperrig_audio_task_effect_scan(uint32_t samples, const hyperrig_audio_task_io *io);
int hyperrig_audio_task_set_input(uint32_t value, const hyperrig_audio_task_io *io);

/* Borrowed views of previously recovered cached/input and four/five-section
 * filter bodies and dynamics reset/clone/single/dual callers. No mapped state
 * is duplicated. This is a new adapter, not a new original function. Only
 * documented original targets are accepted. The five-section clock token
 * must be zero or 0x01c04862 at both reads; other targets return -202. */
int hyperrig_audio_task_recovered(uint32_t target, const uint32_t arguments[5],
    uint32_t *result, const hyperrig_audio_task_io *io);
#endif
