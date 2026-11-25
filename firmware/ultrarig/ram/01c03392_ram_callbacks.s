; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 1 function, 0x01c03392..0x01c0344c

; ram_callbacks_clock_job: 0x01c03392..0x01c0344c, module ram-callbacks (clock_job)
.type ram_callbacks_clock_job,@function
ram_callbacks_clock_job:
    [--sp] = {rets, r15-r4}
    sp += -12
    r15 = L01c26890
    r1 = [r15+684]
    r13 = 0
    r2 = 0
    r3 = 0
    d[sp] = r3_r2
    r7 = 511
    r14 = 1664525
    r3 = 1013904223
    goto L01c03444
L01c033bc:
    r2 = 0
    r4 = 99537814
    goto L01c033d0
L01c033c6:
    r4 *= r14
    r4 += r3  ; @add.rr
    [r1+r2<<2] = r4
    r2 += 1  ; @add.ri.u5
L01c033d0:
    if (r2 != 512) goto L01c033c6
    r6 = 0
    r8 = 1
    r11_r10 = d[sp]
    r5 = 0
    goto L01c0341c
L01c033e4:
    r2 = 0
    r4 = r8
    goto L01c03410
L01c033ea:
    r9 = [r1+r2<<2]
    r12 = r4 & r7
    r0 = [r1+r12<<2]
    r11_r10 += r0 * r9 (u)
    r0 = r11 + r9
    r0 ^= r5
    r5 = r0 <> 27
    r0 = r5 ^ r9
    [r1+r2<<2] = r0
    r4 += 7  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L01c03410:
    if (r2 != 512) goto L01c033ea
    r8 = r8 + 131
    r6 += 1  ; @add.ri.u5
L01c0341c:
    if (r6 != 4) goto L01c033e4
    r0 = r10 ^ r11
    r0 ^= r5
    r2 = 1
    r4 = 1915855605
    if (r0 == r4) {
    r2 = 0
    }
    r0 = r15 + 688
    [r0+4] += r2
    [r0+0] += 1  ; @rmw.add.s12
    r13 = r13 + 1
L01c03444:
    if (r13 != 4) goto L01c033bc
    sp += 12
    {pc, r15-r4} = [sp++]
