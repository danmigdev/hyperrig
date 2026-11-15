/* Executes the probe's C hook on the host, never the target startup or MMIO. */
#include "boot_probe.h"
#include <inttypes.h>
#include <stdio.h>

volatile hyperrig_mini_probe_record hyperrig_mini_probe;

int main(void)
{
    int status = hyperrig_mini_application_probe();
    int valid = status == 0 && hyperrig_mini_probe.audio_status == 0 &&
        hyperrig_mini_probe.rendered_frames == 64 && hyperrig_mini_probe.audio_frames == 64 &&
        hyperrig_mini_probe.output_checksum == UINT32_C(0xf10b5e4c) &&
        hyperrig_mini_probe.tx_checksum == UINT32_C(0xf0a44a06);
    printf("{\"host_c_probe_passed\":%s,\"application_status\":%d,"
           "\"model_bytes\":%" PRIu32 ",\"engine_bytes\":%" PRIu32 ","
           "\"rendered_frames\":%" PRIu32 ",\"dsp_crc32\":\"%08" PRIx32 "\","
           "\"audio_status\":%" PRId32 ",\"audio_frames\":%" PRIu32 ","
           "\"tx_crc32\":\"%08" PRIx32 "\"}\n", valid ? "true" : "false", status,
           hyperrig_mini_probe.model_bytes, hyperrig_mini_probe.engine_bytes,
           hyperrig_mini_probe.rendered_frames, hyperrig_mini_probe.output_checksum,
           hyperrig_mini_probe.audio_status, hyperrig_mini_probe.audio_frames,
           hyperrig_mini_probe.tx_checksum);
    return valid ? 0 : 1;
}
