/* Reconstructed MINI_009 platform fragments. See docs/MINI_PLATFORM.md. */
#ifndef HYPERRIG_MINI_PLATFORM_H
#define HYPERRIG_MINI_PLATFORM_H
#include <stdint.h>

enum {
    HYPERRIG_MINI_PLATFORM_INVALID = -1,
    HYPERRIG_MINI_PLATFORM_TIMEOUT = -2,
    HYPERRIG_MINI_PLATFORM_BUSY = -3,
    HYPERRIG_MINI_PLATFORM_UNSUPPORTED = -4,
    HYPERRIG_MINI_CACHE_CLEAN = 1,
    HYPERRIG_MINI_CACHE_CLEAN_INVALIDATE = 2
};

/* Callbacks allow deterministic host traces. Target callbacks are in RAM.
 * The caller owns P33/cache and serializes interrupts and the other CPU.
 * There is no RTOS lock, clock initialization, or readiness flag here. */
typedef struct {
    void *user;
    uint32_t (*read32)(void *user, uint32_t address);
    void (*write32)(void *user, uint32_t address, uint32_t value);
    void (*sync)(void *user);
    void (*cache_line)(void *user, uint32_t address, unsigned operation);
} hyperrig_mini_platform_io;

/* Installs direct-MMIO callbacks only; does not invoke them. Target-only file.
 * Before calling them, .ramtext must be copied AND instruction visibility
 * established. The data-cache API below does not publish executable code. */
void hyperrig_mini_platform_target_io(hyperrig_mini_platform_io *io);

/* P33 watchdog commands recovered from stock. poll_limit counts SPI status
 * reads per transmitted byte, NOT elapsed time. A timeout leaves transaction
 * completion unknown: CS is released and the caller must stop/recover.
 * Inherited bridge mode bits3:2 must equal 11; another mode is rejected.
 * feed() preserves the timeout/enable bits; it does not initialize the WDT.
 * init_stock_4s() is the six-command stock sequence, with SDK nominal 4s code.
 * Its real deadline depends on P33 clock. Do not enable without a feed policy. */
int hyperrig_mini_watchdog_feed(const hyperrig_mini_platform_io *io, uint32_t poll_limit);
int hyperrig_mini_watchdog_init_stock_4s(const hyperrig_mini_platform_io *io, uint32_t poll_limit);

/* Whole 32-byte DATA-cache lines in lower MINI RAM only. No rounding into adjacent
 * allocations. The caller must own the lines and prevent concurrent CPU/DMA
 * access. Invalidate includes writeback: a dirty stale RX line can overwrite
 * DMA results. Clean/invalidate before RX ownership passes to DMA, and never
 * write those RX lines from either CPU until DMA ownership returns.
 * No cache-way repartition, MMU update, SFC disable or readiness claim. */
int hyperrig_mini_cache_range(const hyperrig_mini_platform_io *io, uint32_t address,
                              uint32_t bytes, unsigned operation, uint32_t poll_limit);

/* Raw handover state. read_snapshot() only reads MMIO, under caller exclusion
 * of clock changes. BAUD is read by stock although the SDK labels it WO. */
typedef struct {
    uint32_t sys_div, clk_con0, clk_con1, clk_con2;
    uint32_t pll_con0, pll_con1, pll2_con0, pll2_con1;
    uint32_t husb_con0, husb_con2, sfc_con, sfc_baud;
    uint32_t cache_con, cache_dways, cache_iways, sdram_con, psram_con;
} hyperrig_mini_clock_snapshot;

typedef struct {
    uint32_t oscillator_hz, pll2_hz, sys_hz, hsb_hz, lsb_hz, sfc_hz, sdram_hz;
    uint32_t sys_selector, main_selector, alnk_mux;
} hyperrig_mini_clock_nominal;

int hyperrig_mini_clock_read_snapshot(const hyperrig_mini_platform_io *io,
                                     hyperrig_mini_clock_snapshot *snapshot);
/* Reproduces the supported stock arithmetic, not a frequency measurement.
 * sys_selector 0..9 supported; 10..15 rejected rather than the stock fallback.
 * main_selector is reported separately: the stock frequency arithmetic does
 * not establish that this source is actually driving the CPU.
 * alnk_mux=0x500 is the observed 48k family selection, not proof of PLL/codec
 * rate or lock. This API never changes SFC/PLL/dividers or enables audio. */
int hyperrig_mini_clock_decode(const hyperrig_mini_clock_snapshot *snapshot,
                               hyperrig_mini_clock_nominal *nominal);
#endif
