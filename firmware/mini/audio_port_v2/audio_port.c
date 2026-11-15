#include "audio_port_v2.h"

static int valid_io(const hyperrig_mini_audio_port_io *io)
{
    return io && io->pa9_output && io->spin_iterations;
}

int hyperrig_mini_audio_v2_pre(hyperrig_mini_codec_bus *bus,
    const hyperrig_mini_audio_port_io *io, unsigned *records_completed,
    hyperrig_mini_audio_v2_result *result)
{
    unsigned index, complete=0;
    int status=HYPERRIG_MINI_CODEC_EINVAL;
    if (records_completed) *records_completed=0;
    if (result) {
        result->records_attempted=result->records_acknowledged=0;
        result->records_nacked=result->records_continued_after_nack=0;
        result->bytes_acknowledged=0;
        result->fatal_status=0;
    }
    if (!valid_io(io) || !bus || !bus->gpio || !bus->sample || !bus->delay)
        goto fatal;
    io->pa9_output(io->user,0);
    io->spin_iterations(io->user,100000);
    status=hyperrig_mini_codec_bus_init(bus);
    if (status) goto fatal;
    for (index=0;index<HYPERRIG_MINI_CODEC_RECORDS;++index) {
        hyperrig_mini_codec_result transaction;
        status=hyperrig_mini_codec_write(bus,hyperrig_mini_codec_stock_record(index),&transaction);
        if (result) {
            ++result->records_attempted;
            result->bytes_acknowledged+=transaction.acknowledged;
            if (status==HYPERRIG_MINI_CODEC_NACK) ++result->records_nacked;
        }
        /* Never hide a failed STOP behind the first NACK status. */
        if (transaction.cleanup_status) {
            status=transaction.cleanup_status;
            goto fatal;
        }
        if (status==HYPERRIG_MINI_CODEC_NACK && transaction.status==status &&
            transaction.stop_attempted && transaction.acknowledged<5 && bus->initialized) {
            if (result) ++result->records_continued_after_nack;
            continue;
        }
        if (status) goto fatal;
        if (transaction.status || !transaction.stop_attempted ||
            transaction.acknowledged!=5 || !bus->initialized) {
            status=HYPERRIG_MINI_CODEC_EIO;
            goto fatal;
        }
        ++complete;
        if (records_completed) *records_completed=complete;
        if (result) ++result->records_acknowledged;
    }
    return 0;
fatal:
    if (result) result->fatal_status=status;
    return status;
}

/* ABI consumed by the unchanged G binding. It does not inspect a success
 * count; the changed policy is intentional and documented above. */
int hyperrig_mini_audio_port_pre(hyperrig_mini_codec_bus *bus,
    const hyperrig_mini_audio_port_io *io, unsigned *records_completed)
{
    return hyperrig_mini_audio_v2_pre(bus,io,records_completed,0);
}

/* Identical post policy to v1: original G start, wait, PA9 high. */
int hyperrig_mini_audio_port_post(const hyperrig_mini_audio_port_io *io)
{
    int status;
    if (!valid_io(io) || !io->start_original_g_channels)
        return HYPERRIG_MINI_CODEC_EINVAL;
    status = io->start_original_g_channels(io->user);
    if (status) return status < 0 ? status : HYPERRIG_MINI_CODEC_EIO;
    io->spin_iterations(io->user, 100000);
    io->pa9_output(io->user, 1);
    return 0;
}
