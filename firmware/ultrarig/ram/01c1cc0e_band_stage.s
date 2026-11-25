; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; band_stage: 1 function, 0x01c1cc0e..0x01c1cd12

; band_stage_band_stage: 0x01c1cc0e..0x01c1cd12, module band-stage (band_stage)
.type band_stage_band_stage,@function
band_stage_band_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r6 = [r2+52]
    r7 = [r2+56]
    r9 = [r2+84]
    r11 = [r2+100]
    r12 = [r2+104]
    r6 = r6 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1cc4e
    r1 += -1
    if (r1 == 0) goto L01c1cc4c
    r1 += -1
    if (r1 == 0) goto L01c1cc4a
    r1 += -1
    goto L01c1cc48
L01c1cc48:
    goto L01c1cc7a
L01c1cc4a:
    goto L01c1cca6
L01c1cc4c:
    goto L01c1ccd2
L01c1cc4e:
    r3 = r15 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r15 = [r13+4]
    r1_r0 >>>= 15
    [r13++=4] = r0
L01c1cc7a:
    r3 = r15 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r15 = [r13+4]
    r1_r0 >>>= 15
    [r13++=4] = r0
L01c1cca6:
    r3 = r15 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r15 = [r13+4]
    r1_r0 >>>= 15
    [r13++=4] = r0
L01c1ccd2:
    r3 = r15 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r15 = [r13+4]
    r1_r0 >>>= 15
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1cc4e
    r2 = [sp]
    [r2+100] = r11
    [r2+104] = r12
    sp += 4
    goto L01c1cd10
L01c1cd10:
    {pc, r15-r4} = [sp++]
