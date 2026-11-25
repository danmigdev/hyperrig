; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; two_pass_drive: 1 function, 0x01c17eba..0x01c1827a

; two_pass_drive_two_pass_drive: 0x01c17eba..0x01c1827a, module two-pass-drive (two_pass_drive)
.type two_pass_drive_two_pass_drive,@function
two_pass_drive_two_pass_drive:
    [--sp] = {rets, r15-r4}
    sp += -12
    [sp] = r2
    [sp+4] = r0
    [sp+8] = r1
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+48]
    r5 = [r2+52]
    r6 = [r2+16]
    r7 = [r2+0]
    r8 = [r2+20]
    r9 = [r2+4]
    r10 = [r2+96]
    r11 = [r2+100]
    r12 = [r2+32]
    r4 = r4 << 16
    r5 = r5 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c17f0c
    r1 += -1
    if (r1 == 0) goto L01c17f0a
    r1 += -1
    if (r1 == 0) goto L01c17f08
    r1 += -1
    goto L01c17f06
L01c17f06:
    goto L01c17f82
L01c17f08:
    goto L01c17ff8
L01c17f0a:
    goto L01c1806e
L01c17f0c:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c18238
L01c17f18:
    r2 = r2 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r3 - r1
    r3 = smin(r3, r6)
    r3 = smax(r3, r12)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r11 += r1
    r3 = r3 - r1
    r0 = 0x0 - r8
    r3 = smin(r3, r8)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r9 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 1
    [r13++=4] = r0
L01c17f82:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c18248
L01c17f8e:
    r2 = r2 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r3 - r1
    r3 = smin(r3, r6)
    r3 = smax(r3, r12)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r11 += r1
    r3 = r3 - r1
    r0 = 0x0 - r8
    r3 = smin(r3, r8)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r9 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 1
    [r13++=4] = r0
L01c17ff8:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c18258
L01c18004:
    r2 = r2 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r3 - r1
    r3 = smin(r3, r6)
    r3 = smax(r3, r12)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r11 += r1
    r3 = r3 - r1
    r0 = 0x0 - r8
    r3 = smin(r3, r8)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r9 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 1
    [r13++=4] = r0
L01c1806e:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c18268
L01c18078:
    r2 = r2 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r3 - r1
    r3 = smin(r3, r6)
    r3 = smax(r3, r12)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r11 += r1
    r3 = r3 - r1
    r0 = 0x0 - r8
    r3 = smin(r3, r8)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r9 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 1
    [r13++=4] = r0
    if (--r14 != 0) goto L01c17f0c
    r2 = [sp]
    [r2+96] = r10
    [r2+100] = r11
    r13 = [sp+4]
    r14 = [sp+8]
    r15 = [r13+0]
    r4 = [r2+24]
    r5 = [r2+40]
    r6 = [r2+8]
    r7 = [r2+60]
    r8 = [r2+72]
    r9 = [r2+64]
    r10 = [r2+104]
    r11 = [r2+108]
    r7 = r7 << 16
    r9 = r9 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c18136
    r1 += -1
    if (r1 == 0) goto L01c18134
    r1 += -1
    if (r1 == 0) goto L01c18132
    r1 += -1
    goto L01c18130
L01c18130:
    goto L01c18172
L01c18132:
    goto L01c181ae
L01c18134:
    goto L01c181ea
L01c18136:
    r3 = smin(r15, r4)
    r3 = smax(r3, r5)
    r1_r0 = r3 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = r0 >>> 2
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c18172:
    r3 = smin(r15, r4)
    r3 = smax(r3, r5)
    r1_r0 = r3 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = r0 >>> 2
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c181ae:
    r3 = smin(r15, r4)
    r3 = smax(r3, r5)
    r1_r0 = r3 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = r0 >>> 2
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c181ea:
    r3 = smin(r15, r4)
    r3 = smax(r3, r5)
    r1_r0 = r3 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = r0 >>> 2
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
    if (--r14 != 0) goto L01c18136
    r2 = [sp]
    [r2+104] = r10
    [r2+108] = r11
    sp += 12
    goto L01c18278
L01c18238:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c17f18
L01c18248:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c17f8e
L01c18258:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c18004
L01c18268:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c18078
L01c18278:
    {pc, r15-r4} = [sp++]
