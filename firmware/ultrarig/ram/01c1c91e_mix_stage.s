; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; mix_stage: 1 function, 0x01c1c91e..0x01c1caa4

; mix_stage_mix_stage: 0x01c1c91e..0x01c1caa4, module mix-stage (mix_stage)
.type mix_stage_mix_stage,@function
mix_stage_mix_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r3
    r13 = r0
    r12 = r1
    r14 = r2
    r4 = [r3+20]
    r5 = [r3+28]
    r6 = [r3+8]
    r10 = [r3+24]
    r11 = [r3+36]
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1c958
    r1 += -1
    if (r1 == 0) goto L01c1c956
    r1 += -1
    if (r1 == 0) goto L01c1c954
    r1 += -1
    goto L01c1c952
L01c1c952:
    goto L01c1c996
L01c1c954:
    goto L01c1c9d4
L01c1c956:
    goto L01c1ca12
L01c1c958:
    r0 = [r12++=4]
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [r13+0]
    r1_r0 >>>= 16
    r10 += r0
    r2 = r2 >>> 2
    r3 = r10 >>> 6
    r2 = r2 + r3
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r1_r0 >>>= 16
    r11 += r0
    r1_r0 = r11 * r6 (s)
    r1_r0 >>>= 14
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1ca62
L01c1c992:
    [r13++=4] = r0
L01c1c996:
    r0 = [r12++=4]
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [r13+0]
    r1_r0 >>>= 16
    r10 += r0
    r2 = r2 >>> 2
    r3 = r10 >>> 6
    r2 = r2 + r3
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r1_r0 >>>= 16
    r11 += r0
    r1_r0 = r11 * r6 (s)
    r1_r0 >>>= 14
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1ca72
L01c1c9d0:
    [r13++=4] = r0
L01c1c9d4:
    r0 = [r12++=4]
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [r13+0]
    r1_r0 >>>= 16
    r10 += r0
    r2 = r2 >>> 2
    r3 = r10 >>> 6
    r2 = r2 + r3
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r1_r0 >>>= 16
    r11 += r0
    r1_r0 = r11 * r6 (s)
    r1_r0 >>>= 14
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1ca82
L01c1ca0e:
    [r13++=4] = r0
L01c1ca12:
    r0 = [r12++=4]
    r3 = r0 - r10
    r1_r0 = r3 * r4 (s)
    r2 = [r13+0]
    r1_r0 >>>= 16
    r10 += r0
    r2 = r2 >>> 2
    r3 = r10 >>> 6
    r2 = r2 + r3
    r3 = r2 - r11
    r1_r0 = r3 * r5 (s)
    r1_r0 >>>= 16
    r11 += r0
    r1_r0 = r11 * r6 (s)
    r1_r0 >>>= 14
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1ca92
L01c1ca4c:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1c958
    r3 = [sp]
    [r3+24] = r10
    [r3+36] = r11
    sp += 4
    goto L01c1caa2
L01c1ca62:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1c992
L01c1ca72:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1c9d0
L01c1ca82:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1ca0e
L01c1ca92:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1ca4c
L01c1caa2:
    {pc, r15-r4} = [sp++]
