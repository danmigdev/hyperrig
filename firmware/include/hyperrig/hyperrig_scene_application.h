/* Reconstructed UltraRig M5.71 scene application, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/SCENE_APPLICATION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_SCENE_APPLICATION_H
#define HYPERRIG_SCENE_APPLICATION_H
#include <stdint.h>

typedef uint8_t *(*hyperrig_scene_application_map)(void *opaque,
    uint32_t address, uint32_t bytes, int writable);
typedef uint32_t (*hyperrig_scene_application_service)(void *opaque,
    uint32_t target, const uint32_t arguments[5], uint32_t count);
typedef struct {
    hyperrig_scene_application_map map;
    hyperrig_scene_application_service call;
    void *opaque;
    uint32_t call_budget;
} hyperrig_scene_application_io;

/* Borrowed original-address storage, never a copy of the earlier small state
 * view. Provide globals 0x01c1f180/272, state 0x01c26890/12976, effects
 * 0x01c2c220/7680, configuration 0x01c1f7d4/68 and callbacks 0x01c34190/768.
 * The callbacks region includes the scene-busy byte at offset 761.
 * Maps are pure, stable and writable where requested. Services may mutate
 * mapped bytes synchronously, but cannot change the IO/mapping lifetimes,
 * re-enter or retain borrowed pointers. Output and IO objects are disjoint
 * from mapped storage. Every argument uses an original integer address token.
 * Unused service argument words are zero. A positive call budget is required.
 * New API status: 0 completed, -200 invalid arguments, -201 missing mapping,
 * -202 service budget, -203 inherited transition domain/mapping guard.
 * Guards can follow partial writes; there is no rollback.
 * Native results are returned separately through result. */
int hyperrig_scene_application_inner(uint32_t scene, uint32_t *result,
    const hyperrig_scene_application_io *io);
int hyperrig_scene_application_apply(uint32_t scene, uint32_t *result,
    const hyperrig_scene_application_io *io);
int hyperrig_scene_application_report(uint32_t result, uint32_t started,
    uint32_t *packed, const hyperrig_scene_application_io *io);

/* Enabled scene transitions execute the real borrowed request and installed
 * gain notification. Additionally map control 0x01c32db0/640, active filters
 * 0x01c33030/176 and staged records 0x01c330e0/176. The transition adapter's
 * typed storage and disabled-bank parameter bounds apply. Alternate installed
 * notification tokens remain explicit one-argument services. */

/* Reused selection/flush bodies with real scene application and reporting.
 * Select accepts every uint32; indices above three are native no-ops. Inner
 * and apply require 0..3 and do not test the scene's availability byte.
 * Flush requires current scene 0..3 or a negative signed32 bit pattern.
 * Selection's incidental return register is not an API result. */
int hyperrig_scene_application_select(uint32_t scene,
    const hyperrig_scene_application_io *io);
int hyperrig_scene_application_flush(const hyperrig_scene_application_io *io);
#endif
