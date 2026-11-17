/* Reconstructed M5.71 effect processing, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/EFFECT_PROCESSING_RECONSTRUCTION.md. */
#ifndef HYPERRIG_EFFECT_PROCESSING_H
#define HYPERRIG_EFFECT_PROCESSING_H
#include "hyperrig_audio_task.h"

#define HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS 12u
/* The borrowed map includes original address storage and any transient local
 * descriptors passed to the service. It is valid only during that callback.
 * Services may modify the original fields and explicit descriptor outputs;
 * they must not retain pointers, inspect unrelated private stack words, or
 * reenter processing. Callback results are original 32-bit return words. */
typedef struct {
    hyperrig_audio_task_map map;
    void *opaque;
} hyperrig_effect_processing_borrowed;
typedef uint32_t (*hyperrig_effect_processing_service)(void *opaque,
    uint32_t target, const uint32_t *arguments, uint32_t count,
    const hyperrig_effect_processing_borrowed *borrowed);
typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
} hyperrig_effect_processing_io;

/* Original targets and complete bodies documented by this module. Arguments
 * contains twelve words; unused words are ignored. Estimator 0x01c05c08 takes
 * all six ABI words (the final two were caller stack arguments). Dispatch
 * 0x01c0deb6 takes effect, samples, count, auxiliary mode; individual
 * 0x01c0f678 takes slot, samples, count; grouped 0x01c10446 takes list,
 * list count, samples, count. Scalar results are reported only where defined;
 * original void entries report zero. New errors -200/-201/-202 mean invalid
 * API, absent mapping, or a domain violation, and can retain partial writes.
 * Mapping must be pure, consistent and naturally aligned up to four bytes.
 * API objects and distinct mapped address spans have distinct host storage.
 * No concurrent mutation or reentry. See the scoped document for the complete
 * numerical, slot, count, callback and transient-descriptor contracts. */
int hyperrig_effect_processing_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t *result, const hyperrig_effect_processing_io *io);

/* Join complete stage routing and its unchanged audio task caller. Original
 * observation/resume boundaries and unresolved service contracts remain. */
int hyperrig_effect_processing_stage(uint32_t stage,uint32_t samples,uint32_t count,
    const hyperrig_effect_processing_io *io);
int hyperrig_effect_processing_audio_resume(hyperrig_audio_task *task,
    uint32_t wait_budget,uint32_t frame_budget,const hyperrig_effect_processing_io *io);
#endif
