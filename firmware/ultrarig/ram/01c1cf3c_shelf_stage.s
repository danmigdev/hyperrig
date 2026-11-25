; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; shelf_stage: 1 function, 0x01c1cf3c..0x01c1d04e

; shelf_stage_shelf_stage: 0x01c1cf3c..0x01c1d04e, module shelf-stage (shelf_stage)
.type shelf_stage_shelf_stage,@function
shelf_stage_shelf_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r7 = [r2+60]
    r8 = [r2+72]
    r9 = [r2+64]
    r10 = [r2+104]
    r11 = [r2+108]
    r7 = r7 << 16
    r9 = r9 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1cf82
    r1 += -1
    if (r1 == 0) goto L01c1cf80
    r1 += -1
    if (r1 == 0) goto L01c1cf7e
    r1 += -1
    goto L01c1cf7c
L01c1cf7c:
    goto L01c1cfb0
L01c1cf7e:
    goto L01c1cfde
L01c1cf80:
    goto L01c1d00c
L01c1cf82:
    r2 = r15 >>> 2
    r15 = [r13+4]
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c1cfb0:
    r2 = r15 >>> 2
    r15 = [r13+4]
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c1cfde:
    r2 = r15 >>> 2
    r15 = [r13+4]
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
L01c1d00c:
    r2 = r15 >>> 2
    r15 = [r13+4]
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r10 += r1
    r3 = r3 - r1
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r2 = r2 + r0
    r3 = r2 - r11
    r1_r0 = r3 * r9 (s)
    r11 += r1
    r3 = r3 - r1
    [r13++=4] = r3
    if (--r14 != 0) goto L01c1cf82
    r2 = [sp]
    [r2+104] = r10
    [r2+108] = r11
    sp += 4
    goto L01c1d04c
L01c1d04c:
    {pc, r15-r4} = [sp++]
