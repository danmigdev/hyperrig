/* Reconstructed M5.71 parameter primitives, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_PARAMETER_SUPPORT_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include "hyperrig/hyperrig_effect_enable.h"
#include <stddef.h>

typedef struct {
    const hyperrig_effect_parameter_support_io *io;
    uint32_t work, services;
    int status;
} Support;

static int spend(Support *s)
{
    if (s->status) return 0;
    if (!s->work) { s->status = -203; return 0; }
    --s->work;
    return 1;
}
static uint8_t *mapped(Support *s, uint32_t address, uint32_t bytes, int writable)
{
    uint8_t *p;
    if (!spend(s)) return NULL;
    if (bytes && address > UINT32_MAX - (bytes - 1u)) {
        s->status = -201; return NULL;
    }
    p = s->io->map(s->io->opaque, address, bytes, writable);
    if (!p) s->status = -201;
    return p;
}
static uint32_t get(Support *s, uint32_t address, uint32_t bytes)
{
    uint8_t *p = mapped(s, address, bytes, 0);
    uint32_t i, value = 0;
    if (p) for (i = 0; i < bytes; ++i) value |= (uint32_t)p[i] << (8u * i);
    return value;
}
static void put(Support *s, uint32_t address, uint64_t value, uint32_t bytes)
{
    uint8_t *p = mapped(s, address, bytes, 1);
    uint32_t i;
    if (p) for (i = 0; i < bytes; ++i) p[i] = (uint8_t)(value >> (8u * i));
}
static int64_t signed32(uint32_t v)
{ return v < UINT32_C(0x80000000) ? (int64_t)v : (int64_t)v - INT64_C(4294967296); }
static uint32_t divide32(uint32_t a, uint32_t b) { return b ? a / b : 0; }

/* Restoring division retains the unsigned core's quotient and remainder,
 * including its distinct zero-divisor paths. No signed C overflow is used. */
