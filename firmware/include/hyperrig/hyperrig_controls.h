/* Reconstructed UltraRig M5.71 control logic, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CONTROL_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CONTROLS_H
#define HYPERRIG_CONTROLS_H

#include <stdint.h>

enum {
    HYPERRIG_CONTROL_GLOBAL_BYTES = 270,
    HYPERRIG_CONTROL_STATE_BYTES = 1860,
    HYPERRIG_CONTROL_LOGICAL_COUNT = 4,
    HYPERRIG_CONTROL_PHYSICAL_COUNT = 5
};

/* Portable storage for the bounded prefixes read by the recovered functions.
 * These are not target pointers or a definition of the complete firmware state.
 * Bytes retain original offsets and little-endian scalar encoding so that
 * untouched state can be compared with the instruction-level reference. */
typedef struct {
    uint8_t global[HYPERRIG_CONTROL_GLOBAL_BYTES];
    uint8_t state[HYPERRIG_CONTROL_STATE_BYTES];
    uint8_t repeat_owner;
} hyperrig_controls;

/* Boundary of the unreconstructed action executor at original 0x020149b6.
 * Event codes 0, 1 and 2 retain their original values. No preset, GPIO, LED or
 * protocol mutation is implemented by this component. The callback may be NULL.
 * Callback effects and concurrent IRQ/task execution are outside verification. */
typedef void (*hyperrig_control_emit)(void *opaque, unsigned logical, unsigned event);

/* Last matching slot wins, including duplicate mappings. -1 means no match or
 * invalid input. Original map: global[116..119]; physical indices 0..4. */
int hyperrig_controls_logical(const hyperrig_controls *controls, unsigned physical);

/* Reconstructs 0x0200c9c2..0x0200c9f4. Returns 0/1, or -1 for invalid input. */
int hyperrig_controls_immediate(const hyperrig_controls *controls, unsigned logical);

/* Reconstructs 0x02014c04..0x02014d44 for physical indices 0..4 and levels 0/1.
 * 1 means pressed, as derived from the original active-low GPIO caller.
 * stamp_a/stamp_b are opaque original 32-bit arguments; no time unit is assumed.
 * Scalar validation is a new API boundary: -1 leaves all bytes/callbacks intact.
 * Returns 0 otherwise. Does not initialize the context, scan pins, advance
 * timers, execute actions, or adapt the original four-slot layout to MINI. */
int hyperrig_controls_transition(hyperrig_controls *controls, unsigned physical,
                                unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                                hyperrig_control_emit emit, void *opaque);

#endif
