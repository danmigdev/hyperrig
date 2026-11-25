; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 4 functions, 0x02022910..0x02022a96

; phase3_p10_sdfile_open: 0x02022910..0x02022996, module phase3-p10 (sdfile_open)
.type phase3_p10_sdfile_open,@function
phase3_p10_sdfile_open:
    [--sp] = {rets, r8-r4}
    r6 = r1
    r4 = r0
    if (r6 == 0) goto L02022968
    r0 = 40
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02022990
    r0 = 0
    r1 = r5
    rep 10 {
    [r1++=4] = r0
    }
    r8 = L0203590a  ; "res"
    r1 = r8 + 4  #
    r0 = [r4+8]
    r7 = r0 + 18
    r0 = r7
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0202296e
    r0 = r7
    r1 = r8
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02022978
    r1 = r8 + 1835
    r0 = r7
    call L02028308  ; @call.xl
    r7 = -1
    if (r0 != 0) goto L02022984
    r0 = r5
    r1 = r6
    call L0202286c
    goto L02022980
L02022968:
    r7 = -254
    goto L02022992
L0202296e:
    r0 = r5
    r1 = r6
    call L02022706
    goto L02022980
L02022978:
    r0 = r5
    r1 = r6
    call L02022808
L02022980:
    r7 = r0
    if (r7 == 0) goto L0202298e
L02022984:
    r0 = r5
    call L0203d218  ; @call.xl
    goto L02022992
L0202298e:
    [r4+12] = r5
L02022990:
    r7 = 0
L02022992:
    r0 = r7
    {pc, r8-r4} = [sp++]

; phase3_p10_sdfile_read: 0x02022996..0x020229c0, module phase3-p10 (sdfile_read)
.type phase3_p10_sdfile_read,@function
phase3_p10_sdfile_read:
    [--sp] = {rets, r5, r4}
    r4 = 0
    if (r0 == 0) goto L020229bc
    r5 = [r0+12]
    if (r5 == 0) goto L020229bc
    r0 = [r5+0]
    r3 = [r5+8]
    r3 += r0  #  ; @add.rr.p
    r4 = [r5+12]
    r0 = r4 - r0
    r4 = umin(r0, r2)
    r0 = r1
    r1 = r3
    r2 = r4
    call phase3_p10_sdfile_ext_read
    [r5+0] += r4
L020229bc:
    r0 = r4
    {pc, r5, r4} = [sp++]

; phase3_p10_dev_bulk_write_1: 0x020229c0..0x020229d0, module phase3-p10 (dev_bulk_write_1)
.type phase3_p10_dev_bulk_write_1,@function
phase3_p10_dev_bulk_write_1:
    [--sp] = {rets, r4}
    r3 = [r0+8]
    r3 = r2  #
    r4 = [r3+16]
    if (r4 == 0) goto L020229ce
    r2 = 1
    call r4
L020229ce:
    {pc, r4} = [sp++]

; phase3_p10_sdfile_write: 0x020229d0..0x02022a96, module phase3-p10 (sdfile_write)
.type phase3_p10_sdfile_write,@function
phase3_p10_sdfile_write:
    [--sp] = {rets, r15-r4}
    r4 = r2
    r9 = r1
    r10 = 0
    if (r0 == 0) goto L02022a92
    r11 = [r0+12]
    if (r11 == 0) goto L02022a92
    r5 = [r11+0]
    r0 = [r11+8]
    r6 = [r11+12]
    r0 += r5  ; @add.rr
    call L02022376
    r14 = r0
    r13 = L01c26354
    r8 = r13 + 36
    r0 = r8
    call L02040614  ; @call.xl
    r0 = r6 - r5
    r12 = umin(r0, r4)
    r15 = r12
    goto L02022a7c
L02022a12:
    r0 = [r13+116]
    r4 = r14 / r0 (u)
    r1 = r4 * r0
    r6 = r14 - r1
    r1 = r0 - r6
    r7 = umin(r1, r15)
    if (r6 != 0) goto L02022a38
    if (r7 != r0) goto L02022a38
    r1 = r10 + r9
    if ((r1 & 0x3) == 0) goto L02022a76
L02022a38:
    r0 = [r13+32]
    r5 = r13 + 636
    r1 = r5
    r2 = r4
    call phase3_p10_dev_bulk_read_1
    r1 = r9 + r10
    r0 = r6 + r5
    r2 = r7
    call effect_parameter_support_memmove  ; @call.xl
    r0 = [r13+32]
    r1 = r5
L02022a5c:
    r2 = r4
    call phase3_p10_dev_bulk_write_1
    r0 = [r13+120]
    if (r0 == r4) {
    [r13+120] = 0xFFFFFFFF
    }
    r10 += r7
    r14 += r7
    r15 = r15 - r7
    goto L02022a7c
L02022a76:
    r0 = [r13+32]
    goto L02022a5c
L02022a7c:
    if (r15 != 0) goto L02022a12
    r0 = r8
    call L0204074c  ; @call.xl
    if (r10 == r12) {
    [r11+0] += r12
    r10 = r12
    }
L02022a92:
    r0 = r10
    {pc, r15-r4} = [sp++]
