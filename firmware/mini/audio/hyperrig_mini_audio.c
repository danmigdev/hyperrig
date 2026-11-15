/* Hand reconstruction from M-VAVE TANK MINI_009; provenance and exact source
 * addresses in docs/MINI_AUDIO_DRIVER.md. No claim of executed hardware. */
#include "hyperrig_mini_audio.h"

typedef char con1_offset[(offsetof(hyperrig_mini_alnk_registers, con1) == 4) ? 1 : -1];
typedef char con2_offset[(offsetof(hyperrig_mini_alnk_registers, con2) == 8) ? 1 : -1];
typedef char con3_offset[(offsetof(hyperrig_mini_alnk_registers, con3) == 12) ? 1 : -1];
typedef char address_offset[(offsetof(hyperrig_mini_alnk_registers, adr) == 16) ? 1 : -1];
typedef char length_offset[(offsetof(hyperrig_mini_alnk_registers, len) == 32) ? 1 : -1];
typedef char direction_offset[(offsetof(hyperrig_mini_porta_registers, direction) == 8) ? 1 : -1];

static int registers_valid(const hyperrig_mini_audio_device *d)
{
    return d && d->alnk && d->clock && d->mux && d->porta;
}

int hyperrig_mini_audio_prepare(hyperrig_mini_audio_device *d, uint32_t tx_bus, uint32_t rx_bus, uint32_t rate)
{
    const uint32_t outputs = UINT32_C(0xf0); /* PA4..PA7 */
    const uint32_t input = UINT32_C(0x100);  /* PA8 */
    uint32_t distance = tx_bus > rx_bus ? tx_bus - rx_bus : rx_bus - tx_bus;
    if (!registers_valid(d) || (rate != 44100 && rate != 48000) ||
        !tx_bus || !rx_bus || ((tx_bus | rx_bus) & 3) || distance < 1024 ||
        tx_bus > UINT32_MAX - 1023 || rx_bus > UINT32_MAX - 1023) return -1;
    if (d->alnk->con0 & UINT16_C(0x800)) return -2;
    /* Equivalent fixed configuration to 0x02006f70/0x0200708c, excluding the
     * stock IRQ registration call and the caller's codec/PLL initialization. */
    d->prepared = 0;
    d->alnk->con0 = 0;
    d->alnk->con1 = 0;
    d->alnk->con2 = 0;
    d->alnk->con3 = 0;
    *d->mux = (*d->mux & ~UINT32_C(0xc0)) | UINT32_C(0x40);
    d->alnk->con3 = 3;
    d->porta->out |= outputs;
    d->porta->direction &= ~outputs;
    d->porta->direction |= input;
    d->porta->pull_down &= ~input;
    d->porta->pull_up |= input;
    d->porta->digital_enable |= input;
    d->alnk->con0 = UINT16_C(0x180);
    d->alnk->len = 128;
    *d->clock = (*d->clock & ~UINT32_C(0xf00)) | (rate == 48000 ? UINT32_C(0x500) : 0);
    d->alnk->con3 = (uint8_t)((d->alnk->con3 & (uint8_t)~0x1c) & (uint8_t)~0xe0);
    d->alnk->con3 |= UINT8_C(0x80);
    d->alnk->con1 = UINT16_C(0xd5); /* ch0 format1/24bit TX; ch1 format1/24bit RX */
    d->alnk->adr[0] = tx_bus;
    d->alnk->adr[1] = rx_bus;
    d->configured_rate = rate;
    d->prepared = 1;
    return 0;
}

int hyperrig_mini_audio_start(hyperrig_mini_audio_device *d, const hyperrig_mini_audio_readiness *ready)
{
    if (!registers_valid(d) || !d->prepared || !ready ||
        ready->clock_rate != d->configured_rate || ready->codec_rate != d->configured_rate ||
        !ready->irq_installed || !ready->dma_coherent || !ready->analog_path_ready) return -1;
    d->alnk->con0 |= UINT16_C(0x800);
    return 0;
}

int hyperrig_mini_audio_stop(hyperrig_mini_audio_device *d)
{
    if (!registers_valid(d) || !d->prepared) return -1;
    d->alnk->con0 &= (uint16_t)~UINT16_C(0x800);
    return 0;
}

unsigned hyperrig_mini_audio_irq(hyperrig_mini_audio_device *d)
{
    unsigned channel, handled = 0;
    if (!d || !d->alnk || !d->prepared) return 0;
    for (channel = 0; channel < 4; ++channel) {
        if (d->alnk->con2 & (1u << (channel + 4))) {
            if (channel == 1 && d->ready) {
                unsigned half = (~((unsigned)d->alnk->con0 >> 13)) & 1;
                d->ready(d->user, half);
            }
            /* Stock handler uses read/OR/write on the byte register, rather
             * than treating its high pending bits as software-owned state. */
            d->alnk->con2 |= (uint8_t)(1u << channel);
            handled |= 1u << channel;
        }
    }
    return handled;
}

