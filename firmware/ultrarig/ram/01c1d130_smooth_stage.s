; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; smooth_stage: 1 function, 0x01c1d130..0x01c1d1ee

; smooth_stage_smooth_stage: 0x01c1d130..0x01c1d1ee, module smooth-stage (smooth_stage)
.type smooth_stage_smooth_stage,@function
smooth_stage_smooth_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r6 = [r2+8]
    r7 = [r2+12]
    r8 = [r2+16]
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1d166
    r1 += -1
    if (r1 == 0) goto L01c1d164
    r1 += -1
    if (r1 == 0) goto L01c1d162
    r1 += -1
    goto L01c1d160
L01c1d160:
    goto L01c1d184
L01c1d162:
    goto L01c1d1a2
L01c1d164:
    goto L01c1d1c0
L01c1d166:
    r3 = r15 - r8
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r1_r0 >>>= 30
    [r13++=4] = r0
L01c1d184:
    r3 = r15 - r8
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r1_r0 >>>= 30
    [r13++=4] = r0
L01c1d1a2:
    r3 = r15 - r8
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r1_r0 >>>= 30
    [r13++=4] = r0
L01c1d1c0:
    r3 = r15 - r8
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r1_r0 >>>= 30
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1d166
    r2 = [sp]
    [r2+16] = r8
    sp += 4
    goto L01c1d1ec
L01c1d1ec:
    {pc, r15-r4} = [sp++]
