#include "audio_port.h"

static int valid_io(const hyperrig_mini_audio_port_io *io)
{
    return io && io->pa9_output && io->spin_iterations;
}

int hyperrig_mini_audio_port_pre(hyperrig_mini_codec_bus *bus,
    const hyperrig_mini_audio_port_io *io, unsigned *records_completed)
{
    int status;
    if (records_completed) *records_completed = 0;
    if (!valid_io(io) || !bus || !bus->gpio || !bus->sample || !bus->delay)
        return HYPERRIG_MINI_CODEC_EINVAL;
    io->pa9_output(io->user, 0);
    io->spin_iterations(io->user, 100000);
    status = hyperrig_mini_codec_bus_init(bus);
    if (status) return status;
    return hyperrig_mini_codec_apply_stock(bus, records_completed);
}

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
