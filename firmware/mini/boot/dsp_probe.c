/* Optional link probe for the reconstructed A2 capture engine. No device IO. */
#include "boot_probe.h"
#include "hyperrig/hyperrig_engine.h"
#include "hyperrig_mini_audio.h"

extern const unsigned char hyperrig_probe_capture[], hyperrig_probe_capture_end[];
static unsigned char model_arena[16384] __attribute__((aligned(8)));
static unsigned char engine_arena[196608] __attribute__((aligned(8)));
static hyperrig_a2l model;
static hyperrig_a2l3 engine;
static int32_t input[64], output[64];
/* RAM-only fake DMA arrays. No ALNK register, DMA bus address or IRQ is used. */
static uint32_t rx[256] __attribute__((aligned(32), section(".dma32")));
static uint32_t tx[256] __attribute__((aligned(32), section(".dma32")));

static uint32_t crc32_word_le(uint32_t crc, uint32_t value)
{
    unsigned byte, bit;
    for (byte = 0; byte < 4; ++byte) {
        crc ^= (value >> (byte * 8)) & 255;
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((crc & 1) ? UINT32_C(0xedb88320) : 0);
    }
    return crc;
}

static int process(void *user, const int32_t *in, int32_t *out, uint32_t frames)
{
    return hyperrig_a2l3_process((hyperrig_a2l3 *)user, in, out, frames);
}

int hyperrig_mini_application_probe(void)
{
    size_t model_bytes, engine_bytes;
    unsigned i;
    uint32_t crc = UINT32_MAX;
    int status;
    status = hyperrig_a2l_size(hyperrig_probe_capture,
             (size_t)(hyperrig_probe_capture_end - hyperrig_probe_capture), &model_bytes);
    if (status) return status;
    hyperrig_mini_probe.model_bytes = (uint32_t)model_bytes;
    if (model_bytes > sizeof(model_arena)) return -102;
    status = hyperrig_a2l_load(&model, model_arena, sizeof(model_arena), hyperrig_probe_capture,
             (size_t)(hyperrig_probe_capture_end - hyperrig_probe_capture));
    if (status) return status;
    status = hyperrig_a2l3_size(&model, &engine_bytes);
    if (status) return status;
    hyperrig_mini_probe.engine_bytes = (uint32_t)engine_bytes;
    if (engine_bytes > sizeof(engine_arena)) return -103;
    status = hyperrig_a2l3_init(&engine, &model, engine_arena, sizeof(engine_arena));
    if (status) return status;
    /* Zero input after reset. Expected CRC was obtained by interpreting the
     * original G kernels, not by executing this C implementation. */
    status = hyperrig_a2l3_process(&engine, input, output, 64);
    if (status) return status;
    for (i = 0; i < 64; ++i)
        crc = crc32_word_le(crc, (uint32_t)output[i]);
    hyperrig_mini_probe.output_checksum = ~crc;
    hyperrig_mini_probe.rendered_frames = 64;
    if (~crc != UINT32_C(0xf10b5e4c)) return -104;

    status = hyperrig_a2l3_reset(&engine);
    if (status) return status;
    for (i = 0; i < 256; ++i) {
        rx[i] = 0;
        tx[i] = UINT32_C(0xa5a5a5a5);
    }
    status = hyperrig_mini_audio_process_half(rx, tx, 0, 30, 31, process, &engine);
    hyperrig_mini_probe.audio_status = status;
    if (status) return status;
    crc = UINT32_MAX;
    for (i = 0; i < 128; ++i) crc = crc32_word_le(crc, tx[i]);
    hyperrig_mini_probe.tx_checksum = ~crc;
    hyperrig_mini_probe.audio_frames = 64;
    if (~crc != UINT32_C(0xf0a44a06)) status = -105;
    for (i = 128; i < 256; ++i)
        if (tx[i] != UINT32_C(0xa5a5a5a5)) status = -106;
    hyperrig_mini_probe.audio_status = status;
    return status;
}
