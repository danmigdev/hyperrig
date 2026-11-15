/* Reconstructed from the local M-VAVE TANK MINI_009 firmware and SDK register
 * layout. This is not a vendor source release. See docs/MINI_AUDIO_DRIVER.md. */
#ifndef HYPERRIG_MINI_AUDIO_H
#define HYPERRIG_MINI_AUDIO_H
#include <stdint.h>
#include <stddef.h>

enum {
    HYPERRIG_MINI_AUDIO_FRAMES = 64,
    HYPERRIG_MINI_AUDIO_SLOTS = 128,
    HYPERRIG_MINI_AUDIO_DMA_WORDS = 256,
    HYPERRIG_MINI_AUDIO_IRQ = 11,
    HYPERRIG_MINI_AUDIO_IRQ_PRIORITY = 6
};

/* Hardware places every register on a four-byte boundary; access widths are
 * significant. Do not replace byte/halfword registers by uint32_t accesses. */
typedef struct {
    volatile uint16_t con0; uint16_t reserved0;
    volatile uint16_t con1; uint16_t reserved1;
    volatile uint8_t con2; uint8_t reserved2[3];
    volatile uint8_t con3; uint8_t reserved3[3];
    volatile uint32_t adr[4];
    volatile uint16_t len; uint16_t reserved8;
} hyperrig_mini_alnk_registers;

typedef struct {
    volatile uint32_t out, in, direction, digital_enable, pull_up, pull_down;
} hyperrig_mini_porta_registers;

typedef void (*hyperrig_mini_audio_ready)(void *user, unsigned half);
typedef struct {
    hyperrig_mini_alnk_registers *alnk; /* physical 0x00012e00 */
    volatile uint32_t *clock;          /* physical 0x00010014 */
    volatile uint32_t *mux;            /* physical 0x00051030 */
    hyperrig_mini_porta_registers *porta; /* physical 0x00050000 */
    hyperrig_mini_audio_ready ready;
    void *user;
    unsigned prepared;
    uint32_t configured_rate;
} hyperrig_mini_audio_device;

typedef struct {
    uint32_t clock_rate, codec_rate;
    unsigned irq_installed, dma_coherent, analog_path_ready;
} hyperrig_mini_audio_readiness;

/* Offline reconstruction of the stock master-mode ALNK register sequence.
 * Only 44100/48000 accepted. tx/rx are DIFFERENT DMA bus addresses, each covers
 * 1024 writable bytes and is word-aligned. Call with IRQ disabled, exclusive
 * register/GPIO ownership, clock/PLL and codec already prepared by board code.
 * This does not establish codec 48k, analog mute, cache coherency or IRQ setup.
 * No DMA starts until start(). A failed validation performs no MMIO writes.
 * The caller must initialize TX to digital silence and make DMA buffers coherent.
 * GPIO sequence preserves other pins, but requires board-level exclusion of
 * concurrent RMW operations. No stock callback or buffer address is reused. */
int hyperrig_mini_audio_prepare(hyperrig_mini_audio_device *device,
                               uint32_t tx_bus, uint32_t rx_bus, uint32_t rate);
/* start() requires the board's actual readiness state: matching clock/codec
 * rates, installed IRQ11 wrapper, coherent DMA buffers and known analog/mute
 * setup. The driver cannot discover or prove these hardware properties. */
int hyperrig_mini_audio_start(hyperrig_mini_audio_device *device,
                             const hyperrig_mini_audio_readiness *ready);
int hyperrig_mini_audio_stop(hyperrig_mini_audio_device *device);
/* Invoke from a real IRQ11 wrapper which saves/restores CPU interrupt state.
 * Dispatches RX1 only, acknowledges pending channels 0..3 as stock does, returns
 * the pending-channel mask. ready() must enqueue/signal, never run heavy DSP.
 * Synchronization, overrun policy, cache barriers and RTOS wakeup are caller-owned. */
unsigned hyperrig_mini_audio_irq(hyperrig_mini_audio_device *device);

/* The stock RX operation is ((word<<8) arithmetic>>7): signextend24 * 2.
 * The normalized adapter below treats those raw low24 bits as signed Q23.
 * Q scaling, clipping and dual-mono TX are explicit HyperRig choices, not a
 * reconstruction of the stock effects, gain stages or output shaping LUT. */
int32_t hyperrig_mini_audio_stock_rx(uint32_t slot);
int32_t hyperrig_mini_audio_rx_q(uint32_t slot, unsigned fraction);
uint32_t hyperrig_mini_audio_tx_q(int32_t value, unsigned fraction);
/* Each DMA array contains 256 uint32_t words: 2 halves of 64 stereo frames.
 * rx reads left/even slots; tx writes identical left/right low24-bit values.
 * Half 0/1 and fractions 0..31 accepted. No overlap; valid array extents required.
 * Invalid scalar arguments/null pointers return -1 without touching output. */
int hyperrig_mini_audio_unpack(const uint32_t *rx, unsigned half, unsigned fraction, int32_t mono[64]);
int hyperrig_mini_audio_pack(const int32_t mono[64], unsigned fraction, uint32_t *tx, unsigned half);
typedef int (*hyperrig_mini_audio_process)(void *user, const int32_t *input, int32_t *output, uint32_t frames);
/* Task-context adapter. Needs 512 bytes of sample scratch on the caller stack.
 * process() must fill all 64 outputs on success. On DSP failure the selected TX
 * half becomes silence; the error is returned. It is the caller's responsibility
 * to meet the DMA deadline and to establish RX/TX half-phase alignment. */
int hyperrig_mini_audio_process_half(const uint32_t *rx, uint32_t *tx, unsigned half,
                                    unsigned input_fraction, unsigned output_fraction,
                                    hyperrig_mini_audio_process process, void *user);

/* The 22 opaque codec records at CPU 0x02035e35, each sent after address byte 0x36.
 * The bus callback returns 0 for a completed transfer. This only replays the
 * stock initialization table: codec identity and 48k-specific semantics unknown.
 * No GPIO I2C bit-banging, timing/delays or analog mute implementation here. */
typedef int (*hyperrig_mini_codec_write)(void *user, uint8_t address_byte, const uint8_t record[4]);
int hyperrig_mini_codec_replay_stock(hyperrig_mini_codec_write write_record, void *user);
#endif
