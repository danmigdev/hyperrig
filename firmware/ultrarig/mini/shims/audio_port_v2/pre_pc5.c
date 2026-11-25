/* Copied unchanged from firmware/mini/audio_port_v2/pre_pc5.c for the source build, except that the application
 * addresses this code uses are macros: tools/build_hyperrig_mini_image.py defines them from the linked
 * application (firmware/ultrarig/mini/bindings.json), so this code follows the application when it
 * moves. The unchanged values are the ones of the original file. */
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
#ifndef HYPERRIG_G_GPIO_SET_DIE
#error "HYPERRIG_G_GPIO_SET_DIE is defined by the build from the linked application"
#endif
#ifndef HYPERRIG_G_GPIO_DIRECTION_OUTPUT
#error "HYPERRIG_G_GPIO_DIRECTION_OUTPUT is defined by the build from the linked application"
#endif
#ifndef HYPERRIG_G_GPIO_SET_HD_0
#error "HYPERRIG_G_GPIO_SET_HD_0 is defined by the build from the linked application"
#endif
#define G_DIGITAL ((gpio_value_fn)(uintptr_t)HYPERRIG_G_GPIO_SET_DIE)
#define G_OUTPUT ((gpio_value_fn)(uintptr_t)HYPERRIG_G_GPIO_DIRECTION_OUTPUT)
/* G's specialization is ONE argument and always clears HD0, not HD. */
#define G_HD0_CLEAR ((gpio_pin_fn)(uintptr_t)HYPERRIG_G_GPIO_SET_HD_0)
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
