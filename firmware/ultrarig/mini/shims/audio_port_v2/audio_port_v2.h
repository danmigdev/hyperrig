#ifndef HYPERRIG_MINI_AUDIO_PORT_V2_H
#define HYPERRIG_MINI_AUDIO_PORT_V2_H
#include "../audio_port/audio_port.h"

typedef struct {
    unsigned records_attempted;
    unsigned records_acknowledged;
    unsigned records_nacked;
    unsigned records_continued_after_nack;
    unsigned bytes_acknowledged;
    int fatal_status;
} hyperrig_mini_audio_v2_result;

/* Original MINI's table caller continues after a record NACK. Retain the
 * existing codec writer's explicit STOP cleanup, and continue only if that
 * cleanup succeeds and leaves the bus initialized. A zero return means the
 * startup policy may continue; it does NOT mean all records were ACKed.
 * records_completed counts only fully ACKed records, never attempted ones.
 * No codec data/OSR/sample-rate changes are introduced here. */
int hyperrig_mini_audio_v2_pre(hyperrig_mini_codec_bus *bus,
    const hyperrig_mini_audio_port_io *io, unsigned *records_completed,
    hyperrig_mini_audio_v2_result *result);

/* Fixed PC5 HD-bit clear under the original G critical/bank-lock protocol.
 * Target only; this function is not a ROM-plugin service. */
void hyperrig_mini_g_pc5_hd_clear(void);
#endif
