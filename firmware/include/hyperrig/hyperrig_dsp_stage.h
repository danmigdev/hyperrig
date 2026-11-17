/* Reconstructed M5.71 stage routing, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_STAGE_RECONSTRUCTION.md. */
#ifndef HYPERRIG_DSP_STAGE_H
#define HYPERRIG_DSP_STAGE_H
#include "hyperrig_audio_task.h"

/* Original address tokens and borrowed mapped state. The mapping/callback
 * contract is the same as audio_task; no mapped state is copied into a second
 * runtime. External effect bodies 0x01c0f678 and 0x01c10446 remain services.
 * Services may synchronously mutate mapped state and audio. Clock targets
 * must be zero or 0x01c04862 at every read. No concurrent mutation or reentry.
 * stage is 0 or 1; count is 0..256. Route lists have at most ten slot indices
 * and the supplemental list at most eight, all indices below sixteen.
 * Effects have type 0..39 and branch 0..2. Missing mappings return -201;
 * domain violations return -202; invalid API returns -200. Partial effects
 * are retained on mapping/domain errors, which are not resumable states. */
int hyperrig_dsp_stage_run(uint32_t stage,uint32_t samples,uint32_t count,
    const hyperrig_audio_task_io *io);

/* Complete original direct helpers listed in the module documentation.
 * arguments always contains five words; unused words are ignored. result
 * records defined scalar returns (capability/active/route_mask/clock/delay),
 * and is zero for original void helpers. API and mapped storage are disjoint.
 * Filter sections and sample spans use compatible aligned int32_t storage.
 * Mapped mix descriptors must be disjoint from destination/sample writes;
 * clock services may mutate them, and stereo_finish reloads/restores only the
 * original fields at the original callback boundaries. Distinct mapped address
 * spans must refer to distinct host storage, preserving address identity.
 * The two-span mixer permits exact source/destination alias; partial overlaps
 * follow original sequential sample ordering, never a buffered substitute. */
int hyperrig_dsp_stage_helper(uint32_t target,const uint32_t arguments[5],
    uint32_t *result,const hyperrig_audio_task_io *io);

/* Join the unchanged complete audio task to this recovered stage body. Its
 * original observation/resume boundaries and remaining services are retained.
 * The original task calls stages zero and one with 128-sample blocks. */
int hyperrig_dsp_stage_audio_resume(hyperrig_audio_task *task,uint32_t wait_budget,
    uint32_t frame_budget,const hyperrig_audio_task_io *io);
#endif
