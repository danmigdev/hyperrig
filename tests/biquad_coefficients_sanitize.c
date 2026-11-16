/* Exact-buffer checks for reconstructed coefficient staging.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_biquad_coefficients.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void produce(void *opaque, hyperrig_biquad_section *destination,
    const hyperrig_biquad_coefficients_request *request)
{
    hyperrig_biquad_coefficients_input *input = opaque;
    if (request->mode > 2 || request->width != UINT32_C(0x3f666666)) abort();
    if (hyperrig_biquad_coefficients_normalize(destination, input)) abort();
}

int main(void)
{
    unsigned section, parameter, cases = 0;
    for (section = 0; section <= 5; ++section) {
        for (parameter = 0; parameter < 256; ++parameter) {
            hyperrig_biquad_chain *runtime = malloc(sizeof(*runtime));
            hyperrig_biquad_coefficients_control *control = malloc(sizeof(*control));
            hyperrig_biquad_coefficients_input *input = malloc(sizeof(*input));
            hyperrig_biquad_coefficients_io *io = malloc(sizeof(*io));
            if (!runtime || !control || !input || !io) return 1;
            memset(runtime, 0xA5, sizeof(*runtime));
            memset(control, 0, sizeof(*control));
            memset(input, 0, sizeof(*input));
            input->numerator[0] = input->denominator[0] = UINT32_C(0x3f800000);
            input->enabled = parameter;
            input->residual = parameter << 8;
            io->produce = produce;
            io->opaque = input;
            if (hyperrig_biquad_coefficients_stage(runtime, control, section,
                    (int32_t)parameter - 128, io) != (section == 5 ? 1 : 0)) return 2;
            if (control->requests != 1) return 3;
            if (section < 5) {
                if (runtime->staged[section].filter.coefficients[0] != (1 << 28) ||
                    runtime->staged[section].enabled != parameter ||
                    runtime->staged[section].residual != (parameter != 0) ||
                    runtime->pending[section] != 1 || runtime->elapsed_average) return 4;
                if (hyperrig_biquad_coefficients_setup(runtime, control, section, io)) return 5;
            }
            free(io);
            free(input);
            free(control);
            free(runtime);
            ++cases;
        }
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u}\n", cases);
    return 0;
}
