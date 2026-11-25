; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; two_stage_drive: 1 function, 0x01c179ae..0x01c17ca2

; two_stage_drive_two_stage_drive: 0x01c179ae..0x01c17ca2, module two-stage-drive (two_stage_drive)
.type two_stage_drive_two_stage_drive,@function
two_stage_drive_two_stage_drive:
    [--sp] = {rets, r15-r4}
    sp += -12
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+48]
    r5 = [r2+16]
    r6 = [r2+20]
    r7 = [r2+60]
    r8 = [r2+72]
    r9 = [r2+64]
    r10 = [r2+96]
    r11 = [r2+100]
    r12 = [r2+104]
    r3 = [r2+0]
    [sp+4] = r3
    r3 = [r2+4]
    [sp+8] = r3
    r4 = r4 << 16
    r7 = r7 << 16
    r9 = r9 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c17a08
    r1 += -1
    if (r1 == 0) goto L01c17a06
    r1 += -1
    if (r1 == 0) goto L01c17a04
    r1 += -1
    goto L01c17a02
L01c17a02:
    goto L01c17a9a
L01c17a04:
    goto L01c17b2a
L01c17a06:
    goto L01c17bba
L01c17a08:
    r3 = r15 << 4
    r2 = r3 >>> 4
    if (r2 != r15) goto L01c17c60
L01c17a14:
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [sp+8]
    r10 += r1
    r3 = r3 - r1
    r0 = 0x0 - r6
    r3 = smin(r3, r6)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
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
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c17a9a:
    r3 = r15 << 4
    r2 = r3 >>> 4
    if (r2 != r15) goto L01c17c70
L01c17aa4:
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [sp+8]
    r10 += r1
    r3 = r3 - r1
    r0 = 0x0 - r6
    r3 = smin(r3, r6)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
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
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c17b2a:
    r3 = r15 << 4
    r2 = r3 >>> 4
    if (r2 != r15) goto L01c17c80
L01c17b34:
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [sp+8]
    r10 += r1
    r3 = r3 - r1
    r0 = 0x0 - r6
    r3 = smin(r3, r6)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
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
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c17bba:
    r3 = r15 << 4
    r2 = r3 >>> 4
    if (r2 != r15) goto L01c17c90
L01c17bc4:
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [sp+8]
    r10 += r1
    r3 = r3 - r1
    r0 = 0x0 - r6
    r3 = smin(r3, r6)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
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
    r12 += r1
    r3 = r3 - r1
    [r13++=4] = r3
    if (--r14 != 0) goto L01c17a08
    r2 = [sp]
    [r2+96] = r10
    [r2+100] = r11
    [r2+104] = r12
    sp += 12
    goto L01c17ca0
L01c17c60:
    r3 = r15 >> 31
    r3 = r3 + r3
    r2 = 2147483647
    r3 = r3 + r2
    goto L01c17a14
L01c17c70:
    r3 = r15 >> 31
    r3 = r3 + r3
    r2 = 2147483647
    r3 = r3 + r2
    goto L01c17aa4
L01c17c80:
    r3 = r15 >> 31
    r3 = r3 + r3
    r2 = 2147483647
    r3 = r3 + r2
    goto L01c17b34
L01c17c90:
    r3 = r15 >> 31
    r3 = r3 + r3
    r2 = 2147483647
    r3 = r3 + r2
    goto L01c17bc4
L01c17ca0:
    {pc, r15-r4} = [sp++]
