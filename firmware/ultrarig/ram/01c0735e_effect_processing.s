; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 3 functions, 0x01c0735e..0x01c0767e

; effect_processing_warning: 0x01c0735e..0x01c07400, module effect-processing (warning)
.type effect_processing_warning,@function
effect_processing_warning:
    [--sp] = {rets, r8-r4}
    r8 = r0 + 44
    r4 = b[r8+1] (u)
    r5 = b[r8+0] (u)
    r6 = L01c32db0
    r6 = [r6+92]
    if (r5 == 0) goto L01c07388
    r7 = r0
    r3 = [++r7=40]
    r3 = r6 - r3
    if (r3 >= 1126) goto L01c0738c
    goto L01c07390
L01c07388:
    r7 = r0 + 40
L01c0738c:
    r5_r4 = 0  #
    [r7+0] = r6
L01c07390:
    r6 = 1
    if (r2 != 0) goto L01c07396
    r6 = r2
L01c07396:
    r4 = r4 + r6
    if (r2 == 0) goto L01c073b0
    if (r4 < 2) goto L01c073b0
    r3 = L01c343d8
    r3 = [r3+r1<<2]
    r6 = [r0+32]
    r3 = umax(r3, r6)
    [r0+36] = r3
L01c073b0:
    r3 = b[r0+1] (u)
    r0 = r5 + 1
    if (r3 == 0) goto L01c073f0
    r5 = 1
    r6 = 1
    if (r4 != 2) {
    r6 = 0
    }
    if (r2 != 0) goto L01c073c4
    r5 = r2
L01c073c4:
    if ((r5 & r6) != 0) goto L01c073cc
    if (r0 < 8) goto L01c073f0
L01c073cc:
    r2 = L01c3443c
    r3 = [r2+0]
    if (r3 != 0) goto L01c073da
    r1 = r1 + 1
    [r2+0] = r1
L01c073da:
    r1 = L01c3442c
    r2 = [r1+0]
    r2 = r2 + 1
    [r1+0] = r2
    r1 = 1
    if (r0 <= 7) {
    r1 = r0
    }
    r0 = r1
L01c073f0:
    b[r8+0] = r0
    if (r4 >= 255) {
    r4 = 255
    }
    b[r8+1] = r4
    {pc, r8-r4} = [sp++]

; effect_processing_peak_fade: 0x01c07400..0x01c07588, module effect-processing (peak_fade)
.type effect_processing_peak_fade,@function
effect_processing_peak_fade:
    [--sp] = {rets, r15-r4}
    sp += -36
    r14 = r1
    if (r1 == 0) goto L01c07584
    [sp+24] = r2
    [sp+28] = r3
    r12 = [sp+88]
    r13 = [sp+92]
    r13_r12 <<= 4
    r4 = 0
    r8 = 0
    r9 = 0
L01c0741c:
    r1 = [r0+r4<<2]
    r10 = abs(r1)
    r11 = r10 >>> 31
    r1 = r10 - r8
    r5 = r11 - r9 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r1 |= r5
    if ((r1 & r6) == 0) {
    r11_r10 = r9_r8
    }
    r4 = r4 + 1
    r9_r8 = r11_r10
    if (r14 != r4) goto L01c0741c
    r1 = 3
    r3_r2 = r8 * r1 (u)
    r1 = r9 * 0x3
    r3 = r3 + r1
    r1 = r12 - r2
    r4 = r13 - r3 - !c
    r5 = psr
    r6 = sextra(r5, p:0, l:1)
    r5 = sextra(r5, p:3, l:1)
    r5 ^= r6
    r5 = ~r5
    r1 |= r4
    if ((r1 & r5) == 0) goto L01c07480
    r8 = [sp+24]
    r9 = [sp+28]
    goto L01c074a4
L01c07480:
    r1 = 0
    r2 = 0x0 - r2
    r3 = r1 - r3 - !c
    r1 = r12 - r2
    r1 = r13 - r3 - !c
    r1 = psr
    r4 = r1 >> 3
    r1 ^= r4
    r8 = [sp+24]
    r9 = [sp+28]
    if ((r1 & 0x1) == 0) {
    r3_r2 = r13_r12
    }
L01c074a4:
    r5 = r3 | r9
    [sp+16] = r2
    [sp+20] = r3
    r4 = r2 | r8
    r1 = r4 | r5
    if (r1 == 0) goto L01c07584
    r1 = 0x10000
    r3 = r1 / r14 (s)
    r4 = r14
    if (r4 >= 16) {
    r4 = 16
    }
    r1 = r1 / r4 (u)
    r11 = 0  #
    [sp+4] = r1
    r2 = 0
    r1 = r4
    [sp+32] = r14
    r6 = r3  #
    [sp+12] = r0
    [sp+8] = r1
