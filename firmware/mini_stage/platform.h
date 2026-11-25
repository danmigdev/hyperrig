/* Registers, time and the few chip services the loader uses. */
#ifndef HYPERRIG_STAGE_PLATFORM_H
#define HYPERRIG_STAGE_PLATFORM_H
#include <stdbool.h>
#include <stdint.h>
#define REG(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define BIT(n) (UINT32_C(1) << (n))
#define DMA_ADDRESS(p) ((uint32_t)(uintptr_t)(p))
static inline void sync_cpu(void) { __asm__ volatile("csync" ::: "memory"); }
void settle(unsigned n);
/* Timer 0 at the 60 MHz LSB clock the bootloader has set; false when the timer does not answer. */
bool hal_delay_us(uint32_t us);
/* The watchdog off, whatever the bootloader left. */
void hal_watchdog_off(void);
/* The chip's key, which the bootloader decodes the application with. */
uint16_t hal_chip_key(void);
void hal_reset(void) __attribute__((noreturn));
#endif
