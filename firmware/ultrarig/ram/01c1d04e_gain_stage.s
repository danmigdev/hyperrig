; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; gain_stage: 1 function, 0x01c1d04e..0x01c1d130

; gain_stage_gain_stage: 0x01c1d04e..0x01c1d130, module gain-stage (gain_stage)
.type gain_stage_gain_stage,@function
gain_stage_gain_stage:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r7 = [r2+80]
    r1 = r14 & 0x1
    if (r1 == 0) goto L01c1d072
    r3 = [r13+0]
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 20
    [r13+0] = r0
    r13 = r13 + 4
L01c1d072:
    r14 = r14 >> 1
    if (r14 == 0) goto L01c1d12e
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1d0a6
    r1 += -1
    if (r1 == 0) goto L01c1d0a0
    r1 += -1
    if (r1 == 0) goto L01c1d09a
    r1 += -1
    goto L01c1d094
L01c1d094:
    r13 = r13 + -8
    goto L01c1d0c6
L01c1d09a:
    r13 = r13 + -16
    goto L01c1d0e6
L01c1d0a0:
    r13 = r13 + -24
    goto L01c1d106
L01c1d0a6:
    r3 = [r13+0]
    r11 = [r13+4]
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+0] = r0
    [r13+4] = r8
L01c1d0c6:
    r3 = [r13+8]
    r11 = [r13+12]
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+8] = r0
    [r13+12] = r8
L01c1d0e6:
    r3 = [r13+16]
    r11 = [r13+20]
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+16] = r0
    [r13+20] = r8
L01c1d106:
    r3 = [r13+24]
    r11 = [r13+28]
    r1_r0 = r3 * r7 (s)
    r9_r8 = r11 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+24] = r0
    [r13+28] = r8
    r13 = r13 + 32
    if (--r14 != 0) goto L01c1d0a6
L01c1d12e:
    {pc, r15-r4} = [sp++]
