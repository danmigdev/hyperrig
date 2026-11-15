#include "../hyperrig_mini_runtime.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

enum { RX_BEGIN = 1, RX_CACHE, RX_END, PROCESS, TX_BEGIN, TX_CACHE, TX_END };
typedef struct {
    uint32_t before[8], data[256], after[8];
} __attribute__((aligned(32))) guarded_dma;
typedef struct {
    hyperrig_mini_runtime runtime;
    hyperrig_mini_runtime_ops ops;
    guarded_dma rx, tx;
    uint32_t flags, saved_flags, half, sequence, process_calls, wakes;
    unsigned depth, in_irq, lease, fail_stage, inject_stage, reenter;
    char order[32];
    size_t order_size;
} fixture;

static unsigned cases, injections, failures, blocks;
static void emit(fixture *f, unsigned half)
{
    assert(!f->depth && !f->in_irq);
    f->half = half;
    ++f->sequence;
    ++f->in_irq;
    hyperrig_mini_runtime_ready(&f->runtime, half);
    --f->in_irq;
}
static uint32_t enter(void *user)
{
    fixture *f = user;
    assert(!f->depth);
    f->depth = 1;
    f->saved_flags = f->flags;
    f->flags &= ~UINT32_C(256);
    return f->saved_flags;
}
static void leave(void *user, uint32_t flags)
{
    fixture *f = user;
    assert(f->depth == 1 && !(f->flags & 256) && flags == f->saved_flags);
    f->flags = flags;
    f->depth = 0;
}
static void stage(fixture *f, unsigned point, char marker)
{
    assert(!f->depth && !f->in_irq);
    assert(f->order_size + 1 < sizeof(f->order));
    f->order[f->order_size++] = marker;
    f->order[f->order_size] = 0;
    if (f->inject_stage == point) { f->inject_stage = 0; emit(f, 1 - f->half); }
}
static int begin(void *user, hyperrig_mini_dma_direction direction, unsigned half, uint32_t sequence)
{
    fixture *f = user;
    unsigned point = direction == HYPERRIG_MINI_DMA_RX ? RX_BEGIN : TX_BEGIN;
    assert(!f->lease && half == f->half && sequence == f->sequence);
    if (f->fail_stage != point) f->lease = 1 + direction;
    stage(f, point, direction == HYPERRIG_MINI_DMA_RX ? 'r' : 't');
    return f->fail_stage == point ? -100 - (int)point : 0;
}
static int end(void *user, hyperrig_mini_dma_direction direction, unsigned half, uint32_t sequence)
{
    fixture *f = user;
    unsigned point = direction == HYPERRIG_MINI_DMA_RX ? RX_END : TX_END;
    (void)half; (void)sequence;
    assert(f->lease == 1u + direction);
    f->lease = 0;
    stage(f, point, direction == HYPERRIG_MINI_DMA_RX ? 'e' : 'f');
    return f->fail_stage == point ? -100 - (int)point : 0;
}
static int cache_rx(void *user, uint32_t *address, size_t bytes)
{
    fixture *f = user;
    assert(f->lease == 1 && address == f->rx.data + f->half * 128 && bytes == 512);
    assert(!((uintptr_t)address & 31));
    stage(f, RX_CACHE, 'c');
    return f->fail_stage == RX_CACHE ? -102 : 0;
}
static int cache_tx(void *user, uint32_t *address, size_t bytes)
{
    fixture *f = user;
    assert(f->lease == 2 && address == f->tx.data + f->half * 128 && bytes == 512);
    assert(!((uintptr_t)address & 31));
    stage(f, TX_CACHE, 'd');
    return f->fail_stage == TX_CACHE ? -106 : 0;
}
static int process(void *user, const int32_t *input, int32_t *output, uint32_t frames)
{
    fixture *f = user;
    unsigned i;
    assert(!f->lease && frames == 64);
    ++f->process_calls;
    stage(f, PROCESS, 'p');
    if (f->reenter) assert(hyperrig_mini_runtime_work(&f->runtime) == HYPERRIG_MINI_WORK_BUSY);
    for (i = 0; i < frames; ++i) output[i] = input[i];
    return f->fail_stage == PROCESS ? -104 : 0;
}
static void wake(void *user)
{
    fixture *f = user;
    assert(f->in_irq && !f->depth);
    ++f->wakes;
}
static void setup(fixture *f)
{
    unsigned i;
    memset(f, 0, sizeof(*f));
    memset(&f->rx, 0xa5, sizeof(f->rx));
    memset(&f->tx, 0x5a, sizeof(f->tx));
    for (i = 0; i < 256; ++i) f->rx.data[i] = UINT32_C(0x9e3779b9) * (i + 1);
    f->flags = UINT32_C(0x1234ffab);
    f->ops.rx = f->rx.data; f->ops.tx = f->tx.data;
    f->ops.io_user = f;
    f->ops.enter = enter; f->ops.leave = leave;
    f->ops.begin = begin; f->ops.end = end;
    f->ops.rx_for_cpu = cache_rx; f->ops.tx_for_device = cache_tx;
    f->ops.wake_from_irq = wake;
    f->ops.process = process; f->ops.process_user = f;
    f->ops.input_fraction = f->ops.output_fraction = 23;
    assert(!hyperrig_mini_runtime_init(&f->runtime, &f->ops));
}
static hyperrig_mini_runtime_snapshot inspect(fixture *f)
{
    hyperrig_mini_runtime_snapshot snapshot;
    assert(!hyperrig_mini_runtime_inspect(&f->runtime, &snapshot));
    return snapshot;
}
static void guards(fixture *f)
{
    unsigned i;
    for (i = 0; i < 8; ++i) {
        assert(f->rx.before[i] == UINT32_C(0xa5a5a5a5) && f->rx.after[i] == UINT32_C(0xa5a5a5a5));
        assert(f->tx.before[i] == UINT32_C(0x5a5a5a5a) && f->tx.after[i] == UINT32_C(0x5a5a5a5a));
    }
    assert(!f->lease && !f->depth && !f->in_irq);
    assert(f->flags == UINT32_C(0x1234ffab));
}
static void success(void)
{
    fixture f;
    unsigned b, i;
    uint32_t saved[256];
    hyperrig_mini_runtime_snapshot snapshot;
    setup(&f);
    assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_IDLE);
    for (b = 0; b < 512; ++b) {
        unsigned half = b & 1;
        memcpy(saved, f.tx.data, sizeof(saved));
        f.order_size = 0;
        emit(&f, half);
        assert(f.process_calls == b && !f.order_size); /* ISR only queues/wakes. */
        snapshot = inspect(&f);
        assert(snapshot.pending && !snapshot.busy && snapshot.half == half);
        f.reenter = b & 1;
        assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_DONE);
        assert(!strcmp(f.order, "rceptdf"));
        for (i = 0; i < 128; ++i) {
            assert(f.tx.data[half * 128 + i] == (f.rx.data[half * 128 + (i & ~1u)] & 0xffffff));
            assert(f.tx.data[(1 - half) * 128 + i] == saved[(1 - half) * 128 + i]);
        }
        snapshot = inspect(&f);
        assert(!snapshot.pending && !snapshot.busy && !snapshot.fault && snapshot.stats.completed == b + 1);
        assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_IDLE);
        guards(&f); ++blocks;
    }
    assert(f.wakes == 512 && inspect(&f).stats.events == 512);
    ++cases;
    setup(&f);
    f.runtime.sequence = f.sequence = UINT32_MAX - 1; /* before DMA starts */
    emit(&f, 0); assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_DONE);
    f.order_size = 0;
    emit(&f, 1); assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_DONE);
    assert(inspect(&f).sequence == 0 && inspect(&f).stats.completed == 2);
    guards(&f); ++cases;
    /* Optional wake hook: foreground polling remains valid, IRQ flags stay off. */
    setup(&f); f.ops.wake_from_irq = NULL;
    assert(!hyperrig_mini_runtime_init(&f.runtime, &f.ops));
    f.flags &= ~UINT32_C(256);
    emit(&f, 1); assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_DONE);
    assert(!f.wakes && !(f.flags & 256)); ++cases;
}
static void fault_paths(void)
{
    fixture f;
    unsigned point, i;
    static const hyperrig_mini_runtime_fault expected[] = {
        HYPERRIG_MINI_FAULT_NONE, HYPERRIG_MINI_FAULT_RX_OWNERSHIP, HYPERRIG_MINI_FAULT_RX_CACHE,
        HYPERRIG_MINI_FAULT_RX_OWNERSHIP, HYPERRIG_MINI_FAULT_PROCESS, HYPERRIG_MINI_FAULT_TX_OWNERSHIP,
        HYPERRIG_MINI_FAULT_TX_CACHE, HYPERRIG_MINI_FAULT_TX_OWNERSHIP
    };
    setup(&f); emit(&f, 0); emit(&f, 1);
    assert(inspect(&f).fault == HYPERRIG_MINI_FAULT_PENDING && inspect(&f).stats.pending_overruns == 1);
    assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_FAULT && !f.process_calls);
    emit(&f, 0); assert(inspect(&f).stats.ignored_events == 1 && !inspect(&f).pending);
    guards(&f); ++cases;
    setup(&f); emit(&f, 0); assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_DONE);
    emit(&f, 0); assert(inspect(&f).fault == HYPERRIG_MINI_FAULT_PHASE && inspect(&f).stats.phase_errors == 1);
    guards(&f); ++cases;
    setup(&f); emit(&f, 2);
    assert(inspect(&f).fault == HYPERRIG_MINI_FAULT_HALF && inspect(&f).stats.invalid_halves == 1);
    guards(&f); ++cases;
    for (point = RX_BEGIN; point <= TX_END; ++point) {
        hyperrig_mini_runtime_snapshot snapshot;
        setup(&f); f.fail_stage = point; emit(&f, 0);
        assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_FAULT);
        snapshot = inspect(&f);
        assert(snapshot.fault == expected[point] && snapshot.fault_detail == -100 - (int)point);
        assert(!snapshot.busy && !snapshot.pending && !snapshot.stats.completed);
        assert(snapshot.stats.rx_errors + snapshot.stats.process_errors + snapshot.stats.tx_errors == 1);
        if (point <= TX_BEGIN) for (i = 0; i < 256; ++i) assert(f.tx.data[i] == UINT32_C(0x5a5a5a5a));
        guards(&f); ++failures;
    }
    for (point = RX_BEGIN; point <= TX_END; ++point) {
        hyperrig_mini_runtime_snapshot snapshot;
        setup(&f); f.inject_stage = point; emit(&f, 0);
        assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_FAULT);
        snapshot = inspect(&f);
        assert(snapshot.fault == HYPERRIG_MINI_FAULT_DEADLINE && snapshot.stats.deadline_overruns == 1);
        assert(!snapshot.busy && !snapshot.pending && !snapshot.stats.completed);
        if (point <= TX_BEGIN) for (i = 0; i < 256; ++i) assert(f.tx.data[i] == UINT32_C(0x5a5a5a5a));
        if (point <= RX_END) assert(!f.process_calls);
        /* TX_CACHE/TX_END injection can happen after writes. A latched fault
         * cannot roll back DMA memory or make a false board lease safe. */
        guards(&f); ++injections;
    }
    setup(&f); f.inject_stage = f.fail_stage = PROCESS; emit(&f, 0);
    assert(hyperrig_mini_runtime_work(&f.runtime) == HYPERRIG_MINI_WORK_FAULT);
    assert(inspect(&f).fault == HYPERRIG_MINI_FAULT_DEADLINE); /* first fault wins */
    assert(inspect(&f).stats.process_errors == 1);
    guards(&f); ++cases;
    assert(!hyperrig_mini_runtime_init(&f.runtime, &f.ops)); /* fixture DMA stopped */
    assert(!inspect(&f).fault && !inspect(&f).stats.events); ++cases;
}
static void invalid_arguments(void)
{
    fixture f;
    hyperrig_mini_runtime before;
    hyperrig_mini_runtime_ops bad;
    unsigned which;
    setup(&f);
    before = f.runtime;
    for (which = 0; which < 14; ++which) {
        bad = f.ops;
        switch (which) {
        case 0: bad.rx = NULL; break;
        case 1: bad.tx = bad.rx; break;
        case 2: bad.rx++; break;
        case 3: bad.tx = bad.rx + 128; break;
        case 4: bad.enter = NULL; break;
        case 5: bad.leave = NULL; break;
        case 6: bad.begin = NULL; break;
        case 7: bad.end = NULL; break;
        case 8: bad.rx_for_cpu = NULL; break;
        case 9: bad.tx_for_device = NULL; break;
        case 10: bad.process = NULL; break;
        case 11: bad.input_fraction = 32; break;
        case 12: bad.output_fraction = 32; break;
        default: bad.rx = (uint32_t *)((uintptr_t)&f.runtime & ~(uintptr_t)31); break;
        }
        assert(hyperrig_mini_runtime_init(&f.runtime, &bad) == -1);
        assert(!memcmp(&before, &f.runtime, sizeof(before))); ++cases;
    }
    assert(hyperrig_mini_runtime_init(NULL, &f.ops) == -1);
    assert(hyperrig_mini_runtime_init(&f.runtime, NULL) == -1);
    assert(hyperrig_mini_runtime_work(NULL) == HYPERRIG_MINI_WORK_INVALID);
    assert(hyperrig_mini_runtime_inspect(&f.runtime, NULL) == -1);
    hyperrig_mini_runtime_ready(NULL, 0);
    ++cases;
}
static void dispatch(void)
{
    fixture f;
    hyperrig_mini_audio_device device;
    hyperrig_mini_alnk_registers alnk;
    unsigned phase, pending;
    assert(!hyperrig_mini_runtime_irq_bind(NULL) && !hyperrig_mini_irq11_dispatch());
    for (phase = 0; phase < 2; ++phase) for (pending = 0; pending < 16; ++pending) {
        setup(&f);
        memset(&device, 0, sizeof(device)); memset(&alnk, 0, sizeof(alnk));
        device.alnk = &alnk; device.user = &f.runtime; device.prepared = 1;
        assert(hyperrig_mini_runtime_irq_bind(&device) == -1);
        device.ready = hyperrig_mini_runtime_ready;
        assert(!hyperrig_mini_runtime_irq_bind(&device));
        alnk.con0 = (uint16_t)(phase << 13);
        alnk.con2 = (uint8_t)(pending << 4);
        f.in_irq = 1;
        assert(hyperrig_mini_irq11_dispatch() == pending);
        f.in_irq = 0;
        assert((alnk.con2 & 15) == pending && !f.process_calls && !f.order_size);
        assert(inspect(&f).pending == !!(pending & 2));
        if (pending & 2) assert(inspect(&f).half == 1 - phase);
        assert(!hyperrig_mini_runtime_irq_bind(NULL));
        guards(&f); ++cases;
    }
}
int main(void)
{
    success(); fault_paths(); invalid_arguments(); dispatch();
    printf("{\"state_cases\":%u,\"alternating_blocks\":%u,\"hook_failure_cases\":%u,"
           "\"irq_during_worker_cases\":%u,\"sanitizers\":\"address,undefined\","
           "\"physical_mmio_accessed\":false}\n", cases, blocks, failures, injections);
    return 0;
}
