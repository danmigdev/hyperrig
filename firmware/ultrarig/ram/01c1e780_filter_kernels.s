; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; filter_kernels: 3 functions, 0x01c1e780..0x01c1ea96

; filter_kernels_split_filter: 0x01c1e780..0x01c1e87a, module filter-kernels (split_filter)
.type filter_kernels_split_filter,@function
filter_kernels_split_filter:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r8 = [r0+12]
    r9 = [r0+16]
    r2 = [r0+20]
    r11 = [r0+24]
    r12 = [r0+28]
    r13 = [r0+32]
    r10 = 2147483649
    r1 = [r4++=4]
    r0 = r6 & 0x1
    if (r0 == 0) goto L01c1e7ee
    r3_r2 = r2 * r9 (s)
    r3_r2 += r1 * r8 (s)
    r1 = [r4++=4]
    r0 = r3 >>> 31
    r3_r2 += r0 * r10 (s)
    r3_r2 >>>= 31
    r7 = [r11++=4]
    r15_r14 = r7 * r13 (s)
    r0 = r15 >>> 31
    r15_r14 += r0 * r10 (s)
    r15_r14 >>>= 31
    r14 += r2
    [r12++=4] = r14
    r15_r14 = r14 * r13 (s)
    r15_r14 >>>= 31
    r14 = r7 - r14
    [r5++=4] = r14
L01c1e7ee:
    r6 = r6 >> 1
    if (r6 == 0) goto L01c1e872
L01c1e7f2:
    r3_r2 = r2 * r9 (s)
    r3_r2 += r1 * r8 (s)
    r1 = [r4++=4]
    r0 = r3 >>> 31
    r3_r2 += r0 * r10 (s)
    r3_r2 >>>= 31
    r7 = [r11++=4]
    r15_r14 = r7 * r13 (s)
    r0 = r15 >>> 31
    r15_r14 += r0 * r10 (s)
    r15_r14 >>>= 31
    r14 += r2
    [r12++=4] = r14
    r15_r14 = r14 * r13 (s)
    r15_r14 >>>= 31
    r14 = r7 - r14
    [r5++=4] = r14
    r3_r2 = r2 * r9 (s)
    r3_r2 += r1 * r8 (s)
    r1 = [r4++=4]
    r0 = r3 >>> 31
    r3_r2 += r0 * r10 (s)
    r3_r2 >>>= 31
    r7 = [r11++=4]
    r15_r14 = r7 * r13 (s)
    r0 = r15 >>> 31
    r15_r14 += r0 * r10 (s)
    r15_r14 >>>= 31
    r14 += r2
    [r12++=4] = r14
    r15_r14 = r14 * r13 (s)
    r15_r14 >>>= 31
    r14 = r7 - r14
    [r5++=4] = r14
    if (--r6 != 0) goto L01c1e7f2
L01c1e872:
    r0 = [sp]
    [r0+20] = r2
    sp += 4
    {pc, r15-r4} = [sp++]

; filter_kernels_ramped_high_pass: 0x01c1e87a..0x01c1e97c, module filter-kernels (ramped_high_pass)
.type filter_kernels_ramped_high_pass,@function
filter_kernels_ramped_high_pass:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
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
    if (r12 == 0) goto L01c1e8d6
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
    if (r3 != r4) goto L01c1e93c
L01c1e8d4:
    [r5++=4] = r2
L01c1e8d6:
    r6 = r6 >> 1
    if (r6 == 0) goto L01c1e93a
L01c1e8da:
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
    if (r3 != r4) goto L01c1e94c
L01c1e906:
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
    if (r3 != r4) goto L01c1e95c
L01c1e934:
    [r5++=4] = r2
    if (--r6 != 0) goto L01c1e8da
L01c1e93a:
    goto L01c1e96c
L01c1e93c:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e8d4
L01c1e94c:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e906
L01c1e95c:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e934
L01c1e96c:
    r0 = [sp]
    [r0+16] = r8
    [r0+20] = r9
    r0 = r15
    sp += 4
    {pc, r15-r4} = [sp++]

; filter_kernels_ramped_high_pass_peak: 0x01c1e97c..0x01c1ea96, module filter-kernels (ramped_high_pass_peak)
.type filter_kernels_ramped_high_pass_peak,@function
filter_kernels_ramped_high_pass_peak:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
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
    if (r12 == 0) goto L01c1e9e0
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
    if (r3 != r4) goto L01c1ea56
L01c1e9d6:
    [r5++=4] = r2
    r4 = r2 >>> 31
    r4 ^= r2
    r15 = r15 | r4
L01c1e9e0:
    r6 = r6 >> 1
    if (r6 == 0) goto L01c1ea54
L01c1e9e4:
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
    if (r3 != r4) goto L01c1ea66
L01c1ea10:
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
    if (r3 != r4) goto L01c1ea76
L01c1ea46:
    [r5++=4] = r2
    r4 = r2 >>> 31
    r4 ^= r2
    r15 = r15 | r4
    if (--r6 != 0) goto L01c1e9e4
L01c1ea54:
    goto L01c1ea86
L01c1ea56:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1e9d6
L01c1ea66:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1ea10
L01c1ea76:
    r4 = r3 >> 31
    r4 = r4 + r4
    r3 = 2147483647
    r4 = r4 + r3
    r2 = r4
    goto L01c1ea46
L01c1ea86:
    r0 = [sp]
    [r0+16] = r8
    [r0+20] = r9
    r0 = r15
    sp += 4
    {pc, r15-r4} = [sp++]
