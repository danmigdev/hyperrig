; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; line_mixers: 2 functions, 0x01c1dd46..0x01c1e3de

; line_mixers_line_mix: 0x01c1dd46..0x01c1e086, module line-mixers (line_mix)
.type line_mixers_line_mix,@function
line_mixers_line_mix:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r14 = r6 & 0x1
    if (r14 == 0) goto L01c1de12
    r8 = [r4+0]
    r9 = [r4+256]
    r10 = [r4+512]
    r11 = [r4+768]
    r0 = r8 + r9
    r1 = r8 - r9
    r2 = r10 + r11
    r3 = r10 - r11
    r8 = r0 + r2
    r9 = r0 - r2
    r10 = r1 + r3
    r11 = r1 - r3
    r3 = r4 + 1024
    r12 = [r3+0]
    r13 = [r3+256]
    r14 = [r3+512]
    r15 = [r3+768]
    r0 = r12 + r13
    r1 = r12 - r13
    r2 = r14 + r15
    r7 = r14 - r15
    r12 = r0 + r2
    r13 = r0 - r2
    r14 = r1 + r7
    r15 = r1 - r7
    r7 = [r5+0]
    r0 = r8 + r12
    r1 = r8 - r12
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+0] = r0
    [r3+0] = r1
    r0 = r10 + r14
    r1 = r10 - r14
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+256] = r0
    [r3+256] = r1
    [r5+0] = r0
    r0 = r9 + r13
    r1 = r9 - r13
    r0 = r0 - r7
    r1 = r1 + r7
    [r4+512] = r0
    [r3+512] = r1
    r0 = r11 + r15
    r1 = r11 - r15
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+768] = r0
    [r3+768] = r1
    r4 = r4 + 4
    r5 = r5 + 4
L01c1de12:
    r6 = r6 >> 1
    if (r6 == 0) goto L01c1df88
L01c1de18:
    r8 = [r4+0]
    r9 = [r4+256]
    r10 = [r4+512]
    r11 = [r4+768]
    r0 = r8 + r9
    r1 = r8 - r9
    r2 = r10 + r11
    r3 = r10 - r11
    r8 = r0 + r2
    r9 = r0 - r2
    r10 = r1 + r3
    r11 = r1 - r3
    r3 = r4 + 1024
    r12 = [r3+0]
    r13 = [r3+256]
    r14 = [r3+512]
    r15 = [r3+768]
    r0 = r12 + r13
    r1 = r12 - r13
    r2 = r14 + r15
    r7 = r14 - r15
    r12 = r0 + r2
    r13 = r0 - r2
    r14 = r1 + r7
    r15 = r1 - r7
    r7 = [r5+0]
    r0 = r8 + r12
    r1 = r8 - r12
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+0] = r0
    [r3+0] = r1
    r0 = r10 + r14
    r1 = r10 - r14
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+256] = r0
    [r3+256] = r1
    [r5+0] = r0
    r0 = r9 + r13
    r1 = r9 - r13
    r0 = r0 - r7
    r1 = r1 + r7
    [r4+512] = r0
    [r3+512] = r1
    r0 = r11 + r15
    r1 = r11 - r15
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+768] = r0
    [r3+768] = r1
    r8 = [r4+4]
    r9 = [r4+260]
    r10 = [r4+516]
    r11 = [r4+772]
    r0 = r8 + r9
    r1 = r8 - r9
    r2 = r10 + r11
    r3 = r10 - r11
    r8 = r0 + r2
    r9 = r0 - r2
    r10 = r1 + r3
    r11 = r1 - r3
    r3 = r4 + 1024
    r12 = [r3+4]
    r13 = [r3+260]
    r14 = [r3+516]
    r15 = [r3+772]
    r0 = r12 + r13
    r1 = r12 - r13
    r2 = r14 + r15
    r7 = r14 - r15
    r12 = r0 + r2
    r13 = r0 - r2
    r14 = r1 + r7
    r15 = r1 - r7
    r7 = [r5+4]
    r0 = r8 + r12
    r1 = r8 - r12
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+4] = r0
    [r3+4] = r1
    r0 = r10 + r14
    r1 = r10 - r14
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+260] = r0
    [r3+260] = r1
    [r5+4] = r0
    r0 = r9 + r13
    r1 = r9 - r13
    r0 = r0 - r7
    r1 = r1 + r7
    [r4+516] = r0
    [r3+516] = r1
    r0 = r11 + r15
    r1 = r11 - r15
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+772] = r0
    [r3+772] = r1
    r4 = r4 + 8
    r5 = r5 + 8
    if (--r6 != 0) goto L01c1de18