L01c074da:
    r13_r12 = r6 * r6 (s)
    r13_r12 >>= 16
    r5_r4 = r12 * r6 (s)
    r5_r4 >>= 15
    r4 &= 4294967294
    r5 = -3
    r5 *= r12
    r4 = r4 + r5
    r4 = r4 + 0x10000
    r7 = r4 * r9
    r15_r14 = r4 * r8 (u)
    r7 += r15
    r5 = r4 >>> 31
    r4 = r5 * r8
    r15 = r7 + r4
    r7 = r2 + 1
    r15_r14 >>>= 16
    if (r7 > r1) goto L01c0756a
    r0 = r3  #
    r4 = [sp+4]
    r4 *= r7
    r1 = 0x10000 - r4
    r9_r8 = r1 * r1 (s)
    r9_r8 >>= 16
    r1 = r4 * r9
    r13_r12 = r4 * r8 (u)
    r1 += r13
    r5 = r4 >>> 31
    r3 = r5 * r8
    r13 = r1 + r3
    r13_r12 <<= 16
    r13_r12 >>>= 32
    r8 = [sp+16]
    r9 = [sp+20]
    r1 = r12 * r9
    r5_r4 = r12 * r8 (u)
    r1 = r1 + r5
    r3 = r13 * r8
    r8 = [sp+24]
    r9 = [sp+28]
    r5 = r1 + r3  #
    r1 = [sp+8]
    r3 = r0  #
    r0 = [sp+12]
    r5_r4 >>>= 16
    r14 += r4
    r15 = r15 + r5 + c
L01c0756a:
    r10 = [r0+r2<<2]
    r4 = r10 + r14
    r5 = r11 + r15 + c
    [r0+r2<<2] = r4
    r6 = r6 + r3
    r2 = r7
    r14 = [sp+32]
    if (r14 != r7) goto L01c074da
L01c07584:
    sp += 36
    {pc, r15-r4} = [sp++]

; effect_processing_automation: 0x01c07588..0x01c0767e, module effect-processing (automation)
.type effect_processing_automation,@function
effect_processing_automation:
    [--sp] = {rets, r15-r4}
    sp += -8
    r3 = b[r0+3] (u)
    if (r3 == 0) goto L01c0767a
    if (r2 == 0) {
    r4 = 3208642560
    } else {
    r4 = 0x3E800000
    }
    r5 = r0 + 288  #
    [sp+4] = r4
    r0 += 85
    r4 = 0x4 - r2
    r10 = 0x3 - r2  #
    [sp] = r4
    r8 = -1
L01c075b4:
    r13 = b[r0+-80] (u)
    r6 = [r1+r13<<2]
    r7 = b[r0+-40] (u)
    if (r7 == 2) goto L01c075e6
    if (r7 != 1) goto L01c075f4
    r7 = [r5+0]
    r14 = r7 >>> 2
    if (r2 == 0) goto L01c07656
    r4 = [sp]
    r15 = r14 * r4
    r12 = r7 & 0x3
    r11 = r12 * r4
    r7 = r11 >>> 2
    r15 += r7
    goto L01c0765c
L01c075e6:
    r7 = [r5+0]
    r4 = [sp+4]
    r7 = r4 * r7 (f)
    r14 = r6 + r7 (f)
    goto L01c0766e
L01c075f4:
    r6 = r7 + -3
    r6 = r6.b0 (u)
    if (r6 > 1) goto L01c07646
    if (r7 != 3) {
    r14 = -1
    r15 = r14 + 0x4000
    } else {
    r14 = -1
    r15 = r14 + 1024
    }
    r9 = r15  #
    r6 = b[r0+0] (u)
    r6 = [r1+r6<<2]
    ifs (r6 <= 1) {
    r6 = 1
    }
    r15_r14 = r9_r8 / r6 (u)
    r4 = 2147483647
    r6 = r14 - r4
    r4 = 0
    r6 = r15 - r4 - !c
    r6 = psr
    if ((r6 & 0x2) != 0) {
    r14 = 2147483647
    r15 = 0
    }
    goto L01c0766e
L01c07646:
    if (r7 != 5) goto L01c07672
    r6 = b[r0+0] (u)
    r6 = [r1+r6<<2]
    r14 = 0x0 - r6
    goto L01c0766e
L01c07656:
    r12 = r7 & 0x3
    r15 = 0
L01c0765c:
    r7 = r14 * r10
    r6 = r6 - r7
    r7 = r12 * r10
    r7 = r7 >>> 2
    r6 = r6 - r7
    r14 = r6 + r15
L01c0766e:
    [r1+r13<<2] = r14
L01c07672:
    r5 = r5 + 4
    r0 = r0 + 1
    if (--r3 != 0) goto L01c075b4
L01c0767a:
    sp += 8
    {pc, r15-r4} = [sp++]
