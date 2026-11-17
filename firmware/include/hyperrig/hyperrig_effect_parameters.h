/* Reconstructed M5.71 effect parameters, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_PARAMETERS_H
#define HYPERRIG_EFFECT_PARAMETERS_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t service_budget;
    uint32_t work_budget;
} hyperrig_effect_parameters_io;

/* Borrow original address storage. Maps are pure and stable; distinct address
 * spans preserve their original relationships. IO and result storage remain
 * disjoint from mapped state throughout synchronous services. No reentry,
 * concurrency, relocation or retained borrowed pointers.
 * Services receive all semantic arguments, including original stack arguments.
 * Only count argument words are readable; inherited services can supply shorter
 * arrays than the maximum public entry argument buffer.
 * The temporary map also resolves explicit private output pointers. They are
 * valid only within that service and must be initialized as its contract requires.
 * Original scalar results are written to result[0], with result[1] set to zero.
 * New API statuses
 * -200/-201/-202/-203 mean invalid API, missing mapping, domain violation and
 * work/service budget exhaustion. Partial writes are retained on failure;
 * result storage is written only after successful completion. */
int hyperrig_effect_parameters_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_parameters_io *io);

/* Join actual parameter probe/commit/fast-update entries to the unchanged
 * scene application. Other scene services retain the supplied boundary.
 * Supported entries are inner 02009e14, apply 0200a1d6, select 02014366 and
 * flush 020148ba. Select/flush have no scalar result and publish zero. The
 * scene orchestration also consumes service budget for its parameter entries;
 * inherited budget/domain statuses are translated to the statuses above. */
int hyperrig_effect_parameters_scene(uint32_t entry, uint32_t scene,
    uint32_t *result, const hyperrig_effect_parameters_io *io);
/* Advance the existing stage with the parameter producer's actual shared RAM. */
int hyperrig_effect_parameters_stage(uint32_t stage, uint32_t samples,
    uint32_t count, const hyperrig_effect_parameters_io *io);
#endif
