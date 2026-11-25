; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201f13a..0x0201f2fc: vendor code (JieLi SDK or library, not reversed), as instructions
L0201f13a:
    [--sp] = {rets, r4}
    r2 = L01c26890
    r0 = 0
    b[r2+71] = r0
    r3 = L01c1f234
    r4 = 345  #
    [r3+0] = r3
    [r3+4] = r3
    r1 = [r2+r4<<2]
    r0 = r3 + 8
    [r3+8] = r0
    [r3+12] = r0
    r0 = L01c25edc
    if (r1 == 0) {  ; @if.eq.ri.s12
    [r2+r4<<2] = r0
    [r0+0] = r0
    [r0+4] = r0
    } else {
    call phase3_p6_list_add_tail
    }
    r0 += 8  ; @add.ri.u5
    r4 += -25
    goto L0201f182
L0201f17a:
    r1 = r3
    call phase3_p6_list_add_tail
    r4 += -32
    r0 += 32
L0201f182:
    if (r4 >= 32) goto L0201f17a
    r0 = L0203a1b7  ; "sys_timer"
    r2 = L0201f1b6
    r1 = 0
    r3 = 100
    call phase3_p6_sys_timer_add_to_task
    r0 = 0
    {pc, r4} = [sp++]
L0201f19e:
    [--sp] = rets
    {r2, r1} = [r0+]
    [r1+4] = r2
    [r2+0] = r1
    [r0+0] = r0
    [r0+4] = r0
    r1 = L01c1f234
    call phase3_p6_list_add_tail
    pc = [sp++]
L0201f1b6:
    [--sp] = {rets, r13-r4}
    sp += -16
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r9 = L01c26890
    r13 = r9 + 71
L0201f1cc:
    testset b[r13]
    ifeq goto L0201f1cc
    csync
    r4 = sp + 0
    r12 = L01c1f180
    r5 = [r12+188]
    r10 = 1
    r11 = 0
    r8 = L02035d46  ; "app_core"
    goto L0201f294
L0201f1ee:
    r7 = r5 + 28
    r0 = b[r7+0] (u)
    r6 = [r5+0]
    if (r0 == 0) goto L0201f1fe
    r0 = r5
    call L0201f19e
    r5 = r6
    goto L0201f294
L0201f1fe:
    b[r7+1] = r10
    csync
    b[r9+71] = r11
    call storage_coordination_irq_leave  ; @call.xl
    r1 = [r5+8]
    if (r1 == 0) goto L0201f218
    r0 = [r5+20]
    call r1
    if (r0 == 0) goto L0201f27e
L0201f218:
    r0 = [r5+12]
    [sp] = r0
    [r4+4] = r10
    r0 = [r5+16]
    [r4+8] = r0
    r1 = h[r5+30] (u)
    r1 = r1 | 0x300000  #
    r0 = [r5+24]
    r3 = sp + 0
    r2 = 3
    call L02040bae  ; @call.xl
    if (r0 == 14) goto L0201f23e
    if (r0 != 4) goto L0201f254
L0201f23e:
    [r5+24] = r8
    r0 = h[r5+30] (u)
    r1 = r0 | 0x300000
    r3 = sp + 0
    r2 = 3
    r0 = r8
    call L02040bae  ; @call.xl
L0201f254:
    b[r7+1] = r11
    if (r0 == 21) goto L0201f282
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201f264:
    testset b[r13]
    ifeq goto L0201f264
    csync
    r0 = r5
    call L0201f19e
    csync
    b[r9+71] = r11
    call storage_coordination_irq_leave  ; @call.xl
    goto L0201f282
L0201f27e:
    b[r7+1] = r11
L0201f282:
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201f28a:
    testset b[r13]
    ifeq goto L0201f28a
    csync
    r5 = r6
L0201f294:
    r0 = r12 + 188
    if (r5 != r0) goto L0201f1ee
    csync
    r0 = 0
    b[r9+71] = r0
    call storage_coordination_irq_leave  ; @call.xl
    sp += 16
    {pc, r13-r4} = [sp++]
L0201f2ae:
    sp += -128
L0201f2b0:
    r0 = sp + 0
    call L020405d6  ; @call.xl
    goto L0201f2b0
L0201f2ba:
    [--sp] = {rets, r5, r4}
    r4 = L020558f4
    r5 = L02055948
    goto L0201f2d2
L0201f2ca:
    r0 = [r4++=28]
    if (r0 == 0) goto L0201f2d2
    call r0
L0201f2d2:
    if (r4 < r5) goto L0201f2ca
    r0 = 0
    {pc, r5, r4} = [sp++]
L0201f2da:
    [--sp] = rets
    r1 = L01c27acc
    if (r0 < r1) goto L0201f2f4
    r1 = r1 + 128
    if (r0 < r1) {
    [r0+0] = 0x0
    pc = [sp++]
    }
L0201f2f4:
    call L0203d218  ; @call.xl
    pc = [sp++]
