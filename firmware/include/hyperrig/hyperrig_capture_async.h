/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_CAPTURE_ASYNC_H
#define HYPERRIG_CAPTURE_ASYNC_H
#include "hyperrig_audio_task.h"

enum { HYPERRIG_CAPTURE_ASYNC_READ, HYPERRIG_CAPTURE_ASYNC_WRITE,
       HYPERRIG_CAPTURE_ASYNC_SYNC, HYPERRIG_CAPTURE_ASYNC_CLI,
       HYPERRIG_CAPTURE_ASYNC_STI };
typedef uint32_t (*hyperrig_capture_async_platform)(void *, uint32_t operation,
                                                   uint32_t address, uint32_t value);
typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_capture_async_platform platform;
    hyperrig_audio_task_service call;
    void *opaque;
} hyperrig_capture_async_io;
/* Original-address borrowed RAM, including DSP 0x01c2bff0/context +76, both
 * 1284-byte work banks, both 1524-byte history banks and numerical scratch.
 * Pure, stable maps preserve original address relationships and return
 * naturally aligned, compatible little-endian typed storage. IO, worker and
 * wait-result storage stay stable and disjoint from mapped firmware state
 * throughout platform/service callbacks. Numerical ownership/domains are
 * inherited from capture_live.
 * Input/output contain 128 words; bypass retains forward-copy overlap.
 * The platform callback owns timer/MMIO/volatile reads and synchronization.
 * At those explicit boundaries it may interleave the worker on the same RAM;
 * it must not relocate mappings or mutate live numerical structure.
 * This is controlled scheduling, not a hardware or interrupt implementation.
 * Status 0 completes a native void call; new -200/-201/-202 identify invalid
 * API/mapping/domain. They can follow partial writes and do not roll back. */
int hyperrig_capture_async_run(uint32_t input, uint32_t output,
                              const hyperrig_capture_async_io *io);
/* Borrowed adapter for the existing 0x01c1245c helper: result is native 0/-1. */
int hyperrig_capture_async_wait(int32_t *result, const hyperrig_capture_async_io *io);
/* Complete 0x01c12556 descriptor submission. All arguments are native words;
 * low 12-bit taps/count, low 10-bit stride and low 8-bit shift are packed. */
int hyperrig_capture_async_submit(uint32_t output, uint32_t input, uint32_t stride,
    uint32_t coefficients, uint32_t taps, uint32_t samples, uint32_t shift,
    const hyperrig_capture_async_io *io);

typedef struct { uint32_t phase, idle_count, iterations, control; } hyperrig_capture_worker;
/* Zero-initialize, then retain the runner and control token between calls.
 * phase 1 observes the original poll at 0x01c04666; phase 2 observes the
 * unbounded handshake at 0x01c04688; phase 3 means the native function returned.
 * Returns 0 after iteration_budget loops, 1 after native return, or 2 after
 * handshake_budget reads. Observation returns are new, not native statuses.
 * Indirect watchdog/job callbacks are restricted to the observed watchdog
 * target 0x01c02dbc; the idle callback may also be zero. Other original target
 * writers are not yet inventoried. io->call owns that unrecovered body.
 * Runner, IO and output arguments are disjoint from mapped state. */
int hyperrig_capture_worker_resume(hyperrig_capture_worker *worker, uint32_t control,
    uint32_t iteration_budget, uint32_t handshake_budget, const hyperrig_capture_async_io *io);
/* Join the unchanged audio task by replacing only its async capture and
 * accelerator-wait service boundaries. Other services delegate to io->call. */
int hyperrig_capture_async_audio_resume(hyperrig_audio_task *task, uint32_t wait_budget,
    uint32_t frame_budget, const hyperrig_capture_async_io *io);
#endif
