; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_stage: 2 functions, 0x01c1a14c..0x01c1a2c4

; dsp_stage_copy: 0x01c1a14c..0x01c1a182, module dsp-stage (copy)
.type dsp_stage_copy,@function
dsp_stage_copy:
    [--sp] = {r8-r4}
    r4 = r1
    r5 = r0
    r6 = r2
    r7 = r6 >> 2
    if (r7 == 0) goto L01c1a16c
L01c1a158:
    rep r7 {
    r0 = [r4++=4]
    r1 = [r4++=4]
    r2 = [r4++=4]
    r3 = [r4++=4]
    [r5++=4] = r0
    [r5++=4] = r1
    [r5++=4] = r2
    [r5++=4] = r3
    }
    if (r7 != 0) goto L01c1a158
L01c1a16c:
    r8 = r6 & 0x3
    if (r8 == 0) goto L01c1a17e
L01c1a174:
    rep r8 {
    r0 = [r4++=4]
    [r5++=4] = r0
    }
    if (r8 != 0) goto L01c1a174
L01c1a17e:
    {r8-r4} = [sp++]
    rts

; dsp_stage_mix: 0x01c1a182..0x01c1a2c4, module dsp-stage (mix)
.type dsp_stage_mix,@function
dsp_stage_mix:
    [--sp] = {r15-r4}
    r14 = r0
    r6 = [r14+0]
    r7 = [r14+4]
    r8 = [r14+8]
    r4 = [r14+20]
    r5 = [r14+24]
    r15 = 2
L01c1a19e:
    r9 = r8 & 0x3
    r8 = r8 >> 2
    if (r8 == 0) goto L01c1a22a
L01c1a1aa:
    r10 = [r6+0]
    r11 = [r7+0]
    r12 = [r6+4]
    r13 = [r7+4]
    r1_r0 = r10 * r4 (s)
    r3_r2 = r12 * r4 (s)
    r1_r0 += r11 * r5 (s)
    r3_r2 += r13 * r5 (s)
    r1_r0 >>>= 15
    r3_r2 >>>= 15
    r10 = r0 >>> 31
    r12 = r2 >>> 31
    if (r1 != r10) goto L01c1a266
L01c1a1de:
    [r6+0] = r0
    if (r3 != r12) goto L01c1a278
L01c1a1e4:
    [r6+4] = r2
    r10 = [r6+8]
    r11 = [r7+8]
    r12 = [r6+12]
    r13 = [r7+12]
    r1_r0 = r10 * r4 (s)
    r3_r2 = r12 * r4 (s)
    r1_r0 += r11 * r5 (s)
    r3_r2 += r13 * r5 (s)
    r1_r0 >>>= 15
    r3_r2 >>>= 15
    r10 = r0 >>> 31
    r12 = r2 >>> 31
    if (r1 != r10) goto L01c1a28a
L01c1a21a:
    [r6+8] = r0
    if (r3 != r12) goto L01c1a29c
L01c1a220:
    [r6+12] = r2
    r6 = r6 + 16
    r7 = r7 + 16
    if (--r8 != 0) goto L01c1a1aa
L01c1a22a:
    if (r9 == 0) goto L01c1a254
L01c1a22e:
    r10 = [r6+0]
    r11 = [r7+0]
    r1_r0 = r10 * r4 (s)
    r1_r0 += r11 * r5 (s)
    r1_r0 >>>= 15
    r12 = r0 >>> 31
    if (r1 != r12) goto L01c1a2ae
L01c1a24a:
    [r6+0] = r0
    r6 = r6 + 4
    r7 = r7 + 4
    if (--r9 != 0) goto L01c1a22e
L01c1a254:
    r15 = r15 + -1
    if (r15 == 0) goto L01c1a2c0
    r7 = [r14+12]
    r8 = [r14+16]
    goto L01c1a19e
L01c1a266:
    r11 = r1 >> 31
    r11 += r11
    r1 = 2147483647
    r11 += r1
    r0 = r11
    goto L01c1a1de
L01c1a278:
    r13 = r3 >> 31
    r13 += r13
    r3 = 2147483647
    r13 += r3
    r2 = r13
    goto L01c1a1e4
L01c1a28a:
    r11 = r1 >> 31
    r11 += r11
    r1 = 2147483647
    r11 += r1
    r0 = r11
    goto L01c1a21a
L01c1a29c:
    r13 = r3 >> 31
    r13 += r13
    r3 = 2147483647
    r13 += r3
    r2 = r13
    goto L01c1a220
L01c1a2ae:
    r13 = r1 >> 31
    r13 += r13
    r1 = 2147483647
    r13 += r1
    r0 = r13
    goto L01c1a24a
L01c1a2c0:
    {r15-r4} = [sp++]
    rts
