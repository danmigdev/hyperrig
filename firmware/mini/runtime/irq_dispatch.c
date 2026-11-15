#include "hyperrig_mini_runtime.h"

/* Written only while IRQ11 is disabled and DMA stopped, read only on CPU0. */
static hyperrig_mini_audio_device *bound_device;

int hyperrig_mini_runtime_irq_bind(hyperrig_mini_audio_device *device)
{
    hyperrig_mini_runtime_snapshot snapshot;
    if (device && (!device->alnk || device->ready != hyperrig_mini_runtime_ready ||
        hyperrig_mini_runtime_inspect((hyperrig_mini_runtime *)device->user, &snapshot) ||
        snapshot.busy || snapshot.pending || snapshot.fault)) return -1;
    bound_device = device;
    return 0;
}

__attribute__((section(".ramtext.mini_runtime"))) unsigned hyperrig_mini_irq11_dispatch(void)
{
    return bound_device ? hyperrig_mini_audio_irq(bound_device) : 0;
}
