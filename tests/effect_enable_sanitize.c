/* Exact-allocation offline checks; no hardware or audio claim. */
#include "hyperrig/hyperrig_effect_enable.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t base, size; uint8_t *p; } Window;
typedef struct { Window windows[8]; unsigned n, services; uint32_t fail; } Memory;
static uint8_t *mapped(void *opaque, uint32_t a, uint32_t n, int writable)
{
    Memory *m = opaque; unsigned i; (void)writable;
    for (i = 0; i < m->n; ++i) {
        Window *w = m->windows + i;
        if (a >= w->base && a - w->base <= w->size && n <= w->size - (a - w->base))
            return w->p + (a - w->base);
    }
    return NULL;
}
static uint8_t *window(Memory *m, uint32_t base, uint32_t bytes)
{
    Window *w = &m->windows[m->n++]; assert(m->n <= 8);
    w->base = base; w->size = bytes; w->p = malloc(bytes ? bytes : 1); assert(w->p);
    memset(w->p, 0xa5, bytes); return w->p;
}
static void release(Memory *m)
{ unsigned i; for (i = 0; i < m->n; ++i) free(m->windows[i].p); m->n = 0; }
static void set(uint8_t *p, uint32_t v)
{ unsigned i; for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8*i)); }
static uint32_t service(void *opaque, uint32_t target, const uint32_t args[6], uint32_t count)
{
    Memory *m = opaque; unsigned i;
    assert(count <= 1); for (i = count; i < 6; ++i) assert(args[i] == 0);
    ++m->services;
    if (target == 0x0203033c) return m->fail;
    return 0;
}
static HyperRigEffectEnableIO interface(Memory *m)
{
    HyperRigEffectEnableIO io;
    io.map = mapped; io.call = service; io.opaque = m; io.call_budget = 1000; io.bulk_store_budget = 10000;
    return io;
}
static void state(Memory *m, unsigned type)
{
    uint8_t *e = window(m, 0x01c2c220, 7680), *cfg = window(m, 0x01c1f7d4, 68);
    uint8_t *ctl = window(m, 0x01c32db0, 640), *callbacks = window(m, 0x01c34190, 768);
    unsigned i;
    for (i = 0; i < 16; ++i) {
        uint8_t *p = e + 480*i; p[0] = (uint8_t)type; p[1] = 0; p[2] = 1;
        p[8] = p[9] = p[10] = p[11] = 0; set(p+84, 0); set(p+88, 0); set(p+288, 0);
        set(p+304, 0); set(p+308, 0); set(p+320, 0); set(p+324, 0); set(p+332, 0); set(p+400, 0); p[369] = 0;
    }
    set(cfg+16, 0); set(ctl+48, 1000); set(callbacks+4, 0); set(callbacks+728, 0);
}
static void zeroes(const uint8_t *p, uint32_t n)
{ uint32_t i; for (i = 0; i < n; ++i) assert(p[i] == 0); }

