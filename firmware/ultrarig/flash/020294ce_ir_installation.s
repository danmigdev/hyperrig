; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_installation: 3 functions, 0x020294ce..0x02029604

; ir_installation_trim: 0x020294ce..0x0202957e, module ir-installation (trim)
.type ir_installation_trim,@function
ir_installation_trim:
    [--sp] = {rets, r15-r4}
    if (r0 == 0) goto L02029578
    if (r1 == 0) goto L02029578
    r7 = 0
    r4 = 0
    r5 = 0
    r8 = 0
    r2 = 0
L020294de:
    r3 = h[r0+r2<<1] (s)
    r3 = abs(r3)
    r6 = r3 * r3
    r4 = r4 + r6
    r5 = r5 + r7 + c
    r2 = r2 + 1
    r8 = umax(r3, r8)
    if (r1 != r2) goto L020294de
    if (r8 == 0) goto L02029578
    r9 = 1
    if (r1 < 2) goto L0202957a
    r5_r4 >>= 20
    r14 = 0
    r15 = 0
    r3 = 3162
    r9 = r1
L02029514:
    r10 = r9 + -1
    r1 = h[r0+r10<<1] (s)
    r12 = abs(r1)
    r6 = r12 * r12
    r7 = 0
    r14 += r6
    r15 = r15 + r7 + c
    r1 = r14 - r4
    r2 = r15 - r5 - !c
    r6 = psr
    r13 = r1 | r2
    r1 = sextra(r6, p:1, l:1)
    r11 = 1
    r6 = 1
    if ((r1 & r13) == 0) {
    r6 = 0
    }
    r2 = r12 * r3
    r7 = 1
    if (r2 <= r8) {
    r7 = 0
    }
    r6 |= r7
    if (r6 != 0) goto L0202955e
    r9 = r10
L0202955e:
    r6 = 1
    if ((r1 & r13) != 0) {
    r6 = 0
    }
    if (r2 > r8) {
    r11 = 0
    }
    if (r9 < 2) goto L0202957a
    r1 = r11 & r6
    if (r1 != 0) goto L02029514
    goto L0202957a
L02029578:
    r9 = r1
L0202957a:
    r0 = r9
    {pc, r15-r4} = [sp++]

; ir_installation_configure: 0x0202957e..0x020295d8, module ir-installation (configure)
.type ir_installation_configure,@function
ir_installation_configure:
    [--sp] = {rets, r8-r4}
    r8 = L01c32db0
    r4 = r1
    r5 = r0
    r7 = r8
    [++r7=60] = r5
    r6 = r3  #
    [r7+4] = r4
    r0 = r2
    call ir_installation_gain_clamp  ; @call.xl
    r0 = itof(r0)
    r1 = 1148846080
    r0 = r0 / r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = L01c1f7dc
    [r1+0] = r0
    r0 = 1
    if (r6 != 0) goto L020295be
    r0 = r6
L020295be:
    [r7+8] = r0
    r0 = 0
    [r7+12] = r0
    [r7+16] = r0
    if (r5 != 0) goto L020295ce
L020295c8:
    [r8+80] = r0
    {pc, r8-r4} = [sp++]
L020295ce:
    r0 = r5
    r1 = r4
    call ir_installation_trim
    goto L020295c8

; ir_installation_slot: 0x020295d8..0x02029604, module ir-installation (slot)
.type ir_installation_slot,@function
ir_installation_slot:
    [--sp] = {rets, r4}
    r2 = r0
    r0 = -1
    if (r2 == 0) goto L02029602
    r3 = L01c3441c
    r3 = [r3+0]
    if (r3 == 0) goto L02029602
    r3 = L01c32db0
    r4 = [r3+64]
    if (r4 == 0) goto L02029602
    r0 = 0
    [r3+60] = r0
    [r3+72] = r2
    [r3+76] = r1
L02029602:
    {pc, r4} = [sp++]
