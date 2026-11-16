/* Hand reconstruction of UltraRig TANK-G M5.71 loader and binding/report helpers.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_LOADER_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_preset_loader.h"

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

static int valid(const hyperrig_loader_runtime *runtime)
{
    const hyperrig_selection_runtime *selection;
    uint32_t scene;
    if (!runtime)
        return 0;
    selection = &runtime->preset.storage.selection;
    scene = read32(selection->controls.controls.global + 88);
    return selection->chain_count[0] <= 10 && selection->chain_count[1] <= 10 &&
           (scene <= 3 || (scene & UINT32_C(0x80000000)));
}

static int valid_io(const hyperrig_loader_io *io)
{
    return io && io->storage.call && io->storage.read && io->apply;
}

uint32_t hyperrig_loader_rate(uint32_t calibration)
{
    return (calibration * UINT32_C(1000)) / 6;
}

static uint32_t rate(const hyperrig_loader_runtime *runtime)
{
    return hyperrig_loader_rate(read32(runtime->preset.storage.selection.controls.controls.global + 44));
}

static uint8_t action_byte(const hyperrig_loader_runtime *runtime, unsigned i)
{
    const hyperrig_control_runtime *controls = &runtime->preset.storage.selection.controls;
    unsigned offset = 236 + i;
    return offset < 270 ? controls->controls.global[offset] : controls->action_tail[offset - 270];
}

static void set_action_byte(hyperrig_loader_runtime *runtime, unsigned i, uint8_t value)
{
    hyperrig_control_runtime *controls = &runtime->preset.storage.selection.controls;
    unsigned offset = 236 + i;
    if (offset < 270)
        controls->controls.global[offset] = value;
    else
        controls->action_tail[offset - 270] = value;
}

int hyperrig_loader_snapshot(const hyperrig_loader_runtime *runtime, uint8_t output[36])
{
    unsigned i;
    if (!runtime || !output)
        return -1;
    for (i = 0; i < 36; ++i)
        output[i] = action_byte(runtime, i);
    for (i = 0; i < 36; i += 3) {
        if (output[i] == 8 && output[i + 2] != 255) {
            uint8_t argument = output[i + 1];
            output[i + 1] = output[i + 2] | 128;
            output[i + 2] = argument;
        }
    }
    return 0;
}

int hyperrig_loader_binding(const uint8_t types[17], uint32_t position,
                             uint8_t *type, uint8_t *occurrence)
{
    unsigned i, count = 0;
    if (!types || types[0] > 16 || !type || !occurrence)
        return -1;
    *type = *occurrence = 0;
    if ((position & UINT32_C(0x80000000)) || position >= types[0])
        return 0;
    for (i = 0; i < position; ++i)
        count += types[i + 1] == types[position + 1];
    *type = types[position + 1];
    *occurrence = (uint8_t)count;
    return 0;
}

int hyperrig_loader_rebind(hyperrig_loader_runtime *runtime)
{
    const hyperrig_selection_runtime *selection;
    uint8_t types[17], actions[36];
    unsigned i, chain, count = 0, rewritten = 0;
    if (!valid(runtime))
        return -1;
    for (i = 0; i < 36; i += 3)
        if (action_byte(runtime, i) == 8 && action_byte(runtime, i + 2) == 255)
            break;
    if (i == 36)
        return 0;
    selection = &runtime->preset.storage.selection;
    for (chain = 0; chain < 2; ++chain) {
        for (i = 0; i < selection->chain_count[chain] && count < 16; ++i) {
            unsigned slot = selection->chain_order[chain][i];
            types[++count] = slot < 16 && selection->effect_header[slot][2]
                ? selection->effect_header[slot][0] : 0;
        }
    }
    types[0] = (uint8_t)count;
    for (i = 0; i < 36; ++i)
        actions[i] = action_byte(runtime, i);
    for (i = 0; i < 36; i += 3) {
        if (actions[i] == 8 && actions[i + 2] == 255 && actions[i + 1] < count) {
            hyperrig_loader_binding(types, actions[i + 1], actions + i + 1, actions + i + 2);
            ++rewritten;
        }
    }
    if (rewritten)
        for (i = 0; i < 36; ++i)
            set_action_byte(runtime, i, actions[i]);
    return (int)rewritten;
}

int hyperrig_loader_compare(const uint8_t *first, const uint8_t *second, uint32_t size)
{
    uint32_t i;
    if (size > 36 || (size && (!first || !second)))
        return -256;
    for (i = 0; i < size; ++i)
        if (first[i] != second[i])
            return (int)first[i] - second[i];
    return 0;
}

static int elapsed(hyperrig_loader_runtime *runtime, uint32_t start,
                    uint32_t *result, const hyperrig_loader_io *io)
{
    uint32_t now = io->storage.call(io->storage.opaque, HYPERRIG_SELECTION_CLOCK, 0, 0, 0);
    uint32_t divisor = rate(runtime);
    if (!divisor)
        return -3;
    *result = (now - start) / divisor;
    return 0;
}

int hyperrig_loader_elapsed(hyperrig_loader_runtime *runtime, uint32_t start,
                             uint32_t *result, const hyperrig_loader_io *io)
{
    if (!valid(runtime) || !valid_io(io) || !result || !rate(runtime))
        return -2;
    return elapsed(runtime, start, result, io);
}

static int report(hyperrig_loader_runtime *runtime, uint32_t preset, uint32_t preflight_time,
                   uint32_t start, uint32_t previous_counter, const hyperrig_loader_io *io)
{
    uint32_t counter = read32(runtime->report_counter), duration, difference;
    if (elapsed(runtime, start, &duration, io))
        return -3;
    if (duration > 65535)
        duration = 65535;
    difference = counter - previous_counter;
    if (difference > 32767)
        difference = 32767;
    io->storage.call(io->storage.opaque, HYPERRIG_CONTROL_NOTIFY, 26,
        (preflight_time << 8) | preset, (difference << 16) | duration);
    return 0;
}

int hyperrig_loader_report(hyperrig_loader_runtime *runtime, uint32_t preset,
                            uint32_t preflight_time, uint32_t start, uint32_t previous_counter,
                            const hyperrig_loader_io *io)
{
    if (!valid(runtime) || !valid_io(io) || !rate(runtime))
        return -2;
    return report(runtime, preset, preflight_time, start, previous_counter, io);
}

int hyperrig_loader_load(hyperrig_loader_runtime *runtime, uint32_t preset,
                          const hyperrig_loader_io *io)
{
    uint8_t header[40], snapshot[36];
    uint8_t *state, *global;
    uint32_t start, end, captured_rate, application_start, counter, application_result;
    uint32_t first_output, second_output, preflight_time;
    int same = 0, rewritten;
    if (!valid(runtime) || !valid_io(io) || rate(runtime) < 1000)
        return -2;
    state = runtime->preset.storage.selection.controls.controls.state;
    global = runtime->preset.storage.selection.controls.controls.global;
    start = io->storage.call(io->storage.opaque, HYPERRIG_SELECTION_CLOCK, 0, 0, 0);
    if (hyperrig_preset_preflight(&runtime->preset, preset, header, &io->storage))
        return -1;
    end = io->storage.call(io->storage.opaque, HYPERRIG_SELECTION_CLOCK, 0, 0, 0);
    captured_rate = rate(runtime);
    if (captured_rate < 1000)
        return -3;
    application_start = io->storage.call(io->storage.opaque, HYPERRIG_SELECTION_CLOCK, 0, 0, 0);
    counter = read32(runtime->report_counter);
    application_result = io->apply(io->storage.opaque, preset, &first_output, &second_output);
    write32(global + 92, preset);
    hyperrig_loader_snapshot(runtime, snapshot);
    preflight_time = (end - start) / (captured_rate / 1000);
    if (state[736])
        same = hyperrig_loader_compare(snapshot, runtime->saved_actions, 36) == 0;
    rewritten = hyperrig_loader_rebind(runtime);
    if (same && rewritten)
        hyperrig_loader_snapshot(runtime, runtime->saved_actions);
    if (report(runtime, preset, preflight_time, application_start, counter, io))
        return -3;
    if (!state[740])
        io->storage.call(io->storage.opaque, HYPERRIG_CONTROL_NOTIFY, 6, preset, application_result);
    return 0;
}

struct load_call {
    hyperrig_loader_runtime *runtime;
    const hyperrig_loader_io *io;
};

static uint32_t dispatch(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    struct load_call *context = (struct load_call *)opaque;
    if (service == HYPERRIG_CONTROL_PRESET_LOAD)
        return (uint32_t)hyperrig_loader_load(context->runtime, a, context->io);
    return context->io->storage.call(context->io->storage.opaque, service, a, b, c);
}

static uint32_t read_bridge(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    struct load_call *context = (struct load_call *)opaque;
    return context->io->storage.read(context->io->storage.opaque, address, destination, size);
}

int hyperrig_loader_step_preset(hyperrig_loader_runtime *runtime, uint32_t step, const hyperrig_loader_io *io)
{
    struct load_call context = {runtime, io};
    hyperrig_storage_io storage = {dispatch, read_bridge, &context};
    if (!valid(runtime) || !valid_io(io) || rate(runtime) < 1000)
        return -2;
    return hyperrig_storage_step_preset(&runtime->preset.storage, step, &storage);
}

int hyperrig_loader_action(hyperrig_loader_runtime *runtime, unsigned logical, unsigned event,
                            const hyperrig_loader_io *io)
{
    struct load_call context = {runtime, io};
    hyperrig_storage_io storage = {dispatch, read_bridge, &context};
    if (!valid(runtime) || !valid_io(io) || rate(runtime) < 1000 || logical > 3 || event > 2)
        return -2;
    return hyperrig_storage_action(&runtime->preset.storage, logical, event, &storage);
}

int hyperrig_loader_tick(hyperrig_loader_runtime *runtime, uint32_t delta, const hyperrig_loader_io *io)
{
    struct load_call context = {runtime, io};
    hyperrig_storage_io storage = {dispatch, read_bridge, &context};
    if (!valid(runtime) || !valid_io(io) || rate(runtime) < 1000)
        return -2;
    return hyperrig_storage_tick(&runtime->preset.storage, delta, &storage);
}

int hyperrig_loader_edge(hyperrig_loader_runtime *runtime, unsigned physical, unsigned pressed,
                          uint32_t stamp_a, uint32_t stamp_b, const hyperrig_loader_io *io)
{
    struct load_call context = {runtime, io};
    hyperrig_storage_io storage = {dispatch, read_bridge, &context};
    if (!valid(runtime) || !valid_io(io) || rate(runtime) < 1000 || physical > 4 || pressed > 1)
        return -2;
    return hyperrig_storage_edge(&runtime->preset.storage, physical, pressed, stamp_a, stamp_b, &storage);
}
