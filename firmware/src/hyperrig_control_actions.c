/* Hand reconstruction of UltraRig TANK-G M5.71 action dispatch and timers.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CONTROL_ACTIONS.md. */
#include "hyperrig/hyperrig_control_actions.h"

static uint32_t read32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static unsigned read16(const uint8_t *p)
{
    return (unsigned)p[0] | (unsigned)p[1] << 8;
}

static void write32(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i)
        p[i] = (uint8_t)(value >> (8 * i));
}

static uint8_t global_byte(const hyperrig_control_runtime *runtime, unsigned offset)
{
    return offset < HYPERRIG_CONTROL_GLOBAL_BYTES ? runtime->controls.global[offset]
        : runtime->action_tail[offset - HYPERRIG_CONTROL_GLOBAL_BYTES];
}

int hyperrig_controls_action(hyperrig_control_runtime *runtime, unsigned logical,
                             unsigned event, hyperrig_control_service_call call,
                             void *opaque)
{
    uint8_t *state;
    unsigned record, type;
    uint32_t now, value;
    if (!runtime || !call || logical >= 4 || event >= 3)
        return -1;
    state = runtime->controls.state;
    record = 236 + logical * 9 + event * 3;
    call(opaque, HYPERRIG_CONTROL_NOTIFY, 9, logical,
         event | (uint32_t)global_byte(runtime, record) << 8 |
         (uint32_t)global_byte(runtime, record + 1) << 16);
    /* Original 0x0200c996 reads global+24 and multiplies by ten, wrapping. */
    now = read32(runtime->controls.global + 24) * UINT32_C(10);
    write32(state + 968, read32(state + 1828 + logical * 4));
    value = read32(state + 1844 + logical * 4);
    type = global_byte(runtime, record);
    write32(state + 972, value);
    if (type == 7)
        write32(state + 928, value);
    write32(state + 1812 + logical * 4, now);
    state[924 + logical] = 1;
    write32(state + 812, now);
    if (event == 1 && type == 7 && read16(state + 1608 + logical * 2)) {
        runtime->controls.repeat_owner = (uint8_t)(logical + 1);
        write32(state + 1508, now + UINT32_C(2500));
        return 0;
    }
    if (read32(state + 956) && type != 5 && type != 6) {
        call(opaque, HYPERRIG_CONTROL_FLUSH_PENDING, 0, 0, 0);
        type = global_byte(runtime, record);
    }
    switch (type) {
    case 1:
        call(opaque, HYPERRIG_CONTROL_SCENE, global_byte(runtime, record + 1), 0, 0);
        break;
    case 2:
        if (!call(opaque, HYPERRIG_CONTROL_PRESET_EXISTS,
                  global_byte(runtime, record + 1), 0, 0))
            break;
        if (call(opaque, HYPERRIG_CONTROL_PRESET_LOAD,
                 global_byte(runtime, record + 1), 0, 0))
            break;
        value = global_byte(runtime, record + 2);
        if (value <= 3)
            call(opaque, HYPERRIG_CONTROL_SCENE, value, 0, 0);
        break;
    case 3:
    case 4:
        call(opaque, HYPERRIG_CONTROL_PRESET_STEP, type == 3 ? 1 : UINT32_MAX, 0, 0);
        break;
    case 5:
    case 6:
        write32(state + 956, read32(state + 956) + (type == 5 ? 1 : UINT32_MAX));
        break;
    case 7:
        call(opaque, HYPERRIG_CONTROL_TAP, read32(state + 968), read32(state + 972), 0);
        break;
    case 8:
        value = call(opaque, HYPERRIG_CONTROL_EFFECT_RESOLVE, record, 0, 0);
        if (!(value & UINT32_C(0x80000000))) {
            uint32_t enabled = call(opaque, HYPERRIG_CONTROL_EFFECT_GET, value, 0, 0);
            call(opaque, HYPERRIG_CONTROL_EFFECT_SET, value, enabled == 0, 0);
        } else {
            uint32_t auxiliary = global_byte(runtime, record + 2);
            call(opaque, HYPERRIG_CONTROL_NOTIFY, 10,
                 auxiliary == 255 ? 768 : (global_byte(runtime, record + 1) | 768),
                 auxiliary);
        }
        break;
    case 9:
        state[52] = state[52] == 0;
        break;
    case 10:
        value = call(opaque, HYPERRIG_CONTROL_MODE_GET, 0, 0, 0);
        if (call(opaque, HYPERRIG_CONTROL_MODE_SET, value == 0, 0, 0))
            call(opaque, HYPERRIG_CONTROL_NOTIFY, 10, 511, 0);
        break;
    default:
        break;
    }
    return 0;
}

static uint32_t advance_timer(uint8_t *timer, uint32_t delta)
{
    /* The native addition wraps before capping; preserve that unusual edge. */
    uint32_t value = (uint32_t)read16(timer) + delta;
    if (value >= 60000)
        value = 60000;
    timer[0] = (uint8_t)value;
    timer[1] = (uint8_t)(value >> 8);
    return value;
}

int hyperrig_controls_tick(hyperrig_control_runtime *runtime, uint32_t delta,
                           hyperrig_control_service_call call, void *opaque)
{
    uint8_t *state;
    unsigned logical;
    if (!runtime || !call)
        return -1;
    state = runtime->controls.state;
    if (!state[74]) {
        call(opaque, HYPERRIG_CONTROL_DISABLED_TICK, delta, 0, 0);
        return 0;
    }
    for (logical = 0; logical < 4; ++logical) {
        /* Retain the captured index across a callback, like native r14.
         * All byte-valued mappings fit the initialized state prefix, although
         * values above 4 do not identify known physical switch inputs. */
        unsigned physical = runtime->controls.global[116 + logical];
        if (state[1567 + physical] && !state[932 + logical]) {
            uint32_t timer = advance_timer(state + 1608 + logical * 2, delta);
            if (timer >= 1000 && runtime->controls.global[239 + logical * 9]) {
                state[932 + logical] = 1;
                state[964 + logical] = 0;
                hyperrig_controls_action(runtime, logical, 1, call, opaque);
            }
        }
        if (state[964 + logical] && !state[1567 + physical]) {
            uint32_t timer = advance_timer(state + 1616 + logical * 2, delta);
            if (timer >= 301) {
                state[964 + logical] = 0;
                hyperrig_controls_action(runtime, logical, 0, call, opaque);
            }
        }
    }
    return 0;
}

struct edge_context {
    hyperrig_control_runtime *runtime;
    hyperrig_control_service_call call;
    void *opaque;
};

static void dispatch_edge(void *opaque, unsigned logical, unsigned event)
{
    struct edge_context *edge = (struct edge_context *)opaque;
    hyperrig_controls_action(edge->runtime, logical, event, edge->call, edge->opaque);
}

int hyperrig_controls_edge(hyperrig_control_runtime *runtime, unsigned physical,
                           unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                           hyperrig_control_service_call call, void *opaque)
{
    struct edge_context edge;
    if (!runtime || !call || physical >= 5 || pressed > 1)
        return -1;
    edge.runtime = runtime;
    edge.call = call;
    edge.opaque = opaque;
    return hyperrig_controls_transition(&runtime->controls, physical, pressed,
                                        stamp_a, stamp_b, dispatch_edge, &edge);
}
