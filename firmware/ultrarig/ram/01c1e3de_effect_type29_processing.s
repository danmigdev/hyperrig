; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_type29_processing: 2 functions, 0x01c1e3de..0x01c1e4a6

; effect_type29_processing_window29: 0x01c1e3de..0x01c1e43a, module effect-type29-processing (window29)
.type effect_type29_processing_window29,@function
effect_type29_processing_window29:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r1
    r6 = r2
    r14 = r3 >> 16
    r14 = r14 & 0xFF
    r15 = r3 << 16
    r15 = r15 >> 17
    r7 = 4
    ifs (r3 >= 0) goto L01c1e400
    r7 = 0x0 - r7
L01c1e400:
    if (r15 == 0) goto L01c1e438
L01c1e404:
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
    r1 = r1 >>> r14
    r3 = r3 >>> r14
    [r4++=4] = r1
    [r4++=4] = r3
    if (--r15 != 0) goto L01c1e404
L01c1e438:
    {pc, r15-r4} = [sp++]

; effect_type29_processing_accumulate29: 0x01c1e43a..0x01c1e4a6, module effect-type29-processing (accumulate29)
.type effect_type29_processing_accumulate29,@function
effect_type29_processing_accumulate29:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r1
    r15 = r2 >> 1
    if (r15 == 0) goto L01c1e4a4
    ifs (r3 < 0) goto L01c1e478
    r14 = r3
L01c1e44e:
    r8 = [r5++=4]
    r9 = [r5++=4]
    r10 = [r4+0]
    r11 = [r4+4]
    r8 = r8 << r14
    r9 = r9 << r14
    r10 += r8
    r11 += r9
    [r4++=4] = r10
    [r4++=4] = r11
    if (--r15 != 0) goto L01c1e44e
    goto L01c1e4a4
L01c1e478:
    r14 = 0x0 - r3
L01c1e47c:
    r8 = [r5++=4]
    r9 = [r5++=4]
    r10 = [r4+0]
    r11 = [r4+4]
    r8 = r8 >>> r14
    r9 = r9 >>> r14
    r10 += r8
    r11 += r9
    [r4++=4] = r10
    [r4++=4] = r11
    if (--r15 != 0) goto L01c1e47c
L01c1e4a4:
    {pc, r15-r4} = [sp++]
