; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; filter_kernels: 1 function, 0x01c1ebcc..0x01c1ecc4

; filter_kernels_section_cascade: 0x01c1ebcc..0x01c1ecc4, module filter-kernels (section_cascade)
.type filter_kernels_section_cascade,@function
filter_kernels_section_cascade:
    [--sp] = {rets, r15-r4}
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r7 = [r0+12]
    r8 = [r0+16]
    r9 = 2147483649
    if (r7 == 0) goto L01c1ecc2
L01c1ebe2:
    r10 = [r5+0]
    r11 = [r5+4]
    r12 = [r5+8]
    r13 = [r5+12]
    r14 = r4
    r2 = r6
    r3 = r2 & 0x1
    if (r3 == 0) goto L01c1ec34
    r15 = [r14+0]
    r3 = r15 - r11
    r1_r0 = r3 * r8 (s)
    r3 = r1 >>> 31
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 31
    r11 = r10 + r0
    r10 = r15
    r3 = r11 - r13
    r1_r0 = r3 * r8 (s)
    r3 = r1 >>> 31
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 31
    r13 = r12 + r0
    r12 = r11
    [r14++=4] = r13
L01c1ec34:
    r2 = r2 >> 1
    if (r2 == 0) goto L01c1ecac
L01c1ec38:
    r15 = [r14+0]
    r3 = r15 - r11
    r1_r0 = r3 * r8 (s)
    r3 = r1 >>> 31
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 31
    r11 = r10 + r0
    r10 = r15
    r3 = r11 - r13
    r1_r0 = r3 * r8 (s)
    r3 = r1 >>> 31
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 31
    r13 = r12 + r0
    r12 = r11
    [r14++=4] = r13
    r15 = [r14+0]
    r3 = r15 - r11
    r1_r0 = r3 * r8 (s)
    r3 = r1 >>> 31
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 31
    r11 = r10 + r0
    r10 = r15
    r3 = r11 - r13
    r1_r0 = r3 * r8 (s)
    r3 = r1 >>> 31
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 31
    r13 = r12 + r0
    r12 = r11
    [r14++=4] = r13
    if (--r2 != 0) goto L01c1ec38
L01c1ecac:
    [r5+0] = r10
    [r5+4] = r11
    [r5+8] = r12
    [r5+12] = r13
    r5 = r5 + 16
    if (--r7 != 0) goto L01c1ebe2
L01c1ecc2:
    {pc, r15-r4} = [sp++]
