#include "hyperrig_mini_runtime.h"

#define RUNTIME_MAGIC UINT32_C(0x48595254)
#define DMA_BYTES (2u * HYPERRIG_MINI_DMA_HALF_BYTES)
#define RAM_CODE __attribute__((section(".ramtext.mini_runtime")))

static int overlaps(uintptr_t a, size_t na, uintptr_t b, size_t nb)
{
    return a < b + nb && b < a + na;
}

int hyperrig_mini_runtime_init(hyperrig_mini_runtime *r, const hyperrig_mini_runtime_ops *ops)
{
    size_t i;
    uintptr_t rx, tx, address;
    hyperrig_mini_runtime_ops copy;
    if (!r || !ops || !ops->rx || !ops->tx || !ops->enter || !ops->leave ||
        !ops->begin || !ops->end || !ops->rx_for_cpu || !ops->tx_for_device ||
        !ops->process || ops->input_fraction > 31 || ops->output_fraction > 31) return -1;
    rx = (uintptr_t)ops->rx;
    tx = (uintptr_t)ops->tx;
    address = (uintptr_t)r;
    if ((rx | tx) & (HYPERRIG_MINI_CACHE_LINE - 1)) return -1;
    if (rx > UINTPTR_MAX - DMA_BYTES || tx > UINTPTR_MAX - DMA_BYTES ||
        address > UINTPTR_MAX - sizeof(*r)) return -1;
    if (overlaps(rx, DMA_BYTES, tx, DMA_BYTES) ||
        overlaps(address, sizeof(*r), rx, DMA_BYTES) ||
        overlaps(address, sizeof(*r), tx, DMA_BYTES)) return -1;
    copy = *ops;
    for (i = 0; i < sizeof(*r); ++i) ((unsigned char *)r)[i] = 0;
    r->ops = copy;
    r->magic = RUNTIME_MAGIC;
    return 0;
}

/* Caller already excluded IRQ on CPU0. Keep the FIRST fault and clear pending
 * work: a future half cannot repair lost ordering or mutated DSP model state. */
static RAM_CODE void fault_locked(hyperrig_mini_runtime *r, hyperrig_mini_runtime_fault fault, int detail)
{
    if (!r->fault) { r->fault = fault; r->fault_detail = detail; }
    r->pending = 0;
}

RAM_CODE void hyperrig_mini_runtime_ready(void *user, unsigned half)
{
    hyperrig_mini_runtime *r = (hyperrig_mini_runtime *)user;
    uint32_t flags;
    if (!r || r->magic != RUNTIME_MAGIC) return;
    flags = r->ops.enter(r->ops.io_user);
    ++r->stats.events;
    ++r->sequence; /* unsigned wrap is defined; zero is a valid token */
    if (r->fault) {
        ++r->stats.ignored_events;
    } else if (half > 1) {
        ++r->stats.invalid_halves;
        fault_locked(r, HYPERRIG_MINI_FAULT_HALF, (int)half);
    } else if (r->busy) {
        ++r->stats.deadline_overruns;
        fault_locked(r, HYPERRIG_MINI_FAULT_DEADLINE, 0);
    } else if (r->pending) {
        ++r->stats.pending_overruns;
        fault_locked(r, HYPERRIG_MINI_FAULT_PENDING, 0);
    } else if (r->have_phase && half == r->last_half) {
        ++r->stats.phase_errors;
        fault_locked(r, HYPERRIG_MINI_FAULT_PHASE, 0);
    } else {
        r->have_phase = 1;
        r->last_half = r->half = half;
        r->pending = 1;
    }
    r->ops.leave(r->ops.io_user, flags);
    if (r->ops.wake_from_irq) r->ops.wake_from_irq(r->ops.io_user);
}

static int current(hyperrig_mini_runtime *r, uint32_t sequence)
{
    uint32_t flags = r->ops.enter(r->ops.io_user);
    int valid = r->busy && !r->fault && r->sequence == sequence;
    r->ops.leave(r->ops.io_user, flags);
    return valid;
}

static int finish(hyperrig_mini_runtime *r, uint32_t sequence,
                  hyperrig_mini_runtime_fault fault, int detail)
{
    uint32_t flags = r->ops.enter(r->ops.io_user);
    int result;
    if (fault) {
        if (fault == HYPERRIG_MINI_FAULT_RX_OWNERSHIP || fault == HYPERRIG_MINI_FAULT_RX_CACHE) ++r->stats.rx_errors;
        else if (fault == HYPERRIG_MINI_FAULT_PROCESS) ++r->stats.process_errors;
        else ++r->stats.tx_errors;
        fault_locked(r, fault, detail);
    }
    if (!r->fault && r->sequence != sequence) fault_locked(r, HYPERRIG_MINI_FAULT_DEADLINE, 0);
    result = r->fault ? HYPERRIG_MINI_WORK_FAULT : HYPERRIG_MINI_WORK_DONE;
    if (result == HYPERRIG_MINI_WORK_DONE) ++r->stats.completed;
    r->busy = 0;
    r->ops.leave(r->ops.io_user, flags);
    return result;
}

