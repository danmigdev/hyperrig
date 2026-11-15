#ifndef HYPERRIG_MINI_BOOT_PROBE_H
#define HYPERRIG_MINI_BOOT_PROBE_H
#include <stdint.h>

/* Debugger-visible RAM only. No GPIO/USB/audio indications are claimed. */
typedef struct {
    uint32_t magic, stage, boot_context, initialized_word, zero_word;
    int32_t application_status;
    uint32_t model_bytes, engine_bytes, rendered_frames, output_checksum;
    int32_t audio_status;
    uint32_t audio_frames, tx_checksum;
} hyperrig_mini_probe_record;
extern volatile hyperrig_mini_probe_record hyperrig_mini_probe;
int hyperrig_mini_application_probe(void);
#endif
