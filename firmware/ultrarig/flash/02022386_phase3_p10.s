; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 3 functions, 0x02022386..0x020224be

; phase3_p10_dev_bulk_read_1: 0x02022386..0x02022396, module phase3-p10 (dev_bulk_read_1)
.type phase3_p10_dev_bulk_read_1,@function
phase3_p10_dev_bulk_read_1:
    [--sp] = {rets, r4}
    r3 = [r0+8]
    r3 = r2  #
    r4 = [r3+12]
    if (r4 == 0) goto L02022394
    r2 = 1
    call r4
L02022394:
    {pc, r4} = [sp++]

; phase3_p10_sdfile_ext_read: 0x02022396..0x020224a4, module phase3-p10 (sdfile_ext_read)
.type phase3_p10_sdfile_ext_read,@function
phase3_p10_sdfile_ext_read:
    [--sp] = {rets, r15-r4}
    r10 = r2
    r9 = r0
    r0 = r1
    call L02022376
    r11 = r0
    r6 = L01c26354
    r8 = r6 + 36
    r0 = r8
    call L02040614  ; @call.xl
    r12 = 0
    goto L02022496
L020223b8:
    r0 = [r6+116]
    r5 = r11 / r0 (u)
    r1 = r5 * r0
    r14 = r11 - r1
    r1 = r0 - r14
    r13 = umin(r1, r10)
    if (r14 != 0) goto L020223e2
    if (r13 != r0) goto L020223e2
    r15 = r12 + r9
    if ((r15 & 0x3) == 0) goto L02022450
L020223e2:
    r0 = [r6+120]
    if (r0 == r5) goto L02022434
    r1 = r6 + 124  #
    r0 = [r6+32]
    r2 = r5
    call phase3_p10_dev_bulk_read_1
    [r6+120] = r5
    r0 = [r6+116]
    r2 = r0 * r5  #
    r1 = [r6+24]
    if (r2 >= r1) goto L02022434
    r4 = 0
    r7 = 0
    goto L0202242e
L0202240c:
    r0 *= r5
    r1 = r7 << 5
    r1 += r0  ; @add.rr
    call phase3_p8_get_system_enc_key
    r2 = [r6+0]
    r3 = r1 - r2
    r1 = r4 + r6
    r1 += 124
    r0 = r0.l (u)
    r2 = 32
    call L0201eec0
    r0 = [r6+116]
    r4 += 32
    r7 += 1  ; @add.ri.u5
L0202242e:
    r1 = r0 >> 5
    if (r7 < r1) goto L0202240c
L02022434:
    r0 = r9 + r12
    r1 = r14 + r6
    r1 += 124
    r2 = r13
    call effect_parameter_support_memmove  ; @call.xl
L02022446:
    r12 += r13
    r11 += r13
    r10 = r10 - r13
    goto L02022496
L02022450:
    r1 = r15  #
    r0 = [r6+32]
    r2 = r5
    call phase3_p10_dev_bulk_read_1
    r0 = [r6+116]
    r2 = r0 * r5  #
    r1 = [r6+24]
    if (r2 >= r1) goto L02022446
    r7 = 0
    r4 = 0
    goto L0202248e
L0202246c:
    r1 = r15 + r7
    r0 *= r5
    r2 = r4 << 5
    r2 += r0  ; @add.rr
    call phase3_p8_get_system_enc_key
    r3 = [r6+0]
    r3 = r2 - r3
    r0 = r0.l (u)
    r2 = 32
    call L0201eec0
    r0 = [r6+116]
    r7 += 32
    r4 += 1  ; @add.ri.u5
L0202248e:
    r1 = r0 >> 5
    if (r4 < r1) goto L0202246c
    goto L02022446
L02022496:
    if (r10 != 0) goto L020223b8
    r0 = r8
    call L0204074c  ; @call.xl
    {pc, r15-r4} = [sp++]

; phase3_p10_sdfile_str_to_upper: 0x020224a4..0x020224be, module phase3-p10 (sdfile_str_to_upper)
.type phase3_p10_sdfile_str_to_upper,@function
phase3_p10_sdfile_str_to_upper:
    goto L020224ba
L020224a6:
    r2 = b[r0+0] (u)
    r3 = r2 + -97
    r3 = r3.b0 (u)
    if (r3 <= 25) {  ; @if.le.ri.s12
    r2 += -32
    b[r0+0] = r2
    }
    r1 += -1
    r0 += 1  ; @add.ri.u5
L020224ba:
    if (r1 != 0) goto L020224a6
    rts
