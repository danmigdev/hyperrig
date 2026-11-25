; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; interrupt_and_stack_calls: 1 function, 0x01c03278..0x01c03392

; interrupt_and_stack_calls_timer_interrupt: 0x01c03278..0x01c03392, module interrupt-and-stack-calls (timer_interrupt)
.type interrupt_and_stack_calls_timer_interrupt,@function
interrupt_and_stack_calls_timer_interrupt:
    [--sp] = {psr, rets, reti}
    [--sp] = {r12-r0}
    r5 = reti
    call storage_platform_clock  ; @call.xl
    r10 = L01c26890
    r1 = [r10+356]
    r8 = r0
    r0 = r1 + 1
    [r10+356] = r0
    if ((r0 & 0x3F) == 0) goto L01c0338a
L01c032a0:
    call L0201ac0a  ; @call.xl
    r0 = b[r10+42] (u)
    if (r0 == 0) goto L01c0333c
    r0 = r10 + 816
    [r0+0] += 1  ; @rmw.add.s12
    r5_r4 = 0
    r9 = L01c1f180
    goto L01c03338
L01c032be:
    r0 = r10 + 1964
    r0 = [r0+r4<<2]
    r0 = r10 + 1984  #
    r1 = [r0+0]
    r2 = [r0+r4<<2]
    r0 = 0
    r6 = 1
    if ((r2 & r1) != 0) {
    r6 = 0
    }
    r1 = r4 + r10
    r7 = r1 + 1552
    r1 = b[r7+0] (u)
    if (r6 == r1) goto L01c03332
    r0 = b[r7+5] (u)
    r0 += 1  ; @add.ri.u5
    r1 = r0.b0 (u)
    if (r1 < 30) goto L01c03332
    r11 = b[r10+43] (u)
    r0 = b[r10+44] (u)
    r0 = r11 - r0
    r0 = r0.b0 (u)
    if (r0 > 15) goto L01c03334
    r0 = r11 & 0xFFFFFF0F
    r0 = r0 * 0xC
    r12 = r0 + r10
    call storage_platform_clock  ; @call.xl
    r1 = r12 + 4796
    [r1+0] = r0
    r0 = [r9+24]
    [r1+4] = r0
    b[r1+8] = r5
    b[r1+9] = r6
    r0 = r11 + 1
    b[r10+43] = r0
    b[r7+0] = r6
    r0 = 0
L01c03332:
    b[r7+5] = r0
L01c03334:
    r5 += 1  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L01c03338:
; HyperRig MINI v4, patch mini_panel_irq_three: Limit the same loop to three physical MINI switches; retain branch/register fields.
.if TARGET_MINI
    if (r4 != 3) goto L01c032be  ; @bne.ri
.else
    if (r4 != 5) goto L01c032be
.endif
L01c0333c:
    call storage_platform_clock  ; @call.xl
    r1 = r10
    r3 = [++r1=568]
    r2 = r0 - r8
    r0 = r3 + r2
    [r1+0] = r0
    r1 = [r1+4]
    if (r2 > r1) {
    [r10+572] = r2
    r1 = r2
    }
    r2 = [r10+576]
    r2 += 1  ; @add.ri.u5
    [r10+576] = r2
    if (r2 != 1024) goto L01c03382
    r0 = r0 >> 10
    r2 = r10 + 292
    [r2+0] = r0
    [r2+4] = r1
    r0 = 0
    r1 = 0
    d[r2+276] = r1_r0
    [r10+576] = r0
L01c03382:
    {r12-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
L01c0338a:
    r1 = r5
    call ram_callbacks_stall_check
    goto L01c032a0
