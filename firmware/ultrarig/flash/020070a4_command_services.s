; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; command_services: 1 function, 0x020070a4..0x020072ea

; command_services_slot_dump: 0x020070a4..0x020072ea, module command-services (slot_dump)
.type command_services_slot_dump,@function
command_services_slot_dump:
    [--sp] = {rets, r14-r4}
    sp += -180
    r4 = r0
    r6 = b[r4+0] (u)
    r0 = 0
    [sp+168] = r0
    d[sp+172] = r1_r0
    [sp+164] = r0
L020070b6:
    r0 = b[r1++=1] (u)
    if (r0 == 32) goto L020070b6
    r0 = r1 + -1
    [sp+176] = r0
    r7 = 15
    if (r6 != 67) {  ; @if.ne.ri.s12
    r7 = 8
    }
    r0 = sp + 176
    r1 = sp + 172
    call command_services_decimal_field
    r10 = L02035810
    if (r0 != 0) goto L02007100
    r5 = [sp+172]
    if (r5 >= r7) goto L02007100
    r0 = [sp+176]
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L02007112
    r0 = sp + 176
    r1 = sp + 164
    call command_services_decimal_field
    if (r0 != 0) goto L02007100
    r0 = [sp+176]
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L020072ac
L02007100:
    r6 = r10 + 779
L02007104:
    r0 = r10 + 1571
    r1 = r4
    r2 = r6
    call link_and_print_print
L0200710e:
    sp += 180
    {pc, r14-r4} = [sp++]
L02007112:
    r8 = 0
L02007114:
    if (r6 != 67) goto L02007148
    r0 = 0xDF000
    r1 = r5
    ifs (r5 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 = r5 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r7 = r1 + r0
    r1 = 1128745812
    r3 = sp + 124
    r2 = 8152
    r0 = r7
    call preset_application_header
    if (r0 != 0) goto L0200716a
    goto L02007290
L02007148:
    r2 = 4056
    if (r5 != 7) {  ; @if.ne.ri.s12
    r2 = 8152
    }
    r1 = sp + 124
    r3 = sp + 168
    r0 = r5
    call preset_application_asset_header
    if (r0 == 0) goto L02007290
    r0 = r5 << 13
    r7 = r0 + 0xEF000
L0200716a:
    r0 = [sp+132]
    [sp+20] = r0
    r1 = 0
    b[sp+163] = r1
    r9 = sp + 124
    if (r8 == 0) goto L02007296
    r6 = r10 + 779  #
    r0 = [sp+128]
    r8 = [sp+164]  ; @ld.w.sp.l
    if (r0 <= r8) goto L02007104
    r0 = r0 - r8
    r9 = 96
    if (r0 > 95) goto L0200719a
    r9 = r0
    if (r0 == 0) goto L02007104
L0200719a:
    r0 = r7 | 0x28
    r0 += r8
    r1 = sp + 26
    r2 = r9
    call storage_control_read
    r6 = r10 + 665
    if (r0 != 0) goto L02007104
    r0 = sp + 26
    r1 = r9
    call preset_storage_checksum
    r2 = r10 + 3726  #
    [sp+12] = r0
    d[sp+4] = r9_r8
    r8 = L01c24358
    r1 = 200
    r0 = r8  #
    [sp] = r5
    r3 = r4
    call L0200691e
    r1 = r9 + -1
    if (r1 > 95) goto L02007104
    ifs (r0 < 0) goto L02007104
    r1 = r9 + 2
    r2 = 3
    r1 = r1 / r2 (u)
    r2 = 1
    r2 <= insert(r1, p:2, l:30)
    r2 += r0  ; @add.rr
    if (r2 > 200) goto L02007104
    r11 = r1 << 2
    r2 = sp + 26
    r3 = r2 + r9
    r13 = 0
    b[r3+1] = r13
    b[r3+0] = r13
    r3 = r0 + r8
    r3 += 3  ; @add.ri.u5
    r12 = 8209
    goto L02007258
L02007214:
    r7 = sp + 26
    r1 = b[++r7=r13] (u)
    r5 = b[r7+1] (u)
    r2 = r1 << 16
    r2 <= insert(r5, p:8, l:8)  #
    r7 = b[r7+2] (u)
    r14 = r7 & 0xFFFFFF3F
    r7 <= insert(r5, p:8, l:8)
    r5 = r10 + r12
    r1 = r1 >> 2
    r1 = b[r1+r5] (u)
    r2 = uextra(r2, p:12, l:6)
    r2 = b[r2+r5] (u)
    r7 = uextra(r7, p:6, l:6)
    r7 = b[r7+r5] (u)
    r5 = b[r14+r5] (u)
    r13 = r13 + 3  #
    b[r3+-3] = r1
    b[r3+-2] = r2
    b[r3+-1] = r7
    b[r3++=4] = r5
L02007258:
    if (r13 < r9) goto L02007214
    r2 = 3
    r2 = r9 / r2 (u)
    r2 = r2 * 0x3
    r2 = r9 - r2
    r0 += r11
    if (r2 == 0) goto L0200727c
    r1 = r0 + r8
    r3 = 61
    b[r1+-1] = r3
    if (r2 == 1) {  ; @if.eq.ri.s12
    b[r1+-2] = r3
    }
L0200727c:
    r2 = 10
    r1 = r0 + 1
    b[r0+r8] = r2
    if (r1 == 0) goto L02007104
    r0 = r8
    call link_and_print_send_line
    goto L0200710e
L02007290:
    r6 = r10 + 3834
    goto L02007104
L02007296:
    if (r6 != 67) goto L020072b2
    r1 = sp + 124
    r2 = sp + 20
    r0 = r5
    call preset_application_asset_resolve
    if (r0 == 0) goto L020072c2
    r6 = r10 + 665
    goto L02007104
L020072ac:
    r8 = 1
    goto L02007114
L020072b2:
    r2 = [sp+168]
    r1 = 48
    if (r2 != 0) goto L020072ba
    r1 = 24
L020072ba:
    r2 = r0  #
    r6 = [sp+136]
    r3 = [sp+128]
    goto L020072ce
L020072c2:
    r2 = [r9+8]
    r0 = [sp+20]
    r6 = [sp+136]
    r3 = [sp+128]
    r1 = 0
L020072ce:
    r7 = sp + 124
    r7 += 16  ; @add.ri.u5
    [sp+16] = r7
    r1 = r4  #
    [sp+12] = r1
    [sp+8] = r6
    r0 = r10 + 7770  #
    [sp+4] = r0
    r2 = r5  #
    [sp] = r2
    call link_and_print_print
    goto L0200710e
