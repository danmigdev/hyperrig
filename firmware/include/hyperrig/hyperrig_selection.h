/* Reconstructed UltraRig M5.71 selection logic, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/SELECTION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_SELECTION_H
#define HYPERRIG_SELECTION_H

#include "hyperrig_control_actions.h"

/* Sparse views of additional original RAM, not a target ABI or preset format.
 * scene_active: state+11936+260*i.
 * chain_count/order: 0x01c32db0+14+i and +348+10*i+j.
 * effect_header: first three bytes at 0x01c2c220+480*i (type, enabled, present).
 * Chains have at most ten entries each; the flattened view stops at sixteen.
 * The previous control context and its verified source remain unchanged. */
typedef struct {
    hyperrig_control_runtime controls;
    uint8_t scene_active[4];
    uint8_t chain_count[2];
    uint8_t chain_order[2][10];
    uint8_t effect_header[16][3];
} hyperrig_selection_runtime;

enum hyperrig_selection_service {
    HYPERRIG_SELECTION_CLOCK = 0x01c04862,
    HYPERRIG_SELECTION_APPLY_SCENE = 0x0200a1d6,
    HYPERRIG_SELECTION_SCENE_REPORT = 0x0200a228
};

/* New service arguments: CLOCK(), APPLY_SCENE(scene), and
 * SCENE_REPORT(apply_result, start_clock). Existing preset availability/load,
 * effect-set and other unreconstructed services retain their previous contract.
 * Callbacks must preserve chain counts <=10 and current scene (global+88)
 * as 0..3 or a negative int32 bit pattern; no re-entry/concurrent mutation.
 * Invalid runtime, callback or API scalar returns -1 before writes/calls.
 * All other entry points return 0, except resolve_effect as specified below. */
int hyperrig_selection_step_preset(hyperrig_selection_runtime *runtime, uint32_t step,
                                  hyperrig_control_service_call call, void *opaque);
int hyperrig_selection_flush_scenes(hyperrig_selection_runtime *runtime,
                                   hyperrig_control_service_call call, void *opaque);
int hyperrig_selection_scene(hyperrig_selection_runtime *runtime, uint32_t scene,
                            hyperrig_control_service_call call, void *opaque);

/* record_offset must identify one of the twelve original three-byte records.
 * Returns the resolved raw byte index, -1 for no binding, -2 for invalid API.
 * An absolute-position binding can return an absent/out-of-range effect ID,
 * just as the original does; the subsequent effect-state getter checks it. */
int hyperrig_selection_resolve_effect(const hyperrig_selection_runtime *runtime,
                                     unsigned record_offset);

int hyperrig_selection_action(hyperrig_selection_runtime *runtime, unsigned logical,
                              unsigned event, hyperrig_control_service_call call,
                              void *opaque);
int hyperrig_selection_tick(hyperrig_selection_runtime *runtime, uint32_t delta,
                            hyperrig_control_service_call call, void *opaque);
int hyperrig_selection_edge(hyperrig_selection_runtime *runtime, unsigned physical,
                            unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                            hyperrig_control_service_call call, void *opaque);

#endif
