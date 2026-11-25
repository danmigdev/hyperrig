; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_stage: 2 functions, 0x01c055d2..0x01c05860

; dsp_stage_active: 0x01c055d2..0x01c05618, module dsp-stage (active)
.type dsp_stage_active,@function
dsp_stage_active:
    [--sp] = {rets, r4}
    r3 = b[r0+0] (u)
    if (r3 != 25) goto L01c055ea
    r1 = 420
    r1 = b[r0+r1] (u)
    r0 = 1
    if (r1 == 0) goto L01c05612
    r0 = 0
    {pc, r4} = [sp++]
L01c055ea:
    r1 = effect_stage_capabilities
    r1 = b[r3+r1] (u)
    r4 = r1 >> 5
    if (r4 == 0) goto L01c05614
    r1 = 1
    r2 = 1
    if (r3 != 14) {
    r2 = 0
    }
    r0 += 70
    r0 = h[r0+r4<<1] (u)
    if (r0 == 0) goto L01c0560c
    r1 = 0
L01c0560c:
    r0 = r2 ^ r1
    r0 ^= 1
L01c05612:
    {pc, r4} = [sp++]
L01c05614:
    r0 = 0
    {pc, r4} = [sp++]

; dsp_stage_route_mask: 0x01c05618..0x01c05860, module dsp-stage (route_mask)
.type dsp_stage_route_mask,@function
dsp_stage_route_mask:
    [--sp] = {rets, r15-r4}
    sp += -44
    r10 = r1  #
    [sp+4] = r3
    r11 = r0  #
    [sp+8] = r2
    r0 = 0
    b[sp+32] = r0
    r6 = L01c32db0
    r5 = L01c2c220
    r13 = effect_stage_capabilities
    r14 = 0  #
    [sp+16] = r0
    ifs (r11 < 1) goto L01c056be
    r15 = 0  #
    [sp+16] = r0
    r4 = 358
    r9 = 1
    r8 = 0
L01c05652:
    r0 = r8 + r6
    r0 = b[r0+r4] (u)
    r0 = r0 * 0x1E0
    r7 = r0 + r5
    r1 = b[r7+2] (u)
    r2 = sp + 32
    r2 += r8  #
    r0 = b[r7+4] (u)
    b[r2+1] = r0
    b[r2+2] = r15
    if (r1 == 0) goto L01c05680
    r0 = b[r7+1] (u)
    if (r0 != 0) goto L01c0568a
    r0 = h[r7+8] (u)
    if (r0 != 0) goto L01c0568a
    if (r10 == 0) goto L01c05680
    r0 = b[r7+10] (u)
    if (r0 != 0) goto L01c0568a
L01c05680:
    r8 = r8 + 1
    ifs (r8 < r11) goto L01c05652
    goto L01c056be
L01c0568a:
    r0 = r7
    call dsp_stage_active
    r1 = r0
    r0 = r7
    call dsp_stage_capability
    if (r0 == 0) goto L01c056a2
    r1 = b[r7+0] (u)
    r1 = b[r1+r13] (u)
    if ((r1 & 16) == 0) goto L01c056a6
L01c056a2:
    r14 = r14 | (1 << r8)
L01c056a6:
    r1 = r9 << r8
    r8 = r8 + 1
    if (r0 != 1) {
    r1 = 0
    }
    r0 = [sp+16]
    r0 |= r1
    [sp+16] = r0
    ifs (r8 < r11) goto L01c05652
L01c056be:
    r0 = L01c33320
    r1 = b[r0+40] (u)
    r2 = b[r0+84] (u)
    r3 = b[r0+128] (u)
    r4 = b[r0+172] (u)
    r0 = b[r0+216] (u)
    r1 |= r2
    r1 |= r3
    r1 |= r4
    r0 |= r1
    r7 = 1
    if ((r0 & 0xFF) != 0) {
    r7 = 0
    }
    [sp+20] = r7
    r8 = [sp+8]
    if (r8 == 0) goto L01c05734
    r4 = r8
    goto L01c056fe
L01c056f4:
    if (r10 == 0) goto L01c0572a
    r0 = b[r5+10] (u)
    if (r0 != 0) goto L01c0570e
    goto L01c0572a
L01c056fe:
    if ((r4 & 1) == 0) goto L01c0572a
    r0 = b[r5+2] (u)
    if (r0 == 0) goto L01c0572a
    r0 = b[r5+1] (u)
    if (r0 != 0) goto L01c0570e
    r0 = h[r5+8] (u)
    if (r0 == 0) goto L01c056f4