int main(void)
{
    static const uint32_t counts[] = {0, 1, 2, 3, 4, 5, 7, 8, 9, 255, 256, 257, 1023, 1024, 1025, 8192};
    static const uint32_t fills[] = {0, 255, 0x12345678, 0xffffffff};
    static const unsigned types[] = {5,7,11,12,15,25,27,29,30,31,38,39,255};
    static const uint32_t entries[] = {HYPERRIG_EFFECT_ENABLE_COMMIT, HYPERRIG_EFFECT_ENABLE_FAST,
        HYPERRIG_EFFECT_ENABLE_COMMIT_UNCHECKED, HYPERRIG_EFFECT_ENABLE_FAST_UNCHECKED,
        HYPERRIG_EFFECT_ENABLE_COMMIT_CORE, HYPERRIG_EFFECT_ENABLE_FAST_CORE};
    unsigned alignment, i, j, k, mode, enabled, cases = 0, guards = 0;
    for (alignment = 0; alignment < 4; ++alignment) for (i = 0; i < sizeof counts/sizeof *counts; ++i)
        for (j = 0; j < sizeof fills/sizeof *fills; ++j) {
            Memory m = {0}; uint8_t *p = window(&m, 0x33000000+alignment, counts[i]);
            HyperRigEffectEnableIO io = interface(&m);
            uint32_t args[3] = {0x33000000+alignment, fills[j], counts[i]}, result = 0;
            assert(!hyperrig_effect_enable_execute(HYPERRIG_EFFECT_ENABLE_MEMSET, args, &result, &io));
            assert(result == args[0]); for (k = 0; k < counts[i]; ++k) assert(p[k] == (uint8_t)fills[j]);
            release(&m); ++cases;
        }
    for (i = 0; i < 8; ++i) for (enabled = 0; enabled < 2; ++enabled) {
        Memory m = {0}; uint8_t *obj = window(&m, 0x33000000, 52);
        uint8_t *ring = window(&m, 0x34000000, i*129*8), *tail = window(&m, 0x35000000, 1024);
        HyperRigEffectEnableIO io = interface(&m);
        set(obj, enabled); set(obj+4, i); set(obj+24, 0x34000000); set(obj+48, 0x35000000);
        assert(!hyperrig_effect_enable_ir_reset(0x33000000, &io));
        if (enabled) { zeroes(ring, i*129*8); zeroes(tail, 1024); zeroes(obj+8, 8); }
        else { assert(tail[0] == 0xa5); assert(obj[8] == 0xa5); }
        release(&m); ++cases;
    }
    for (i = 0; i < sizeof types/sizeof *types; ++i) for (mode = 0; mode < 7; ++mode)
        for (enabled = 0; enabled < 2; ++enabled) for (j = 0; j < 4; ++j) {
            Memory m = {0}; HyperRigEffectEnableIO io; uint32_t result, args[3] = {0x01c2c220, enabled, 0};
            state(&m, types[i]); io = interface(&m);
            m.windows[0].p[10] = (uint8_t)mode; m.windows[0].p[11] = (uint8_t)(j == 3 ? 255 : j);
            assert(!hyperrig_effect_enable_execute(HYPERRIG_EFFECT_ENABLE_FADE, args, &result, &io));
            assert(result == 0); release(&m); ++cases;
        }
    for (i = 0; i < 5; ++i) for (j = 0; j < 2; ++j) {
        static const unsigned clear_types[] = {11,12,15,29,39};
        Memory m = {0}; HyperRigEffectEnableIO io; uint32_t result, args[3] = {0x01c2c220, 1, 0};
        uint32_t bytes = clear_types[i] == 29 ? 8192 : 2052; uint8_t *p;
        state(&m, clear_types[i]); p = window(&m, 0x33000000, bytes); io = interface(&m);
        set(m.windows[0].p+84, 0x33000000); set(m.windows[0].p+88, 1025);
        if (j) set(m.windows[3].p+4, HYPERRIG_EFFECT_ENABLE_CLEAR);
        assert(!hyperrig_effect_enable_execute(HYPERRIG_EFFECT_ENABLE_FADE, args, &result, &io));
        zeroes(p, bytes); release(&m); ++cases;
    }
    for (i = 0; i < sizeof entries/sizeof *entries; ++i) for (j = 0; j < sizeof types/sizeof *types; ++j)
        for (enabled = 0; enabled < 2; ++enabled) for (k = 0; k < 3; ++k) {
            Memory m = {0}; HyperRigEffectEnableIO io; uint32_t result, args[3] = {0, enabled, k&1};
            state(&m, types[j]); io = interface(&m); m.windows[0].p[1] = (uint8_t)(k == 2);
            m.fail = k == 1 ? 0xfffffffd : 0;
            assert(!hyperrig_effect_enable_execute(entries[i], args, &result, &io));
            release(&m); ++cases;
        }
    {
        Memory m = {0}; HyperRigEffectEnableIO io; uint32_t result = 0xdeadbeef, args[3] = {0x33000000, 0, 4};
        uint8_t *p = window(&m, 0x33000000, 4); io = interface(&m); io.bulk_store_budget = 0;
        assert(hyperrig_effect_enable_execute(HYPERRIG_EFFECT_ENABLE_MEMSET,args,&result,&io)==-202);
        assert(result==0xdeadbeef && p[0]==0xa5); ++guards;
        io.bulk_store_budget=1;args[2]=8;
        assert(hyperrig_effect_enable_execute(HYPERRIG_EFFECT_ENABLE_MEMSET,args,&result,&io)==-202);
        zeroes(p,4); assert(result==0xdeadbeef); ++guards;
        io.bulk_store_budget=2;
        assert(hyperrig_effect_enable_execute(HYPERRIG_EFFECT_ENABLE_MEMSET,args,&result,&io)==-201); ++guards;
        release(&m);
    }
    printf("{\"result\":\"pass\",\"exact_allocation_cases\":%u,\"partial_failure_guards\":%u}\n",cases,guards);
    return 0;
}
