/* PC5 preparation is before the original clock-getter/PA9/codec path.
 * This preserves an observed board setup; PC5 is not a proven audio rail. */
#include "audio_port_v2.h"

typedef void (*gpio_value_fn)(unsigned pin,unsigned value);
typedef void (*gpio_pin_fn)(unsigned pin);
#ifdef HYPERRIG_AUDIO_V2_HOST
extern void hyperrig_audio_v2_test_digital(unsigned,unsigned);
extern void hyperrig_audio_v2_test_output(unsigned,unsigned);
extern void hyperrig_audio_v2_test_hd0(unsigned);
#define G_DIGITAL hyperrig_audio_v2_test_digital
#define G_OUTPUT hyperrig_audio_v2_test_output
#define G_HD0_CLEAR hyperrig_audio_v2_test_hd0
#else
#define G_DIGITAL ((gpio_value_fn)(uintptr_t)0x0200187cu)
#define G_OUTPUT ((gpio_value_fn)(uintptr_t)0x02004998u)
/* G's specialization is ONE argument and always clears HD0, not HD. */
#define G_HD0_CLEAR ((gpio_pin_fn)(uintptr_t)0x0201b1b6u)
#endif

/* The frozen v1 g_bindings.c is compiled with this one symbol renamed.
 * Its bus callbacks, getter, rate checks and original G channel start stay
 * unchanged. Its pre() resolves to the explicit v2 table policy. */
extern int hyperrig_mini_g_audio_pre_current_clock_v1(void);

int hyperrig_mini_g_audio_pre_current_clock(void)
{
    G_DIGITAL(37,1);
    G_OUTPUT(37,1); /* Original helper updates OUT then DIR under bank C lock. */
    hyperrig_mini_g_pc5_hd_clear();
    G_HD0_CLEAR(37);
    return hyperrig_mini_g_audio_pre_current_clock_v1();
}