static int32_t signed24(uint32_t value)
{
    value &= UINT32_C(0xffffff);
    return value & UINT32_C(0x800000) ? (int32_t)value - INT32_C(0x1000000) : (int32_t)value;
}

static int32_t signed32(uint32_t bits)
{
    if (bits <= INT32_MAX) return (int32_t)bits;
    return -1 - (int32_t)(UINT32_MAX - bits);
}

static int32_t floor_shift(int32_t value, unsigned shift)
{
    uint32_t bits = (uint32_t)value;
    if (!shift) return value;
    return signed32((bits >> shift) | ((bits >> 31) ? (UINT32_MAX << (32 - shift)) : 0));
}

int32_t hyperrig_mini_audio_stock_rx(uint32_t slot)
{
    return signed24(slot) * 2;
}

int32_t hyperrig_mini_audio_rx_q(uint32_t slot, unsigned fraction)
{
    int32_t value = signed24(slot);
    if (fraction > 31) return 0;
    if (fraction < 23) return floor_shift(value, 23 - fraction);
    return (int32_t)((int64_t)value * (INT64_C(1) << (fraction - 23)));
}

uint32_t hyperrig_mini_audio_tx_q(int32_t value, unsigned fraction)
{
    int64_t result;
    if (fraction > 31) return 0;
    result = fraction > 23 ? floor_shift(value, fraction - 23) :
                             (int64_t)value * (INT64_C(1) << (23 - fraction));
    if (result < -INT64_C(0x800000)) result = -INT64_C(0x800000);
    if (result > INT64_C(0x7fffff)) result = INT64_C(0x7fffff);
    return (uint32_t)result & UINT32_C(0xffffff);
}

int hyperrig_mini_audio_unpack(const uint32_t *rx, unsigned half, unsigned fraction, int32_t mono[64])
{
    unsigned i;
    if (!rx || !mono || half > 1 || fraction > 31) return -1;
    for (i = 0; i < 64; ++i) mono[i] = hyperrig_mini_audio_rx_q(rx[half * 128 + 2 * i], fraction);
    return 0;
}

int hyperrig_mini_audio_pack(const int32_t mono[64], unsigned fraction, uint32_t *tx, unsigned half)
{
    unsigned i;
    if (!tx || !mono || half > 1 || fraction > 31) return -1;
    for (i = 0; i < 64; ++i) {
        uint32_t value = hyperrig_mini_audio_tx_q(mono[i], fraction);
        tx[half * 128 + 2 * i] = value;
        tx[half * 128 + 2 * i + 1] = value;
    }
    return 0;
}

int hyperrig_mini_audio_process_half(const uint32_t *rx, uint32_t *tx, unsigned half,
                                    unsigned input_fraction, unsigned output_fraction,
                                    hyperrig_mini_audio_process process, void *user)
{
    int32_t input[64], output[64];
    unsigned i;
    int status;
    if (!rx || !tx || !process || half > 1 || input_fraction > 31 || output_fraction > 31) return -1;
    hyperrig_mini_audio_unpack(rx, half, input_fraction, input);
    for (i = 0; i < 64; ++i) output[i] = 0;
    status = process(user, input, output, 64);
    if (status) {
        for (i = 0; i < 128; ++i) tx[half * 128 + i] = 0;
        return status;
    }
    return hyperrig_mini_audio_pack(output, output_fraction, tx, half);
}

int hyperrig_mini_codec_replay_stock(hyperrig_mini_codec_write write_record, void *user)
{
    static const uint8_t records[22][4] = {
        {0x00,0x00,0xff,0xff},{0x00,0x66,0x00,0x60},{0x00,0x01,0x0f,0xd0},
        {0x00,0x03,0x00,0x00},{0x00,0x1d,0x00,0x02},{0x00,0x1c,0x00,0x0e},
        {0x00,0x72,0x01,0x70},{0x00,0x2b,0x00,0x03},{0x00,0x2c,0x00,0x81},
        {0x00,0x73,0x33,0x0c},{0x00,0x76,0x71,0x40},{0x00,0x34,0xcf,0xcf},
        {0x00,0x35,0xcf,0xcf},{0x00,0x4b,0x20,0x07},{0x00,0x6a,0x10,0x03},
        {0x00,0x77,0x00,0x00},{0x00,0x7e,0x0a,0x0a},{0x00,0x7f,0xc0,0x3f},
        {0x00,0x32,0x00,0x00},{0x00,0x80,0x07,0x20},{0x00,0x0d,0xc0,0x00},
        {0x00,0x31,0x10,0x04}
    };
    unsigned i;
    if (!write_record) return -1;
    for (i = 0; i < 22; ++i) {
        int status = write_record(user, UINT8_C(0x36), records[i]);
        if (status) return status;
    }
    return 0;
}
