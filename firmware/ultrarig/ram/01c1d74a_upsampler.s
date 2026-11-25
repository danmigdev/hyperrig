; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; upsampler: 1 function, 0x01c1d74a..0x01c1da72

; upsampler_upsample: 0x01c1d74a..0x01c1da72, module upsampler (upsample)
.type upsampler_upsample,@function
upsampler_upsample:
    [--sp] = {rets, r15-r4}
    r13 = [r0+0]
    r14 = [r0+4]
    r2 = [r0+8]
    sp += -16
    r1 = r0 + 12
    r8 = [r1++=4]
    [sp+8] = r1
    r9 = 0x8000
    [sp+4] = r2
    r1 = r2 + r13
    [sp] = r1
    r2 = r2 << 2
    r2 += r13
    [sp+12] = r2
    r4 = 665320397
    r5 = 4117437020
    r6 = 65670763
    r7 = 4274656822
    r12 = [r13+-28]
    r15 = [r13+-24]
L01c1d792:
    r1_r0 = r12 * r7 (s)
    r12 = [r13+-20]
    r1_r0 += r15 * r6 (s)
    r3_r2 = r15 * r7 (s)
    r15 = [r13+-16]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r6 (s)
    r12 = [r13+-12]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+-8]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r4 (s)
    r12 = [r13+-4]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r4 (s)
    r15 = [r13+0]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+4]
    r1_r0 += r15 * r7 (s)
    r3_r2 += r15 * r6 (s)
    r3_r2 += r12 * r7 (s)
    r15 = [r13+-20]
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r12 = r0 >>> 31
    if (r1 != r12) goto L01c1d99a
L01c1d802:
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c1d9ac
L01c1d808:
    r12 = [r13+-16]
    r1 = [r13+-12]
    r3 = [r13+-8]
    r11 = [r14+0]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r0 * r9 (s)
    r11_r10 >>>= 15
    r0 = r10 >>> 31
    if (r11 != r0) goto L01c1d9bc
L01c1d82c:
    [r14+0] = r10
    r11 = [r14+4]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r1 * r9 (s)
    r11_r10 >>>= 15
    r1 = r10 >>> 31
    if (r11 != r1) goto L01c1d9ce
L01c1d848:
    [r14+4] = r10
    r11 = [r14+8]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r2 * r9 (s)
    r11_r10 >>>= 15
    r2 = r10 >>> 31
    if (r11 != r2) goto L01c1d9e0
L01c1d864:
    [r14+8] = r10
    r11 = [r14+12]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r3 * r9 (s)
    r11_r10 >>>= 15
    r3 = r10 >>> 31
    if (r11 != r3) goto L01c1d9f2
L01c1d880:
    [r14+12] = r10
    r1_r0 = r15 * r7 (s)
    r15 = [r13+-12]
    r1_r0 += r12 * r6 (s)
    r3_r2 = r12 * r7 (s)
    r12 = [r13+-8]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r6 (s)
    r15 = [r13+-4]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+0]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r4 (s)
    r15 = [r13+4]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r4 (s)
    r12 = [r13+8]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+12]
    r1_r0 += r12 * r7 (s)
    r3_r2 += r12 * r6 (s)
    r3_r2 += r15 * r7 (s)
    r12 = [r13+-12]
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c1da04
L01c1d8f4:
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c1da16
L01c1d8fa:
    r15 = [r13+-8]
    r1 = [r13+-4]
    r3 = [r13+0]
    r11 = [r14+16]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r0 * r9 (s)
    r11_r10 >>>= 15
    r0 = r10 >>> 31
    if (r11 != r0) goto L01c1da26
L01c1d91e:
    [r14+16] = r10
    r11 = [r14+20]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r1 * r9 (s)
    r11_r10 >>>= 15
    r1 = r10 >>> 31
    if (r11 != r1) goto L01c1da38
L01c1d93a:
    [r14+20] = r10
    r11 = [r14+24]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r2 * r9 (s)
    r11_r10 >>>= 15
    r2 = r10 >>> 31
    if (r11 != r2) goto L01c1da4a
L01c1d956:
    [r14+24] = r10
    r11 = [r14+28]
    r11_r10 = r11 * r8 (s)
    r11_r10 += r3 * r9 (s)
    r11_r10 >>>= 15
    r3 = r10 >>> 31
    if (r11 != r3) goto L01c1da5c
L01c1d972:
    [r14+28] = r10
    r13 = r13 + 16
    r14 = r14 + 32
    r2 = [sp]
    if (r13 != r2) goto L01c1d792
    r1 = [sp+12]
    if (r13 == r1) goto L01c1da6e
    r1 = [sp+4]
    r2 = r2 + r1
    [sp] = r2
    r1 = [sp+8]
    r8 = [r1++=4]
    [sp+8] = r1
    goto L01c1d792
L01c1d99a:
    r12 = r1 >> 31
    r12 += r12
    r1 = 2147483647
    r12 += r1
    r0 = r12
    goto L01c1d802
L01c1d9ac:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c1d808
L01c1d9bc:
    r0 = r11 >> 31
    r0 = r0 + r0
    r11 = 2147483647
    r0 += r11
    r10 = r0
    goto L01c1d82c
L01c1d9ce:
    r1 = r11 >> 31
    r1 = r1 + r1
    r11 = 2147483647
    r1 += r11
    r10 = r1
    goto L01c1d848
L01c1d9e0:
    r2 = r11 >> 31
    r2 = r2 + r2
    r11 = 2147483647
    r2 += r11
    r10 = r2
    goto L01c1d864
L01c1d9f2:
    r3 = r11 >> 31
    r3 = r3 + r3
    r11 = 2147483647
    r3 += r11
    r10 = r3
    goto L01c1d880
L01c1da04:
    r15 = r1 >> 31
    r15 += r15
    r1 = 2147483647
    r15 += r1
    r0 = r15
    goto L01c1d8f4
L01c1da16:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c1d8fa
L01c1da26:
    r0 = r11 >> 31
    r0 = r0 + r0
    r11 = 2147483647
    r0 += r11
    r10 = r0
    goto L01c1d91e
L01c1da38:
    r1 = r11 >> 31
    r1 = r1 + r1
    r11 = 2147483647
    r1 += r11
    r10 = r1
    goto L01c1d93a
L01c1da4a:
    r2 = r11 >> 31
    r2 = r2 + r2
    r11 = 2147483647
    r2 += r11
    r10 = r2
    goto L01c1d956
L01c1da5c:
    r3 = r11 >> 31
    r3 = r3 + r3
    r11 = 2147483647
    r3 += r11
    r10 = r3
    goto L01c1d972
L01c1da6e:
    sp += 16
    {pc, r15-r4} = [sp++]