static uint64_t divide64(Support *s, uint64_t numerator, uint64_t denominator,
                         uint64_t *remainder)
{
    uint64_t quotient = 0, rem = 0;
    uint32_t bit;
    if (!denominator) {
        *remainder = numerator >> 32 ? 0 : numerator;
        return 0;
    }
    for (bit = 64; bit && spend(s); --bit) {
        uint64_t carry = rem >> 63;
        rem = (rem << 1) | ((numerator >> (bit - 1u)) & 1u);
        quotient <<= 1;
        if (carry || rem >= denominator) { rem -= denominator; quotient |= 1u; }
    }
    *remainder = rem;
    return quotient;
}
static uint64_t signed_divide(Support *s, uint64_t a, uint64_t b)
{
    uint64_t remainder, quotient;
    uint32_t negative = (uint32_t)((a ^ b) >> 63);
    if (a >> 63) a = UINT64_C(0) - a;
    if (b >> 63) b = UINT64_C(0) - b;
    quotient = divide64(s, a, b, &remainder);
    return negative ? UINT64_C(0) - quotient : quotient;
}
static uint8_t *borrow_map(void *opaque, uint32_t address, uint32_t bytes, int writable)
{ return mapped((Support *)opaque, address, bytes, writable); }
static uint32_t service(Support *s, uint32_t target, uint32_t a, uint32_t b)
{
    uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS] = {0};
    hyperrig_effect_processing_borrowed borrowed;
    if (s->status) return 0;
    if (!s->services) { s->status = -203; return 0; }
    if (!s->io->call) { s->status = -200; return 0; }
    --s->services; args[0] = a; args[1] = b;
    borrowed.map = borrow_map; borrowed.opaque = s;
    return s->io->call(s->io->opaque, target, args, 2, &borrowed);
}
static uint32_t clear_service(void *opaque, uint32_t target,
                              const uint32_t args[6], uint32_t count)
{
    Support *s = opaque;
    if (count != 2) { s->status = -202; return 0; }
    return service(s, target, args[0], args[1]);
}
static void clear_halfwords(Support *s, uint32_t address, uint32_t count)
{
    uint32_t callback = count >= 1024u ? get(s, UINT32_C(0x01c34194), 4) : 0;
    if (callback) {
        uint32_t bytes = (2u * count + 2u) & ~3u;
        if (callback == HYPERRIG_EFFECT_ENABLE_CLEAR) {
            HyperRigEffectEnableIO io;
            uint32_t args[3] = {address, bytes, 0}, result;
            int status;
            io.map = borrow_map; io.call = clear_service; io.opaque = s;
            io.call_budget = s->services; io.bulk_store_budget = s->work;
            status = hyperrig_effect_enable_execute(callback, args, &result, &io);
            if (status && !s->status) s->status = status == -202 ? -203 : status;
        } else (void)service(s, callback, address, bytes);
    } else {
        count = (count + 1u) >> 1;
        while (count && !s->status) { put(s, address, 0, 4); address += 4u; --count; }
    }
}
static void copy_byte(Support *s, uint32_t destination, uint32_t source)
{ uint32_t value = get(s, source, 1); put(s, destination, value, 1); }
static void copy_word(Support *s, uint32_t destination, uint32_t source, int split)
{
    uint32_t value = 0, i;
    if (split) {
        for (i = 0; i < 4; ++i) value |= get(s, source + i, 1) << (8u * i);
    } else value = get(s, source, 4);
    put(s, destination, value, 4);
}
static uint32_t move(Support *s, uint32_t destination, uint32_t source, uint32_t count)
{
    uint32_t result = destination, alignment, source_alignment, n;
    int backwards = source <= destination && source + count > destination;
    if (backwards) {
        destination += count; source += count;
        if (count >= 8) {
            alignment = destination & 3u; source_alignment = source & 3u;
            n = alignment; count -= n;
            while (n && !s->status) { --source; --destination; copy_byte(s, destination, source); --n; }
            n = count >> 2;
            while (n && !s->status) {
                uint32_t value = 0, i;
                source -= 4u; destination -= 4u;
                if (alignment != source_alignment) {
                    /* Native unaligned reverse copies read the high byte first. */
                    for (i = 4; i; --i) value |= get(s, source + i - 1u, 1) << (8u * (i - 1u));
                } else value = get(s, source, 4);
                put(s, destination, value, 4); --n;
            }
            count &= 3u;
        }
        while (count && !s->status) { --source; --destination; copy_byte(s, destination, source); --count; }
    } else {
        if (count >= 8) {
            alignment = destination & 3u; source_alignment = source & 3u;
            n = alignment ? 4u - alignment : 0; count -= n;
            while (n && !s->status) { copy_byte(s, destination, source); ++source; ++destination; --n; }
            n = count >> 2;
            while (n && !s->status) {
                copy_word(s, destination, source, alignment != source_alignment);
                source += 4u; destination += 4u; --n;
            }
            count &= 3u;
        }
        while (count && !s->status) { copy_byte(s, destination, source); ++source; ++destination; --count; }
    }
    return result;
}
static uint32_t size_base(Support *s, uint32_t value)
{
    value *= get(s, UINT32_C(0x01c1f7f8), 4);
    return (divide32(value, 1000) + 128u) & UINT32_C(0x00ffffc0);
}
static uint32_t tempo(Support *s, uint32_t id, uint32_t value)
{
    uint32_t a, b;
    if (id - 1u >= 9u) return 0;
    a = get(s, UINT32_C(0x0203b658) + id, 1);
    b = get(s, UINT32_C(0x0203b665) + id, 1);
    a *= value; b *= 1200000u;
    return divide32(a + b, a << 1);
}
int hyperrig_effect_parameter_support_execute(uint32_t entry,
    const uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_parameter_support_io *io)
{
    Support s;
    uint32_t a, b, c, d, value = 0, high = 0;
    uint64_t wide, remainder;
    if (!io || !io->map || !args || !result) return -200;
    s.io = io; s.work = io->work_budget; s.services = io->service_budget; s.status = 0;
    a = args[0]; b = args[1]; c = args[2]; d = args[3];
    switch (entry) {
    case UINT32_C(0x01c060e6):
        value = a - 3u <= 20u ? get(&s, UINT32_C(0x0203b880) + 4u * (a - 3u), 4) : UINT32_MAX;
        break;
    case UINT32_C(0x01c06466): {
        uint32_t first = get(&s, a + 8u, 2), second = get(&s, a + 12u, 2);
        uint32_t packed = first ? 100u : 0u;
        if (first && second) packed = get(&s, a + 10u, 1);
        put(&s, b, packed, 1);
        put(&s, c, get(&s, a + (second ? 12u : 8u), 2) == 2u, 1);
        break;
    }
    case UINT32_C(0x01c06554): clear_halfwords(&s, a, b); break;
    case UINT32_C(0x01c06582):
        b = get(&s, a + 84u, 4);
        if (b) {
            if (get(&s, a + 7u, 1)) value = get(&s, a + 92u, 4);
            else if ((get(&s, a + 88u, 4) >> 4) >= 2021u) value = b + 8192u;
        }
        break;
    case UINT32_C(0x01c065b4): value = signed32(a) < 1 ? 0 : a == 1 ? 1 : 3; break;
    case UINT32_C(0x01c065c4): value = signed32(a) <= 0 ? 0 : 2; break;
    case UINT32_C(0x01c065d0):
        if (a >= 40u) { s.status = -202; break; }
        value = get(&s, UINT32_C(0x0203b480) + a, 1) >> 5;
        if (!value) value = UINT32_MAX;
        break;
    case UINT32_C(0x01c067e0): value = get(&s, a + 12280u, 4); break;
    case UINT32_C(0x01c06926):
        wide = (((uint64_t)b << 32 | a) << 16) - UINT64_C(1);
        wide = signed_divide(&s, wide, signed32(c) <= 1 ? 1u : c);
        if (!(wide >> 63) && wide >= UINT32_C(0x7fffffff)) wide = UINT32_C(0x7fffffff);
        value = (uint32_t)wide; high = (uint32_t)(wide >> 32); break;
    case UINT32_C(0x01c0696a):
        if (get(&s, UINT32_C(0x01c32db3), 1)) break;
        d = get(&s, UINT32_C(0x01c1f7f0), 1);
        if (!a || !d) break;
        if (!(get(&s, UINT32_C(0x01c32dd8), 4) & (1u << (c & 31u)))) break;
        value = a == 100u && d == 100u ? (b ? 2350u : 1200u) : (b ? 3550u : 2750u);
        break;
    case UINT32_C(0x02029e12): value = size_base(&s, a); break;
    case UINT32_C(0x02029e32): value = size_base(&s, a); value += value >> 5; break;
    case UINT32_C(0x0202a75e): value = a - 1u < 9u; break;
    case UINT32_C(0x0202a7a8): value = divide32(a, 33) << 5; break;
    case UINT32_C(0x0202ed38): value = tempo(&s, a, b); break;
    case UINT32_C(0x0202ed70): value = tempo(&s, a, get(&s, UINT32_C(0x01c1f7fc), 4)); break;
    case UINT32_C(0x02032b2e): value = move(&s, a, b, c); break;
    case UINT32_C(0x02033172):
        wide = signed_divide(&s, (uint64_t)b << 32 | a, (uint64_t)d << 32 | c);
        value = (uint32_t)wide; high = (uint32_t)(wide >> 32); break;
    case UINT32_C(0x020331ec):
        wide = divide64(&s, (uint64_t)b << 32 | a, (uint64_t)d << 32 | c, &remainder);
        if (args[4]) put(&s, args[4], remainder, 8);
        value = (uint32_t)wide; high = (uint32_t)(wide >> 32); break;
    default: return -200;
    }
    if (!s.status) { result[0] = value; result[1] = high; }
    return s.status;
}
