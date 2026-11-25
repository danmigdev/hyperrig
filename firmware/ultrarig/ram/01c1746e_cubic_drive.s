; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; cubic_drive: 1 function, 0x01c1746e..0x01c17718

; cubic_drive_cubic_drive: 0x01c1746e..0x01c17718, module cubic-drive (cubic_drive)
.type cubic_drive_cubic_drive,@function
cubic_drive_cubic_drive:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+48]
    r5 = [r2+16]
    r6 = [r2+0]
    r7 = [r2+60]
    r8 = [r2+72]
    r9 = [r2+64]
    r10 = [r2+96]
    r11 = [r2+100]
    r12 = [r2+104]
    r4 = r4 << 16
    r7 = r7 << 16
    r9 = r9 << 16
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c176a8
    r2 = r15 << 3
L01c174ae:
    r2 = r2 - r10
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c174d2
    r1 += -1
    if (r1 == 0) goto L01c174d0
    r1 += -1
    if (r1 == 0) goto L01c174ce
    r1 += -1
    goto L01c174cc
L01c174cc:
    goto L01c17542
L01c174ce:
    goto L01c175b2
L01c174d0:
    goto L01c17622
L01c174d2:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r2)
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 2
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r12
    r1_r0 = r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c176be
    r2 = r15 << 3
L01c17536:
    r2 = r2 - r10
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c17542:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r2)
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 2
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r12
    r1_r0 = r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c176d4
    r2 = r15 << 3
L01c175a6:
    r2 = r2 - r10
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c175b2:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r2)
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 2
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r12
    r1_r0 = r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c176ea
    r2 = r15 << 3
L01c17616:
    r2 = r2 - r10
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c17622:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r2)
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 2
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r12
    r1_r0 = r3 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c17700
    r2 = r15 << 3
L01c17686:
    r2 = r2 - r10
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
    if (--r14 != 0) goto L01c174d2
    r2 = [sp]
    [r2+96] = r10
    [r2+100] = r11
    [r2+104] = r12
    sp += 4
    goto L01c17716
L01c176a8:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c174ae
L01c176be:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c17536
L01c176d4:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c175a6
L01c176ea:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c17616
L01c17700:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c17686
L01c17716:
    {pc, r15-r4} = [sp++]
