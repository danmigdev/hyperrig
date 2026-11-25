; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 3 functions, 0x02022ed2..0x02023126

; phase3_p10_sdfile_sel: 0x02022ed2..0x020230ec, module phase3-p10 (sdfile_sel)
.type phase3_p10_sdfile_sel,@function
phase3_p10_sdfile_sel:
    [--sp] = {rets, r13-r4}
    sp += -8
    r10 = r0
    r7 = [r0+80]
    r4 = r3
    r8 = r2
    r6 = r1
    r0 = 40
    call L0203d940  ; @call.xl
    r9 = r0
    if (r0 == 0) goto L02022f18
    r0 = b[r10+4] (u)
    b[r7+1] = r0
    r2 = h[r7+12] (u)
    if (r2 == 0) goto L02023024
    r11 = 1
    if (r0 != 3) goto L02022f1c
    r1 = h[r7+16] (u)
    if (r1 == 0) goto L02022f1c
    r12 = r2  #
    r3 = h[r7+18] (u)
    r1 += r3  ; @add.rr
    if (r1 <= r2) {
    r11 = r3 + 1
    r12 = r1
    }
    goto L02022f1e
L02022f18:
    r5 = -12
    goto L020230e6
L02022f1c:
    r12 = r2
L02022f1e:
    r5 = -22
    if (r6 > 7) goto L02023026
    r3 = 80640
    tbb [r6]
phase3_p10_case_table:
    .byte (L02022f34 - phase3_p10_case_table) / 2, (L02022f42 - phase3_p10_case_table) / 2, (L02022f4c - phase3_p10_case_table) / 2, (L02022f52 - phase3_p10_case_table) / 2, (L02023026 - phase3_p10_case_table) / 2, (L0202304e - phase3_p10_case_table) / 2, (L02022f78 - phase3_p10_case_table) / 2, (L02022fd2 - phase3_p10_case_table) / 2
L02022f34:
    r1 = 0
    r13 = r7 + 10  #
    h[r7+10] = r1
    h[r7+14] = r2
    r4 = 1
    goto L0202305c
L02022f42:
    r0 = 0
    r4 = r2  #
    h[r7+10] = r0
    h[r7+14] = r2
    goto L0202304e
L02022f4c:
    r4 = h[r7+10] (u)
    if (r4 != 0) goto L02022fe0
    goto L02023026
L02022f52:
    r1 = h[r7+10] (u)
    if (r1 == 0) goto L02023026
    if (r0 != 4) goto L02023030
    r3 = 0x1 - r11  #
    r0 = [r3+0]
    r3 += r12  #
    h[r7+14] = r2
    r4 = r0 / r3 (u)
    r3 *= r4
    r0 = r0 - r3
    r0 += r11
    r4 = r1 + 1
    if (r0 != r1) {
    r4 = r0
    }
    goto L02023038
L02022f78:
    r13 = 0
    b[r7+3] = r13
    h[r7+10] = r13
    h[r7+8] = r13
    r0 = r7 + 64  #
    [r7+20] = r4
    [r7+16] = r13
    call phase3_p10_sdf_opendir
    r3 = b[r7+2] (u)
    r2 = [r7+28]
    r1 = b[r7+0] (u)
    [sp+4] = r7
    r0 = L0202341c
    r0 = r7  #
    [sp] = r0
    call L02022d14
    if (r0 != 1) goto L02023026
    r0 = r9
    [r0++=4] = r13
    r1 = r7 + 32
    rep 8 {
    r2 = [r1++=4]
    [r0++=4] = r2
    }
    r4 = h[r7+8] (u)
    h[r7+10] = r4
    r0 = h[r7+16] (u)
    if (r0 != 0) goto L0202304e
    r0 = r7
    call L02022e8a
    h[r7+16] = r0
    r4 = h[r7+10] (u)
    goto L0202304e
L02022fd2:
    r13 = r7
    r4 = h[++r13=10] (u)
    if (r4 == 0) goto L02023026
    r1 = r4
    if (r0 == 2) goto L0202305c
L02022fe0:
    if (r0 != 4) goto L02023002
    r2 = 0x1 - r11  #
    r1 = [r3+0]
    r2 += r12
    r3 = r1 / r2 (u)
    r2 *= r3
    r1 = r1 - r2
    r2 = r1 + r11
    r1 = r4 + 1
    if (r2 != r4) {
    r1 = r2
    }
    goto L02023004
