; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 3 functions, 0x02008d90..0x02008e54

; preset_application_services_decibel_gain: 0x02008d90..0x02008de2, module preset-application-services (decibel_gain)
.type preset_application_services_decibel_gain,@function
preset_application_services_decibel_gain:
    [--sp] = {rets, r11, r10, r8-r4}
    r1 = abs(r0)
    r4 = 0
    r2 = r4 + 0x10000
    r3 = 0
    r8 = 36766
    r6 = r2 + 7997
    r7 = 0
    goto L02008dd8
L02008dae:
    ifs (r0 <= -1) goto L02008dca
    r5 = r3 * r6
    r11_r10 = r2 * r6 (u)
    r11 += r5
    r2 = r10 + 0x8000
    r3 = r11 + r4 + c
    r3_r2 >>>= 16
    goto L02008dd6
L02008dca:
    r3_r2 <<= 16
    r2 = r2 | r8
    r3_r2 = r3_r2 / r6 (s)
L02008dd6:
    r7 += 1  ; @add.ri.u5
L02008dd8:
    ifs (r7 < r1) goto L02008dae
    r0 = r2
    {pc, r11, r10, r8-r4} = [sp++]

; preset_application_services_set_levels: 0x02008de2..0x02008e2e, module preset-application-services (set_levels)
.type preset_application_services_set_levels,@function
preset_application_services_set_levels:
    [--sp] = {rets, r7-r4}
    r6 = r1
    r1 = r0
    ifs (r0 >= 12) {  ; @ifs.ge.ri.s12
    r1 = 12
    }
    r4 = -30
    r5 = -30
    ifs (r0 >= -30) {
    r5 = r1
    }
    r0 = r5
    call preset_application_services_decibel_gain
    r7 = L01c1f180
    r0 = r6  #
    [r7+28] = r0
    ifs (r6 >= 12) {  ; @ifs.ge.ri.s12
    r0 = 12
    }
    ifs (r6 >= -30) {
    r4 = r0
    }
    r0 = r4
    call preset_application_services_decibel_gain
    r0 = 1038  #
    [r7+32] = r0
    r1 = L01c26890
    [r1+r0<<2] = r5
    r0 += 1  ; @add.ri.u5
    [r1+r0<<2] = r4
    {pc, r7-r4} = [sp++]

; preset_application_services_select_assets: 0x02008e2e..0x02008e54, module preset-application-services (select_assets)
.type preset_application_services_select_assets,@function
preset_application_services_select_assets:
    r3 = L01c24790
    r2 = L01c1f180
    if (r0 == 0) goto L02008e46
    r0 = b[r3+2] (u)
    if (r0 <= 14) {  ; @if.le.ri.s12
    b[r2+18] = r0
    }
L02008e46:
    if (r1 == 0) goto L02008e52
    r0 = b[r3+3] (u)
    if (r0 <= 7) {  ; @if.le.ri.s12
    b[r2+19] = r0
    }
L02008e52:
    rts