L01c0570e:
    r0 = b[r5+0] (u)
    r0 = b[r0+r13] (u)
    if ((r0 & 16) != 0) goto L01c05728
    r0 = r5
    call dsp_stage_active
    r1 = r0
    r0 = r5
    call dsp_stage_capability
    if (r0 != 0) goto L01c0572a
L01c05728:
    r7 = 0
L01c0572a:
    r4 = r4 >> 1
    r5 = r5 + 480
    if (r4 != 0) goto L01c056fe
    [sp+20] = r7
L01c05734:
    if (r7 == 0) goto L01c05738
    r7 = r8
L01c05738:
    r0 = r11 + -1
    ifs (r0 < 0) goto L01c05794
    r1 = sp + 20
    r2 = 0
    r3 = 358
L01c05748:
    r4 = sp + 32
    r4 = r4 + r0
    r4 = b[r4+1] (u)
    if (r4 == 0) goto L01c0575e
    r5 = sp + 32
    r5 = r5 + r0
    r5 = b[r5+2] (u)
    if (r5 != 0) goto L01c0575e
    r5 = [sp+20]
    [r1+8] = r5
    [r1+4] = r5
L01c0575e:
    r5 = sp + 20
    r5 = [r5+r4<<2]
    if (r5 == 0) goto L01c05770
    r5 = r0 + r6
    r5 = b[r5+r3] (u)
    r7 = r7 | (1 << r5)
L01c05770:
    r5 = r14 & (1 << r0)
    if (r5 == 0) goto L01c0577c
    r5 = sp + 20
    [r5+r4<<2] = r2
L01c0577c:
    if (r4 == 0) goto L01c0578e
    r4 = sp + 32
    r4 = b[r4+r0] (u)
    if (r4 != 0) goto L01c0578e
    r4 = [r1+4]
    r5 = [r1+8]
    r4 |= r5
    [sp+20] = r4
L01c0578e:
    r0 += -1
    ifs (r0 > -1) goto L01c05748
L01c05794:
    r3 = 0
    [sp+20] = r3
    r0 = 0
    ifs (r11 < 1) goto L01c0584e
    r15 = sp + 20
    r2 = 1
    r13 = 358
    r5_r4 = 0
    r12 = r6
L01c057ac:
    r1 = r4 + 16
    r1 = r2 << r1  #
    [sp] = r4
    [sp+12] = r1
L01c057b6:
    r1 = r5 + r6
    r3 = sp + 32
    r3 = r3 + r5
    r4 = b[r3+1] (u)
    r3 = b[r1+r13] (u)
    if (r4 == 0) goto L01c057dc
    r1 = sp + 32
    r1 = b[r1+r5] (u)
    if (r1 != 0) goto L01c057dc
    r1 = [sp+20]
    [r15+8] = r1
    [r15+4] = r1
    if (r1 == 0) goto L01c057da
    r1 = [sp+12]
L01c057da:
    r0 |= r1
L01c057dc:
    r1 = sp + 20
    r1 = [r1+r4<<2]
    r10 = r2 << r3
    r3 = r5 + 1
    r8 = r2 << r5
    if (r1 == 0) goto L01c057f0
    r1 = r10
L01c057f0:
    r6 = [sp+16]
    if ((r8 & r6) == 0) goto L01c05802
    r9 = 1
    if ((r10 & r7) == 0) {
    r9 = 0
    }
    goto L01c05808
L01c05802:
    r9 = 0
    if ((r8 & r14) == 0) goto L01c0580e
L01c05808:
    r6 = sp + 20
    [r6+r4<<2] = r9
L01c0580e:
    r0 |= r1
    if (r4 == 0) goto L01c0581a
    r1 = sp + 32
    r1 = r1 + r5
    r1 = b[r1+2] (u)
    if (r1 == 0) goto L01c05824
L01c0581a:
    r5 = r3
    r6 = r12
    ifs (r3 < r11) goto L01c057b6
    goto L01c0584c
L01c05824:
    r1 = [r15+4]
    r3 = [r15+8]
    r3 |= r1
    [sp+20] = r3
    r5 = r5 + 1
    if (r3 != 0) {
    r4 = [sp]
    r1 = r4 + 24
    r0 = r0 | (1 << r1)
    r6 = r12
    } else {
    r6 = r12
    r4 = [sp]
    }
    r4 = r4 + 1
    ifs (r5 < r11) goto L01c057ac
    goto L01c0584e
L01c0584c:
    r3 = [sp+20]
L01c0584e:
    r1 = [sp+8]
    if (r3 != 0) goto L01c05854
    r1 = r3
L01c05854:
    r0 |= r1  #
    r1 = [sp+4]
    r0 = r7  #
    [r1+0] = r0
    sp += 44
    {pc, r15-r4} = [sp++]
