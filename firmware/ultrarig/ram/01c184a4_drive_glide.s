; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; drive_glide: 1 function, 0x01c184a4..0x01c185aa

; drive_glide_drive: 0x01c184a4..0x01c185aa, module drive-glide (drive)
.type drive_glide_drive,@function
drive_glide_drive:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+0]
    r5 = [r2+4]
    r6 = [r2+8]
    r7 = [r2+12]
    r8 = [r2+16]
    r9 = 0x0 - r5
    r1 = r14 & 0x1
    if (r1 == 0) goto L01c1850c
    r3 = smin(r15, r5)
    r3 = smax(r3, r9)
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 12
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r3 = r0 - r8
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 30
    [r13++=4] = r0
L01c1850c:
    r14 = r14 >> 1
    if (r14 == 0) goto L01c185a0
L01c18514:
    r3 = smin(r15, r5)
    r3 = smax(r3, r9)
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 12
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r3 = r0 - r8
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 30
    [r13++=4] = r0
    r3 = smin(r15, r5)
    r3 = smax(r3, r9)
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 12
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r3 = r0 - r8
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 30
    [r13++=4] = r0
    if (--r14 != 0) goto L01c18514
L01c185a0:
    r2 = [sp]
    [r2+16] = r8
    sp += 4
    {pc, r15-r4} = [sp++]
