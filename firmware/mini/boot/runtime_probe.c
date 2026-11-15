/* Exercise the real worker/audio/DSP path with fake DMA; no board MMIO. */
#include "runtime_probe.h"
#include "../runtime/hyperrig_mini_runtime.h"

typedef struct {
    uint32_t *rx, *tx;
    uint32_t flags;
    unsigned depth, lease, begins, ends, rx_syncs, tx_syncs, wakes, failed;
} memory_context;

static hyperrig_mini_runtime worker;

static uint32_t enter(void *opaque)
{
    memory_context *c = opaque;
    uint32_t saved = c->flags;
    if (c->depth++) c->failed = 1;
    c->flags = 0;
    return saved;
}

static void leave(void *opaque, uint32_t saved)
{
    memory_context *c = opaque;
    if (c->depth != 1 || c->flags != 0) c->failed = 1;
    c->depth = 0;
    c->flags = saved;
}

static int begin(void *opaque, hyperrig_mini_dma_direction direction,
                 unsigned half, uint32_t sequence)
{
    memory_context *c = opaque;
    if (c->lease || half != 0 || sequence != 1) return -201;
    c->lease = (unsigned)direction + 1;
    ++c->begins;
    return 0;
}

static int end(void *opaque, hyperrig_mini_dma_direction direction,
               unsigned half, uint32_t sequence)
{
    memory_context *c = opaque;
    int invalid = c->lease != (unsigned)direction + 1 || half != 0 || sequence != 1;
    c->lease = 0;
    ++c->ends;
    return invalid ? -202 : 0;
}

static int rx_sync(void *opaque, uint32_t *address, size_t bytes)
{
    memory_context *c = opaque;
    if (address != c->rx || bytes != 512 || c->lease != 1) return -203;
    ++c->rx_syncs;
    return 0; /* No hardware DMA/cache transaction: private RAM test array. */
}

static int tx_sync(void *opaque, uint32_t *address, size_t bytes)
{
    memory_context *c = opaque;
    if (address != c->tx || bytes != 512 || c->lease != 2) return -204;
    ++c->tx_syncs;
    return 0; /* No hardware DMA/cache transaction: private RAM test array. */
}

static void wake(void *opaque)
{
    memory_context *c = opaque;
    ++c->wakes;
}

int hyperrig_mini_runtime_memory_probe(uint32_t *rx, uint32_t *tx,
                                      hyperrig_mini_audio_process process, void *user)
{
    memory_context context = {.rx = rx, .tx = tx, .flags = 0x100};
    hyperrig_mini_runtime_ops ops = {
        .rx = rx, .tx = tx, .io_user = &context,
        .enter = enter, .leave = leave, .begin = begin, .end = end,
        .rx_for_cpu = rx_sync, .tx_for_device = tx_sync, .wake_from_irq = wake,
        .process = process, .process_user = user,
        .input_fraction = 30, .output_fraction = 31
    };
    hyperrig_mini_runtime_snapshot snapshot;
    int status;
    status = hyperrig_mini_runtime_init(&worker, &ops);
    if (status) return status;
    hyperrig_mini_runtime_ready(&worker, 0); /* Simulated event, no IRQ entry. */
    status = hyperrig_mini_runtime_work(&worker);
    if (status != HYPERRIG_MINI_WORK_DONE) return -205;
    status = hyperrig_mini_runtime_inspect(&worker, &snapshot);
    if (status || snapshot.fault != HYPERRIG_MINI_FAULT_NONE ||
        snapshot.stats.events != 1 || snapshot.stats.completed != 1 ||
        snapshot.pending || snapshot.busy) return -206;
    if (context.failed || context.depth || context.lease || context.flags != 0x100 ||
        context.begins != 2 || context.ends != 2 || context.rx_syncs != 1 ||
        context.tx_syncs != 1 || context.wakes != 1) return -207;
    if (hyperrig_mini_runtime_work(&worker) != HYPERRIG_MINI_WORK_IDLE) return -208;
    return 0;
}
