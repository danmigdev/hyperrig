; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_signal: 1 function, 0x01c1ee40..0x01c1f088

; effect_signal_variable_filter: 0x01c1ee40..0x01c1f088, module effect-signal (variable_filter)
.type effect_signal_variable_filter,@function
effect_signal_variable_filter:
    [--sp] = {r15-r4}
    sp += -8
    [sp] = r2
    r12 = r0
    r1 = r1 << 2
    r1 = r0 + r1
    [sp+4] = r1
    r10 = [r2+0]
    r11 = [r2+4]
    r13 = [r2+8]
    r14 = [r2+12]
    r4 = [r2+16]
    r5 = [r2+20]
    r6 = [r2+24]
    r7 = [r2+28]
    r8 = [r2+32]
    r9 = [r2+36]
L01c1ee6e:
    r15 = [r12+0]
    r15 = r15 >>> 4
    r15 = r15 - r11
    r0 = r13
    r1 = 0
    r1_r0 += r4 * r10 (s)
    r1_r0 += r5 * r15 (s)
    r2 = r14
    r3 = 0
    r3_r2 += r5 * r10 (s)
    r3_r2 += r6 * r15 (s)
    r13 = r0 << 2
    r13 = r13 >> 2
    r14 = r2 << 2
    r14 = r14 >> 2
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r2 += r11
    r3 = [r12+0]
    r15 = r0 + r0
    r10 = r15 - r10
    r15 = r2 + r2
    r11 = r15 - r11
    r15 = r0
    r1_r0 = r3 * r7 (s)
    r1_r0 += r15 * r8 (s)
    r15 = [r12+4]
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 26
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1f048
L01c1eedc:
    [r12+0] = r0
    r15 = r15 >>> 4
    r15 = r15 - r11
    r0 = r13
    r1 = 0
    r1_r0 += r4 * r10 (s)
    r1_r0 += r5 * r15 (s)
    r2 = r14
    r3 = 0
    r3_r2 += r5 * r10 (s)
    r3_r2 += r6 * r15 (s)
    r13 = r0 << 2
    r13 = r13 >> 2
    r14 = r2 << 2
    r14 = r14 >> 2
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r2 += r11
    r3 = [r12+4]
    r15 = r0 + r0
    r10 = r15 - r10
    r15 = r2 + r2
    r11 = r15 - r11
    r15 = r0
    r1_r0 = r3 * r7 (s)
    r1_r0 += r15 * r8 (s)
    r15 = [r12+8]
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 26
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1f058
L01c1ef4a:
    [r12+4] = r0
    r15 = r15 >>> 4
    r15 = r15 - r11
    r0 = r13
    r1 = 0
    r1_r0 += r4 * r10 (s)
    r1_r0 += r5 * r15 (s)
    r2 = r14
    r3 = 0
    r3_r2 += r5 * r10 (s)
    r3_r2 += r6 * r15 (s)
    r13 = r0 << 2
    r13 = r13 >> 2
    r14 = r2 << 2
    r14 = r14 >> 2
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r2 += r11
    r3 = [r12+8]
    r15 = r0 + r0
    r10 = r15 - r10
    r15 = r2 + r2
    r11 = r15 - r11
    r15 = r0
    r1_r0 = r3 * r7 (s)
    r1_r0 += r15 * r8 (s)
    r15 = [r12+12]
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 26
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1f068
L01c1efb8:
    [r12+8] = r0
    r15 = r15 >>> 4
    r15 = r15 - r11
    r0 = r13
    r1 = 0
    r1_r0 += r4 * r10 (s)
    r1_r0 += r5 * r15 (s)
    r2 = r14
    r3 = 0
    r3_r2 += r5 * r10 (s)
    r3_r2 += r6 * r15 (s)
    r13 = r0 << 2
    r13 = r13 >> 2
    r14 = r2 << 2
    r14 = r14 >> 2
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r2 += r11
    r3 = [r12+12]
    r15 = r0 + r0
    r10 = r15 - r10
    r15 = r2 + r2
    r11 = r15 - r11
    r15 = r0
    r1_r0 = r3 * r7 (s)
    r1_r0 += r15 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 26
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1f078
L01c1f022:
    [r12+12] = r0
    r12 = r12 + 16
    r0 = [sp+4]
    if (r12 != r0) goto L01c1ee6e
    r2 = [sp]
    [r2+0] = r10
    [r2+4] = r11
    [r2+8] = r13
    [r2+12] = r14
    sp += 8
    {r15-r4} = [sp++]
    rts
L01c1f048:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1eedc
L01c1f058:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1ef4a
L01c1f068:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1efb8
L01c1f078:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1f022
