; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; command_services: 1 function, 0x0200adbe..0x0200af4e

; command_services_calibration_status: 0x0200adbe..0x0200af4e, module command-services (calibration_status)
.type command_services_calibration_status,@function
command_services_calibration_status:
    [--sp] = {rets, r13-r4}
    sp += -200
    r11 = L01c26890
    r1_r0 = d[r11+700]
    r2 = -30
    r5 = r2 - r0
    if (r1 != 0) goto L0200add6
    r5 = -180
L0200add6:
    r0 = 1038
    r8 = [r11+r0<<2]
    r0 = [r11+772]
    r13 = 0
    r6 = 0
    r10 = 0
    ifs (r0 < -599) goto L0200ae0e
    r1 = -10
    r1 *= r8
    r0 = r5 - r0
    r0 += r1  ; @add.rr
    call link_and_print_rounded_fifth
    r3 = r0
    call capture_command_gain_clamp
    r10 = 1
    if (r3 != r0) {
    r10 = 2
    }
    r6 = r0 * 0x5
L0200ae0e:
    r9 = L01c1f180
    r1 = [r9+96]
    r0 = sp + 152
    r2 = 0
    call link_and_print_tenths
    r0 = sp + 128
    r2 = 0
    r1 = r5
    call link_and_print_tenths
    r4 = r11 + 696
    r0 = [r4+0]
    r1 = r0 * 0x5
    r0 = sp + 92
    r2 = 0
    call link_and_print_tenths
    r0 = sp + 116
    r2 = 1
    r1 = r6
    call link_and_print_tenths
    r1 = [r4+4]
    r0 = sp + 140
    r2 = 0
    call link_and_print_tenths
    r0 = [r4+4]
    r1 = [r9+96]
    r0 = r1 - r0
    call link_and_print_rounded_fifth
    call capture_command_gain_clamp
    r1 = r0 * 0x5
    r0 = sp + 104
    r2 = 1
    call link_and_print_tenths
    r0 = sp + 44
    r1 = 0
    r2 = 48
    call effect_enable_memset  ; @call.xl
    r0 = [r11+760]
    r12 = L02035810
    if (r0 == 0) goto L0200aecc
    r7 = r11 + 760
    r4 = sp + 188
    r2 = 0
    r0 = r4  #
    r1 = [r7+4]
    call link_and_print_tenths
    r5 = sp + 176
    r2 = 0
    r0 = r5  #
    r1 = [r7+8]
    call link_and_print_tenths
    r6 = sp + 164
    r2 = 0
    r0 = r6  #
    r1 = [r7+12]
    call link_and_print_tenths
    r2 = r12 + 4156  #
    [sp+4] = r6
    r0 = sp + 44
    r1 = 48
    r3 = r4  #
    [sp] = r5
    call L0200691e
    r13 = [r7+0]
L0200aecc:
    r0 = 748
    r6 = [r11+704]
    r1 = b[r11+r0] (u)
    r0 = sp + 140
    if (r6 == 0) {  ; @if.eq.ri.s12
    r11 = r12
    r0 = r12
    } else {
    r11 = r12 + 415
    }
    r3 = r12 + 1560
    if (r10 != 2) {  ; @if.ne.ri.s12
    r3 = r12
    }
    r4 = r12 + 530
    r5 = sp + 116
    if (r10 == 0) {  ; @if.eq.ri.s12
    r5 = r4
    }
    r7 = sp + 104
    if (r6 == 0) {  ; @if.eq.ri.s12
    r6 = r12
    r7 = r12
    } else {
    r6 = r12 + 671
    }
    r4 = b[r9+9] (u)
    r2 = -1
    if (r4 != 255) {  ; @if.ne.ri.s12
    r2 = r4
    }
    [sp+40] = r2
    r2 = sp + 92
    [sp+36] = r2
    d[sp+28] = r7_r6
    [sp+24] = r3
    [sp+20] = r5
    r2 = sp + 128
    r2 = r13  #
    [sp+16] = r2
    [sp+12] = r0
    [sp+8] = r11  ; @st.w.sp.l
    r0 = sp + 152
    r0 = 9625  #
    [sp+4] = r0
    r0 += r12
    r3 = sp + 44
    [sp] = r8  ; @st.w.sp.l
    call link_and_print_print
    sp += 200
    {pc, r13-r4} = [sp++]
