/* Exact-buffer checks for the reconstructed complete coefficient generator.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_biquad_generator.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void)
{
    const uint32_t divisors[3] = {0, 48000, UINT32_MAX};
    unsigned section, rate, cases = 0;
    int parameter;
    for (section = 0; section <= 5; ++section) {
        for (rate = 0; rate < 3; ++rate) {
            for (parameter = -12; parameter <= 12; ++parameter) {
                hyperrig_biquad_chain *runtime = malloc(sizeof(*runtime));
                hyperrig_biquad_coefficients_control *control = malloc(sizeof(*control));
                hyperrig_biquad_coefficients_request *request = malloc(sizeof(*request));
                hyperrig_biquad_coefficients_input *raw = malloc(sizeof(*raw));
                hyperrig_biquad_section *destination = malloc(sizeof(*destination));
                if (!runtime || !control || !request || !raw || !destination) return 1;
                memset(runtime, 0xA5, sizeof(*runtime));
                memset(control, 0, sizeof(*control));
                memset(destination, 0xA5, sizeof(*destination));
                request->mode = section;
                request->table_value = UINT32_C(0x44960000);
                request->parameter = UINT32_C(0x40c00000);
                request->width = UINT32_C(0x3f666666);
                if (hyperrig_biquad_generate_input(raw, request, divisors[rate]) ||
                    hyperrig_biquad_generate(destination, request, divisors[rate])) return 2;
                if (hyperrig_biquad_generate_stage(runtime, control, section, parameter,
                        divisors[rate]) != (section == 5 ? 1 : 0)) return 3;
                if (control->requests != 1) return 4;
                if (section < 5) {
                    if (runtime->staged[section].enabled != (parameter != 0) ||
                        runtime->staged[section].residual != (section == 0) ||
                        runtime->pending[section] != 1 || runtime->elapsed_average) return 5;
                    if (hyperrig_biquad_generate_setup(runtime, control, section, divisors[rate])) return 6;
                }
                free(destination);
                free(raw);
                free(request);
                free(control);
                free(runtime);
                ++cases;
            }
        }
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u}\n", cases);
    return 0;
}
