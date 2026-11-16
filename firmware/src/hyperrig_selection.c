/* Hand reconstruction of UltraRig TANK-G M5.71 preset/scene/effect selection.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/SELECTION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_selection.h"

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

static int negative(uint32_t bits)
{
    return (bits & UINT32_C(0x80000000)) != 0;
}

static int valid(const hyperrig_selection_runtime *runtime)
{
    uint32_t scene;
    if (!runtime || runtime->chain_count[0] > 10 || runtime->chain_count[1] > 10)
        return 0;
    scene = read32(runtime->controls.controls.global + 88);
    return scene <= 3 || negative(scene);
}

static uint8_t global_byte(const hyperrig_selection_runtime *runtime, unsigned offset)
{
    return offset < 270 ? runtime->controls.controls.global[offset]
        : runtime->controls.action_tail[offset - 270];
}

/* Signed remainder after a wrapping add, without signed-overflow UB or
 * implementation-defined conversion of negative uint32 bit patterns. */
static uint32_t remainder32(uint32_t bits, uint32_t divisor)
{
    return negative(bits) ? UINT32_C(0) - ((UINT32_C(0) - bits) % divisor)
                          : bits % divisor;
}

static void step_preset(hyperrig_selection_runtime *runtime, uint32_t step,
                        hyperrig_control_service_call call, void *opaque)
{
    uint32_t previous = read32(runtime->controls.controls.global + 92);
    uint32_t fallback = step == 0 || negative(step) ? 31 : 0;
    unsigned attempt;
    for (attempt = 0; attempt < 32; ++attempt) {
        uint32_t selected = negative(previous) ? fallback
            : remainder32(previous + step + UINT32_C(32), 32);
        if (call(opaque, HYPERRIG_CONTROL_PRESET_EXISTS, selected, 0, 0) &&
            !call(opaque, HYPERRIG_CONTROL_PRESET_LOAD, selected, 0, 0))
            return;
        previous = selected;
    }
}

static void apply_scene(hyperrig_selection_runtime *runtime, uint32_t scene,
                        hyperrig_control_service_call call, void *opaque)
{
    uint32_t start = call(opaque, HYPERRIG_SELECTION_CLOCK, 0, 0, 0);
    uint32_t result = call(opaque, HYPERRIG_SELECTION_APPLY_SCENE, scene, 0, 0);
    if (!runtime->controls.controls.state[740]) {
        uint32_t report = call(opaque, HYPERRIG_SELECTION_SCENE_REPORT, result, start, 0);
        call(opaque, HYPERRIG_CONTROL_NOTIFY, 8, scene, report);
    }
}

static void select_scene(hyperrig_selection_runtime *runtime, uint32_t scene,
                         hyperrig_control_service_call call, void *opaque)
{
    if (scene <= 3 && runtime->scene_active[scene])
        apply_scene(runtime, scene, call, opaque);
}

static void flush_scenes(hyperrig_selection_runtime *runtime,
                         hyperrig_control_service_call call, void *opaque)
{
    uint8_t *state = runtime->controls.controls.state;
    uint32_t steps = read32(state + 956), current, remaining, increment, fallback;
    uint32_t selected = UINT32_MAX;
    unsigned active = 0, i;
    write32(state + 956, 0);
    if (steps == 0)
        return;
    remaining = negative(steps) ? UINT32_C(0) - steps : steps;
    /* Native abs saturates INT32_MIN to INT32_MAX. */
    if (remaining == UINT32_C(0x80000000))
        remaining = UINT32_C(0x7fffffff);
    for (i = 0; i < 4; ++i)
        active += runtime->scene_active[i] != 0;
    if (!active)
        return;
    /* No calls occur during selection, and concurrent mutation is excluded.
     * After the first step, active scenes form a cycle. Reduce complete cycles
     * to bound work even for extreme counters; preserve the final selection. */
    remaining = (remaining - 1) % active + 1;
    increment = negative(steps) ? 3 : 5;
    fallback = negative(steps) ? 3 : 0;
    current = read32(runtime->controls.controls.global + 88);
    while (remaining) {
        unsigned attempt;
        for (attempt = 0; attempt < 4; ++attempt) {
            selected = negative(current) ? fallback : (current + increment) % 4;
            if (runtime->scene_active[selected])
                break;
            current = selected;
        }
        if (attempt == 4)
            return;
        --remaining;
        current = selected;
    }
    apply_scene(runtime, selected, call, opaque);
}

static unsigned effect_type(const hyperrig_selection_runtime *runtime, unsigned index)
{
    return index < 16 && runtime->effect_header[index][2]
        ? runtime->effect_header[index][0] : 0;
}

