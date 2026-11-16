/* Hand reconstruction of UltraRig TANK-G M5.71 switch transition logic.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CONTROL_RECONSTRUCTION.md.
 * No hardware access or action executor is supplied by this component. */
#include "hyperrig/hyperrig_controls.h"

enum {
    GLOBAL_IMMEDIATE_MASK = 11,
    GLOBAL_MAP = 116,
    GLOBAL_ACTION_1 = 239,
    GLOBAL_ACTION_2 = 242,
    GLOBAL_ACTION_STRIDE = 9,
    STATE_ENABLED = 74,
    STATE_EVENT_1 = 932,
    STATE_SKIP_RELEASE = 960,
    STATE_PENDING = 964,
    STATE_REPEAT_DEADLINE = 1508,
    STATE_PHYSICAL = 1567,
    STATE_TIMER_1 = 1608,
    STATE_TIMER_2 = 1616,
    STATE_STAMP_A = 1828,
    STATE_STAMP_B = 1844
};

static uint32_t read32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static void write32(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i)
        p[i] = (uint8_t)(value >> (8 * i));
}

static void clear16(uint8_t *p)
{
    p[0] = p[1] = 0;
}

int hyperrig_controls_logical(const hyperrig_controls *controls, unsigned physical)
{
    unsigned i;
    int logical = -1;
    if (!controls || physical >= HYPERRIG_CONTROL_PHYSICAL_COUNT)
        return -1;
    for (i = 0; i < HYPERRIG_CONTROL_LOGICAL_COUNT; ++i)
        if (controls->global[GLOBAL_MAP + i] == physical)
            logical = (int)i;
    return logical;
}

int hyperrig_controls_immediate(const hyperrig_controls *controls, unsigned logical)
{
    if (!controls || logical >= HYPERRIG_CONTROL_LOGICAL_COUNT)
        return -1;
    if (controls->global[GLOBAL_ACTION_2 + GLOBAL_ACTION_STRIDE * logical])
        return 0;
    if (!controls->global[GLOBAL_ACTION_1 + GLOBAL_ACTION_STRIDE * logical])
        return 1;
    return (controls->global[GLOBAL_IMMEDIATE_MASK] >> logical) & 1;
}

static void stamp(hyperrig_controls *controls, unsigned logical, uint32_t a, uint32_t b)
{
    write32(controls->state + STATE_STAMP_A + 4 * logical, a);
    write32(controls->state + STATE_STAMP_B + 4 * logical, b);
}

int hyperrig_controls_transition(hyperrig_controls *controls, unsigned physical,
                                unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                                hyperrig_control_emit emit, void *opaque)
{
    int mapped;
    unsigned logical, event;
    uint8_t *state;
    if (!controls || physical >= HYPERRIG_CONTROL_PHYSICAL_COUNT || pressed > 1)
        return -1;
    state = controls->state;
    if (state[STATE_PHYSICAL + physical] == pressed)
        return 0;
    /* Raw state is recorded even when action processing is disabled/unmapped. */
    state[STATE_PHYSICAL + physical] = (uint8_t)pressed;
    if (!state[STATE_ENABLED])
        return 0;
    mapped = hyperrig_controls_logical(controls, physical);
    if (mapped < 0)
        return 0;
    logical = (unsigned)mapped;
    if (pressed) {
        clear16(state + STATE_TIMER_1 + 2 * logical);
        state[STATE_EVENT_1 + logical] = 0;
        state[STATE_SKIP_RELEASE + logical] = 0;
        /* Native signed comparison uses the wrapped 32-bit subtraction. */
        if (controls->repeat_owner == logical + 1 &&
            ((stamp_b - read32(state + STATE_REPEAT_DEADLINE)) & UINT32_C(0x80000000))) {
            write32(state + STATE_REPEAT_DEADLINE, stamp_b + UINT32_C(2500));
            state[STATE_PENDING + logical] = 0;
            state[STATE_SKIP_RELEASE + logical] = 1;
            state[STATE_EVENT_1 + logical] = 1;
            stamp(controls, logical, stamp_a, stamp_b);
            event = 1;
        } else {
            controls->repeat_owner = 0;
            if (!state[STATE_PENDING + logical])
                stamp(controls, logical, stamp_a, stamp_b);
            if (!hyperrig_controls_immediate(controls, logical))
                return 0;
            state[STATE_SKIP_RELEASE + logical] = 1;
            event = 0;
        }
    } else {
        if (state[STATE_SKIP_RELEASE + logical]) {
            state[STATE_SKIP_RELEASE + logical] = 0;
            return 0;
        }
        if (state[STATE_EVENT_1 + logical])
            return 0;
        if (!controls->global[GLOBAL_ACTION_2 + GLOBAL_ACTION_STRIDE * logical]) {
            event = 0;
        } else if (state[STATE_PENDING + logical]) {
            state[STATE_PENDING + logical] = 0;
            event = 2;
        } else {
            state[STATE_PENDING + logical] = 1;
            clear16(state + STATE_TIMER_2 + 2 * logical);
            return 0;
        }
    }
    if (emit)
        emit(opaque, logical, event);
    return 0;
}