int hyperrig_mini_runtime_work(hyperrig_mini_runtime *r)
{
    uint32_t flags, sequence, *dma;
    unsigned half, i;
    int status, released;
    hyperrig_mini_runtime_fault fault;
    if (!r || r->magic != RUNTIME_MAGIC) return HYPERRIG_MINI_WORK_INVALID;
    flags = r->ops.enter(r->ops.io_user);
    if (r->fault || r->busy || !r->pending) {
        status = r->fault ? HYPERRIG_MINI_WORK_FAULT : (r->busy ? HYPERRIG_MINI_WORK_BUSY : HYPERRIG_MINI_WORK_IDLE);
        r->ops.leave(r->ops.io_user, flags);
        return status;
    }
    r->pending = 0;
    r->busy = 1;
    sequence = r->sequence;
    half = r->half;
    r->ops.leave(r->ops.io_user, flags);

    status = r->ops.begin(r->ops.io_user, HYPERRIG_MINI_DMA_RX, half, sequence);
    if (status) return finish(r, sequence, HYPERRIG_MINI_FAULT_RX_OWNERSHIP, status);
    dma = r->ops.rx + half * HYPERRIG_MINI_AUDIO_SLOTS;
    status = 0;
    fault = HYPERRIG_MINI_FAULT_NONE;
    if (current(r, sequence)) {
        status = r->ops.rx_for_cpu(r->ops.io_user, dma, HYPERRIG_MINI_DMA_HALF_BYTES);
        if (status) fault = HYPERRIG_MINI_FAULT_RX_CACHE;
        else if (current(r, sequence))
            for (i = 0; i < HYPERRIG_MINI_AUDIO_SLOTS; ++i) r->rx_copy[i] = dma[i];
    }
    released = r->ops.end(r->ops.io_user, HYPERRIG_MINI_DMA_RX, half, sequence);
    if (!status && released) { status = released; fault = HYPERRIG_MINI_FAULT_RX_OWNERSHIP; }
    if (fault || !current(r, sequence)) return finish(r, sequence, fault, status);

    for (i = 0; i < HYPERRIG_MINI_AUDIO_FRAMES; ++i)
        r->input[i] = hyperrig_mini_audio_rx_q(r->rx_copy[2 * i], r->ops.input_fraction);
    status = r->ops.process(r->ops.process_user, r->input, r->output, HYPERRIG_MINI_AUDIO_FRAMES);
    if (status) return finish(r, sequence, HYPERRIG_MINI_FAULT_PROCESS, status);
    if (!current(r, sequence)) return finish(r, sequence, HYPERRIG_MINI_FAULT_NONE, 0);
    for (i = 0; i < HYPERRIG_MINI_AUDIO_FRAMES; ++i) {
        uint32_t word = hyperrig_mini_audio_tx_q(r->output[i], r->ops.output_fraction);
        r->tx_copy[2 * i] = r->tx_copy[2 * i + 1] = word;
    }

    status = r->ops.begin(r->ops.io_user, HYPERRIG_MINI_DMA_TX, half, sequence);
    if (status) return finish(r, sequence, HYPERRIG_MINI_FAULT_TX_OWNERSHIP, status);
    dma = r->ops.tx + half * HYPERRIG_MINI_AUDIO_SLOTS;
    fault = HYPERRIG_MINI_FAULT_NONE;
    if (current(r, sequence)) {
        for (i = 0; i < HYPERRIG_MINI_AUDIO_SLOTS; ++i) dma[i] = r->tx_copy[i];
        status = r->ops.tx_for_device(r->ops.io_user, dma, HYPERRIG_MINI_DMA_HALF_BYTES);
        if (status) fault = HYPERRIG_MINI_FAULT_TX_CACHE;
    }
    released = r->ops.end(r->ops.io_user, HYPERRIG_MINI_DMA_TX, half, sequence);
    if (!status && released) { status = released; fault = HYPERRIG_MINI_FAULT_TX_OWNERSHIP; }
    return finish(r, sequence, fault, status);
}

int hyperrig_mini_runtime_inspect(hyperrig_mini_runtime *r, hyperrig_mini_runtime_snapshot *snapshot)
{
    uint32_t flags;
    if (!r || r->magic != RUNTIME_MAGIC || !snapshot) return -1;
    flags = r->ops.enter(r->ops.io_user);
    snapshot->sequence = r->sequence;
    snapshot->pending = r->pending;
    snapshot->busy = r->busy;
    snapshot->half = r->half;
    snapshot->fault = r->fault;
    snapshot->fault_detail = r->fault_detail;
    snapshot->stats = r->stats;
    r->ops.leave(r->ops.io_user, flags);
    return 0;
}
