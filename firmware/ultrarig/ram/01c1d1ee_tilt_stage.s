; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tilt_stage: 1 function, 0x01c1d1ee..0x01c1d3b6

; tilt_stage_tilt_stage: 0x01c1d1ee..0x01c1d3b6, module tilt-stage (tilt_stage)
.type tilt_stage_tilt_stage,@function
tilt_stage_tilt_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+20]
    r5 = [r2+28]
    r6 = [r2+8]
    r8 = [r2+32]
    r11 = [r2+40]
    r12 = [r2+44]
    r9 = r8 + r8
    r0 = 0x10000
    r8 = r0 - r8
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1d23a
    r1 += -1
    if (r1 == 0) goto L01c1d238
    r1 += -1
    if (r1 == 0) goto L01c1d236
    r1 += -1
    goto L01c1d234
L01c1d234:
    goto L01c1d284
L01c1d236:
    goto L01c1d2ce
L01c1d238:
    goto L01c1d318
L01c1d23a:
    r3 = r15 - r11
    r1_r0 = r3 * r4 (s)
    r2 = r15 >>> 1
    r1_r0 >>>= 16
    r11 += r0
    r3 = r15 - r12
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r12 += r0
    r3 = r12 >>> 1
    r2 = r2 - r3
    r1_r0 = r11 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 16
    r2 = r0
    r1_r0 = r2 * r6 (s)
    r1_r0 >>>= 19
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d374
L01c1d280:
    [r13++=4] = r0
L01c1d284:
    r3 = r15 - r11
    r1_r0 = r3 * r4 (s)
    r2 = r15 >>> 1
    r1_r0 >>>= 16
    r11 += r0
    r3 = r15 - r12
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r12 += r0
    r3 = r12 >>> 1
    r2 = r2 - r3
    r1_r0 = r11 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 16
    r2 = r0
    r1_r0 = r2 * r6 (s)
    r1_r0 >>>= 19
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d384
L01c1d2ca:
    [r13++=4] = r0
L01c1d2ce:
    r3 = r15 - r11
    r1_r0 = r3 * r4 (s)
    r2 = r15 >>> 1
    r1_r0 >>>= 16
    r11 += r0
    r3 = r15 - r12
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r12 += r0
    r3 = r12 >>> 1
    r2 = r2 - r3
    r1_r0 = r11 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 16
    r2 = r0
    r1_r0 = r2 * r6 (s)
    r1_r0 >>>= 19
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d394
L01c1d314:
    [r13++=4] = r0
L01c1d318:
    r3 = r15 - r11
    r1_r0 = r3 * r4 (s)
    r2 = r15 >>> 1
    r1_r0 >>>= 16
    r11 += r0
    r3 = r15 - r12
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r12 += r0
    r3 = r12 >>> 1
    r2 = r2 - r3
    r1_r0 = r11 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r1_r0 >>>= 16
    r2 = r0
    r1_r0 = r2 * r6 (s)
    r1_r0 >>>= 19
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d3a4
L01c1d35e:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1d23a
    r2 = [sp]
    [r2+40] = r11
    [r2+44] = r12
    sp += 4
    goto L01c1d3b4
L01c1d374:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d280
L01c1d384:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d2ca
L01c1d394:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d314
L01c1d3a4:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d35e
L01c1d3b4:
    {pc, r15-r4} = [sp++]
