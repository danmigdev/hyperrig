; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 3 functions, 0x0200ff76..0x0200ffea

; phase3_p13_adc_sample_blocking: 0x0200ff76..0x0200ffc2, module phase3-p13 (adc_sample_blocking)
.type phase3_p13_adc_sample_blocking,@function
phase3_p13_adc_sample_blocking:
    [--sp] = {rets, r4}
    r1 = r0 << 8
    r1 = r1 & 0xF00
    r2 = 61454
    r3 = r0.l (u)
    r4 = r1 | r2
    if (r3 == 15) {  ; @if.eq.ri.s12
    r0 = r0 >> 16
    call L0200ff48
    }
    r1 = 78080
    [r1+0] = r4
    [r1+0] |= 0x10
    [r1+0] |= 0x40
    r0 = 0
L0200ffa4:
    r2 = [r1+0]
    r3 = r0 >> 7
    if (r3 > 3124) goto L0200ffb6
    r2 = r2.b0 (s)
    r0 += 1  ; @add.ri.u5
    ifs (r2 > -1) goto L0200ffa4
L0200ffb6:
    r0 = [r1+4]
    [r1+0] = 0x40
    [r1+0] = 0x0
    {pc, r4} = [sp++]

; phase3_p13_adc_sample_average: 0x0200ffc2..0x0200ffde, module phase3-p13 (adc_sample_average)
.type phase3_p13_adc_sample_average,@function
phase3_p13_adc_sample_average:
    [--sp] = {rets, r6-r4}
    r4 = r0
    call phase3_p13_adc_sample_blocking
    r5 = 0
    r6 = 8
    goto L0200ffd6
L0200ffce:
    r0 = r4
    call phase3_p13_adc_sample_blocking
    r5 += r0  ; @add.rr
    r6 += -1
L0200ffd6:
    if (r6 != 0) goto L0200ffce
    r0 = r5 + 4
    r0 = r0 >> 3
    {pc, r6-r4} = [sp++]

; phase3_p13_get_vbg_trim: 0x0200ffde..0x0200ffea, module phase3-p13 (get_vbg_trim)
.type phase3_p13_get_vbg_trim,@function
phase3_p13_get_vbg_trim:
    r0 = 29883724
    r0 = b[r0+30] (u)
    rts
