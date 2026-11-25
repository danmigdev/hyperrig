; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; resampling_kernels: 1 function, 0x01c1b582..0x01c1b6f4

; resampling_kernels_resample: 0x01c1b582..0x01c1b6f4, module resampling-kernels (resample)
.type resampling_kernels_resample,@function
resampling_kernels_resample:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
    r4 = [r0+0]
    r5 = [r0+4]
    r11 = [r0+8]
    r6 = [r0+12]
    r7 = [r0+16]
    r8 = [r0+20]
    r9 = [r0+24]
    r12 = [r0+28]
    r1 = [r0+32]
    r10 = 2147483649
    r2 = r12
    if (r1 == 0) goto L01c1b680
    r14 = r11 & 0x1
    if (r14 == 0) goto L01c1b5f4
    r14 = r6 >> 14
    r14 = r14 & 0xFFFFFFFC
    r15 = [r4+r14]
    r14 = r14 + 4
    r1 = [r4+r14]
    r1 = r1 - r15
    r14 = uextra(r6, p:0, l:16)
    r6 = r6 + r7
    r1_r0 = r1 * r14 (s)
    r1_r0 >>>= 16
    r15 += r0
    r13_r12 = r15 * r8 (s)
    r13_r12 += r2 * r9 (s)
    r14 = r13 >>> 31
    r13_r12 += r14 * r10 (s)
    r13_r12 >>>= 31
    [r5++=4] = r12
L01c1b5f4:
    r11 = r11 >> 1
    if (r11 == 0) goto L01c1b67e
L01c1b5fc:
    r14 = r6 >> 14
    r14 = r14 & 0xFFFFFFFC
    r15 = [r4+r14]
    r14 = r14 + 4
    r1 = [r4+r14]
    r1 = r1 - r15
    r14 = uextra(r6, p:0, l:16)
    r6 = r6 + r7
    r1_r0 = r1 * r14 (s)
    r1_r0 >>>= 16
    r15 += r0
    r3_r2 = r15 * r8 (s)
    r3_r2 += r12 * r9 (s)
    r14 = r3 >>> 31
    r3_r2 += r14 * r10 (s)
    r3_r2 >>>= 31
    [r5++=4] = r2
    r14 = r6 >> 14
    r14 = r14 & 0xFFFFFFFC
    r15 = [r4+r14]
    r14 = r14 + 4
    r1 = [r4+r14]
    r1 = r1 - r15
    r14 = uextra(r6, p:0, l:16)
    r6 = r6 + r7
    r1_r0 = r1 * r14 (s)
    r1_r0 >>>= 16
    r15 += r0
    r13_r12 = r15 * r8 (s)
    r13_r12 += r2 * r9 (s)
    r14 = r13 >>> 31
    r13_r12 += r14 * r10 (s)
    r13_r12 >>>= 31
    [r5++=4] = r12
    if (--r11 != 0) goto L01c1b5fc
L01c1b67e:
    goto L01c1b6ea
L01c1b680:
    r15 = [r4++=4]
    r14 = r11 & 0x1
    if (r14 != 0) goto L01c1b690
    r1 = r15
    goto L01c1b6aa
L01c1b690:
    r13_r12 = r15 * r8 (s)
    r1 = [r4++=4]
    r13_r12 += r2 * r9 (s)
    r14 = r13 >>> 31
    r13_r12 += r14 * r10 (s)
    r13_r12 >>>= 31
    [r5++=4] = r12
L01c1b6aa:
    r11 = r11 >> 1
    if (r11 == 0) goto L01c1b6ea
L01c1b6b2:
    r3_r2 = r1 * r8 (s)
    r15 = [r4++=4]
    r3_r2 += r12 * r9 (s)
    r14 = r3 >>> 31
    r3_r2 += r14 * r10 (s)
    r3_r2 >>>= 31
    [r5++=4] = r2
    r13_r12 = r15 * r8 (s)
    r1 = [r4++=4]
    r13_r12 += r2 * r9 (s)
    r14 = r13 >>> 31
    r13_r12 += r14 * r10 (s)
    r13_r12 >>>= 31
    [r5++=4] = r12
    if (--r11 != 0) goto L01c1b6b2
L01c1b6ea:
    r0 = [sp]
    [r0+28] = r12
    sp += 4
    {pc, r15-r4} = [sp++]
