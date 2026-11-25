; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tone_stage: 1 function, 0x01c1caa4..0x01c1cc0e

; tone_stage_tone_stage: 0x01c1caa4..0x01c1cc0e, module tone-stage (tone_stage)
.type tone_stage_tone_stage,@function
tone_stage_tone_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+52]
    r5 = [r2+56]
    r8 = [r2+72]
    r9 = [r2+76]
    r11 = [r2+100]
    r12 = [r2+104]
    r4 = r4 << 16
    r5 = r5 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1caea
    r1 += -1
    if (r1 == 0) goto L01c1cae8
    r1 += -1
    if (r1 == 0) goto L01c1cae6
    r1 += -1
    goto L01c1cae4
L01c1cae4:
    goto L01c1cb1e
L01c1cae6:
    goto L01c1cb52
L01c1cae8:
    goto L01c1cb86
L01c1caea:
    r2 = r15 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r4 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r5 (s)
    r12 += r1
    r3 = r3 - r1
    r15 = [r13+4]
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1cbcc
L01c1cb1a:
    [r13++=4] = r0
L01c1cb1e:
    r2 = r15 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r4 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r5 (s)
    r12 += r1
    r3 = r3 - r1
    r15 = [r13+4]
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1cbdc
L01c1cb4e:
    [r13++=4] = r0
L01c1cb52:
    r2 = r15 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r4 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r5 (s)
    r12 += r1
    r3 = r3 - r1
    r15 = [r13+4]
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1cbec
L01c1cb82:
    [r13++=4] = r0
L01c1cb86:
    r2 = r15 >>> 5
    r3 = r2 - r11
    r1_r0 = r3 * r4 (s)
    r3 = r2 - r12
    r11 += r1
    r1_r0 = r3 * r5 (s)
    r12 += r1
    r3 = r3 - r1
    r15 = [r13+4]
    r1_r0 = r11 * r8 (s)
    r1_r0 += r3 * r9 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1cbfc
L01c1cbb6:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1caea
    r2 = [sp]
    [r2+100] = r11
    [r2+104] = r12
    sp += 4
    goto L01c1cc0c
L01c1cbcc:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1cb1a
L01c1cbdc:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1cb4e
L01c1cbec:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1cb82
L01c1cbfc:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1cbb6
L01c1cc0c:
    {pc, r15-r4} = [sp++]
