/* Reconstructed M5.71 sample engines and their original callers.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_SAMPLE_PROCESSING_H
#define HYPERRIG_EFFECT_SAMPLE_PROCESSING_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t work_budget;
} hyperrig_effect_sample_processing_io;

/* New raw entries: 01c08b3e (nine words), 01c0b5d6 (effect), 01c0ba14
 * (eight words), 01c0bbce (width, mode, output1, output2), 01c0bd8c (effect),
 * 01c18f90 (68-byte descriptor), 01c19448 (56-byte descriptor).
 * Existing processing entries retain their previous domains. Only the ten
 * documented direct dispatcher call sites enter these new bodies internally.
 * Raw counts and address arithmetic are uint32 words. There is no raw sample
 * ceiling; zero and odd decrementing-loop counts are not invented no-ops.
 * A finite shared work budget charges mapped accesses and long-loop work.
 * Exhaustion is -203; invalid API/mapping/domain use -200/-201/-202. Earlier
 * writes remain, results publish only on success, and errors are not resumable.
 * These portable failures do not assert equivalent arbitrary native prefixes.
 *
 * Raw entries use a pure stable byte map, including unaligned host backing.
 * Native sample/descriptor/ring/coefficient/history/residue overlap is allowed.
 * Different original bytes must not acquire additional host aliases. API,
 * arguments, results and IO objects are disjoint from mapped storage. No
 * concurrency, relocation, reentry or retained borrowed callback views.
 * Each reached access must fit without wrapping; address increments wrap.
 * Original private stack 30000000..30001020 cannot be ordinary public data.
 * Original instructions and ROM data remain immutable. The correlation
 * updater computes its ROM pointer from the full byte index; direct indices
 * above one require the corresponding pinned original bytes to be mapped.
 * Only its caller-proven two blocks are classified as a 160-byte weight table.
 * Reused caller typed-memory, slot and count bounds remain unchanged.
 */
int hyperrig_effect_sample_processing_execute(uint32_t entry,
    const uint32_t arguments[12],uint32_t *result,
    const hyperrig_effect_sample_processing_io *io);
int hyperrig_effect_sample_processing_stage(uint32_t stage,uint32_t samples,
    uint32_t count,const hyperrig_effect_sample_processing_io *io);
int hyperrig_effect_sample_processing_audio_resume(hyperrig_audio_task *task,
    uint32_t wait_budget,uint32_t frame_budget,
    const hyperrig_effect_sample_processing_io *io);
/* Separate synchronous constructor invocation for types 25, 36 and 37.
 * Actual frozen model-construction arithmetic and its finite-math domains
 * apply. Preparation and later processing are separate caller operations;
 * no newly discovered scheduler or resource-allocation edge is claimed. */
int hyperrig_effect_sample_processing_prepare(uint32_t effect,
    const hyperrig_effect_sample_processing_io *io);
#endif