L01c1df88:
    r0 = [sp]
    r5 = [r0+4]
    r6 = [r0+8]
    r10 = [r0+12]
    r8 = [r0+16]
    r9 = [r0+20]
    r13 = [r0+24]
    r14 = [r0+28]
    r11 = 2147483649
    r15 = 0
    r12 = r6 & 0x1
    if (r12 == 0) goto L01c1dfe0
    r7 = [r5+0]
    r1_r0 = r9 * r10 (s)
    r12 = r1 >>> 31
    r1_r0 += r12 * r11 (s)
    r1_r0 >>>= 31
    r12 = r7 - r8
    r8 = r7
    r9 = r0 + r12
    r13 += r14
    r3_r2 = r9 * r13 (s)
    r3_r2 >>>= 16
    r4 = r2 >>> 31
    if (r3 != r4) goto L01c1e046
L01c1dfde:
    [r5++=4] = r2
L01c1dfe0:
    r6 = r6 >> 1
    if (r6 == 0) goto L01c1e044
L01c1dfe4:
    r7 = [r5+0]
    r1_r0 = r9 * r10 (s)
    r12 = r1 >>> 31
    r1_r0 += r12 * r11 (s)
    r1_r0 >>>= 31
    r12 = r7 - r8
    r8 = r7
    r9 = r0 + r12
    r13 += r14
    r3_r2 = r9 * r13 (s)
    r3_r2 >>>= 16
    r4 = r2 >>> 31
    if (r3 != r4) goto L01c1e056
L01c1e010:
    [r5++=4] = r2
    r7 = [r5+0]
    r1_r0 = r9 * r10 (s)
    r12 = r1 >>> 31
    r1_r0 += r12 * r11 (s)
    r1_r0 >>>= 31
    r12 = r7 - r8
    r8 = r7
    r9 = r0 + r12
    r13 += r14
    r3_r2 = r9 * r13 (s)
    r3_r2 >>>= 16
    r4 = r2 >>> 31
    if (r3 != r4) goto L01c1e066
L01c1e03e:
    [r5++=4] = r2
    if (--r6 != 0) goto L01c1dfe4
L01c1e044:
    goto L01c1e076
L01c1e046:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1dfde
L01c1e056:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e010
L01c1e066:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e03e
L01c1e076:
    r0 = [sp]
    [r0+16] = r8
    [r0+20] = r9
    r0 = r15
    sp += 4
    {pc, r15-r4} = [sp++]

; line_mixers_line_mix_peak: 0x01c1e086..0x01c1e3de, module line-mixers (line_mix_peak)
.type line_mixers_line_mix_peak,@function
line_mixers_line_mix_peak:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r14 = r6 & 0x1
    if (r14 == 0) goto L01c1e152
    r8 = [r4+0]
    r9 = [r4+256]
    r10 = [r4+512]
    r11 = [r4+768]
    r0 = r8 + r9
    r1 = r8 - r9
    r2 = r10 + r11
    r3 = r10 - r11
    r8 = r0 + r2
    r9 = r0 - r2
    r10 = r1 + r3
    r11 = r1 - r3
    r3 = r4 + 1024
    r12 = [r3+0]
    r13 = [r3+256]
    r14 = [r3+512]
    r15 = [r3+768]
    r0 = r12 + r13
    r1 = r12 - r13
    r2 = r14 + r15
    r7 = r14 - r15
    r12 = r0 + r2
    r13 = r0 - r2
    r14 = r1 + r7
    r15 = r1 - r7
    r7 = [r5+0]
    r0 = r8 + r12
    r1 = r8 - r12
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+0] = r0
    [r3+0] = r1
    r0 = r10 + r14
    r1 = r10 - r14
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+256] = r0
    [r3+256] = r1
    [r5+0] = r0
    r0 = r9 + r13
    r1 = r9 - r13
    r0 = r0 - r7
    r1 = r1 + r7
    [r4+512] = r0
    [r3+512] = r1
    r0 = r11 + r15
    r1 = r11 - r15
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+768] = r0
    [r3+768] = r1
    r4 = r4 + 4
    r5 = r5 + 4
L01c1e152:
    r6 = r6 >> 1
    if (r6 == 0) goto L01c1e2c8
