/* Reconstructed M5.71 constructor/signal integration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_CONFIGURED_SIGNAL_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_configured_signal.h"

int hyperrig_effect_configured_signal_prepare(uint32_t effect,
    const hyperrig_effect_configured_signal_io *io)
{
    uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS]={0},result[2];
    hyperrig_effect_construction_io construction;
    if(!io)return -200;
    construction.map=io->map;construction.call=io->call;construction.opaque=io->opaque;
    construction.service_budget=io->construction_service_budget;
    construction.work_budget=io->construction_work_budget;arguments[0]=effect;
    return hyperrig_effect_construction_execute(UINT32_C(0x0202cf62),arguments,result,&construction);
}
static hyperrig_effect_signal_io signal_io(const hyperrig_effect_configured_signal_io *io)
{
    hyperrig_effect_signal_io signal={io->map,io->call,io->opaque,io->signal_block_budget};
    return signal;
}
int hyperrig_effect_configured_signal_execute(uint32_t entry,const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t *result,const hyperrig_effect_configured_signal_io *io)
{
    hyperrig_effect_signal_io signal;
    if(!io)return -200;
    signal=signal_io(io);return hyperrig_effect_signal_execute(entry,arguments,result,&signal);
}
int hyperrig_effect_configured_signal_stage(uint32_t stage,uint32_t samples,uint32_t count,
    const hyperrig_effect_configured_signal_io *io)
{
    hyperrig_effect_signal_io signal;
    if(!io)return -200;
    signal=signal_io(io);return hyperrig_effect_signal_stage(stage,samples,count,&signal);
}
int hyperrig_effect_configured_signal_audio_resume(hyperrig_audio_task *task,uint32_t wait_budget,uint32_t frame_budget,
    const hyperrig_effect_configured_signal_io *io)
{
    hyperrig_effect_signal_io signal;
    if(!io)return -200;
    signal=signal_io(io);return hyperrig_effect_signal_audio_resume(task,wait_budget,frame_budget,&signal);
}
