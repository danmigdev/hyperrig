; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020543a6..0x020543e6: system layer code (not reversed), as instructions
L020543a6:
    [--sp] = {rets, r5, r4}
    r5 = r0.l (u)
    r0 = r5
    call L0205288c
    r0 = r5
    call L020522d0
    r4 = r0
    if (r4 == 0) goto L020543da
    r1 = 19
    r0 = r5
    call L0204a5da  ; @call.xl
    r2 = b[r4+46] (u)
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    r3 = 15
    r3 <= insert(r2, p:8, l:8)
    r2 = r4
    call L020525f8
L020543da:
    {pc, r5, r4} = [sp++]
L020543dc:
    [--sp] = rets
    r0 = r0.l (u)
    call L020537f6
    pc = [sp++]

; 0x020543e6..0x020543fe: data
    .fill ((6 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L020543e6:
    .byte 0x06,0x01,0x00,0xff,0xff,0x00,0x28,0xd0,0x00,0x2d,0x12,0x1e,0x4b,0x0f,0xa4,0x99
    .byte 0x4e,0xce,0xb5,0x31,0xf4,0x05,0x79,0x00

; 0x020543fe..0x02055754: system layer code (not reversed), as instructions
L020543fe:
    [--sp] = rets
    call L0204cbd4  ; @call.xl
    r1 = r0 + 120
    if (r0 == 0) goto L0205440e
    r0 = r1
L0205440e:
    pc = [sp++]
L02054410:
    [--sp] = {rets, r4}
    r4 = 0
    if (r0 == 0) goto L0205442c
    call L020543fe
    if (r0 == 0) goto L0205442c
    r1 = 579
    r0 = b[r0+r1] (u)
    r4 = uextra(r0, p:2, l:3)
    if (r4 >= 3) {  ; @if.ge.ri.s12
    r4 = 0
    }
L0205442c:
    r0 = r4.b0 (u)
    {pc, r4} = [sp++]
L02054430:
    r0 = L01c21c58
    r1 = 0
    rep 16 {
    [r0++=4] = r1
    }
    rts
L0205443e:
    [--sp] = {rets, r4}
    r3 = L01c21c58
    r4 = L020546d2
    r0 = r3 + 36  #
    [r3+40] = r4
    call L0204d5ba  ; @call.xl
    r0 = r3 + 44  #
    [r3+48] = r4
    call L020537a2  ; @call.xl
    r0 = L020548ea
    [r3+4] = r0
    r0 = L0205460a
    r1 = 4
    call L0204d6e8  ; @call.xl
    r0 = L02035224
    [r3+16] = r0
    r0 = att_read_att_read
    [r3+20] = r0
    r0 = boundary_hooks_att_write
    [r3+24] = r0
    {pc, r4} = [sp++]
L02054494:
    r0 = L01c21c58
    r1 = boundary_hooks_packet_handler
    [r0+52] = r1
    rts
L020544a4:
    [--sp] = rets
    call L0204cd12  ; @call.xl
    pc = [sp++]
L020544ae:
    [--sp] = rets
    r0 = L01c21c58
    r1 = b[r0+8] (u)
    r1 |= 1
    b[r0+8] = r1
    r0 = 4
    call L0204cf76  ; @call.xl
    pc = [sp++]
L020544c6:
    [--sp] = {rets, r4}
    r4 = r1
    if (r0 == 0) goto L020544f0
    call L020543fe
    if (r0 == 0) goto L020544f0
    r1 = r0 + 576
    r2 = b[r1+3] (u)
    r2 = r2 & 0xFFFFFFC3
    r3 = r4 << 2
    r3 = r3 & 0x1C
    r2 |= r3
    b[r1+3] = r2
    r2 = [r1+4]
    if (r2 == 0) goto L020544f0
    r0 = h[r0+44] (u)
    r1 = r4
    call r2
L020544f0:
    {pc, r4} = [sp++]
L020544f2:
    [--sp] = rets
    r0 = L01c21c58
    r1 = b[r0+8] (u)
    r1 |= 2
    b[r0+8] = r1
    r0 = 4
    call L0204cf76  ; @call.xl
    pc = [sp++]
L0205450a:
    [--sp] = rets
    call L020544f2
    pc = [sp++]
L02054510:
    [--sp] = rets
    call L0204cd12  ; @call.xl
    pc = [sp++]
L0205451a:
    [--sp] = {rets, r8-r4}
    r8 = r3
    r5 = r2
    r6 = r1
    r4 = r0
    call L020543fe
    r7 = r0
    if (r7 == 0) goto L02054568
    r0 = r4
    call L02054510
    if (r0 == 0) goto L0205456c
    call L0205144e  ; @call.xl
    r0 = L01c21714
    r1 = 27
    b[r0+16] = r1
    r0 = r7 + 44
    r1 = r6
    r2 = r5
    r3 = r8
    call L02027264  ; @call.xl
    r2 = h[r7+44] (u)
    r3 = r0
    r1 = 4
    r0 = r2
    r2 = r3
    call L0204ce4e  ; @call.xl
    {pc, r8-r4} = [sp++]
L02054568:
    r0 = 2
    {pc, r8-r4} = [sp++]
L0205456c:
    r0 = 87
    {pc, r8-r4} = [sp++]
L02054570:
    [--sp] = {rets, r8-r4}
    r8 = r3
    r5 = r2
    r6 = r1
    r4 = r0
    call L020543fe
    r7 = r0
    if (r7 == 0) goto L020545ea
    r1 = [r7+20]
    r0 = 144
    if (r1 != 0) goto L020545e8
    r0 = r4
    call L02054510
    if (r0 == 0) goto L020545ee
    [r7+20] = r6
    r0 = 0
    r1 = 0
    d[r7+24] = r1_r0
    r0 = 30000
    [r7+32] = r0
    r0 = L02054ba2
    [r7+36] = r0
    [r7+40] = r7
    r0 = r7 + 24
    r1 = 130
    call L0204cffa  ; @call.xl
    call L0205144e  ; @call.xl
    r0 = L01c21714
    r1 = 29
    b[r0+16] = r1
    r0 = r7 + 44
    r1 = r6
    r2 = r5
    r3 = r8
    call L02027264  ; @call.xl
    r2 = h[r7+44] (u)
    r3 = r0
    r1 = 4
    r0 = r2
    r2 = r3
    call L0204ce4e  ; @call.xl
    r0 = 0
L020545e8:
    {pc, r8-r4} = [sp++]
L020545ea:
    r0 = 2
    {pc, r8-r4} = [sp++]
L020545ee:
    r0 = 87
    {pc, r8-r4} = [sp++]
L020545f2:
    [--sp] = rets
    r0 = L01c21c58
    r1 = b[r0+60] (u)
    r1 |= 1
    b[r0+60] = r1
    call L020544f2
    pc = [sp++]
L0205460a:
    [--sp] = {rets, r9-r4}
    r4 = r3
    r5 = r2
    r6 = r1
    r9 = L01c21c58
    if (r0 == 4) goto L02054634
    if (r0 != 8) goto L020546b2
    r0 = b[r5+0] (u)
    if ((r0 & 1) != 0) goto L020546a0
    r7 = [r9+4]
    if (r7 != 0) goto L020546ac
    r7 = [r9+0]
    if (r7 != 0) goto L020546ac
    {pc, r9-r4} = [sp++]
L02054634:
    r0 = b[r5+0] (u)
    if (r0 != 120) goto L020546b2
    r7 = b[r9+8] (u)
    if ((r7 & 4) != 0) goto L020546b2
    call L0204cee2  ; @call.xl
    if (r0 == 0) goto L020546b2
    r0 = r7 | 0x4
    b[r9+8] = r0
    if ((r7 & 2) == 0) goto L02054674
    r7 = [r9+4]
    if (r7 == 0) goto L02054674
    r0 &= 4294967293
    b[r9+8] = r0
    r0 = 4
    r1 = r6
    r2 = r5
    r3 = r4
    call r7
    call L0204cee2  ; @call.xl
    if (r0 == 0) goto L02054694
L02054674:
    r8 = [r9+0]
    if (r8 == 0) goto L02054694
    r0 = b[r9+8] (u)
    if ((r0 & 1) == 0) goto L02054694
    r0 &= 4294967294
    b[r9+8] = r0
    r0 = 4
    r1 = r6
    r2 = r5
    r3 = r4
    call r8
L02054694:
    r0 = b[r9+8] (u)
    r0 &= 4294967291
    b[r9+8] = r0
    {pc, r9-r4} = [sp++]
L020546a0:
    r7 = [r9+0]
    if (r7 != 0) goto L020546ac
    r7 = [r9+4]
    if (r7 == 0) goto L020546b2
L020546ac:
    r0 = 8
    call r7
    {pc, r9-r4} = [sp++]
L020546b2:
    {pc, r9-r4} = [sp++]
L020546b4:
    [--sp] = rets
    r0 = [r0+28]
    call L0204cfee  ; @call.xl
    pc = [sp++]
L020546c0:
    [--sp] = rets
    r1 = [r0+0]
    if (r1 == 1) {  ; @if.eq.ri.s12
    [r0+0] = 0x3
    call L020544f2
    }
    pc = [sp++]
L020546d2:
    [--sp] = {rets, r6-r4}
    sp += -4
    r4 = r2
    if (r0 != 4) goto L0205485c
    r0 = b[r4+0] (u)
    r1 = r0 + -216
    if (r1 <= 4) goto L02054784
    if (r0 == 5) goto L02054836
    if (r0 == 8) goto L020547a2
    if (r0 == 48) goto L020547a2
    if (r0 != 62) goto L0205485c
    r0 = b[r4+2] (u)
    if (r0 != 1) goto L0205485c
    r1 = 4
    r0 = r4
    call L0204cb74  ; @call.xl
    r6 = r0
    call L020543fe
    r5 = r0
    if (r5 == 0) goto L0205485c
    r0 = b[r4+7] (u)
    b[r5+4] = r0
    r0 = r4 + 8
    r4 = r5 + 5
    r1 = r4
    call L0204cc5a  ; @call.xl
    r3 = r5 + 44
    h[r3+0] = r6
    r0 = L01c21c58
    r0 = [r0+16]
    [r5+56] = r0
    r2 = 0
    [r5+0] = r2
    r0 = 23
    h[r3+2] = r0
    call L0205143c  ; @call.xl
    if (r0 >= 517) {
    r0 = 517
    }
    r6 = r5 + 576  #
    h[r3+4] = r0
    b[r3+6] = r2
    b[r3+7] = r2
    b[r3+8] = r2
    [r5+12] = 0xFFFFFFFF
    r0 = b[r6+3] (u)
    r0 &= 4294967294
    r0 = r4  #
    b[r6+3] = r0
    b[sp+3] = r2
    r1 = b[r5+4] (u)
    r2 = sp + 3
    call L02051f12  ; @call.xl
    r0 = b[r6+3] (u)
    r1 = b[sp+3] (u)
    r0 = r0 & 0xFFFFFFE3
    r1 = r1 << 2
    r1 = r1 & 0x1C
    r0 |= r1
    b[r6+3] = r0
    goto L0205485c
L02054784:
    tbb [r1]
L02054786:
    .byte (L0205478c - L02054786) / 2, (L020547d0 - L02054786) / 2, (L020547f0 - L02054786) / 2, (L0205485c - L02054786) / 2, (L0205481a - L02054786) / 2
    .byte 0x00  ; alignment
L0205478c:
    r1 = 2
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020543fe
    if (r0 == 0) goto L0205485c
    [r0+16] = 0x1
    goto L0205485c
L020547a2:
    r1 = 3
    r0 = r4
    call L0204cb74  ; @call.xl
    r4 = r0
    call L020543fe
    r5 = r0
    if (r5 == 0) goto L0205485c
    r0 = r4
    call L02053944  ; @call.xl
    b[r5+50] = r0
    r0 = r4
    call L0205395e  ; @call.xl
    b[r5+51] = r0
    goto L0205485c
L020547d0:
    r1 = 2
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020543fe
    if (r0 == 0) goto L0205485c
    r2 = 0xFFFFFFFF  ; @li.modimm
    r3 = 0
    d[r0+12] = r3_r2
    call L020546c0
    goto L0205485c
L020547f0:
    r1 = 2
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020543fe
    r2 = r0
    if (r2 == 0) goto L0205485c
    [r2+16] = 0x0
    r1 = 18
    r0 = r4
    call L0204cb74  ; @call.xl
    r0 = r2  #
    [r2+12] = r0
    call L020546c0
    goto L0205485c
L0205481a:
    r1 = 2
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020543fe
    if (r0 == 0) goto L0205485c
    r1 = b[r4+11] (u)
    b[r0+52] = r1
    call L020544f2
    goto L0205485c
L02054836:
    r1 = 3
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020543fe
    r4 = r0
    if (r4 == 0) goto L0205485c
    r0 = [r4+20]
    if (r0 == 0) goto L02054852
    r0 = r4
    call L020546b4
L02054852:
    r0 = 0
    h[r4+44] = r0
    [r4+20] = r0
    [r4+0] = r0
L0205485c:
    sp += 4
    {pc, r6-r4} = [sp++]
L02054860:
    [--sp] = {rets, r5, r4}
    sp += -8
    r5 = L01c21c58
    r3_r2 = r1_r0  #
    r4 = [r5+52]
    if (r4 == 0) goto L0205489e
    r0 = 181
    b[sp+2] = r0
    r0 = 4
    b[sp+3] = r0
    r4 = sp + 2
    r1 = 2
    r0 = r4
    call L0204cc4a  ; @call.xl
    r1 = 4
    r2 = r3
    call L0204cc4a  ; @call.xl
    r2 = r4  #
    r5 = [r5+52]
    r0 = 4
    r1 = 0
    r3 = 6
    call r5
L0205489e:
    sp += 8
    {pc, r5, r4} = [sp++]
L020548a2:
    [--sp] = {rets, r5, r4}
    sp += -8
    r5 = L01c21c58
    r3 = r2  #
    r4 = [r5+52]
    r2 = r1
    if (r4 == 0) goto L020548e6
    r1 = 182
    b[sp+1] = r1
    r1 = 5
    b[sp+2] = r1
    b[sp+3] = r0
    r4 = sp + 1
    r1 = 3
    r0 = r4
    call L0204cc4a  ; @call.xl
    r1 = 5
    r2 = r3
    call L0204cc4a  ; @call.xl
    r2 = r4  #
    r5 = [r5+52]
    r0 = 4
    r1 = 0
    r3 = 7
    call r5
L020548e6:
    sp += 8
    {pc, r5, r4} = [sp++]
L020548ea:
    [--sp] = {rets, r14-r4}
    sp += -16
    r5_r4 = r3_r2
    r12 = L01c21c58
    if (r0 == 8) goto L02054ae8
    if (r0 != 4) goto L02054b9e
    r0 = b[r4+0] (u)
    if (r0 != 120) goto L02054b9e
    r0 = sp + 0
    call L0204cc3e  ; @call.xl
    r8 = L01c21714
    r9 = 0
    r10 = L020543e6
    r11 = 2
    goto L02054a98
L02054924:
    r0 = sp + 0
    call L0204cbb4  ; @call.xl
    r4 = r0
    r5 = r4 + 120
    r7 = r4 + 696  #
    r0 = [r5+56]
    [r12+12] = r0
    r0 = b[r7+3] (u)
    if ((r0 & 1) != 0) goto L02054a98
    r13 = r4 + 164  #
    r1 = [r5+0]
    if (r1 != 3) goto L020549ae
    r6 = r5 + 44
    call L0205144e  ; @call.xl
    r2 = h[r4+180] (u)
    r14 = r5 + 46
    r4 = r14 + 16
    r3 = r8 + 16
    r0 = r6
    r1 = r4
    call phase3_p1_att_wrapper  ; @call.xl
    r6 = r0
    if (r6 < 4) goto L020549ee
    r0 = b[r8+16] (u)
    if (r0 != 1) goto L02054a14
    r0 = b[r8+20] (u)
    if (r0 != 8) goto L02054a14
    r0 = b[r14+5] (u)
    if (r0 == 0) goto L02054a14
    r0 = h[r13+0] (u)
    call L02053976  ; @call.xl
    if (r0 == 1) goto L02054a92
    if (r0 != 0) goto L02054a14
    call L0205142a  ; @call.xl
    r0 = h[r13+0] (u)
    call L020537f6  ; @call.xl
    goto L02054a98
L020549ae:
    if ((r0 & 32) != 0) goto L02054a98
    if ((r0 & 2) != 0) goto L02054a50
    r0 = r0 & 0xFFFFFF1C
    if (r0 != 20) goto L02054a98
    call L0205144e  ; @call.xl
    if (r0 == 0) goto L02054a8c
    r0 = r8 + 16
    r1 = r10
    rep 23 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = h[r13+0] (u)
    r1 = 4
    r2 = 23
    call L0204ce4e  ; @call.xl
    if (r0 != 0) goto L02054a7a
    r0 = b[r7+3] (u)
    r0 = r0 & 0xFFFFFFC3
    r0 = r0 | 0x38
    goto L02054a8a
L020549ee:
    [r5+0] = r9
    if (r6 != 0) goto L02054a18
    call L0205142a  ; @call.xl
    r0 = b[r4+0] (u)
    if (r0 != 3) goto L02054a98
    r0 = b[r7+3] (u)
    r0 &= 4294967263
    b[r7+3] = r0
    r1 = h[r14+0] (u)
    r0 = h[r13+0] (u)
    call L02054860
    goto L02054a98
L02054a14:
    [r5+0] = r9
L02054a18:
    r0 = h[r13+0] (u)
    r1 = 4
    r2 = r6
    call L0204ce4e  ; @call.xl
    r0 = b[r8+16] (u)
    if (r0 == 3) {  ; @if.eq.ri.s12
    r1 = h[r14+0] (u)
    r0 = h[r13+0] (u)
    call L02054860
    }
    r0 = b[r12+60] (u)
    if ((r0 & 1) != 0) goto L02054ae2
    r0 = [r12+56]
    call L0204cc62  ; @call.xl
    if (r0 != 0) goto L02054a98
    goto L02054ae2
L02054a50:
    call L0205144e  ; @call.xl
    if (r0 == 0) goto L02054a8c
    r0 = r8
    b[++r0=16] = r11
    r2 = h[r4+168] (u)
    r1 = 1
    call L0204cc4a  ; @call.xl
    r0 = h[r13+0] (u)
    r1 = 4
    r2 = 3
    call L0204ce4e  ; @call.xl
    if (r0 == 0) goto L02054a82
L02054a7a:
    call L0205142a  ; @call.xl
    goto L02054a8c
L02054a82:
    r0 = b[r7+3] (u)
    r0 = r0 & 0xFFFFFFDD
    r0 |= 32
L02054a8a:
    b[r7+3] = r0
L02054a8c:
    call L020544f2
    goto L02054a98
L02054a92:
    call L0205142a  ; @call.xl
L02054a98:
    r0 = sp + 0
    call L0204cb98  ; @call.xl
    if (r0 != 0) goto L02054924
L02054aa4:
    r3 = [r12+56]
    r0 = r3
    call L0204cc62  ; @call.xl
    if (r0 != 0) goto L02054b54
    r0 = r12 + 56  #
    r4 = h[r3+8] (u)
    r1 = r3
    call L0204c724  ; @call.xl
    r0 = [r3+8]
    r1 = [r3+4]
    call r1
    r0 = r4
    call L02054510
    if (r0 != 0) goto L02054aa4
    r0 = [r12+56]
    call L0204cc62  ; @call.xl
    if (r0 == 0) goto L02054ae2
    r0 = b[r12+60] (u)
    if ((r0 & 1) == 0) goto L02054b9e
L02054ae2:
    call L020544f2
    goto L02054b9e
L02054ae8:
    r0 = r1
    call L020543fe
    r6 = r0
    if (r6 == 0) goto L02054b9e
    r7 = r6 + 44  #
    r0 = [r6+56]
    [r12+12] = r0
    r0 = b[r4+0] (u)
    if (r0 == 82) goto L02054b44
    if (r0 != 30) goto L02054b1e
    r1 = [r6+20]
    if (r1 == 0) goto L02054b1e
    r0 = r6
    call L020546b4
    r2 = h[r6+20] (u)
    r0 = 0
    [r6+20] = r0
    r1 = h[r7+0] (u)
    call L020548a2
    goto L02054b9e
L02054b1e:
    if (r5 > 517) goto L02054b9e
    r1 = [r6+0]
    if (r1 != 0) goto L02054b9e
    r1 = 579
    r1 = b[r6+r1] (u)
    r1 = r1 & 0xFFFFFF1C
    if (r1 != 24) goto L02054b7a
    if (r0 == 1) goto L02054b96
    if (r0 != 7) goto L02054b7a
    r0 = h[r7+0] (u)
    r1 = 2
    goto L02054b9a
L02054b44:
    r3 = 0
    r0 = r7
    r1 = r4
    r2 = r5
    call phase3_p1_att_wrapper  ; @call.xl
    goto L02054b9e
L02054b54:
    r0 = b[r12+60] (u)
    if ((r0 & 1) == 0) goto L02054b9e
    r0 &= 4294967294
    b[r12+60] = r0
    r4 = [r12+52]
    if (r4 == 0) goto L02054b9e
    r0 = 183
    h[sp+14] = r0
    r2 = sp + 14
    r0 = 4
    r1 = 0
    r3 = 2
    call r4
    goto L02054b9e
L02054b7a:
    [r6+0] = 0x1
    r0 = r6 + 62  #
    h[r7+16] = r5
    r1 = r4
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r6
    call L020546c0
    goto L02054b9e
L02054b96:
    r0 = h[r7+0] (u)
    r1 = 1
L02054b9a:
    call L020544c6
L02054b9e:
    sp += 16
    {pc, r14-r4} = [sp++]
L02054ba2:
    [--sp] = rets
    r0 = [r0+16]
    if (r0 == 0) goto L02054bb4
    r1 = h[r0+44] (u)
    r2 = h[r0+20] (u)
    r0 = 145
    call L020548a2
L02054bb4:
    pc = [sp++]
L02054bb6:
    r1 = r0
    r0 = L01c21c98
L02054bbe:
    r0 = [r0+0]
    if (r0 == 0) goto L02054bca
    r2 = h[r0+12] (u)
    if (r2 != r1) goto L02054bbe
    rts
L02054bca:
    r0 = 0
    rts
L02054bce:
    [--sp] = rets
    r3 = r0
    call L02054bb6
    r1 = r0
    if (r1 == 0) goto L02054bdc
L02054bd8:
    r0 = r1
    pc = [sp++]
L02054bdc:
    call L02051418  ; @call.xl
    r1 = r0
    if (r1 == 0) goto L02054c10
    r0 = 0
    r2 = r1
    rep 32 {
    [r2++=4] = r0
    }
    h[r1+12] = r3
    r2 = 23
    h[r1+22] = r2
    [r1+24] = r0
    [r1+4] = r0
    r0 = L01c21c98
    call L0204ec4a  ; @call.xl
    r0 = b[r0+20] (u)
    if (r0 == 0) goto L02054bd8
    [r1+24] = 0x2
    goto L02054bd8
L02054c10:
    r1 = 0
    goto L02054bd8
L02054c14:
    [--sp] = rets
    r2 = r0
    r3 = r2.l (u)
    call L0205143c  ; @call.xl
    if (r0 >= r3) {
    r0 = r2
    }
    r0 = r0.l (u)
    pc = [sp++]
L02054c2a:
    [--sp] = rets
    r0 = [r0+100]
    call L0204cfee  ; @call.xl
    pc = [sp++]
L02054c38:
    [--sp] = rets
    [r0+4] = 0x0
    call L02054c2a
    pc = [sp++]
L02054c42:
    [--sp] = {rets, r4}
    sp += -12
    r3 = r0
    r0 = 160
    b[sp+2] = r0
    r0 = 7
    b[sp+3] = r0
    r4 = r1  #
    r2 = h[r3+12] (u)
    r0 = sp + 2
    r1 = 2
    call L0204cc4a  ; @call.xl
    b[sp+6] = r4
    r2 = h[r3+58] (u)
    r1 = 5
    call L0204cc4a  ; @call.xl
    r2 = h[r3+60] (u)
    r1 = 7
    call L0204cc4a  ; @call.xl
    r4 = [r3+8]
    if (r4 == 0) goto L02054c8c
    r2 = sp + 2
    r0 = 4
    r1 = 0
    r3 = 10
    call r4
L02054c8c:
    sp += 12
    {pc, r4} = [sp++]
L02054c90:
    [--sp] = {rets, r7-r4}
    r5_r4 = r3_r2
    r6 = r1
    r7 = r0
    call L0205144e  ; @call.xl
    r0 = L01c21714
    b[++r0=16] = r7
    r1 = 1
    r2 = r5
    call L0204cc4a  ; @call.xl
    r2 = [sp+20]
    r1 = 3
    call L0204cc4a  ; @call.xl
    r1 = 5
    r2 = r6
    call L0204cc4a  ; @call.xl
    r1 = 4
    r2 = 7
    r0 = r4
    call L0204ce4e  ; @call.xl
    {pc, r7-r4} = [sp++]
L02054cd4:
    [--sp] = {rets, r7-r4}
    r5 = r3
    r6 = r2
    r7 = r1
    r4 = r0
    call L0205144e  ; @call.xl
    r3 = L01c21714
    r0 = 6
    b[r3+16] = r0
    r0 = r3 + 16
    r1 = 1
    r2 = r7
    call L0204cc4a  ; @call.xl
    r1 = 3
    r2 = r6
    call L0204cc4a  ; @call.xl
    r1 = 5
    r2 = 10240
    call L0204cc4a  ; @call.xl
    r1 = r5  #
    r6 = [sp+20]
    r0 = r3 + 23
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r6 + 7
    r2 = r0.l (u)
    r1 = 4
    r0 = r4
    call L0204ce4e  ; @call.xl
    {pc, r7-r4} = [sp++]
L02054d30:
    [--sp] = {rets, r7-r4}
    r5 = r3
    r6 = r2
    r4 = r1
    r7 = r0
    call L0205144e  ; @call.xl
    r3 = L01c21714
    r0 = 8
    b[r3+16] = r0
    r0 = r3 + 16
    r1 = 1
    r2 = r6
    call L0204cc4a  ; @call.xl
    r1 = 3
    r2 = r5
    call L0204cc4a  ; @call.xl
    r1 = r3 + 21
    r0 = r7
    call L0204cc2a  ; @call.xl
    r1 = 4
    r2 = 21
    r0 = r4
    call L0204ce4e  ; @call.xl
    {pc, r7-r4} = [sp++]
L02054d7a:
    [--sp] = {rets, r6-r4}
    sp += -4
    r2 = b[r0+82] (u)
    r1 = r0 + 46
    if (r2 == 0) goto L02054d9c
    r4 = h[r1+2] (u)
    r3 = h[r1+0] (u)
    r1 = h[r0+28] (u)
    r2 = h[r0+12] (u)
    if (r1 == 0) goto L02054de2
    r0 = 8
    [sp] = r4
    call L02054c90  ; @call.l
    goto L02054dec
L02054d9c:
    r4 = h[r0+12] (u)
    r5 = h[r1+2] (u)
    r6 = h[r1+0] (u)
    call L0205144e  ; @call.xl
    r0 = L01c21714
    r1 = 8
    b[++r0=16] = r1
    r1 = 1
    r2 = r6
    call L0204cd32  ; @call.xl
    r1 = 3
    r2 = r5
    call L0204cd32  ; @call.xl
    r1 = 5
    r2 = 10243
    call L0204cd32  ; @call.xl
    r1 = 4
    r2 = 7
    r0 = r4
    call L0204ce4e  ; @call.xl
    goto L02054dec
L02054de2:
    r0 += 30  ; @add.ri.u5
    r1 = r2
    r2 = r3
    r3 = r4
    call L02054d30
L02054dec:
    sp += 4
    {pc, r6-r4} = [sp++]
L02054df0:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    call L0205144e  ; @call.xl
    r0 = L01c21714
    r1 = 10
    b[++r0=16] = r1
    r1 = 1
    r2 = r4
    call L0204cc4a  ; @call.xl
    r1 = 4
    r2 = 3
    r0 = r5
    call L0204ce4e  ; @call.xl
    {pc, r5, r4} = [sp++]
L02054e20:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r5 = r1
    r6 = r0
    call L0205144e  ; @call.xl
    r0 = L01c21714
    r1 = 12
    b[++r0=16] = r1
    r2 = r5.l (u)
    r1 = 1
    call L0204cc4a  ; @call.xl
    r2 = r4.l (u)
    r1 = 3
    call L0204cc4a  ; @call.xl
    r0 = r6.l (u)
    r1 = 4
    r2 = 5
    call L0204ce4e  ; @call.xl
    {pc, r6-r4} = [sp++]
L02054e5c:
    [--sp] = {rets, r7-r4}
    r4 = r3
    r5 = r2
    r6 = r1
    r7 = r0
    call L0205144e  ; @call.xl
    r3 = L01c21714
    b[r3+16] = r7
    r0 = r3 + 16
    r1 = 1
    r2 = r5
    call L0204cc4a  ; @call.xl
    r2 = r4  #
    r1 = [sp+20]
    r0 = r3 + 19
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r4 + 3
    r2 = r0.l (u)
    r1 = 4
    r0 = r6
    call L0204ce4e  ; @call.xl
    {pc, r7-r4} = [sp++]
L02054e9e:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r0 + 56  #
    r1 = h[r0+12] (u)
    r3 = h[r4+6] (u)
    r2 = h[r4+2] (u)
    r4 = [r4+8]
    r0 = 18
    [sp] = r4
    call L02054e5c
    sp += 4
    {pc, r4} = [sp++]
L02054eb8:
    [--sp] = {rets, r8-r4}
    r4 = r0 + 56
    r5 = h[r4+4] (u)
    r6 = h[r4+2] (u)
    r8 = h[r0+12] (u)
    r0 = h[r0+22] (u)
    call L02054c14
    r1 = h[r4+6] (u)
    r7 = 0
    if (r1 <= r5) goto L02054ee2
    r0 += -5
    r7 = r1 - r5
    r1 = r7.l (u)
    r2 = r0.l (u)
    if (r2 <= r1) {
    r7 = r0
    }
L02054ee2:
    r4 = [r4+8]
    call L0205144e  ; @call.xl
    r3 = L01c21714
    r0 = 22
    b[r3+16] = r0
    r0 = r3 + 16
    r1 = 1
    r2 = r6
    call L0204cc4a  ; @call.xl
    r1 = 3
    r2 = r5
    call L0204cc4a  ; @call.xl
    r1 = r4 + r5
    r0 = r3 + 21
    r2 = r7.l (u)
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r7 + 5
    r2 = r0.l (u)
    r1 = 4
    r0 = r8
    call L0204ce4e  ; @call.xl
    {pc, r8-r4} = [sp++]
L02054f28:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    call L0205144e  ; @call.xl
    r0 = L01c21714
    r1 = 24
    b[r0+16] = r1
    b[r0+17] = r4
    r1 = 4
    r2 = 2
    r0 = r5
    call L0204ce4e  ; @call.xl
    {pc, r5, r4} = [sp++]
L02054f52:
    [--sp] = rets
    r0 = r0.l (u)
    r1 = 1
    call L02054f28
    pc = [sp++]
L02054f5c:
    [--sp] = rets
    r0 = r0.l (u)
    r1 = 0
    call L02054f28
    pc = [sp++]
L02054f66:
    [--sp] = {rets, r10-r4}
    sp += -24
    r4 = L01c21c98
    r10 = L01c21714
    goto L02055102
L02054f78:
    r0 = h[r4+12] (u)
    call L020544a4  ; @call.xl
    if (r0 == 0) goto L0205510a
    r0 = [r4+24]
    if (r0 == 3) goto L02055170
    if (r0 == 1) goto L020551a2  ; @beq.ri.l
    r9 = r4 + 76
    if (r0 == 0) goto L020551a6  ; @beq.ri.l
    r0 = [r9+40]
    if (r0 == 1) goto L02055112
    r0 = b[r9+7] (u)
    if (r0 != 0) goto L02055146
    r0 = [r4+4]
    r7 = r0 + -1
    if (r7 > 48) goto L02055102
    r5 = r7 << 1
    r6 = r4 + 44
    tbh [r5]
L02054fbc:
    .short (L020551f6 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L02055208 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L0205522a - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L02055230 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2
    .short (L0205523c - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L02055272 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L02055284 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L0205528c - L02054fbc) / 2, (L02055102 - L02054fbc) / 2
    .short (L02055292 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L02055096 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L020550ae - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L0205501e - L02054fbc) / 2, (L02055102 - L02054fbc) / 2
    .short (L02055298 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L0205529e - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L020552a4 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L020552aa - L02054fbc) / 2, (L02055102 - L02054fbc) / 2
    .short (L020552b0 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L020552bc - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L020552d4 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L020552ec - L02054fbc) / 2, (L02055102 - L02054fbc) / 2
    .short (L020552fa - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L0205501e - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L0205530a - L02054fbc) / 2, (L02055102 - L02054fbc) / 2, (L02055310 - L02054fbc) / 2, (L02055102 - L02054fbc) / 2
    .short (L0205531c - L02054fbc) / 2
L0205501e:
    r8 = h[r6+18] (u)
    r0 = h[r4+22] (u)
    call L02054c14
    r0 += -3
    ifs (r8 > r0) goto L02055160
    if (r7 > 48) goto L02055102
    tbh [r5]
L02055034:
    .short (L020551f6 - L02055034) / 2, (L02055102 - L02055034) / 2, (L02055208 - L02055034) / 2, (L02055102 - L02055034) / 2, (L0205522a - L02055034) / 2, (L02055102 - L02055034) / 2, (L02055230 - L02055034) / 2, (L02055102 - L02055034) / 2
    .short (L0205523c - L02055034) / 2, (L02055102 - L02055034) / 2, (L02055272 - L02055034) / 2, (L02055102 - L02055034) / 2, (L02055284 - L02055034) / 2, (L02055102 - L02055034) / 2, (L0205528c - L02055034) / 2, (L02055102 - L02055034) / 2
    .short (L02055292 - L02055034) / 2, (L02055102 - L02055034) / 2, (L02055096 - L02055034) / 2, (L02055102 - L02055034) / 2, (L020550ae - L02055034) / 2, (L02055102 - L02055034) / 2, (L02055346 - L02055034) / 2, (L02055102 - L02055034) / 2
    .short (L02055298 - L02055034) / 2, (L02055102 - L02055034) / 2, (L0205529e - L02055034) / 2, (L02055102 - L02055034) / 2, (L020552a4 - L02055034) / 2, (L02055102 - L02055034) / 2, (L020552aa - L02055034) / 2, (L02055102 - L02055034) / 2
    .short (L020552b0 - L02055034) / 2, (L02055102 - L02055034) / 2, (L020552bc - L02055034) / 2, (L02055102 - L02055034) / 2, (L020552d4 - L02055034) / 2, (L02055102 - L02055034) / 2, (L020552ec - L02055034) / 2, (L02055102 - L02055034) / 2
    .short (L020552fa - L02055034) / 2, (L02055102 - L02055034) / 2, (L0205534c - L02055034) / 2, (L02055102 - L02055034) / 2, (L0205530a - L02055034) / 2, (L02055102 - L02055034) / 2, (L02055310 - L02055034) / 2, (L02055102 - L02055034) / 2
    .short (L0205531c - L02055034) / 2
L02055096:
    [r4+4] = 0x14
    r7 = h[r6+4] (u)
    r3 = h[r6+2] (u)
    r1 = h[r4+28] (u)
    r2 = h[r4+12] (u)
    if (r1 == 0) goto L020550f6
    r0 = 8
    [sp] = r7
    call L02054c90
    goto L02055102
L020550ae:
    [r4+4] = 0x16
    r7 = [r6+28]
    r9 = h[r6+24] (u)
    r8 = h[r4+12] (u)
    call L0205144e  ; @call.xl
    r0 = 14
    b[r10+16] = r0
    r3 = 1
    r6 = r9
    goto L020550e0
L020550ce:
    r0 = r10 + 16  #
    r2 = h[r7++=2] (u)
    r1 = r3.l (u)
    call L0204cc4a  ; @call.xl
    r3 += 2  ; @add.ri.u5
    r6 += -1
L020550e0:
    if (r6 != 0) goto L020550ce
    r0 = 1
    r0 <= insert(r9, p:1, l:16)
    r2 = r0.l (u)
    r1 = 4
    r0 = r8
    call L0204ce4e  ; @call.xl
    goto L02055102
L020550f6:
    r0 = r4 + 30
    r1 = r2
    r2 = r3
    r3 = r7
    call L02054d30
L02055102:
    r4 = [r4+0]
    if (r4 != 0) goto L02054f78
    goto L020551a2
L0205510a:
    call L020544ae  ; @call.xl
    goto L020551a2
L02055112:
    r6 = b[r4+127] (u)
    r8 = h[r4+12] (u)
    call L0205144e  ; @call.xl
    if (r0 == 0) goto L020551a2
    r0 = r10 + 16
    r1 = r4 + 120
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r1 = 4
    r0 = r8
    r2 = r6
    call L0204ce4e  ; @call.xl
    if (r0 != 0) goto L020551a2
    [r9+40] = 0x0
    goto L020551a2
L02055146:
    r0 = 0
    b[r9+7] = r0
    r4 = h[r4+12] (u)
    call L0205144e  ; @call.xl
    r0 = 30
    b[r10+16] = r0
    r1 = 4
    r2 = 1
    goto L0205519a
L02055160:
    r0 = r4
    call L02054c38
    r1 = 13
    r0 = r4
    call L02054c42
    goto L020551a2
L02055170:
    [r4+24] = 0x2
    r4 = h[r4+12] (u)
    call L0205143c  ; @call.xl
    r6 = r0
    call L0205144e  ; @call.xl
    r0 = 3
    b[++r10=16] = r0
    r1 = 1
    r0 = r10
    r2 = r6
    call L0204cc4a  ; @call.xl
    r1 = 4
    r2 = 3
L0205519a:
    r0 = r4
L0205519c:
    call L0204ce4e  ; @call.xl
L020551a2:
    sp += 24
    {pc, r10-r4} = [sp++]
L020551a6:
    r0 = 1
    [r4+24] = r0
    r8 = h[r4+12] (u)
    call L0205143c  ; @call.xl
    r6 = r0
    call L0205144e  ; @call.xl
    r0 = 2
    b[++r10=16] = r0
    r1 = 1
    r0 = r10
    r2 = r6
    call L0204cc4a  ; @call.xl
    r1 = 4
    r2 = 3
    r0 = r8
    call L0204ce4e  ; @call.xl
    r0 = h[r9+0] (u)
    if (r0 != 0) goto L020551a2
    r0 = h[r4+12] (u)
    r1 = L02055358
    r2 = 200
    call L0201ee98  ; @call.xl
    h[r9+0] = r0
    goto L020551a2
L020551f6:
    [r4+4] = 0x2
    r1 = 10240  #
    r3 = h[r6+2] (u)
    r2 = h[r4+12] (u)
    r4 = h[r6+4] (u)
    r0 = 16
    goto L020552cc
L02055208:
    [r4+4] = 0x4
    r2 = h[r4+28] (u)
    if (r2 == 0) goto L02055328
    r3 = sp + 22
    r1 = 0
    r0 = r3
    call L0204cc4a  ; @call.xl
    r2 = h[r6+4] (u)
    r1 = h[r6+2] (u)
    r0 = h[r4+12] (u)
    r4 = 2
    [sp] = r4
    goto L02055340
L0205522a:
    [r4+4] = 0x6
    goto L02055234
L02055230:
    [r4+4] = 0x8
L02055234:
    r0 = r4
    call L02054d7a
    goto L020551a2
L0205523c:
    [r4+4] = 0x8
    r8 = h[r4+12] (u)
    r4 = h[r6+4] (u)
    r7 = h[r6+2] (u)
    call L0205144e  ; @call.xl
    r0 = 4
    b[++r10=16] = r0
    r1 = 1
    r0 = r10
    r2 = r7
    call L0204cc4a  ; @call.xl
    r1 = 3
    r2 = r4
    call L0204cc4a  ; @call.xl
    r1 = 4
    r2 = 5
    r0 = r8
    goto L0205519c
L02055272:
    [r4+4] = 0xC
    r1 = 10242  #
    r3 = h[r6+2] (u)
    r2 = h[r4+12] (u)
    r4 = h[r6+4] (u)
    r0 = 8
    goto L020552cc
L02055284:
    [r4+4] = 0xE
    r1 = h[r6+6] (u)
    goto L020552f2
L0205528c:
    [r4+4] = 0x10
    goto L020552f0
L02055292:
    [r4+4] = 0x12
    goto L020552fe
L02055298:
    [r4+4] = 0x1A
    goto L02055320
L0205529e:
    [r4+4] = 0x1C
    goto L02055320
L020552a4:
    [r4+4] = 0x1E
    goto L02055314
L020552aa:
    [r4+4] = 0x20
    goto L020552b4
L020552b0:
    [r4+4] = 0x22
L020552b4:
    r0 = h[r4+12] (u)
    call L02054f5c
    goto L020551a2
L020552bc:
    [r4+4] = 0x24
    r1 = 10498  #
    r3 = h[r6+2] (u)
    r2 = h[r4+12] (u)
    r4 = h[r6+4] (u)
    r0 = 8
L020552cc:
    [sp] = r4
    call L02054c90
    goto L020551a2
L020552d4:
    [r4+4] = 0x26
    r2 = h[r9+2] (u)
    r1 = h[r4+12] (u)
    r4 += 80
    r0 = 18
    r3 = 2
    [sp] = r4
    call L02054e5c
    goto L020551a2
L020552ec:
    [r4+4] = 0x28
L020552f0:
    r1 = h[r6+14] (u)
L020552f2:
    r0 = h[r4+12] (u)
    call L02054df0
    goto L020551a2
L020552fa:
    [r4+4] = 0x2A
L020552fe:
    r2 = h[r6+16] (u)
    r1 = h[r6+14] (u)
    r0 = h[r4+12] (u)
    call L02054e20
    goto L020551a2
L0205530a:
    [r4+4] = 0x2E
    goto L02055320
L02055310:
    [r4+4] = 0x30
L02055314:
    r0 = h[r4+12] (u)
    call L02054f52
    goto L020551a2
L0205531c:
    [r4+4] = 0x32
L02055320:
    r0 = r4
    call L02054eb8
    goto L020551a2
L02055328:
    r0 = r4 + 30
    r5 = sp + 6
    r1 = r5
    call L0204cc2a  ; @call.xl
    r2 = h[r6+4] (u)
    r1 = h[r6+2] (u)
    r0 = h[r4+12] (u)
    r3 = 16
    r3 = r5  #
    [sp] = r3
L02055340:
    call L02054cd4
    goto L020551a2
L02055346:
    [r4+4] = 0x18
    goto L02055350
L0205534c:
    [r4+4] = 0x2C
L02055350:
    r0 = r4
    call L02054e9e
    goto L020551a2
L02055358:
    [--sp] = rets
    r0 = r0.l (u)
    call L02054bce
    r3 = r0
    if (r3 == 0) goto L02055378
    call L0205142a  ; @call.xl
    [r3+24] = 0x2
    r0 = 0
    h[r3+76] = r0
    call L02054f66
L02055378:
    pc = [sp++]
L0205537a:
    [--sp] = {rets, r4}
    r4 = [r0+16]
    if (r4 == 0) goto L02055392
    r0 = [r4+4]
    if (r0 == 0) goto L02055392
    r0 = r4
    call L02054c38
    r1 = 127
    r0 = r4
    call L02054c42
L02055392:
    {pc, r4} = [sp++]
L02055394:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r2 = r0
    r1 = 4
    call L0204cb74  ; @call.xl
    r0 = r2  #
    h[r4+0] = r0
    r1 = 6
    call L0204cb74  ; @call.xl
    h[r4+2] = r0
    r0 = r2 + 8
    r5 = r4 + 6
    r1 = r5
    call L0204cc2a  ; @call.xl
    r0 = r5
    call L02051456  ; @call.xl
    if (r0 == 0) goto L020553d2
    r1 = 0
    r0 = r5
    call L0204d034  ; @call.xl
    h[r4+4] = r0
L020553d2:
    {pc, r5, r4} = [sp++]
L020553d4:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r2 = r0
    r1 = 4
    call L0204cb74  ; @call.xl
    r0 = r2  #
    h[r4+0] = r0
    r1 = 6
    call L0204cb74  ; @call.xl
    r0 = r2  #
    h[r4+2] = r0
    r1 = 8
    call L0204cb74  ; @call.xl
    r0 = r2  #
    h[r4+4] = r0
    r1 = 10
    call L0204cb74  ; @call.xl
    h[r4+6] = r0
    r0 = r2 + 12
    r5 = r4 + 10
    r1 = r5
    call L0204cc2a  ; @call.xl
    r0 = r5
    call L02051456  ; @call.xl
    if (r0 == 0) goto L0205542a
    r1 = 0
    r0 = r5
    call L0204d034  ; @call.xl
    h[r4+8] = r0
L0205542a:
    {pc, r5, r4} = [sp++]
L0205542c:
    [--sp] = rets
    r3 = r0
    r1 = r3  #
    [r3+4] = r1
    h[r3+8] = r2
    r0 = L01c21c9c
    call L0204ec4a  ; @call.xl
    pc = [sp++]
L02055444:
    [--sp] = {rets, r4}
    call L02054bce
    r4 = r0
    if (r4 == 0) goto L02055476
    call L02054c2a
    r2 = 0
    r3 = 0
    r0 = r4 + 96
    d[r0+0] = r3_r2
    [r0+8] = 0x1E
    r1 = L0205537a
    [r0+12] = r1
    [r0+16] = r4
    r1 = 131
    call L0204cffa  ; @call.xl
    goto L02055478
L02055476:
    r4 = 0
L02055478:
    r0 = r4
    {pc, r4} = [sp++]
L0205547c:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r6 = r0
    r0 = r1
    call L02055444
    if (r0 == 0) goto L020554b6
    r1 = [r0+4]
    r5 = 149
    if (r1 != 0) goto L020554b8
    [r0+8] = r6
    r1 = 1
    h[r0+46] = r1
    r1 = 65535
    h[r0+48] = r1
    r5 = 0
    h[r0+28] = r5
    r1 = r0 + 30
    rep 16 {
    r2 = b[r4++=1] (u)
    b[r1++=1] = r2
    }
    [r0+4] = 0x3
    call L02054f66
    goto L020554b8
L020554b6:
    r5 = 86
L020554b8:
    r0 = r5
    {pc, r6-r4} = [sp++]
L020554bc:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r6 = r0
    r0 = r1
    call L02055444
    if (r0 == 0) goto L020554ee
    r1 = [r0+4]
    r5 = 149
    if (r1 != 0) goto L020554f0
    r2 = r0 + 44  #
    [r0+8] = r6
    r1 = h[r4+0] (u)
    h[r2+2] = r1
    r1 = h[r4+2] (u)
    h[r2+4] = r1
    r5 = 0
    b[r0+82] = r5
    h[r2+12] = r5
    [r0+4] = 0x5
    call L02054f66
    goto L020554f0
L020554ee:
    r5 = 86
L020554f0:
    r0 = r5
    {pc, r6-r4} = [sp++]
L020554f4:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r5 = r0
    r0 = r1
    call L02055444
    r3 = r0
    if (r3 == 0) goto L02055538
    r0 = [r3+4]
    r6 = 149
    if (r0 != 0) goto L0205553a
    r0 = b[r4+6] (u)
    r6 = 152
    if ((r0 & 16) == 0) goto L0205553a
    [r3+8] = r5
    r0 = h[r4+2] (u)
    h[r3+46] = r0
    r0 = h[r4+4] (u)
    h[r3+48] = r0
    r0 = r3 + 80
    r1 = 0
    r2 = 1
    r6 = 0
    call L0204cc4a  ; @call.xl
    [r3+4] = 0x23
    call L02054f66
    goto L0205553a
L02055538:
    r6 = 86
L0205553a:
    r0 = r6
    {pc, r6-r4} = [sp++]
L0205553e:
    [--sp] = {rets, r7-r4}
    r4 = r3
    r5 = r2
    r7 = r0
    r0 = r1
    call L02055444
    r6 = r0
    if (r6 == 0) goto L0205558c
    r1 = [r6+4]
    r0 = 149
    if (r1 != 0) goto L0205558a
    r0 = h[r6+22] (u)
    call L02054c14
    r1 = r0 + -3
    r0 = 151
    ifs (r4 > r1) goto L0205558a
    r0 = h[r6+12] (u)
    call L020544a4  ; @call.xl
    if (r0 == 0) goto L02055590
    r1 = r6 + 56  #
    r0 = [sp+20]
    [r6+8] = r7
    h[r1+2] = r5
    h[r1+6] = r4
    r0 = r6  #
    [r1+8] = r0
    [r6+4] = 0x18
    call L02054e9e
    r0 = 0
L0205558a:
    {pc, r7-r4} = [sp++]
L0205558c:
    r0 = 86
    {pc, r7-r4} = [sp++]
L02055590:
    r0 = 148
    {pc, r7-r4} = [sp++]
L02055594:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    r0 = 0
    call L02055444
    if (r0 == 0) goto L020555be
    r1 = [r0+4]
    if (r1 != 0) goto L020555be
    r1 = L02051596
    [r0+8] = r1
    h[r0+46] = r5
    h[r0+48] = r4
    [r0+4] = 0x9
    call L02054f66
L020555be:
    {pc, r5, r4} = [sp++]
L020555c0:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = 0
    call L02054bce
    r1 = 23
    if (r0 == 0) goto L020555d6
    r2 = [r0+24]
    if (r2 == 2) {  ; @if.eq.ri.s12
    r1 = h[r0+22] (u)
    }
L020555d6:
    h[r4+0] = r1
    {pc, r4} = [sp++]
L020555da:
    [--sp] = {rets, r7-r4}
    sp += -4
    r5_r4 = r3_r2
    r6 = r1
    call L02054bce
    r7 = r0
    if (r7 == 0) goto L0205561e
    r1 = [r7+4]
    r0 = 149
    if (r1 != 0) goto L02055620
    r0 = h[r7+22] (u)
    call L02054c14
    r1 = r0 + -3
    r0 = 151
    ifs (r4 > r1) goto L02055620
    r0 = h[++r7=12] (u)
    call L020544a4  ; @call.xl
    if (r0 == 0) goto L02055624
    r2 = r6  #
    r1 = h[r7+0] (u)
    r0 = 82
    r3 = r4  #
    [sp] = r5
    call L02054e5c
    r0 = 0
    goto L02055620
L0205561e:
    r0 = 86
L02055620:
    sp += 4
    {pc, r7-r4} = [sp++]
L02055624:
    r0 = 148
    goto L02055620
L02055628:
    [--sp] = {rets, r5, r4}
    r4 = r1
    call L02055444
    if (r0 == 0) goto L02055654
    r1 = [r0+4]
    r5 = 149
    if (r1 != 0) goto L02055656
    r1 = L02051596
    [r0+8] = r1
    h[r0+58] = r4
    r5 = 0
    h[r0+60] = r5
    [r0+4] = 0xF
    call L02054f66
    goto L02055656
L02055654:
    r5 = 86
L02055656:
    r0 = r5
    {pc, r5, r4} = [sp++]
L0205565a:
    [--sp] = {rets, r5, r4}
    r4 = r1
    call L02055444
    if (r0 == 0) goto L02055686
    r1 = [r0+4]
    r5 = 149
    if (r1 != 0) goto L02055688
    r1 = L02051596
    [r0+8] = r1
    h[r0+58] = r4
    r5 = 0
    h[r0+60] = r5
    [r0+4] = 0x11
    call L02054f66
    goto L02055688
L02055686:
    r5 = 86
L02055688:
    r0 = r5
    {pc, r5, r4} = [sp++]
L0205568c:
    [--sp] = rets
    call L020544ae  ; @call.xl
    pc = [sp++]
L02055696:
    [--sp] = {rets, r7-r4}
    r4 = L01c26838
    r0 = [r4+0]
    if (r0 == 0) goto L02055704
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    r6 = L01c1fa20
    if (r1 != 0) goto L020556ce
    csync
L020556c6:
    testset b[r6]
    ifeq goto L020556c6
    csync
L020556ce:
    r3 = [r4+0]
    r7 = 0
    b[r3+174] = r7
    r0 = r3 + 132
    call L02051af4  ; @call.xl
    r0 = r3
    call L0203d218  ; @call.xl
    [r4+0] = r7
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L020556fe
    csync
    b[r6+0] = r7
L020556fe:
    call storage_coordination_irq_leave  ; @call.xl
L02055704:
    {pc, r7-r4} = [sp++]
L02055706:
    [--sp] = {rets, r6-r4}
    sp += -8
    r3 = r1
    r4 = r0
    call L02054bb6
    if (r0 == 0) goto L02055750
    h[r0+22] = r3
    r6 = L01c21c98
    r0 = [r6+16]
    if (r0 == 0) goto L02055750
    r0 = 181
    b[sp+2] = r0
    r0 = 4
    b[sp+3] = r0
    r5 = sp + 2
    r1 = 2
    r0 = r5
    r2 = r4
    call L0204cc4a  ; @call.xl
    r1 = 4
    r2 = r3
    call L0204cc4a  ; @call.xl
    r2 = r5  #
    r4 = [r6+16]
    r0 = 4
    r1 = 0
    r3 = 6
    call r4
L02055750:
    sp += 8
    {pc, r6-r4} = [sp++]

; 0x02055754..0x020559cc: data
    .fill ((20 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L02055754:
    .long L0203a190  ; "nor_sdfile"
    .long phase3_p10_nor_sdfile_mount
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02021e68
    .long L02021f82
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p9_sdfile_write
    .long phase3_p9_sdfile_seek
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p9_sdfile_len
    .long phase3_p9_sdfile_pos
    .long L020213d6
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02021400
    .byte 0x00,0x00,0x00,0x00
    .long L02021726
    .byte 0x00,0x00,0x00,0x00
    .long L020217ac
    .long L02021822
    .long L02021a1c
    .byte 0x00,0x00,0x00,0x00
    .long L02021a32
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02021a56
    .byte 0x00,0x00,0x00,0x00
    .long L02035be8  ; "sdfile"
    .long L02020d8c
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long phase3_p9_sdfile_open
    .long phase3_p9_sdfile_read
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p9_sdfile_write
    .long phase3_p9_sdfile_seek
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p9_sdfile_len
    .long phase3_p9_sdfile_pos
    .long L020213d6
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02021400
    .long phase3_p9_sdfile_delete
    .long L02021726
    .byte 0x00,0x00,0x00,0x00
    .long L020217ac
    .long L02021822
    .long L02021a1c
    .byte 0x00,0x00,0x00,0x00
    .long L02021a32
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02021a56
    .byte 0x00,0x00,0x00,0x00
    .long L0203a19b  ; "sdfile_ext"
    .long L020222fc
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long phase3_p10_sdfile_open
    .long phase3_p10_sdfile_read
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p10_sdfile_write
    .long L02022a96
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p10_sdfile_len
    .long phase3_p10_sdfile_pos
    .long L02022ad8
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02022b02
    .long phase3_p10_sdfile_delete
    .long phase3_p10_sdfile_scan
    .byte 0x00,0x00,0x00,0x00
    .long L02022e74
    .long phase3_p10_sdfile_sel
    .long phase3_p10_sdfile_get_attr
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p10_sdfile_get_attrs
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02023126
    .byte 0x00,0x00,0x00,0x00
L020558bc:
    .long phase3_p3_app_update_init
L020558c0:
    .long phase3_p1_app_version_check
    .long L020012f2
    .long L02041062
    .long phase3_p10_sdfile_init
L020558d0:
    .long L0204145a
L020558d4:
    .long L0201f2ba
L020558d8:
    .long L0201f13a
L020558dc:
    .byte 0x04,0x00,0x00,0x00
    .long clock_record_and_usb_link_usb_event
    .byte 0x00,0x00,0x00,0x00,0x01,0x00,0x00,0x00
    .long L0204bba4
    .byte 0x00,0x00,0x00,0x00
L020558f4:
    .long phase3_p8_syscfg_btif_init
    .long L0201ff12
    .long L0201ff2a
    .long phase3_p8_btif_area_write
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long phase3_p9_vm_init
    .long phase3_p9_vm_check_id
    .long phase3_p9_vm_read
    .long phase3_p9_vm_write
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L0201faaa
    .long L0201fb6c
    .long L0201fccc
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long phase3_p8_syscfg_bin_group_read
    .long phase3_p8_syscfg_bin_ptr_read
L02055948:
    .long L02035906  ; "otg"
    .long L02035378
    .long L0203507c
L02055954:
    .long L02039f80  ; "ota"
    .long phase3_p1_ota_idle_query
    .long L0203a116  ; "iic"
    .long L0201b17a
    .long L0203a11a  ; "adc_scan"
    .long phase3_p13_adc_scan_idle_query
    .long L0203a145  ; "sys_power"
    .long phase3_p6_sys_power_idle_query
    .long L0203a14f  ; "dac"
    .long sdk_dac_idle_query
    .long L0203a153  ; "alnk"
    .long sdk_alnk_idle_query
    .long L0203a158  ; "norflash"
    .long phase3_p6_norflash_idle_query
    .long L02035906  ; "otg"
    .long L0201dfea
    .long L0203a172  ; "usr_systimer"
    .long L0201ef06
    .long L02035851  ; "vm"
    .long phase3_p8_vm_idle_query
    .long L0203a1fb  ; "ble_slave_mult"
    .long L02046246
    .long L0203a20a  ; "btstack_lowpwer_deal"
    .long L0204d56c
L020559b4:
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p13_iic_open
    .long L0201b3bc
    .long L0201b476
    .long phase3_p13_iic_ioctl
    .long phase3_p13_iic_close

; 0x020559cc..0x0205677a: system layer code (not reversed), as instructions
L020559cc:
    sp += -4
    [sp] = r1
    if (r0 == 0) goto L020559dc
    r2 = 0xC000
    [r0+r2<<2] = r1
    goto L02055a08
L020559dc:
    r0 = 200452
    [r0+0] |= 0x400
    csync
    r1 = sp + 0
    r1 += 4  ; @add.ri.u5
    [r0+12] = r1
    [r0+16] = 0x4
    csync
L020559f4:
    r1 = [r0+0]
    if ((r1 & 1048576) == 0) goto L020559f4
    [r0+0] |= 0x400
    r0 = L01c267d4
    [r0+0] += 1  ; @rmw.add.s12
L02055a08:
    sp += 4
    rts
L02055a0c:
    r2 = 200732
L02055a12:
    r3 = [r2+0]
    if ((r3 & 131072) != 0) goto L02055a12
    r1 <= insert(r0, p:8, l:8)
    r0 = r1 | 0x80000
    r0 = r1 | 0xA0000  #
    [r2+0] = r0
    [r2+0] = r0
    rts
L02055a2a:
    [--sp] = rets
    r0 = 4100
    r1 = 12
    call L020559cc
    r0 = 22
    r1 = 0
    call L02055a0c
    r0 = 21
    r1 = 49
    call L02055a0c
    r0 = 21
    r1 = 48
    call L02055a0c
    r0 = 25
    r1 = 0
    call L02055a0c
    pc = [sp++]
L02055a4e:
    [--sp] = {rets, r4}
    r4 = r1
    r1 = r0
    r0 = 209
    call L02055a0c
    r0 = 210
    r1 = r4
    call L02055a0c
    r0 = 208
    r1 = 1
    call L02055a0c
    {pc, r4} = [sp++]
L02055a66:
    [--sp] = {rets, r4}
    r4 = r1
    r1 = r0
    r0 = 201
    call L02055a0c
    r0 = 202
    r1 = r4
    call L02055a0c
    r0 = 200
    r1 = 1
    call L02055a0c
    {pc, r4} = [sp++]
L02055a7e:
    [--sp] = {rets, r4}
    r4 = r1
    r1 = r0
    r0 = 213
    call L02055a0c
    r0 = 214
    r1 = r4
    call L02055a0c
    r0 = 212
    r1 = 1
    call L02055a0c
    {pc, r4} = [sp++]
L02055a96:
    [--sp] = {rets, r8-r4}
    r2 = r0 + -1
    if (r2 > 4) goto L02055ab8
    r8 = 1
    r4 = 0
    r1_r0 = 0
    r6 = 0
    tbb [r2]
L02055aac:
    .byte (L02055ad2 - L02055aac) / 2, (L02055ab2 - L02055aac) / 2, (L02055abe - L02055aac) / 2, (L02055ac4 - L02055aac) / 2, (L02055aca - L02055aac) / 2
    .byte 0x00  ; alignment
L02055ab2:
    r1 = 1
    r8 = 0
    goto L02055ad0
L02055ab8:
    r8 = 0
    r4 = 1
    goto L02055acc
L02055abe:
    r0 = 1
    r8 = 0
    goto L02055ace
L02055ac4:
    r6 = 1
    r8 = 0
    goto L02055ad2
L02055aca:
    r8 = 0
L02055acc:
    r0 = 0
L02055ace:
    r1 = 0
L02055ad0:
    r6 = 0
L02055ad2:
    r2 = 71936
    r3 = r0 | r4  #
    r7 = [r2+0]
    r5 = r3 | r1
    r5 |= r6
    r7 &= 4286578687
    r7 <= insert(r5, p:23, l:1)
    [r2+0] = r7
    r7 = [r2+4]
    r7 &= 4294934527
    r7 <= insert(r4, p:15, l:1)
    [r2+4] = r7
    r4 = r3 | r6  #
    r7 = [r2+12]
    r3 = r7 & 0xFFFFFFEF
    r3 <= insert(r4, p:4, l:1)
    [r2+12] = r3
    r3 = [r2+12]
    r3 &= 4294967263
    r3 <= insert(r4, p:5, l:1)
    [r2+12] = r3
    r3 = [r2+12]
    r3 &= 4293918719
    r3 <= insert(r4, p:20, l:1)
    [r2+12] = r3
    r3 = [r2+16]
    r3 &= 4294963199
    r3 <= insert(r5, p:12, l:1)
    [r2+16] = r3
    r3 = [r2+16]
    r3 &= 4160749567
    r3 <= insert(r5, p:27, l:1)
    [r2+16] = r3
    r3 = [r2+20]
    r3 &= 4294965247
    r3 <= insert(r5, p:11, l:1)
    [r2+20] = r3
    r3 = [r2+20]
    r3 &= 4294705151
    r3 <= insert(r5, p:18, l:1)
    [r2+20] = r3
    r3 = [r2+24]
    r3 &= 4294967294
    r3 |= r5
    [r2+24] = r3
    r3 = [r2+24]
    r3 &= 4294967293
    r3 <= insert(r5, p:1, l:1)
    [r2+24] = r3
    r3 = [r2+20]
    r3 &= 4227858431
    r3 <= insert(r5, p:26, l:1)
    [r2+20] = r3
    r3 = r0 | r8  #
    r5 = [r2+8]
    r3 |= r1
    r5 &= 4294967231
    r5 <= insert(r3, p:6, l:1)
    [r2+8] = r5
    r5 = [r2+24]
    r5 &= 4294443007
    r5 <= insert(r3, p:19, l:1)
    [r2+24] = r5
    r5 = [r2+28]
    r5 &= 4294967294
    r5 |= r3
    [r2+28] = r5
    r5 = [r2+28]
    r5 &= 4294967279
    r5 <= insert(r3, p:4, l:1)
    [r2+28] = r5
    r5 = [r2+32]
    r5 &= 4294966783
    r5 <= insert(r3, p:9, l:1)
    [r2+32] = r5
    r5 = [r2+36]
    r5 &= 4294967263
    r5 <= insert(r3, p:5, l:1)
    [r2+36] = r5
    r5 = [r2+36]
    r5 &= 4294967167
    r5 <= insert(r3, p:7, l:1)
    [r2+36] = r5
    r5 = [r2+36]
    r5 &= 4294967039
    r5 <= insert(r3, p:8, l:1)
    [r2+36] = r5
    r5 = [r2+36]
    r5 &= 4160749567
    r5 <= insert(r3, p:27, l:1)
    [r2+36] = r5
    r5 = [r2+40]
    r5 &= 4294963199
    r5 <= insert(r3, p:12, l:1)
    [r2+40] = r5
    r5 = [r2+40]
    r5 &= 4227858431
    r5 <= insert(r3, p:26, l:1)
    [r2+40] = r5
    r5 = [r2+56]
    r5 &= 4227858431
    r5 <= insert(r4, p:26, l:1)
    [r2+56] = r5
    r4 = [r2+56]
    r4 &= 4160749567
    r4 <= insert(r3, p:27, l:1)
    [r2+56] = r4
    r3 = [r2+16]
    r3 &= 4294959103
    r3 <= insert(r1, p:13, l:1)
    [r2+16] = r3
    r3 = [r2+44]
    r3 &= 4294950911
    r3 <= insert(r1, p:14, l:1)
    [r2+44] = r3
    r1 = [r2+44]
    r1 &= 4294965247
    r1 <= insert(r0, p:11, l:1)
    [r2+44] = r1
    r1 = [r2+8]
    r1 &= 3758096383
    r1 <= insert(r0, p:29, l:1)
    [r2+8] = r1
    {pc, r8-r4} = [sp++]
L02055c0e:
    r0 = 72040
    r1 = [r0+0]
    r1 = r1 & 0xFFFFFFF
    r1 |= 268435456
    [r0+0] = r1
    r1 = 8
L02055c20:
    [r0+16] = 0x1
    r1 += -1
    if ((r1 & 0xFF) != 0) goto L02055c20
    [r0+16] = 0x0
    r0 = [r0+16]
    rts
L02055c34:
    [--sp] = {rets, r8-r4}
    r3 = 71940
    r0 = [r3+0]
    r0 = r0 & 0xFFFFF0FF
    r0 |= 2048
    [r3+0] = r0
    [r3+76] |= 0x8000000
    r4 = 0
    r2 = r3 + 88
    r6 = -1023
L02055c54:
    if ((r4 & 0xFF) == 0) goto L02055c6e
    r1 = r4.b0 (u)
    r0 = 290
    if (r1 != 1) {  ; @if.ne.ri.s12
    r0 = 160
    }
    r1 = [r2+12]
    r1 &= r6
    r0 |= r1
    goto L02055c76
L02055c6e:
    r0 = [r2+12]
    r0 &= r6
    r0 = r0 | 0x1FC
L02055c76:
    [r2+12] = r0
    r0 = [r2+12]
    r0 = r0 & 0xFFFC03FF
    r0 = r0 | 0x7800
    [r2+12] = r0
    [r3+100] &= 0xFF83FFFF
    [r3+100] &= 0xFF7FFFFF
    [r3+100] |= 0x1
L02055c90:
    call L02055c0e
    if ((r0 & 32) == 0) goto L02055c90
    if ((r4 & 0xFF) != 0) goto L02055ca8
    call L02055c0e
    [r3+100] &= 0xFFFFFFFE
    r5 = r0 >> 8
    r4 = 1
    goto L02055c54
L02055ca8:
    call L02055c0e
    r1 = r4.b0 (u)
    r0 = r0 >> 8
    if (r1 != 1) {  ; @if.ne.ri.s12
    r8 = r0
    } else {
    r7 = r0
    }
    [r3+100] &= 0xFFFFFFFE
    r4 += 1  ; @add.ri.u5
    r0 = r4.b0 (u)
    if (r0 != 3) goto L02055c54
    [r3+76] &= 0xF7FFFFFF
    r0 = r7.b0 (u)  #
    r1 = [r3+28]
    r1 = r1 & 0xFFFC03FF
    r1 <= insert(r0, p:10, l:8)
    [r3+28] = r1
    r1 = [r3+12]
    r1 = r1 & 0xFFC03FFF
    r1 <= insert(r0, p:14, l:8)
    [r3+12] = r1
    [r3+88] |= 0xFF
    r4 = r5.b0 (u)  #
    r1 = [r2+0]
    r1 = r1 & 0xFFFF00FF
    r1 <= insert(r4, p:8, l:8)
    [r2+0] = r1
    r1 = [r2+0]
    r1 = r1 & 0xFF00FFFF
    r1 <= insert(r0, p:16, l:8)
    [r2+0] = r1
    r5 = uextra(r8, p:0, l:8)  #
    r1 = [r2+0]
    r1 = r1 & 0xFFFFFF
    r1 <= insert(r5, p:24, l:8)
    [r2+0] = r1
    [r3+92] |= 0xFF
    r1 = [r2+4]
    r1 = r1 & 0xFFFF00FF
    r1 <= insert(r4, p:8, l:8)
    [r2+4] = r1
    r1 = [r2+4]
    r1 = r1 & 0xFF00FFFF
    r1 <= insert(r0, p:16, l:8)
    [r2+4] = r1
    r0 = [r2+4]
    r0 = r0 & 0xFFFFFF
    r0 <= insert(r5, p:24, l:8)
    [r2+4] = r0
    {pc, r8-r4} = [sp++]
L02055d38:
    r1 = 71952
    [r1+16] &= 0xFFEFFFFF
    [r1+16] |= 0x200000
    r2 = [r1+16]
    if (r0 != 1) goto L02055d5e
    r0 = r2 & 0xFFBFFFFF
    [r1+16] = r0
    r0 = [r1+16]
    r2 = r0 | 0x800000
    r0 = 0x18000000
    goto L02055d6e
L02055d5e:
    r0 = r2 | 0x400000
    [r1+16] = r0
    r0 = [r1+16]
    r2 = r0 & 0xFF7FFFFF
    r0 = 0x8000000
L02055d6e:
    [r1+16] = r2
    r2 = [r1+20]
    r2 = r2 & 0x8FFFFFFF
    r2 = r2 | 0x50000000
    [r1+20] = r2
    [r1+24] |= 0x6000
    r2 = [r1+24]
    r2 = r2 & 0xE7FFFFFF
    r0 |= r2
    [r1+24] = r0
    r0 = [r1+0]
    r0 = r0 & 0xFFFFF0FF
    r0 = r0 | 0x900
    [r1+0] = r0
    rts
L02055d98:
    [--sp] = rets
    r3 = r0
    r1 = 0x90000
    r1 <= insert(r3, p:8, l:8)
    r0 = 4124
    call L020559cc
    r1 = 0xB0000
    r1 <= insert(r3, p:8, l:8)
    r0 = 4124
    call L020559cc
    r0 = 200732
    r0 = [r0+0]
    r0 = r0.b0 (u)
    pc = [sp++]
L02055dc8:
    [--sp] = rets
    r1 = r0
    r0 = 201
    call L02055a0c
    r0 = 200
    r1 = 2
    call L02055a0c
    r0 = 203
    call L02055d98
    pc = [sp++]
L02055de0:
    [--sp] = rets
    r0 = 64
    call L02055dc8
    r1 = r0 & 0xFFFFFF7F
    r0 = 64
    call L02055a66
    r0 = 65
    call L02055dc8
    r1 = r0 & 0xFFFFFF7F
    r0 = 65
    call L02055a66
    r0 = 40
    r1 = 0
    call L02055a66
    r0 = 39
    r1 = 5
    call L02055a66
    r0 = 4
    call L02055d98
    r1 = r0 & 0xFFFFFFE7
    r0 = 4
    call L02055a0c
    pc = [sp++]
L02055e1e:
    [--sp] = rets
    call L02055a2a
    r0 = 4100
    r1 = 12
    call L020559cc
    r0 = 25
    r1 = 24
    call L02055a0c
    pc = [sp++]
L02055e38:
    [--sp] = rets
    r1 = r0
    r0 = 209
    call L02055a0c
    r0 = 208
    r1 = 2
    call L02055a0c
    r0 = 211
    call L02055d98
    pc = [sp++]
L02055e50:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = uextra(r4, p:2, l:8)
    r0 = 4
    call L02055a4e
    r0 = 97
    call L02055e38
    r1 = r4 & 0x3
    r0 = r0 & 0xFFFFFFFC
    r1 |= r0
    r0 = 97
    call L02055a4e
    {pc, r4} = [sp++]
L02055e74:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = uextra(r4, p:2, l:8)
    r0 = 6
    call L02055a4e
    r0 = 97
    call L02055e38
    r1 = r4 << 4
    r1 = r1 & 0x30
    r0 = r0 & 0xFFFFFFCF
    r1 |= r0
    r0 = 97
    call L02055a4e
    {pc, r4} = [sp++]
L02055e9a:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = uextra(r4, p:2, l:8)
    r0 = 5
    call L02055a4e
    r0 = 97
    call L02055e38
    r1 = r4 << 2
    r1 = r1 & 0xC
    r0 = r0 & 0xFFFFFFF3
    r1 |= r0
    r0 = 97
    call L02055a4e
    {pc, r4} = [sp++]
L02055ec0:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = uextra(r4, p:2, l:8)
    r0 = 7
    call L02055a4e
    r0 = 97
    call L02055e38
    r0 = r0 & 0xFFFFFF3F
    r0 <= insert(r4, p:6, l:26)
    r1 = r0.b0 (u)
    r0 = 97
    call L02055a4e
    {pc, r4} = [sp++]
L02055ee4:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = uextra(r4, p:2, l:8)
    r0 = 8
    call L02055a4e
    r0 = 98
    call L02055e38
    r1 = r4 & 0x3
    r0 = r0 & 0xFFFFFFFC
    r1 |= r0
    r0 = 98
    call L02055a4e
    {pc, r4} = [sp++]
L02055f08:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = uextra(r4, p:2, l:8)
    r0 = 9
    call L02055a4e
    r0 = 98
    call L02055e38
    r1 = r4 << 2
    r1 = r1 & 0xC
    r0 = r0 & 0xFFFFFFF3
    r1 |= r0
    r0 = 98
    call L02055a4e
    {pc, r4} = [sp++]
L02055f2e:
    r1 = 71964
    r2 = [r1+0]
    r0 &= 4294967167
    r2 = r2 & 0xFFFF80FF
    r2 <= insert(r0, p:8, l:7)
    [r1+0] = r2
    rts
L02055f44:
    r1 = 71968
    r2 = [r1+0]
    r2 = r2 >> 7
    r0 <= insert(r2, p:7, l:25)
    [r1+0] = r0
    rts
L02055f56:
    [--sp] = {rets, r4}
    r0 = r0 << 2
    r1 = L01c1f0c8
    r2 = b[++r0=r1] (u)
    r1 = 71952
    r4 = r2 & 0xFFFFFF01  #
    r3 = [r1+0]
    r3 &= 4290772991
    r3 <= insert(r4, p:22, l:1)
    [r1+0] = r3
    r2 = r2.b0 (s)  #
    r3 = [r1+0]
    r2 = r2 << 22
    r4 = r2 >> 23
    r3 <= insert(r4, p:23, l:1)
    [r1+0] = r3
    r3 = [r1+0]
    r2 = r2 >> 24
    r3 <= insert(r2, p:24, l:1)
    [r1+0] = r3
    r2 = b[r0+1] (u)
    r4 = r2 & 0xFFFFFF01  #
    r3 = [r1+0]
    r3 &= 4261412863
    r3 <= insert(r4, p:25, l:1)
    [r1+0] = r3
    r3 = [r1+0]
    r2 = r2 << 25
    r2 = r2 >> 26
    r3 <= insert(r2, p:26, l:1)
    [r1+0] = r3
    r2 = b[r0+2] (u)
    r4 = r2 & 0xFFFFFF07  #
    r3 = [r1+4]
    r3 = r3 & 0xFFFC7FFF
    r3 <= insert(r4, p:15, l:3)
    [r1+4] = r3
    r2 = r2.b0 (s)  #
    r3 = [r1+4]
    r2 = r2 << 8
    r4 = r2 >> 12
    r3 <= insert(r4, p:12, l:1)
    [r1+4] = r3
    r3 = [r1+4]
    r4 = r2 >> 13
    r3 <= insert(r4, p:13, l:1)
    [r1+4] = r3
    r3 = [r1+4]
    r2 = r2 >> 14
    r3 <= insert(r2, p:14, l:1)
    [r1+4] = r3
    r0 = b[r0+3] (u)
    r2 = [r1+4]
    r2 <= insert(r0, p:5, l:3)
    [r1+4] = r2
    {pc, r4} = [sp++]
L02055fec:
    [--sp] = rets
    r1 = r0
    r0 = 213
    call L02055a0c
    r0 = 212
    r1 = 2
    call L02055a0c
    r0 = 215
    call L02055d98
    pc = [sp++]
L02056006:
    [--sp] = {rets, r4}
    r0 = 23
    r1 = 130
    call L02055a7e
    r0 = 262656
    r0 = [r0+0]
    if ((r0 & 0x1) != 0) {
    r0 = 8000000
    } else {
    r0 = 4000000
    }
    r1 = L01c373b8
    r1 = [r1+8]
    r0 = r1 / r0 (s)
    r1 = -1000
    r0 *= r1
    goto L02056040
L0205603c:
    nop
    r0 += 1  ; @add.ri.u5
L02056040:
    if (r0 != 0) goto L0205603c
    r0 = 128
    call L02055fec
    r4 = r0
    r0 = 23
    r1 = 2
    call L02055a7e
    r0 = r4
    {pc, r4} = [sp++]
L02056054:
    [--sp] = {rets, r4}
    r0 = 0
    r4 = 0
    call L02055f56
    call L02056006
    call L02056006
    if (r0 > 47) goto L0205607c
L02056066:
    r0 = r4.b0 (u)
    if (r0 > 35) goto L0205607c
    r4 += 1  ; @add.ri.u5
    r0 = r4.b0 (s)
    call L02055f56
    call L02056006
    call L02056006
    if (r0 < 48) goto L02056066
L0205607c:
    r0 = r4.b0 (s)
    call L02055f56
    {pc, r4} = [sp++]
L02056084:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = 21
    r1 = 1
    call L02055a7e
    r0 = 22
    r1 = 1
    call L02055a7e
    r0 = 21
    r1 = 3
    call L02055a7e
    r0 = 22
    r1 = 3
    call L02055a7e
L020560a8:
    r0 = 141
    call L02055fec
    if ((r0 & 0x3) != 0) goto L020560a8
    if (r4 > 3) goto L020560da
    tbb [r4]
L020560b8:
    .byte (L020560bc - L020560b8) / 2, (L02056108 - L020560b8) / 2, (L02056120 - L020560b8) / 2, (L020560bc - L020560b8) / 2
L020560bc:
    r0 = 129
    call L02055fec
    r4 = r0
    r0 = 130
    call L02055fec
    r0 <= insert(r4, p:8, l:8)
    r0 = r0.l (s)
    r5 = r0 * r0
    r0 = 132
    call L02055fec
    r4 = r0
    r0 = 133
    goto L020560f8
L020560da:
    r0 = 135
    call L02055fec
    r4 = r0
    r0 = 136
    call L02055fec
    r0 <= insert(r4, p:8, l:8)
    r0 = r0.l (s)
    r5 = r0 * r0
    r0 = 138
    call L02055fec
    r4 = r0
    r0 = 139
L020560f8:
    call L02055fec
    r0 <= insert(r4, p:8, l:8)
    r0 = r0.l (s)
    r0 *= r0
    r0 += r5  ; @add.rr
    {pc, r5, r4} = [sp++]
L02056108:
    r0 = 129
    call L02055fec
    r1 = r0
    r0 = 130
    r4 = r1 << 24
    call L02055fec
    r4 <= insert(r0, p:16, l:8)
    r0 = 131
    goto L02056136
L02056120:
    r0 = 138
    call L02055fec
    r1 = r0
    r0 = 139
    r4 = r1 << 24
    call L02055fec
    r4 <= insert(r0, p:16, l:8)
    r0 = 140
L02056136:
    call L02055fec
    r4 <= insert(r0, p:8, l:8)
    r0 = 256
    r0 = r4 / r0 (s)
    {pc, r5, r4} = [sp++]
L02056148:
    [--sp] = {rets, r8-r4}
    call L02055a2a
    r0 = 21
    r1 = 0
    r5 = 0
    call L02055a66
    r0 = 20
    r1 = 0
    call L02055a66
    call L02055de0
    call L02055e1e
    r0 = 0
    r1 = 3
    call L02055a4e
    r0 = 95
    r1 = 16
    call L02055a4e
    r0 = 1
    r1 = 20
    call L02055a4e
    r0 = 2
    r1 = 0
    call L02055a4e
    r0 = 3
    r1 = 0
    call L02055a4e
    r0 = 0
    r1 = 62
    call L02055a7e
    r0 = 19
    r1 = 30
    call L02055a7e
    r0 = 20
    r1 = 56
    call L02055a7e
    r0 = 20
    r1 = 52
    call L02055a7e
    r0 = 1023
    call L02055e50
    r0 = 1023
    call L02055e74
    r0 = 0
    call L02055e9a
    r0 = 0
    call L02055ec0
    r0 = 0
    call L02055ee4
    r0 = 0
    call L02055f08
    r0 = 64
    r6 = 64
    call L02055f2e
    r0 = 64
    call L02055f44
    call L02056054
    r0 = 64
    call L02055f2e
    r0 = 0
    call L02056084
    r4 = r0
    r7 = 128
L020561fa:
    r0 = r5.b0 (u)
    call L02055f2e
    r0 = 0
    call L02056084
    r1 = r5
    ifs (r0 >= r4) {
    r0 = r4
    r1 = r6
    }
    r7 += -1
    r2 = r7.l (u)
    r5 += 1  ; @add.ri.u5
    r6 = r1
    r4 = r0
    if (r2 != 0) goto L020561fa
    r0 = r1.b0 (u)
    call L02055f2e
    r0 = 64
    r7 = 64
    call L02055f44
    r0 = 0
    r5 = 0
    call L02056084
    r4 = r0
    r6 = 128
L02056236:
    r0 = r5.b0 (u)
    call L02055f44
    r0 = 0
    call L02056084
    r1 = r5
    ifs (r0 >= r4) {
    r0 = r4
    r1 = r7
    }
    r6 += -1
    r2 = r6.l (u)
    r5 += 1  ; @add.ri.u5
    r7 = r1
    r4 = r0
    if (r2 != 0) goto L02056236
    r0 = r1.b0 (u)
    call L02055f44
    r0 = 0
    r5 = 0
    call L02055ee4
    r0 = 0
    call L02055f08
    call L02056054
    r0 = 0
    call L02055ee4
    r0 = 0
    call L02056084
    r4 = r0
    r6 = 401
    r7 = 56
L02056284:
    r0 = r7.b0 (s)
    call L02055ee4
    r0 = 0
    call L02056084
    r1 = r7
    ifs (r0 >= r4) {
    r1_r0 = r5_r4
    }
    r6 += -1
    r2 = r6.l (u)
    r7 += 1  ; @add.ri.u5
    r5_r4 = r1_r0
    if (r2 != 0) goto L02056284
    r0 = r1.b0 (s)
    call L02055ee4
    r0 = 0
    r7 = 0
    call L02055f08
    r0 = 0
    call L02056084
    r4 = r0
    r5 = 401
    r6 = 56
L020562be:
    r0 = r6.b0 (s)
    call L02055f08
    r0 = 0
    call L02056084
    r1 = r6
    ifs (r0 >= r4) {
    r0 = r4
    r1 = r7
    }
    r5 += -1
    r2 = r5.l (u)
    r6 += 1  ; @add.ri.u5
    r7 = r1
    r4 = r0
    if (r2 != 0) goto L020562be
    r0 = r1.b0 (s)
    call L02055f08
    r0 = 19
    r1 = 60
    call L02055a7e
    r0 = 1023
    call L02055e50
    r0 = 1023
    call L02055e74
    r0 = 0
    r8 = 0
    call L02056084
    r6 = r0
    r4 = 1446
    r7 = 89
    r5 = 600
L02056312:
    r0 = r5 + -1023
    ifs (r0 <= -1) goto L02056326
    r0 = 1023
    call L02055e50
    r0 = r4
    goto L02056330
L02056326:
    r0 = r5
    call L02055e50
    r0 = 1023
L02056330:
    call L02055e74
    r0 = 0
    call L02056084
    r1 = r7
    ifs (r0 >= r6) {
    r0 = r6
    r1 = r8
    }
    r5 += 1  ; @add.ri.u5
    r4 += -1
    r7 += 1  ; @add.ri.u5
    r8 = r1
    r6 = r0
    if (r4 != 599) goto L02056312
    r4 = r1.b0 (s)
    if ((r1 & 128) != 0) goto L02056370
    r0 = 1023
    r5 = r0
    call L02055e50
    r0 = r5 - r4
    call L02055e74
    r8 = 1
    goto L02056382
L02056370:
    r0 = r4 + 1023
    call L02055e50
    r0 = 1023
    call L02055e74
    r8 = 0
L02056382:
    r0 = 0
    r7 = 0
    call L02055e9a
    r0 = 0
    call L02055ec0
    r0 = 0
    call L02056084
    r5 = r0
    r4 = -200
    r6 = 56
L0205639e:
    if (r8 == 0) goto L020563aa
    r0 = r4
    call L02055ec0
    goto L020563b0
L020563aa:
    r0 = r4
    call L02055e9a
L020563b0:
    r0 = 0
    call L02056084
    r1 = r6
    ifs (r0 >= r5) {
    r0 = r5
    r1 = r7
    }
    r4 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
    r7 = r1
    r5 = r0
    if (r4 != 201) goto L0205639e
    r0 = r1.b0 (s)
    if (r8 == 0) goto L020563d8
    call L02055ec0
    {pc, r8-r4} = [sp++]
L020563d8:
    call L02055e9a
    {pc, r8-r4} = [sp++]
L020563de:
    r0 = 71956
    [r0+0] &= 0xFFFFFFF8
    [r0+0] &= 0xFFFFFFF7
    [r0+0] &= 0xFFFFFFEF
    rts
L020563f2:
    r1 = 71944
    ifs (r0 < 0) goto L0205640c
    r2 = [r1+0]
    r2 <= insert(r0, p:7, l:9)
    [r1+0] = r2
    [r1+0] |= 0x10000
    r0 |= 512
    goto L0205641c
L0205640c:
    r0 = 0x0 - r0  #
    r2 = [r1+0]
    r2 <= insert(r0, p:7, l:9)
    [r1+0] = r2
    [r1+0] &= 0xFFFEFFFF
L0205641c:
    r0 = r0.l (s)
    rts
L02056420:
    [--sp] = {rets, r4}
    r1 = 71944
    ifs (r0 < 0) goto L0205643c
    r2 = [r1+0]
    r2 <= insert(r0, p:17, l:9)
    [r1+0] = r2
    [r1+0] |= 0x4000000
    r0 |= 512
    goto L0205645a
L0205643c:
    r0 = 0x0 - r0
    r3 = 511  #
    r2 = [r1+0]
    r3 &= r0
    r4 = 4227989503
    r2 &= r4
    r2 <= insert(r3, p:17, l:9)
    [r1+0] = r2
    [r1+0] &= 0xFBFFFFFF
L0205645a:
    r0 = r0.l (s)
    {pc, r4} = [sp++]
L0205645e:
    [--sp] = {rets, r14-r4}
    call L02055a2a
    r0 = 21
    r1 = 0
    r12 = 0
    call L02055a66
    r0 = 20
    r1 = 0
    call L02055a66
    call L02055de0
    call L02055e1e
    r0 = 0
    r1 = 3
    call L02055a4e
    r0 = 95
    r1 = 16
    call L02055a4e
    r0 = 0
    r1 = 62
    call L02055a7e
    r0 = 27
    r1 = 56
    call L02055a7e
    r0 = 8
    r1 = 192
    call L02055a7e
    r0 = 19
    r1 = 0
    call L02055a7e
    r0 = 20
    r1 = 56
    call L02055a7e
    r0 = 20
    r1 = 52
    call L02055a7e
    r0 = 40
    call L02055f56
    r11 = 71948
    r8 = L01c26890
    r9 = 954
    r10 = 955
L020564d8:
    r0 = uextra(r12, p:0, l:16)
    if (r0 == 1) goto L020564e8
    if (r0 != 0) goto L02056502
    [r11+0] &= 0xFFFFFF3F
    goto L020564f6
L020564e8:
    r0 = [r11+0]
    r0 = r0 & 0xFFFFFF3F
    r0 |= 64
    [r11+0] = r0
L020564f6:
    r0 = [r11+4]
    r1 = r0 & 0xFFFFF0FF
    r0 = 127
    goto L0205652a
L02056502:
    r0 = [r11+0]
    r0 = r0 & 0xFFFFFF3F
    r0 |= 64
    [r11+0] = r0
    r0 = [r11+4]
    r1 = r0 & 0xFFFFF0FF
    if (r12 != 2) {  ; @if.ne.ri.s12
    r0 = 14
    r2 = 2304
    } else {
    r0 = 69
    r2 = 768
    }
    r1 |= r2
L0205652a:
    [r11+4] = r1
    r1 = [r11+4]
    r1 = r1 & 0xFFFFFF80
    r0 |= r1
    [r11+4] = r0
    r0 = 0
    r14 = 0
    call L020563f2
    r0 = 0
    call L02056420
    r4 = 256
    r6 = 12
    r7 = 0
L02056552:
    r0 = 1
    call L02056084
    ifs (r14 < -509) goto L02056568
    ifs (r0 < 1) goto L02056568
    r0 = r4.l (s)
    r14 = r14 - r0
    goto L02056574
L02056568:
    ifs (r14 > 509) goto L02056574
    ifs (r0 <= -1) {  ; @ifs.le.ri.s12
    r0 = r4.l (s)
    r14 += r0
    }
L02056574:
    r13 = sextra(r14, p:0, l:16)
    r0 = r13
    call L020563f2
    r0 = 2
    call L02056084
    ifs (r7 < -509) goto L02056592
    ifs (r0 < 1) goto L02056592
    r0 = r4.l (s)
    r7 = r7 - r0
    goto L0205659e
L02056592:
    ifs (r7 > 509) goto L0205659e
    ifs (r0 <= -1) {  ; @ifs.le.ri.s12
    r0 = r4.l (s)
    r7 += r0  ; @add.rr
    }
L0205659e:
    r5 = r7.l (s)
    r0 = r5
    call L02056420
    r0 = r4.l (s)
    r4 = r0 >>> 1
    ifs (r0 <= 1) {  ; @ifs.le.ri.s12
    r4 = 1
    }
    r6 += -1
    r0 = r6.l (u)
    if (r0 != 0) goto L02056552
    r0 = r12 << 2
    r4 = r0 + r8
    r0 = r13
    call L020563f2
    h[r4+r9<<1] = r0
    r0 = r5
    call L02056420
    r12 = r12 + 1
    h[r4+r10<<1] = r0
    if (r12 != 4) goto L020564d8
    {pc, r14-r4} = [sp++]
L020565dc:
    r0 = 71956
    r1 = [r0+0]
    r1 = r1 & 0xFFFFFFF8
    r1 |= 1
    [r0+0] = r1
    [r0+0] |= 0x8
    [r0+0] |= 0x10
    rts
L020565f6:
    [--sp] = rets
    r1 = r0
    r0 = 9
    call L02055a7e
    pc = [sp++]
L02056602:
    [--sp] = rets
    r1 = r0
    r0 = 11
    call L02055a7e
    pc = [sp++]
L0205660e:
    [--sp] = rets
    r1 = r0.b0 (u)
    r0 = 10
    call L02055a7e
    pc = [sp++]
L0205661a:
    [--sp] = rets
    r1 = r0.b0 (u)
    r0 = 12
    call L02055a7e
    pc = [sp++]
L02056626:
    [--sp] = {rets, r9-r4}
    call L02055a2a
    r0 = 21
    r1 = 0
    r8 = 0
    call L02055a66
    r0 = 20
    r1 = 0
    call L02055a66
    call L02055de0
    call L02055e1e
    r0 = 0
    r1 = 3
    call L02055a4e
    r0 = 95
    r1 = 16
    call L02055a4e
    r0 = 1
    r1 = 20
    call L02055a4e
    r0 = 2
    r1 = 0
    call L02055a4e
    r0 = 3
    r1 = 17
    call L02055a4e
    r0 = 255
    call L020565f6
    r0 = 255
    call L02056602
    r0 = 0
    call L0205660e
    r0 = 0
    call L0205661a
    r0 = 0
    r1 = 62
    call L02055a7e
    r0 = 20
    r1 = 56
    call L02055a7e
    r0 = 20
    r1 = 4
    call L02055a7e
    r0 = 19
    r1 = 30
    call L02055a7e
    call L02056054
    r0 = 255
    call L020565f6
    r0 = 255
    call L02056602
    r0 = 3
    call L02056084
    r4 = r0
    r6 = -105
    r7 = 104
    r9 = 150
L020566bc:
    ifs (r6 <= -1) goto L020566c8
    r0 = 255
    call L020565f6
    r0 = r7.b0 (u)
    goto L020566d0
L020566c8:
    r0 = uextra(r9, p:0, l:8)
    call L020565f6
    r0 = 255
L020566d0:
    call L02056602
    r0 = 3
    call L02056084
    r9 = r9 + 1
    r5 = r9
    ifs (r0 >= r4) {
    r0 = r4
    r5 = r8
    }
    r6 += 1  ; @add.ri.u5
    r7 += -1
    r8 = r5
    r4 = r0
    if (r6 != 106) goto L020566bc
    if ((r5 & 128) != 0) goto L0205670c
    r0 = 255
    r4 = 255
    call L020565f6
    r0 = r4 & ~r5
    call L02056602
    r8 = 1
    goto L0205671e
L0205670c:
    r0 = r5 + -1
    r0 = r0.b0 (u)
    call L020565f6
    r0 = 255
    call L02056602
    r8 = 0
L0205671e:
    r0 = 0
    r6 = 0
    call L0205660e
    r0 = 0
    call L0205661a
    r0 = 3
    call L02056084
    r4 = r0
    r7 = 101
    r5 = 206
L02056738:
    if (r8 == 0) goto L02056744
    r0 = r5.b0 (s)
    call L0205661a
    goto L0205674a
L02056744:
    r0 = r5.b0 (s)
    call L0205660e
L0205674a:
    r0 = 3
    call L02056084
    r1 = r5
    ifs (r0 >= r4) {
    r0 = r4
    r1 = r6
    }
    r7 += -1
    r2 = r7.l (u)
    r5 += 1  ; @add.ri.u5
    r6 = r1
    r4 = r0
    if (r2 != 0) goto L02056738
    if (r8 == 0) goto L02056772
    r0 = r1.b0 (s)
    call L0205661a
    {pc, r9-r4} = [sp++]
L02056772:
    r0 = r1.b0 (s)
    call L0205660e
    {pc, r9-r4} = [sp++]