L01c1e158:
    r8 = [r4+0]
    r9 = [r4+256]
    r10 = [r4+512]
    r11 = [r4+768]
    r0 = r8 + r9
    r1 = r8 - r9
    r2 = r10 + r11
    r3 = r10 - r11
    r8 = r0 + r2
    r9 = r0 - r2
    r10 = r1 + r3
    r11 = r1 - r3
    r3 = r4 + 1024
    r12 = [r3+0]
    r13 = [r3+256]
    r14 = [r3+512]
    r15 = [r3+768]
    r0 = r12 + r13
    r1 = r12 - r13
    r2 = r14 + r15
    r7 = r14 - r15
    r12 = r0 + r2
    r13 = r0 - r2
    r14 = r1 + r7
    r15 = r1 - r7
    r7 = [r5+0]
    r0 = r8 + r12
    r1 = r8 - r12
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+0] = r0
    [r3+0] = r1
    r0 = r10 + r14
    r1 = r10 - r14
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+256] = r0
    [r3+256] = r1
    [r5+0] = r0
    r0 = r9 + r13
    r1 = r9 - r13
    r0 = r0 - r7
    r1 = r1 + r7
    [r4+512] = r0
    [r3+512] = r1
    r0 = r11 + r15
    r1 = r11 - r15
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+768] = r0
    [r3+768] = r1
    r8 = [r4+4]
    r9 = [r4+260]
    r10 = [r4+516]
    r11 = [r4+772]
    r0 = r8 + r9
    r1 = r8 - r9
    r2 = r10 + r11
    r3 = r10 - r11
    r8 = r0 + r2
    r9 = r0 - r2
    r10 = r1 + r3
    r11 = r1 - r3
    r3 = r4 + 1024
    r12 = [r3+4]
    r13 = [r3+260]
    r14 = [r3+516]
    r15 = [r3+772]
    r0 = r12 + r13
    r1 = r12 - r13
    r2 = r14 + r15
    r7 = r14 - r15
    r12 = r0 + r2
    r13 = r0 - r2
    r14 = r1 + r7
    r15 = r1 - r7
    r7 = [r5+4]
    r0 = r8 + r12
    r1 = r8 - r12
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+4] = r0
    [r3+4] = r1
    r0 = r10 + r14
    r1 = r10 - r14
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+260] = r0
    [r3+260] = r1
    [r5+4] = r0
    r0 = r9 + r13
    r1 = r9 - r13
    r0 = r0 - r7
    r1 = r1 + r7
    [r4+516] = r0
    [r3+516] = r1
    r0 = r11 + r15
    r1 = r11 - r15
    r0 = r0 + r7
    r1 = r1 - r7
    [r4+772] = r0
    [r3+772] = r1
    r4 = r4 + 8
    r5 = r5 + 8
    if (--r6 != 0) goto L01c1e158
L01c1e2c8:
    r0 = [sp]
    r5 = [r0+4]
    r6 = [r0+8]
    r10 = [r0+12]
    r8 = [r0+16]
    r9 = [r0+20]
    r13 = [r0+24]
    r14 = [r0+28]
    r11 = 2147483649
    r15 = 0
    r12 = r6 & 0x1
    if (r12 == 0) goto L01c1e328
    r7 = [r5+0]
    r1_r0 = r9 * r10 (s)
    r12 = r1 >>> 31
    r1_r0 += r12 * r11 (s)
    r1_r0 >>>= 31
    r12 = r7 - r8
    r8 = r7
    r9 = r0 + r12
    r13 += r14
    r3_r2 = r9 * r13 (s)
    r3_r2 >>>= 16
    r4 = r2 >>> 31
    if (r3 != r4) goto L01c1e39e
L01c1e31e:
    [r5++=4] = r2
    r4 = r2 >>> 31
    r4 ^= r2
    r15 = r15 | r4
L01c1e328:
    r6 = r6 >> 1
    if (r6 == 0) goto L01c1e39c
L01c1e32c:
    r7 = [r5+0]
    r1_r0 = r9 * r10 (s)
    r12 = r1 >>> 31
    r1_r0 += r12 * r11 (s)
    r1_r0 >>>= 31
    r12 = r7 - r8
    r8 = r7
    r9 = r0 + r12
    r13 += r14
    r3_r2 = r9 * r13 (s)
    r3_r2 >>>= 16
    r4 = r2 >>> 31
    if (r3 != r4) goto L01c1e3ae
L01c1e358:
    [r5++=4] = r2
    r4 = r2 >>> 31
    r4 ^= r2
    r15 = r15 | r4
    r7 = [r5+0]
    r1_r0 = r9 * r10 (s)
    r12 = r1 >>> 31
    r1_r0 += r12 * r11 (s)
    r1_r0 >>>= 31
    r12 = r7 - r8
    r8 = r7
    r9 = r0 + r12
    r13 += r14
    r3_r2 = r9 * r13 (s)
    r3_r2 >>>= 16
    r4 = r2 >>> 31
    if (r3 != r4) goto L01c1e3be
L01c1e38e:
    [r5++=4] = r2
    r4 = r2 >>> 31
    r4 ^= r2
    r15 = r15 | r4
    if (--r6 != 0) goto L01c1e32c
L01c1e39c:
    goto L01c1e3ce
L01c1e39e:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e31e
L01c1e3ae:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e358
L01c1e3be:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e38e
L01c1e3ce:
    r0 = [sp]
    [r0+16] = r8
    [r0+20] = r9
    r0 = r15
    sp += 4
    {pc, r15-r4} = [sp++]
