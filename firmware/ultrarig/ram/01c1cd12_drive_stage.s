; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; drive_stage: 1 function, 0x01c1cd12..0x01c1cf3c

; drive_stage_drive_stage: 0x01c1cd12..0x01c1cf3c, module drive-stage (drive_stage)
.type drive_stage_drive_stage,@function
drive_stage_drive_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+48]
    r5 = [r2+52]
    r6 = [r2+16]
    r7 = [r2+0]
    r8 = [r3+0]
    r9 = [r2+4]
    r10 = [r2+96]
    r11 = [r2+100]
    r12 = [r2+32]
    r4 = r4 << 16
    r5 = r5 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1cd60
    r1 += -1
    if (r1 == 0) goto L01c1cd5e
    r1 += -1
    if (r1 == 0) goto L01c1cd5c
    r1 += -1
    goto L01c1cd5a
L01c1cd5a:
    goto L01c1cdc2
L01c1cd5c:
    goto L01c1ce24
L01c1cd5e:
    goto L01c1ce86
L01c1cd60:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c1cefa
L01c1cd6a:
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
    r1_r0 >>>= 22
    [r13++=4] = r0
L01c1cdc2:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c1cf0a
L01c1cdcc:
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
    r1_r0 >>>= 22
    [r13++=4] = r0
L01c1ce24:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c1cf1a
L01c1ce2e:
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
    r1_r0 >>>= 22
    [r13++=4] = r0
L01c1ce86:
    r2 = r15 << 4
    r3 = r2 >>> 4
    if (r3 != r15) goto L01c1cf2a
L01c1ce90:
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
    r1_r0 >>>= 22
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1cd60
    r2 = [sp]
    [r2+96] = r10
    [r2+100] = r11
    sp += 4
    goto L01c1cf3a
L01c1cefa:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c1cd6a
L01c1cf0a:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c1cdcc
L01c1cf1a:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c1ce2e
L01c1cf2a:
    r2 = r15 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    goto L01c1ce90
L01c1cf3a:
    {pc, r15-r4} = [sp++]
