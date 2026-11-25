; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; blend_stage: 1 function, 0x01c1d3b6..0x01c1d4fc

; blend_stage_blend_stage: 0x01c1d3b6..0x01c1d4fc, module blend-stage (blend_stage)
.type blend_stage_blend_stage,@function
blend_stage_blend_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r3
    r13 = r0
    r12 = r1
    r14 = r2
    r15 = [r0+0]
    r4 = [r3+52]
    r5 = [r3+72]
    r6 = [r3+76]
    r10 = [r3+100]
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1d3f4
    r1 += -1
    if (r1 == 0) goto L01c1d3f2
    r1 += -1
    if (r1 == 0) goto L01c1d3f0
    r1 += -1
    goto L01c1d3ee
L01c1d3ee:
    goto L01c1d422
L01c1d3f0:
    goto L01c1d450
L01c1d3f2:
    goto L01c1d47e
L01c1d3f4:
    r0 = [r12++=4]
    r0 = r0 >>> 5
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r15 * r5 (s)
    r1_r0 += r10 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d4ba
L01c1d41e:
    [r13++=4] = r0
L01c1d422:
    r0 = [r12++=4]
    r0 = r0 >>> 5
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r15 * r5 (s)
    r1_r0 += r10 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d4ca
L01c1d44c:
    [r13++=4] = r0
L01c1d450:
    r0 = [r12++=4]
    r0 = r0 >>> 5
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r15 * r5 (s)
    r1_r0 += r10 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d4da
L01c1d47a:
    [r13++=4] = r0
L01c1d47e:
    r0 = [r12++=4]
    r0 = r0 >>> 5
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r15 * r5 (s)
    r1_r0 += r10 * r6 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d4ea
L01c1d4a8:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1d3f4
    r3 = [sp]
    [r3+100] = r10
    sp += 4
    goto L01c1d4fa
L01c1d4ba:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d41e
L01c1d4ca:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d44c
L01c1d4da:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d47a
L01c1d4ea:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d4a8
L01c1d4fa:
    {pc, r15-r4} = [sp++]
