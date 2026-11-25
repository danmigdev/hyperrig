; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; clamp_stage: 1 function, 0x01c1c6a8..0x01c1c7d6

; clamp_stage_clamp_stage: 0x01c1c6a8..0x01c1c7d6, module clamp-stage (clamp_stage)
.type clamp_stage_clamp_stage,@function
clamp_stage_clamp_stage:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r5 = [r2+8]
    r7 = [r2+12]
    r6 = 0x0 - r5
    r1 = r14 & 0x1
    if (r1 == 0) goto L01c1c6d8
    r3 = [r13+0]
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 22
    [r13+0] = r0
    r13 = r13 + 4
L01c1c6d8:
    r14 = r14 >> 1
    if (r14 == 0) goto L01c1c7d4
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1c70c
    r1 += -1
    if (r1 == 0) goto L01c1c706
    r1 += -1
    if (r1 == 0) goto L01c1c700
    r1 += -1
    goto L01c1c6fa
L01c1c6fa:
    r13 = r13 + -8
    goto L01c1c73c
L01c1c700:
    r13 = r13 + -16
    goto L01c1c76c
L01c1c706:
    r13 = r13 + -24
    goto L01c1c79c
L01c1c70c:
    r3 = [r13+0]
    r11 = [r13+4]
    r3 = smin(r3, r5)
    r11 = smin(r11, r5)
    r3 = smax(r3, r6)
    r11 = smax(r11, r6)
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 22
    r9_r8 >>>= 22
    [r13+0] = r0
    [r13+4] = r8
L01c1c73c:
    r3 = [r13+8]
    r11 = [r13+12]
    r3 = smin(r3, r5)
    r11 = smin(r11, r5)
    r3 = smax(r3, r6)
    r11 = smax(r11, r6)
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 22
    r9_r8 >>>= 22
    [r13+8] = r0
    [r13+12] = r8
L01c1c76c:
    r3 = [r13+16]
    r11 = [r13+20]
    r3 = smin(r3, r5)
    r11 = smin(r11, r5)
    r3 = smax(r3, r6)
    r11 = smax(r11, r6)
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 22
    r9_r8 >>>= 22
    [r13+16] = r0
    [r13+20] = r8
L01c1c79c:
    r3 = [r13+24]
    r11 = [r13+28]
    r3 = smin(r3, r5)
    r11 = smin(r11, r5)
    r3 = smax(r3, r6)
    r11 = smax(r11, r6)
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 22
    r9_r8 >>>= 22
    [r13+24] = r0
    [r13+28] = r8
    r13 = r13 + 32
    if (--r14 != 0) goto L01c1c70c
L01c1c7d4:
    {pc, r15-r4} = [sp++]
