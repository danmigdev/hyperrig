/* Hand reconstruction of UltraRig TANK-G M5.71 preset layout conversion.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_PREFLIGHT_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_preset_preflight.h"

static uint32_t read32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static int read_signed16(const uint8_t *p)
{
    unsigned value = (unsigned)p[0] | (unsigned)p[1] << 8;
    return value < 32768 ? (int)value : (int)value - 65536;
}

static void write16(uint8_t *p, unsigned value)
{
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)(value >> 8);
}

static unsigned percent(int value)
{
    return value < 0 ? 0 : value > 100 ? 100 : (unsigned)value;
}

int hyperrig_preset_needs_conversion(uint32_t type)
{
    return type == 6 || type == 24;
}

uint32_t hyperrig_preset_convert_effect(uint32_t type, uint8_t parameters[14])
{
    /* Original eleven-byte table at 0x0203b334. */
    static const uint8_t curve[11] = {16, 19, 22, 25, 28, 32, 37, 43, 50, 61, 81};
    if (type == 6) {
        if (parameters) {
            unsigned a = percent(read_signed16(parameters));
            unsigned b = percent(read_signed16(parameters + 2));
            unsigned c = percent(read_signed16(parameters + 4));
            unsigned index = a == 100 ? 9 : a / 10;
            unsigned interpolated = curve[index] +
                ((a - 10 * index) * (curve[index + 1] - curve[index]) + 5) / 10;
            write16(parameters, a / 2 + 40);
            write16(parameters + 2, interpolated);
            write16(parameters + 4, b * 7 / 10);
            write16(parameters + 6, 0);
            write16(parameters + 8, c);
            write16(parameters + 10, 0);
            write16(parameters + 12, 40);
        }
        return 27;
    }
    if (type == 24) {
        if (parameters) {
            int value = read_signed16(parameters + 8);
            if (value >= 28)
                write16(parameters + 8, 27);
            write16(parameters + 10, 50);
            write16(parameters + 12, 0);
        }
        return 29;
    }
    return type;
}

/* Every migration destination is at or above its source. Backward copying
 * preserves the original memmove contract, including overlapping records. */
static void move_up(uint8_t *working, unsigned to, unsigned from, unsigned size)
{
    while (size) {
        --size;
        working[to + size] = working[from + size];
    }
}

static int convert_layout(uint8_t *working, uint32_t length)
{
    int group, slot, scene;
    unsigned effect;
    if (length == 1474) {
        /* Five trailing groups grow from five to six halfwords. */
        for (group = 4; group >= 0; --group) {
            unsigned to = 1424 + 12 * (unsigned)group;
            unsigned from = 1424 + 10 * (unsigned)group;
            write16(working + to + 10, 0);
            for (slot = 4; slot >= 0; --slot) {
                unsigned offset = 2 * (unsigned)slot;
                unsigned value = (unsigned)working[from + offset] |
                                 (unsigned)working[from + offset + 1] << 8;
                write16(working + to + offset, value);
            }
        }
    }
    if (working[0] < 5) {
        if (length > 1200)
            return -4;
        move_up(working, 1340, 1180, 20);
        for (scene = 3; scene >= 0; --scene) {
            unsigned old_scene = 268 + 228 * (unsigned)scene;
            unsigned new_scene = 300 + 260 * (unsigned)scene;
            for (slot = 15; slot >= 0; --slot) {
                unsigned to = new_scene + 4 + 16 * (unsigned)slot;
                move_up(working, to, old_scene + 4 + 14 * (unsigned)slot, 14);
                write16(working + to + 14, 0);
            }
            move_up(working, new_scene, old_scene, 4);
        }
        for (slot = 15; slot >= 0; --slot) {
            unsigned to = 12 + 18 * (unsigned)slot;
            move_up(working, to, 12 + 16 * (unsigned)slot, 16);
            write16(working + to + 16, 0);
        }
    }
    for (effect = 0; effect < 16 && effect < working[1]; ++effect) {
        uint8_t *descriptor = working + 12 + 18 * effect;
        uint32_t type = descriptor[1];
        if (hyperrig_preset_needs_conversion(type)) {
            descriptor[1] = (uint8_t)hyperrig_preset_convert_effect(type, descriptor + 4);
            for (scene = 0; scene < 4; ++scene)
                hyperrig_preset_convert_effect(type, working + 306 + 260 * (unsigned)scene + 16 * effect);
        }
    }
    return 0;
}

int hyperrig_preset_preflight(hyperrig_preset_runtime *runtime, uint32_t preset,
                              uint8_t header[HYPERRIG_PRESET_HEADER_BYTES],
                              const hyperrig_storage_io *io)
{
    unsigned i;
    int status;
    if (!runtime || !header || !io || !io->call || !io->read)
        return -5;
    for (i = 0; i < HYPERRIG_PRESET_PAYLOAD_MAX; ++i)
        runtime->working[i] = 0;
    io->call(io->opaque, HYPERRIG_STORAGE_PREPARE, 0, 0, 0);
    io->call(io->opaque, HYPERRIG_STORAGE_PRIORITY, 1, 0, 0);
    if (preset >= 32) {
        io->call(io->opaque, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0);
        return -1;
    }
    status = hyperrig_storage_record(hyperrig_storage_preset_address(&runtime->storage, preset),
        UINT32_C(0x51474b54), HYPERRIG_PRESET_PAYLOAD_MAX, header, runtime->working,
        HYPERRIG_PRESET_PAYLOAD_MAX, io);
    io->call(io->opaque, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0);
    if (status)
        return status;
    return convert_layout(runtime->working, read32(header + 4));
}
