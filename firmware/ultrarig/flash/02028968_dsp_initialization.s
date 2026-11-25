; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_initialization: 3 functions, 0x02028968..0x02028a34

; dsp_initialization_gain: 0x02028968..0x0202898e, module dsp-initialization (gain), dsp-transition-notification (initialization_gain)
.type dsp_initialization_gain,@function
dsp_initialization_gain:
    [--sp] = rets
    if (r0 == 0) goto L02028988
    r0 = itof(r0)
    r1 = 1036831949
    r0 = r0 * r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
    pc = [sp++]
L02028988:
    r0 = 0x10000
    pc = [sp++]

; dsp_initialization_setup: 0x0202898e..0x020289d4, module dsp-initialization (setup), dsp-transition-notification (initialization_setup)
.type dsp_initialization_setup,@function
dsp_initialization_setup:
    [--sp] = {rets, r5, r4}
    sp += -4
    r3 = 1060320051
    [sp] = r3
    r3 = 1
    if (r0 != 2) {
    r3 = 2
    }
    r4 = 0
    if (r0 != 1) {
    r4 = r3
    }
    r3 = effect_prior_initialization_coefficients
    r0 = h[r3+r0<<1] (u)
    r1 = itof(r1)
    r3 = 1036831949
    r3 = r1 * r3 (f)
    r5 = utof(r0)
    r0 = r2
    r1 = r4
    r2 = r5
    call biquad_generator_generate
    sp += 4
    {pc, r5, r4} = [sp++]

; dsp_initialization_reset_filters: 0x020289d4..0x02028a34, module dsp-initialization (reset_filters), dsp-transition-notification (initialization_reset_filters)
.type dsp_initialization_reset_filters,@function
dsp_initialization_reset_filters:
    [--sp] = {rets, r11-r4}
    r8 = L01c32db0
    r6 = 0
    b[r8+1] = r6
    r7 = 110
    r9 = L01c32fa0
    r10 = 0
    r11 = 0
    r5 = 0
L020289f0:
    r1 = h[r8+r7<<1] (s)
    r0 = r5 + r9
    r4 = r0 + 144
    r0 = r7 + -109
    r2 = r4
    call dsp_initialization_setup
    [r4+36] = r6
    [r4+32] = r6
    [r4+28] = r6
    [r4+20] = r10
    [r4+24] = r11
    r5 += 44
    r7 = r7 + 1
    if (r5 != 176) goto L020289f0
    r0 = h[r8+218] (s)
    call dsp_initialization_gain
    r1 = L01c1f7d4
    [r8+32] = 0x0
    [r1+0] = r0
    r0 = 1
    b[r8+28] = r0
    {pc, r11-r4} = [sp++]
