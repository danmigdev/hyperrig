; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; crossover_drive: 1 function, 0x01c16bd4..0x01c16f0c

; crossover_drive_crossover_drive: 0x01c16bd4..0x01c16f0c, module crossover-drive (crossover_drive)
.type crossover_drive_crossover_drive,@function
crossover_drive_crossover_drive:
    [--sp] = {rets, r15-r4}
    sp += -8
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+48]
    r5 = [r2+52]
    r6 = [r2+56]
    r7 = [r2+16]
    r8 = [r2+72]
    r9 = [r2+76]
    r10 = [r2+96]
    r11 = [r2+100]
    r12 = [r2+104]
    r3 = [r2+0]
    [sp+4] = r3
    r4 = r4 << 16
    r5 = r5 << 16
    r6 = r6 << 16
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16e9c
    r2 = r15 << 3
L01c16c18:
    r2 = r2 - r10
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c16c3c
    r1 += -1
    if (r1 == 0) goto L01c16c3a
    r1 += -1
    if (r1 == 0) goto L01c16c38
    r1 += -1
    goto L01c16c36
L01c16c36:
    goto L01c16cc0
L01c16c38:
    goto L01c16d42
L01c16c3a:
    goto L01c16dc4
L01c16c3c:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r7
    r3 = smin(r3, r7)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r6 (s)
    r12 += r1
    r3 = r3 - r1
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16eb2
    r2 = r15 << 3
L01c16cae:
    r2 = r2 - r10
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16e5c
L01c16cbc:
    [r13++=4] = r0
L01c16cc0:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r7
    r3 = smin(r3, r7)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r6 (s)
    r12 += r1
    r3 = r3 - r1
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16ec8
    r2 = r15 << 3
L01c16d30:
    r2 = r2 - r10
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16e6c
L01c16d3e:
    [r13++=4] = r0
L01c16d42:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r7
    r3 = smin(r3, r7)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r6 (s)
    r12 += r1
    r3 = r3 - r1
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16ede
    r2 = r15 << 3
L01c16db2:
    r2 = r2 - r10
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16e7c
L01c16dc0:
    [r13++=4] = r0
L01c16dc4:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r7
    r3 = smin(r3, r7)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r6 (s)
    r12 += r1
    r3 = r3 - r1
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16ef4
    r2 = r15 << 3
L01c16e34:
    r2 = r2 - r10
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16e8c
L01c16e42:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c16c3c
    r2 = [sp]
    [r2+96] = r10
    [r2+100] = r11
    [r2+104] = r12
    sp += 8
    goto L01c16f0a
L01c16e5c:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16cbc
L01c16e6c:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16d3e
L01c16e7c:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16dc0
L01c16e8c:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16e42
L01c16e9c:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16c18
L01c16eb2:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16cae
L01c16ec8:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16d30
L01c16ede:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16db2
L01c16ef4:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16e34
L01c16f0a:
    {pc, r15-r4} = [sp++]
