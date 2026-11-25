; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_type30_processing: 2 functions, 0x01c1e4a6..0x01c1e620

; effect_type30_processing_complex30: 0x01c1e4a6..0x01c1e5b4, module effect-type30-processing (complex30)
.type effect_type30_processing_complex30,@function
effect_type30_processing_complex30:
    [--sp] = {rets, r15-r4}
    sp += -12
    r4 = [r0+32]
    [sp] = r4
    r4 = [r0+36]
    [sp+4] = r4
    [sp+8] = r0
    r11 = [r0+28]
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r8 = [r0+12]
    r7 = [r0+16]
    r15 = [r0+20]
    r9 = [r0+24]
    r10 = 0
L01c1e4ce:
    r12 = r9 & 0x7F8
    r12 += r8
    r13 = [r12+4]
    r12 = [r12+0]
    r14 = [r4+0]
    r9 = r9 + 1336
    r0 = 0x20000000
    r1 = 0
    r2 = 0x20000000
    r3 = 0
    r1_r0 += r14 * r12 (s)
    r3_r2 += r14 * r13 (s)
    r14 = [r4+4]
    r1_r0 -= r14 * r13 (s)
    r3_r2 += r14 * r12 (s)
    r12 = [r7++=4]
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r13 = r0
    r14 = r2
    r0 = 0x20000000
    r1 = 0
    r2 = 0x20000000
    r3 = 0
    r1_r0 += r13 * r12 (s)
    r3_r2 += r14 * r12 (s)
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r13 = r0
    r14 = r2
    r12 = [r6++=4]
    r1_r0 = r12 * r11 (s)
    r12 = [r6++=4]
    r3_r2 = r12 * r11 (s)
    r12 = [sp]
    r1_r0 >>>= r12
    r3_r2 >>>= r12
    r0 = r0 + 1
    r2 = r2 + 1
    r0 = r0 >>> 1
    r2 = r2 >>> 1
    r13 += r0
    r14 += r2
    [r4++=4] = r13
    [r4++=4] = r14
    r0 = r13 >>> 31
    r2 = r14 >>> 31
    r0 = r0 ^ r13
    r2 = r2 ^ r14
    r10 = r10 | r0
    r10 = r10 | r2
    r12 = [sp+4]
    r13 = r13 >>> r12
    r14 = r14 >>> r12
    r0 = 33554431
    r13 = smin(r13, r0)
    r14 = smin(r14, r0)
    r0 = 0x0 - r0
    r13 = smax(r13, r0)
    r14 = smax(r14, r0)
    [r5++=4] = r13
    [r5++=4] = r14
    if (--r15 != 0) goto L01c1e4ce
    r0 = [sp+8]
    [r0+40] = r10
    sp += 12
    {pc, r15-r4} = [sp++]

; effect_type30_processing_window_add30: 0x01c1e5b4..0x01c1e620, module effect-type30-processing (window_add30)
.type effect_type30_processing_window_add30,@function
effect_type30_processing_window_add30:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r1
    r6 = r2
    r14 = r3 >> 16
    r14 = r14 & 0xFF
    r15 = r3 << 16
    r15 = r15 >> 17
    r7 = 4
    ifs (r3 >= 0) goto L01c1e5d6
    r7 = 0x0 - r7
L01c1e5d6:
    if (r15 == 0) goto L01c1e61e
L01c1e5da:
    r8 = [r5++=4]
    r9 = [r6+0]
    r6 = r6 + r7
    r10 = [r5++=4]
    r11 = [r6+0]
    r6 = r6 + r7
    r1_r0 = r8 * r9 (s)
    r3_r2 = r10 * r11 (s)
    r1_r0 <<= 1
    r3_r2 <<= 1
    r12 = [r4+0]
    r13 = [r4+4]
    r1 = r1 << r14
    r3 = r3 << r14
    r12 += r1
    r13 += r3
    [r4++=4] = r12
    [r4++=4] = r13
    if (--r15 != 0) goto L01c1e5da
L01c1e61e:
    {pc, r15-r4} = [sp++]
