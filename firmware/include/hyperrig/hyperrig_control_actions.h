/* Reconstructed UltraRig M5.71 controls, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CONTROL_ACTIONS.md. */
#ifndef HYPERRIG_CONTROL_ACTIONS_H
#define HYPERRIG_CONTROL_ACTIONS_H

#include "hyperrig_controls.h"

/* The final action's argument/auxiliary bytes extend the previously recovered
 * global prefix from 270 to 272 bytes. Keep the transition component's layout
 * intact; action_tail holds original global offsets 270 and 271. */
typedef struct {
    hyperrig_controls controls;
    uint8_t action_tail[2];
} hyperrig_control_runtime;

/* Addresses identify unreconstructed original call boundaries, not callable
 * host pointers. Names describe observed roles, not recovered original symbols. */
enum hyperrig_control_service {
    HYPERRIG_CONTROL_NOTIFY = 0x02002d10,
    HYPERRIG_CONTROL_FLUSH_PENDING = 0x020148ba,
    HYPERRIG_CONTROL_SCENE = 0x02014366,
    HYPERRIG_CONTROL_PRESET_EXISTS = 0x0200cf88,
    HYPERRIG_CONTROL_PRESET_LOAD = 0x0200ca7e,
    HYPERRIG_CONTROL_PRESET_STEP = 0x02014952,
    HYPERRIG_CONTROL_TAP = 0x0200a4b2,
    HYPERRIG_CONTROL_EFFECT_RESOLVE = 0x0201499c,
    HYPERRIG_CONTROL_EFFECT_GET = 0x020308ea,
    HYPERRIG_CONTROL_EFFECT_SET = 0x0200d060,
    HYPERRIG_CONTROL_MODE_GET = 0x0200733e,
    HYPERRIG_CONTROL_MODE_SET = 0x02008ca2,
    HYPERRIG_CONTROL_DISABLED_TICK = 0x020146ae
};

/* Unused arguments are zero. EFFECT_RESOLVE receives an original global byte
 * offset in a, not a host/target pointer. Signed return/argument values use
 * their original uint32 bit patterns. See CONTROL_ACTIONS.md for arities.
 * The callback may synchronously mutate this runtime through opaque; it must
 * not re-enter these functions. External handler implementations are required
 * for integration. A recorder alone does not execute their effects. */
typedef uint32_t (*hyperrig_control_service_call)(void *opaque, uint32_t service,
                                                uint32_t a, uint32_t b, uint32_t c);

/* A non-null callback is required. Invalid context/callback/scalars return -1
 * before any writes or calls. Valid calls return 0. No initialization, target
 * ABI, concurrency guarantees or physical time units are supplied. */
int hyperrig_controls_action(hyperrig_control_runtime *runtime, unsigned logical,
                             unsigned event, hyperrig_control_service_call call,
                             void *opaque);
int hyperrig_controls_tick(hyperrig_control_runtime *runtime, uint32_t delta,
                           hyperrig_control_service_call call, void *opaque);
int hyperrig_controls_edge(hyperrig_control_runtime *runtime, unsigned physical,
                           unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                           hyperrig_control_service_call call, void *opaque);

#endif
