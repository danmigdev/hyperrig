; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; modulated_delay: 1 function, 0x01c188c2..0x01c18f90

; modulated_delay_line: 0x01c188c2..0x01c18f90, module modulated-delay (line)
.type modulated_delay_line,@function
modulated_delay_line:
    [--sp] = {rets, r15-r4}
    sp += -8
    [sp] = r0
    r9 = [r0+0]
    r4 = [r0+4]
    r8 = [r0+8]
    r6 = [r0+16]
    r11 = [r0+36]
    r12 = [r0+40]
    r13 = [r0+32]
    r14 = [r0+44]
    r1 = [r0+48]
    r8 = r8 << 2
    r5 = [r0+52]
    [sp+4] = r14
    r2 = 2
    if (r1 == r2) goto L01c18bb2
L01c188f6:
    r2 = [sp]
    r0 = [r2+20]
    r15 = [r2+12]
    r0 = r0 << 4
    r15 += r0
    [r2+12] = r15
    r0 = r15 >>> 31
    r0 = r0 ^ r15
    r1 = 0x40000000
    r0 = r0 - r1
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = [sp]
    r1 = [r2+28]
    r3_r2 = r0 * r1 (s)
    r3_r2 >>>= 30
    r3 = [sp]
    r3 = [r3+24]
    r2 = r2 + r3
    r2 = r2 - r6
    r7 = r2 >>> 4
    r10 = 4
L01c18944:
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+0]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r14 = r3 >>> 3
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18eb0
L01c189d6:
    [r9+0] = r2
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+4]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r14 = r3 >>> 3
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18ec0
L01c18a6c:
    [r9+4] = r2
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+8]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r14 = r3 >>> 3
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18ed0
L01c18b02:
    [r9+8] = r2
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+12]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r14 = r3 >>> 3
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18ee0
L01c18b98:
    [r9+12] = r2
    r9 = r9 + 16
    if (--r10 != 0) goto L01c18944
    r0 = [sp+4]
    r0 += -1
    [sp+4] = r0
    if (r0 != 0) goto L01c188f6
    goto L01c18f80
L01c18bb2:
    r2 = [sp]
    r0 = [r2+20]
    r15 = [r2+12]
    r0 = r0 << 4
    r15 += r0
    [r2+12] = r15
    r0 = r15 >>> 31
    r0 = r0 ^ r15
    r1 = 0x40000000
    r0 = r0 - r1
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = [sp]
    r1 = [r2+28]
    r3_r2 = r0 * r1 (s)
    r3_r2 >>>= 30
    r3 = [sp]
    r3 = [r3+24]
    r2 = r2 + r3
    r2 = r2 - r6
    r7 = r2 >>> 4
    r10 = 4
L01c18c00:
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+0]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r15_r14 = r0 * r13 (s)
    r15_r14 >>>= 16
    r1 = r3 >>> 3
    r14 += r1
    r1 = abs(r14)
    r1 = r1 >> 28
    if (r1 != 0) goto L01c18ef0
L01c18c7a:
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18f04
L01c18ca6:
    [r9+0] = r2
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+4]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r15_r14 = r0 * r13 (s)
    r15_r14 >>>= 16
    r1 = r3 >>> 3
    r14 += r1
    r1 = abs(r14)
    r1 = r1 >> 28
    if (r1 != 0) goto L01c18f14
L01c18d22:
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18f28
L01c18d4c:
    [r9+4] = r2
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+8]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r15_r14 = r0 * r13 (s)
    r15_r14 >>>= 16
    r1 = r3 >>> 3
    r14 += r1
    r1 = abs(r14)
    r1 = r1 >> 28
    if (r1 != 0) goto L01c18f38
L01c18dc8:
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18f4c
L01c18df2:
    [r9+8] = r2
    r6 = r6 + r7
    r2 = r8 << 14
    r2 = r2 - r6
    r3 = r2 >> 14
    r3 += -4
    r3 &= r5
    r3 = r3 + r4
    r0 = [r3+0]
    r14 = [r3+4]
    r15 = [r3+8]
    r3 = [r3+12]
    r2 = r2.l (u)
    r0 = r14 - r0
    r3 = r3 - r15
    r15 = r15 - r14
    r0 = r15 - r0
    r3 = r3 - r15
    r1 = r3 - r0
    r1 = r1 >>> 1
    r3 = r3 >>> 1
    r3 = r0 - r3
    r0 = r0 >>> 1
    r15 = r15 - r0
    r1_r0 = r1 * r2 (s)
    r1_r0 >>>= 16
    r0 = r0 + r3
    r1_r0 = r0 * r2 (s)
    r3 = [r9+12]
    r1_r0 >>>= 16
    r0 += r15
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 16
    r0 += r14
    r15_r14 = r0 * r13 (s)
    r15_r14 >>>= 16
    r1 = r3 >>> 3
    r14 += r1
    r1 = abs(r14)
    r1 = r1 >> 28
    if (r1 != 0) goto L01c18f5c
L01c18e6c:
    [r4+r8] = r14
    if (r8 < 12) {
    r1 = r4 + r5
    r1 += r8
    [r1+4] = r14
    }
    r8 = r8 + 4
    r8 = r8 & r5
    r3_r2 = r3 * r12 (s)
    r3_r2 += r0 * r11 (s)
    r3_r2 >>>= 16
    r1 = r2 >>> 31
    if (r3 != r1) goto L01c18f70
L01c18e96:
    [r9+12] = r2
    r9 = r9 + 16
    if (--r10 != 0) goto L01c18c00
    r0 = [sp+4]
    r0 += -1
    [sp+4] = r0
    if (r0 != 0) goto L01c18bb2
    goto L01c18f80
L01c18eb0:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c189d6
L01c18ec0:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c18a6c
L01c18ed0:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c18b02
L01c18ee0:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c18b98
L01c18ef0:
    r1 = 268435455
    r14 = smin(r14, r1)
    r1 = 0xF0000000
    r14 = smax(r14, r1)
    goto L01c18c7a
L01c18f04:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c18ca6
L01c18f14:
    r1 = 268435455
    r14 = smin(r14, r1)
    r1 = 0xF0000000
    r14 = smax(r14, r1)
    goto L01c18d22
L01c18f28:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c18d4c
L01c18f38:
    r1 = 268435455
    r14 = smin(r14, r1)
    r1 = 0xF0000000
    r14 = smax(r14, r1)
    goto L01c18dc8
L01c18f4c:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c18df2
L01c18f5c:
    r1 = 268435455
    r14 = smin(r14, r1)
    r1 = 0xF0000000
    r14 = smax(r14, r1)
    goto L01c18e6c
L01c18f70:
    r1 = r3 >> 31
    r1 = r1 + r1
    r3 = 2147483647
    r1 = r1 + r3
    r2 = r1
    goto L01c18e96
L01c18f80:
    r0 = [sp]
    r8 = r8 >> 2
    [r0+8] = r8
    [r0+16] = r6
    sp += 8
    {pc, r15-r4} = [sp++]
