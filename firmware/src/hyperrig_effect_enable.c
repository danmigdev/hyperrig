/* Reconstructed M5.71 effect enable/fade and installed clear adapters.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_ENABLE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_enable.h"
#include <stddef.h>

#define EFFECTS UINT32_C(0x01c2c220)
#define TAILS UINT32_C(0x01c1f7e4)
#define LIMIT UINT32_C(0x01c32de0)
#define CLEAR UINT32_C(0x01c34194)
#define COUNTER UINT32_C(0x01c34468)
typedef struct {
    const HyperRigEffectEnableIO *io;
    uint32_t calls, words;
    int status;
} Run;

static uint8_t *map(Run *r, uint32_t address, uint32_t size, int writable)
{
    uint8_t *p;
    if (r->status) return NULL;
    if (size && address > UINT32_MAX - (size - 1u)) {
        r->status = -201; return NULL;
    }
    p = r->io->map(r->io->opaque, address, size, writable);
    if (!p) r->status = -201;
    return p;
}
static uint32_t get(Run *r, uint32_t address, uint32_t size)
{
    uint8_t *p = map(r, address, size, 0);
    uint32_t v = 0, i;
    if (p) for (i = 0; i < size; ++i) v |= (uint32_t)p[i] << (8u * i);
    return v;
}
static void put(Run *r, uint32_t address, uint32_t value, uint32_t size)
{
    uint8_t *p = map(r, address, size, 1);
    uint32_t i;
    if (p) for (i = 0; i < size; ++i) p[i] = (uint8_t)(value >> (8u * i));
}
static uint32_t service(Run *r, uint32_t target, uint32_t a, uint32_t b, uint32_t n)
{
    uint32_t args[6] = {0, 0, 0, 0, 0, 0};
    if (r->status) return 0;
    if (!r->calls) { r->status = -202; return 0; }
    if (!r->io->call) { r->status = -203; return 0; }
    --r->calls;
    if (n) args[0] = a;
    if (n > 1) args[1] = b;
    return r->io->call(r->io->opaque, target, args, n);
}
static int64_t s32(uint32_t x)
{ return x < UINT32_C(0x80000000) ? (int64_t)x : (int64_t)x - INT64_C(4294967296); }
static uint32_t smax(uint32_t x, uint32_t y) { return s32(x) > s32(y) ? x : y; }
static void clear_word(Run *r, uint32_t address)
{
    if (r->status) return;
    if (!r->words) { r->status = -202; return; }
    --r->words; put(r, address, 0, 4);
}
static void clear_words(Run *r, uint32_t address, uint32_t count)
{
    while (count && !r->status) { clear_word(r, address); address += 4u; --count; }
}
static void fill_byte(Run *r, uint32_t address, uint32_t fill)
{
    if (r->status) return;
    if (!r->words) { r->status = -202; return; }
    --r->words; put(r, address, fill, 1);
}
static uint32_t memory_fill(Run *r, uint32_t address, uint32_t fill, uint32_t count)
{
    uint32_t original = address, words;
    while (count && (address & 3u) && !r->status) {
        fill_byte(r, address, fill); ++address; --count;
    }
    fill = (fill & 255u) * UINT32_C(0x01010101);
    words = count >> 2;
    while (words && !r->status) {
        if (!r->words) { r->status = -202; break; }
        --r->words; put(r, address, fill, 4); address += 4u; --words;
    }
    count &= 3u;
    while (count && !r->status) { fill_byte(r, address, fill); ++address; --count; }
    return original;
}
static void clear_callback(Run *r, uint32_t callback, uint32_t address, uint32_t bytes)
{
    if (callback == HYPERRIG_EFFECT_ENABLE_CLEAR) (void)memory_fill(r, address, 0, bytes);
    else (void)service(r, callback, address, bytes, 2);
}
static void counter(Run *r)
{ uint32_t v = get(r, COUNTER, 4); put(r, COUNTER, v + 1u, 4); }
static uint32_t tail_type(uint32_t type)
{ uint32_t n = type - 5u; return n <= 30u ? (UINT32_C(0x7e400001) >> n) & 1u : 0u; }
static uint32_t duration(Run *r, uint32_t e)
{
    uint32_t type = get(r, e, 1), a, b, n;
    if (type == 11 || type == 12 || type == 15 || type == 39) {
        a = get(r, e + (type == 39 ? 400u : 304u), 4);
        b = get(r, e + 308u, 4); n = a + b;
    } else if (type == 25) {
        b = get(r, e + 324u, 4); a = get(r, e + 320u, 4);
        n = get(r, e + 332u, 4);
        n = ((n >> 1) | (n & UINT32_C(0x80000000))) + smax(a, b);
    } else if (type == 29) {
        if (get(r, e + 369u, 1)) return 0;
        b = get(r, e + 308u, 4); a = get(r, e + 304u, 4);
        n = smax(a, b) + UINT32_C(0x800000);
    } else return 0;
    if (s32(n) < 1 || !get(r, e + 84u, 4)) return 0;
    n = ((n >> 16) + 146u) >> 7;
    return n < 16 ? n : 16;
}
static void ir_reset(Run *r, uint32_t e)
{
    uint32_t n, p;
    if (!e || !get(r, e, 4)) return;
    n = get(r, e + 4u, 4) * 129u;
    if (n) {
        p = get(r, e + 24u, 4);
        while (n && !r->status) {
            clear_word(r, p); p += 4u; clear_word(r, p); p += 4u; --n;
        }
    }
    p = get(r, e + 48u, 4); clear_words(r, p, 256);
    put(r, e + 8u, 0, 4); put(r, e + 12u, 0, 4);
}
static void fade(Run *r, uint32_t e, uint32_t enabled)
{
    uint32_t count, mode, type, p, length, callback, n, i;
    static const uint32_t offsets[] = {300, 296, 288, 292, 336, 340, 328, 332};
    if (get(r, e + 8u, 2)) {
        if (!enabled) return;
        n = get(r, e, 1) - 27u;
        if (n <= 8 && (497u & (1u << n))) put(r, e + 10u, 5, 1);
        return;
    }
    count = get(r, e + 11u, 1); mode = get(r, e + 10u, 1);
    if (enabled && mode == 2) {
        if (!count) { put(r, e + 10u, 0, 1); return; }
        put(r, e + 11u, 4u - count, 1); put(r, e + 10u, 1, 1); return;
    }
    if (!enabled) {
        if (mode == 3 || ((mode == 4 || mode == 1) && !count)) {
            put(r, e + 10u, 0, 1); return;
        }
        put(r, e + 11u, mode == 4 || mode == 1 ? 4u - count : 0, 1);
        put(r, e + 10u, 2, 1); return;
    }
    p = get(r, e + 84u, 4); type = get(r, e, 1);
    if (p && (type == 11 || type == 12 || type == 15 || type == 39)) {
        length = get(r, e + 88u, 4);
        callback = length >= 1024 ? get(r, CLEAR, 4) : 0;
        if (callback) clear_callback(r, callback, p, (length * 2u + 2u) & ~3u);
        else clear_words(r, p, (length + 1u) >> 1);
    } else if (p && type == 29) {
        callback = get(r, CLEAR, 4);
        if (callback) clear_callback(r, callback, p, 8192);
        else clear_words(r, p, 2048);
        (void)service(r, UINT32_C(0x0202e328), e, 0, 1);
    } else if (p && type == 30) {
        (void)service(r, UINT32_C(0x0202e3ce), e, 0, 1);
    } else if (type == 38) {
        for (i = 0; i < 8; ++i) put(r, e + offsets[i], 0, 4);
    }
    count = duration(r, e); type = get(r, e, 1); mode = 1;
    if (type == 7 && (p = get(r, e + 288u, 4)) != 0) {
        ir_reset(r, p); mode = 4;
    }
    put(r, e + 11u, count, 1);
    if (count) mode = 3;
    put(r, e + 10u, mode, 1);
}
static uint32_t commit(Run *r, uint32_t slot, uint32_t enabled, uint32_t checked)
{
    uint32_t e, old, cost, total, ret;
    counter(r);
    if (slot > 15) return UINT32_MAX;
    e = EFFECTS + slot * 480u;
    if (!get(r, e + 2u, 1)) return UINT32_MAX;
    old = get(r, e + 1u, 1);
    if (enabled) {
        if (!old && !get(r, e + 8u, 2)) {
            cost = service(r, UINT32_C(0x0203023c), slot, 0, 1);
            if (checked) {
                total = service(r, UINT32_C(0x02028de8), 0, 0, 0);
                if (total + cost > get(r, LIMIT, 4)) return UINT32_C(0xfffffffc);
            }
            ret = service(r, UINT32_C(0x0203033c), e, 0, 1);
            if (ret) return ret;
            old = get(r, e + 1u, 1);
        }
    } else if (old && get(r, TAILS, 4) && tail_type(get(r, e, 1))) {
        put(r, e + 8u, 1500, 2);
    }
    if (!!old != !!enabled) fade(r, e, enabled);
    if (enabled) put(r, e + 8u, 0, 2);
    put(r, e + 1u, !!enabled, 1);
    return 0;
}
static uint32_t fast(Run *r, uint32_t slot, uint32_t enabled, uint32_t checked)
{
    uint32_t e, type, needed, total, cost, old;
    if (slot > 15) return UINT32_MAX;
    e = EFFECTS + slot * 480u;
    if (!get(r, e + 2u, 1)) return UINT32_MAX;
    if (enabled) {
        if (!get(r, e + 1u, 1) && !get(r, e + 8u, 2)) {
            type = get(r, e, 1);
            if (type == 7) {
                if (!get(r, e + 288u, 4)) return UINT32_C(0xfffffffa);
            } else {
                needed = service(r, UINT32_C(0x0202def2), e, 0, 1);
                if (needed && !get(r, e + 84u, 4)) return UINT32_C(0xfffffffa);
            }
            if (checked) {
                total = service(r, UINT32_C(0x02028de8), 0, 0, 0);
                cost = service(r, UINT32_C(0x0203023c), slot, 0, 1);
                if (total + cost > get(r, LIMIT, 4)) return UINT32_C(0xfffffffc);
            }
        }
        counter(r);
        if (!get(r, e + 1u, 1)) fade(r, e, 1);
        put(r, e + 1u, 1, 1); put(r, e + 8u, 0, 2);
    } else {
        counter(r); old = get(r, e + 1u, 1);
        if (old) {
            if (get(r, TAILS, 4) && tail_type(get(r, e, 1))) put(r, e + 8u, 1500, 2);
            fade(r, e, 0);
        }
        put(r, e + 1u, 0, 1);
    }
    return 0;
}
static uint32_t finish(Run *r, uint32_t result)
{
    if (!result) (void)service(r, UINT32_C(0x0202ec30), 0, 0, 0);
    return result;
}
int hyperrig_effect_enable_execute(uint32_t entry, const uint32_t args[3],
                                  uint32_t *result, const HyperRigEffectEnableIO *io)
{
    Run r; uint32_t value = 0;
    if (!io || !io->map || !args || !result) return -200;
    r.io = io; r.calls = io->call_budget; r.words = io->bulk_store_budget; r.status = 0;
    switch (entry) {
    case HYPERRIG_EFFECT_ENABLE_DURATION: value = duration(&r, args[0]); break;
    case HYPERRIG_EFFECT_ENABLE_TAIL_TYPE: value = tail_type(args[0]); break;
    case HYPERRIG_EFFECT_ENABLE_FADE: fade(&r, args[0], args[1]); break;
    case HYPERRIG_EFFECT_ENABLE_IR_RESET: ir_reset(&r, args[0]); break;
    case HYPERRIG_EFFECT_ENABLE_COUNTER: counter(&r); break;
    case HYPERRIG_EFFECT_ENABLE_CLEAR: value = memory_fill(&r, args[0], 0, args[1]); break;
    case HYPERRIG_EFFECT_ENABLE_MEMSET: value = memory_fill(&r, args[0], args[1], args[2]); break;
    case HYPERRIG_EFFECT_ENABLE_FINISH: value = finish(&r, args[0]); break;
    case HYPERRIG_EFFECT_ENABLE_COMMIT_CORE: value = commit(&r, args[0], args[1], args[2]); break;
    case HYPERRIG_EFFECT_ENABLE_FAST_CORE: value = fast(&r, args[0], args[1], args[2]); break;
    case HYPERRIG_EFFECT_ENABLE_COMMIT: value = finish(&r, commit(&r, args[0], args[1], 1)); break;
    case HYPERRIG_EFFECT_ENABLE_FAST: value = finish(&r, fast(&r, args[0], args[1], 1)); break;
    case HYPERRIG_EFFECT_ENABLE_COMMIT_UNCHECKED: value = commit(&r, args[0], args[1], 0); break;
    case HYPERRIG_EFFECT_ENABLE_FAST_UNCHECKED: value = fast(&r, args[0], args[1], 0); break;
    default: return -200;
    }
    if (!r.status) *result = value;
    return r.status;
}
int hyperrig_effect_enable_ir_reset(uint32_t object_token, const HyperRigEffectEnableIO *io)
{
    uint32_t args[3] = {object_token, 0, 0}, result;
    return hyperrig_effect_enable_execute(HYPERRIG_EFFECT_ENABLE_IR_RESET, args, &result, io);
}