L02023002:
    r1 = r4 + 1
L02023004:
    r2 = h[r7+14] (u)
    ifs (r1 <= r2) goto L02023014
    if (r0 == 0) goto L02023024
    r1 = r11
    if (r0 != 3) {  ; @if.ne.ri.s12
    r1 = 1
    }
L02023014:
    r4 = r11
    ifs (r1 > r12) goto L02023052
    r4 = r12
    ifs (r1 >= r11) {
    r4 = r1
    }
    goto L0202304e
L02023024:
    r5 = -2
L02023026:
    r0 = r9
    call L0203d218  ; @call.xl
    goto L020230e6
L02023030:
    r4 = r1 + -1  #
    h[r7+14] = r2
    if (r0 == 0) goto L0202304e
L02023038:
    ifs (r4 <= r12) goto L02023044
    r13 = r7 + 10
    r4 = r11
    goto L0202305c
L02023044:
    r0 = r12
    ifs (r4 >= r11) {
    r0 = r4
    }
    r4 = r0
L0202304e:
    r5 = -2
    if (r4 == 0) goto L02023026
L02023052:
    if (r6 == 6) goto L020230da
    r13 = r7
    r1 = h[++r13=10] (u)
L0202305c:
    ifs (r4 >= r11) {
    r11 = smin(r4, r12)
    }
    if (r1 != r11) goto L0202307a
    r0 = 0
    r1 = r9
    r0 = r7 + 32  #
    [r1++=4] = r0
    rep 8 {
    r2 = [r0++=4]
    [r1++=4] = r2
    }
    goto L020230da
L0202307a:
    if (r1 == 0) goto L02023084
    ifs (r1 >= r11) goto L02023084
    h[r7+8] = r1
    goto L02023096
L02023084:
    r0 = 0
    b[r7+3] = r0
    h[r7+8] = r0
    h[r7+16] = r0
    r0 = r7 + 64  #
    h[r7+18] = r0
    call phase3_p10_sdf_opendir
L02023096:
    h[r13+0] = r11
    r3 = b[r7+2] (u)
    r2 = [r7+28]
    r1 = b[r7+0] (u)
    [sp+4] = r7
    r0 = L0202343c
    r0 = r7  #
    [sp] = r0
    call L02022d14
    r5 = -254
    if (r0 != 1) goto L02023026
    r0 = 0
    r1 = r9
    r0 = r7 + 32  #
    [r1++=4] = r0
    rep 8 {
    r2 = [r0++=4]
    [r1++=4] = r2
    }
    r0 = h[r7+8] (u)
    h[r13+0] = r0
    r0 = h[r7+16] (u)
    if (r0 != 0) goto L020230da
    r0 = r7
    call L02022e8a
    h[r7+16] = r0
L020230da:
    r0 = h[r7+10] (u)
    h[r10+70] = r0
    [r8+12] = r9
    r5 = 0
L020230e6:
    r0 = r5
    sp += 8
    {pc, r13-r4} = [sp++]

; phase3_p10_sdfile_get_attr: 0x020230ec..0x02023102, module phase3-p10 (sdfile_get_attr)
.type phase3_p10_sdfile_get_attr,@function
phase3_p10_sdfile_get_attr:
    r0 = [r0+12]
    r0 = b[r0+16] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 3) {  ; @if.eq.ri.s12
    [r1+0] |= 0x10
    }
    r0 = 0
    rts

; phase3_p10_sdfile_get_attrs: 0x02023102..0x02023126, module phase3-p10 (sdfile_get_attrs)
.type phase3_p10_sdfile_get_attrs,@function
phase3_p10_sdfile_get_attrs:
    if (r0 == 0) goto L02023122
    r0 = [r0+12]
    if (r0 == 0) goto L02023122
    r2 = b[r0+16] (u)
    r2 = r2 & 0xFFFFFF0F
    if (r2 == 3) {  ; @if.eq.ri.s12
    r2 = b[r1+0] (u)
    r2 |= 16
    b[r1+0] = r2
    }
    r2 = [r0+12]
    [r1+4] = r2
    r0 = [r0+8]
    [r1+8] = r0
L02023122:
    r0 = 0
    rts
