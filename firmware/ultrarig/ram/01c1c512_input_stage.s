; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; input_stage: 1 function, 0x01c1c512..0x01c1c6a8

; input_stage_input_stage: 0x01c1c512..0x01c1c6a8, module input-stage (input_stage)
.type input_stage_input_stage,@function
input_stage_input_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r3
    r13 = r0
    r12 = r1
    r14 = r2
    r15 = [r0+0]
    r4 = [r3+0]
    r8 = [r3+4]
    r5 = [r3+8]
    r7 = [r3+12]
    r6 = 0x0 - r5
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1c550
    r1 += -1
    if (r1 == 0) goto L01c1c54e
    r1 += -1
    if (r1 == 0) goto L01c1c54c
    r1 += -1
    goto L01c1c54a
L01c1c54a:
    goto L01c1c58c
L01c1c54c:
    goto L01c1c5c8
L01c1c54e:
    goto L01c1c604
L01c1c550:
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c1c64e
    r2 = r15 << 3
L01c1c55e:
    r3 = r2 - r8
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r3 = r2 - r8
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r13 = r13 + 4
    r1_r0 >>>= 22
    [r12++=4] = r0
L01c1c58c:
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c1c664
    r2 = r15 << 3
L01c1c59a:
    r3 = r2 - r8
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r3 = r2 - r8
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r13 = r13 + 4
    r1_r0 >>>= 22
    [r12++=4] = r0
L01c1c5c8:
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c1c67a
    r2 = r15 << 3
L01c1c5d6:
    r3 = r2 - r8
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r3 = r2 - r8
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r13 = r13 + 4
    r1_r0 >>>= 22
    [r12++=4] = r0
L01c1c604:
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c1c690
    r2 = r15 << 3
L01c1c612:
    r3 = r2 - r8
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r8 += r0
    r3 = r2 - r8
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r13 = r13 + 4
    r1_r0 >>>= 22
    [r12++=4] = r0
    if (--r14 != 0) goto L01c1c550
    r3 = [sp]
    [r3+4] = r8
    sp += 4
    goto L01c1c6a6
L01c1c64e:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c1c55e
L01c1c664:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c1c59a
L01c1c67a:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c1c5d6
L01c1c690:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c1c612
L01c1c6a6:
    {pc, r15-r4} = [sp++]
