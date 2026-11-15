/* CPU0-only ALNK IRQ -> foreground worker. See docs/MINI_RUNTIME.md. */
#ifndef HYPERRIG_MINI_RUNTIME_H
#define HYPERRIG_MINI_RUNTIME_H
#include <stdint.h>
#include <stddef.h>
#include "../audio/hyperrig_mini_audio.h"

enum { HYPERRIG_MINI_DMA_HALF_BYTES = 512, HYPERRIG_MINI_CACHE_LINE = 32 };
typedef enum {
    HYPERRIG_MINI_FAULT_NONE = 0,
    HYPERRIG_MINI_FAULT_HALF,
    HYPERRIG_MINI_FAULT_PENDING,
    HYPERRIG_MINI_FAULT_DEADLINE,
    HYPERRIG_MINI_FAULT_PHASE,
    HYPERRIG_MINI_FAULT_RX_OWNERSHIP,
    HYPERRIG_MINI_FAULT_RX_CACHE,
    HYPERRIG_MINI_FAULT_PROCESS,
    HYPERRIG_MINI_FAULT_TX_OWNERSHIP,
    HYPERRIG_MINI_FAULT_TX_CACHE
} hyperrig_mini_runtime_fault;
typedef enum { HYPERRIG_MINI_DMA_RX = 0, HYPERRIG_MINI_DMA_TX = 1 } hyperrig_mini_dma_direction;
enum {
    HYPERRIG_MINI_WORK_FAULT = -1, HYPERRIG_MINI_WORK_INVALID = -2,
    HYPERRIG_MINI_WORK_BUSY = -3, HYPERRIG_MINI_WORK_IDLE = 0,
    HYPERRIG_MINI_WORK_DONE = 1
};

typedef struct {
    uint32_t *rx, *tx; /* separate 1024-byte, 32-byte-aligned DMA arrays */
    void *io_user;
    /* CPU0 IRQ exclusion AND compiler/hardware ordering, exact flag restore.
     * No CPU1 access or competing ISR/worker is allowed. Not just volatile. */
    uint32_t (*enter)(void *user);
    void (*leave)(void *user, uint32_t saved_flags);
    /* begin() must GUARANTEE exclusive ownership for the entire cache/copy/end
     * transaction, including a measured deadline margin or stopped DMA. Merely
     * reading the half bit or masking CPU IRQs does not supply this guarantee.
     * The board must establish RX/TX half phase alignment before using this API.
     * end() is always called after a successful begin(), including error paths.
     * A failed begin() must leave no lease held; end() must release on failure. */
    int (*begin)(void *user, hyperrig_mini_dma_direction direction, unsigned half, uint32_t sequence);
    int (*end)(void *user, hyperrig_mini_dma_direction direction, unsigned half, uint32_t sequence);
    /* Mandatory explicit cache hooks; coherent memory still needs a verified
     * barrier implementation. Addresses/lengths are whole exclusive lines.
     * RX must have been cleaned/invalidated before DMA starts and remain CPU
     * read-only. Never write a dirty RX cache line back over fresh DMA samples. */
    int (*rx_for_cpu)(void *user, uint32_t *address, size_t bytes);
    int (*tx_for_device)(void *user, uint32_t *address, size_t bytes);
    /* Optional bounded IRQ notification, ordinary C ABI. No context switching,
     * interrupt nesting, REP/DSP/coproc code or writes to extra special state.
     * Its generated instructions are a board-integration review obligation. */
    void (*wake_from_irq)(void *user);
    hyperrig_mini_audio_process process; /* worker only, must fill all 64 outputs */
    void *process_user;
    unsigned input_fraction, output_fraction; /* 0..31, explicit model scaling */
} hyperrig_mini_runtime_ops;

typedef struct {
    uint32_t events, completed, pending_overruns, deadline_overruns, phase_errors;
    uint32_t invalid_halves, rx_errors, process_errors, tx_errors, ignored_events;
} hyperrig_mini_runtime_stats;
typedef struct {
    uint32_t sequence, pending, busy, half;
    hyperrig_mini_runtime_fault fault;
    int fault_detail;
    hyperrig_mini_runtime_stats stats;
} hyperrig_mini_runtime_snapshot;

typedef struct {
    hyperrig_mini_runtime_ops ops;
    /* These fields are accessed only with CPU0 IRQ excluded (also in ISR).
     * They are exposed for static allocation, not for direct application writes. */
    uint32_t magic, sequence, pending, busy, half, have_phase, last_half;
    hyperrig_mini_runtime_fault fault;
    int fault_detail;
    hyperrig_mini_runtime_stats stats;
    uint32_t rx_copy[HYPERRIG_MINI_AUDIO_SLOTS];
    uint32_t tx_copy[HYPERRIG_MINI_AUDIO_SLOTS];
    int32_t input[HYPERRIG_MINI_AUDIO_FRAMES], output[HYPERRIG_MINI_AUDIO_FRAMES];
} hyperrig_mini_runtime;

/* Init/reinit only with DMA stopped, IRQ disabled and no worker in progress.
 * TX silence/cache preparation, board clock and analog mute are caller-owned.
 * Runtime and DMA allocations must not overlap. Invalid arguments do not write.
 * Reinitialization resets counters and fault; it does not reset DSP model state. */
int hyperrig_mini_runtime_init(hyperrig_mini_runtime *runtime, const hyperrig_mini_runtime_ops *ops);
/* Install as audio_device.ready, with user=runtime; enqueues/wakes, never DSP. */
void hyperrig_mini_runtime_ready(void *user, unsigned half);
/* Single CPU0 foreground worker. On fault, do not resume: board must stop/mute
 * safely before reinitializing. No promise of silence is made by a fault latch. */
int hyperrig_mini_runtime_work(hyperrig_mini_runtime *runtime);
int hyperrig_mini_runtime_inspect(hyperrig_mini_runtime *runtime, hyperrig_mini_runtime_snapshot *snapshot);

/* Target-only exclusion primitives. They preserve ICFG, mask bit8 and csync.
 * They are not cross-core locks and cannot exclude DMA or nonmaskable faults. */
uint32_t hyperrig_mini_runtime_enter_cpu0(void *user);
void hyperrig_mini_runtime_leave_cpu0(void *user, uint32_t saved_flags);

/* Bind/unbind only with DMA stopped and IRQ11 disabled on both CPUs; CPU0 only.
 * device must already have ready=runtime_ready and user=initialized runtime.
 * NULL unbinds. Does not install/enable a vector or touch peripheral registers. */
int hyperrig_mini_runtime_irq_bind(hyperrig_mini_audio_device *device);
unsigned hyperrig_mini_irq11_dispatch(void);
void hyperrig_mini_irq11_entry(void); /* target ASM saves IRQ context, then rti */
#endif