static unsigned effect_enabled(const hyperrig_selection_runtime *runtime, unsigned index)
{
    return index < 16 && runtime->effect_header[index][2]
        ? runtime->effect_header[index][1] : 0;
}

static int resolve_effect(const hyperrig_selection_runtime *runtime, unsigned record)
{
    uint8_t indices[16], types[16];
    unsigned count = 0, chain, item, argument, auxiliary, occurrence = 0;
    for (chain = 0; chain < 2; ++chain) {
        for (item = 0; item < runtime->chain_count[chain] && count < 16; ++item) {
            unsigned index = runtime->chain_order[chain][item];
            indices[count] = (uint8_t)index;
            types[count++] = (uint8_t)effect_type(runtime, index);
        }
    }
    if (global_byte(runtime, record) != 8)
        return -1;
    argument = global_byte(runtime, record + 1);
    auxiliary = global_byte(runtime, record + 2);
    if (auxiliary == 255)
        return argument < count ? indices[argument] : -1;
    if (argument == 0)
        return -1;
    for (item = 0; item < count; ++item) {
        if (types[item] == argument) {
            if (occurrence == auxiliary)
                return indices[item];
            ++occurrence;
        }
    }
    return -1;
}

struct selection_call {
    hyperrig_selection_runtime *runtime;
    hyperrig_control_service_call call;
    void *opaque;
};

static uint32_t dispatch(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    struct selection_call *context = (struct selection_call *)opaque;
    hyperrig_selection_runtime *runtime = context->runtime;
    switch (service) {
    case HYPERRIG_CONTROL_PRESET_STEP:
        step_preset(runtime, a, context->call, context->opaque);
        return 0;
    case HYPERRIG_CONTROL_SCENE:
        select_scene(runtime, a, context->call, context->opaque);
        return 0;
    case HYPERRIG_CONTROL_FLUSH_PENDING:
        flush_scenes(runtime, context->call, context->opaque);
        return 0;
    case HYPERRIG_CONTROL_EFFECT_RESOLVE:
        return (uint32_t)resolve_effect(runtime, a);
    case HYPERRIG_CONTROL_EFFECT_GET:
        return effect_enabled(runtime, a);
    default:
        return context->call(context->opaque, service, a, b, c);
    }
}

int hyperrig_selection_step_preset(hyperrig_selection_runtime *runtime, uint32_t step,
                                  hyperrig_control_service_call call, void *opaque)
{
    if (!valid(runtime) || !call)
        return -1;
    step_preset(runtime, step, call, opaque);
    return 0;
}

int hyperrig_selection_flush_scenes(hyperrig_selection_runtime *runtime,
                                   hyperrig_control_service_call call, void *opaque)
{
    if (!valid(runtime) || !call)
        return -1;
    flush_scenes(runtime, call, opaque);
    return 0;
}

int hyperrig_selection_scene(hyperrig_selection_runtime *runtime, uint32_t scene,
                            hyperrig_control_service_call call, void *opaque)
{
    if (!valid(runtime) || !call)
        return -1;
    select_scene(runtime, scene, call, opaque);
    return 0;
}

int hyperrig_selection_resolve_effect(const hyperrig_selection_runtime *runtime, unsigned record)
{
    if (!valid(runtime) || record < 236 || record > 269 || (record - 236) % 3)
        return -2;
    return resolve_effect(runtime, record);
}

int hyperrig_selection_action(hyperrig_selection_runtime *runtime, unsigned logical,
                              unsigned event, hyperrig_control_service_call call, void *opaque)
{
    struct selection_call context = {runtime, call, opaque};
    if (!valid(runtime) || !call)
        return -1;
    return hyperrig_controls_action(&runtime->controls, logical, event, dispatch, &context);
}

int hyperrig_selection_tick(hyperrig_selection_runtime *runtime, uint32_t delta,
                            hyperrig_control_service_call call, void *opaque)
{
    struct selection_call context = {runtime, call, opaque};
    if (!valid(runtime) || !call)
        return -1;
    return hyperrig_controls_tick(&runtime->controls, delta, dispatch, &context);
}

int hyperrig_selection_edge(hyperrig_selection_runtime *runtime, unsigned physical,
                            unsigned pressed, uint32_t stamp_a, uint32_t stamp_b,
                            hyperrig_control_service_call call, void *opaque)
{
    struct selection_call context = {runtime, call, opaque};
    if (!valid(runtime) || !call)
        return -1;
    return hyperrig_controls_edge(&runtime->controls, physical, pressed, stamp_a, stamp_b,
                                 dispatch, &context);
}
