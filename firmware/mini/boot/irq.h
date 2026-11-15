/* CPU0/1 physical IRQ registration reconstructed from MINI_009 0x02001756.
 * Hardware routing/latency is not verified; these are explicit board hooks,
 * never called by the boot probe. Handler must use the pi32v2 interrupt ABI. */
#ifndef HYPERRIG_MINI_IRQ_H
#define HYPERRIG_MINI_IRQ_H
int hyperrig_mini_irq_register(unsigned index, unsigned priority,
                              void (*handler)(void), unsigned core);
int hyperrig_mini_irq_unregister(unsigned index);
#endif
