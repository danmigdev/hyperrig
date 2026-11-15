#ifndef HYPERRIG_MINI_ENTRY_RECOVERY_H
#define HYPERRIG_MINI_ENTRY_RECOVERY_H

#include <stdint.h>

/* Ordinary C ABI for a future RAM qualification plugin. No BSS, GPIO helper,
 * clock setup, USB callback or RTOS dependency. Restores the four selected
 * GPIO configuration fields before returning. Requires all three DIR bits
 * already input, otherwise returns CONFIG_ERROR without GPIO writes.
 * Not an interrupt handler. */
enum hyperrig_mini_entry_key_result {
    HYPERRIG_ENTRY_NOT_HELD = 0,
    HYPERRIG_ENTRY_ALL_THREE_HELD = 1,
    HYPERRIG_ENTRY_GPIO_CONFIG_ERROR = 2
};
uint32_t hyperrig_mini_entry_recovery_check(void);

/* Separate, deliberate nonreturning operation: write the stock 16-byte ROM
 * marker, csync, then set only stock RST_CON bit4. Never call merely because
 * a GPIO probe or host handshake failed. This component has not run on MINI. */
void hyperrig_mini_entry_recovery_to_rom(void) __attribute__((noreturn));

#endif
