; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 2 functions, 0x02026676..0x02026818

; phase3_p10_usr_timer_add: 0x02026676..0x020267c6, module phase3-p10 (usr_timer_add)
.type phase3_p10_usr_timer_add,@function
phase3_p10_usr_timer_add:
    [--sp] = {rets, r10-r4}
    r8 = r2
    r9 = r1
    r10 = r0
    r0 = rets
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r4 = L01c26890
    r7 = r4 + 70
L02026694:
    testset b[r7]
    ifeq goto L02026694
    csync
    r0 = 0
    r5 = L01c25cf8
    goto L020266b0
L020266a6:
    r1 = b[r5+31] (u)
    if (r1 == 0) goto L020266d0
    r5 += 32
    r0 += 1  ; @add.ri.u5
L020266b0:
    if (r0 <= 14) goto L020266a6
    csync
    r6 = 0
    b[r4+70] = r6
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 32
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 != 0) goto L020266e4
    goto L020267c2
L020266d0:
    r0 = 1
    b[r5+31] = r0
    csync
    r0 = 0
    b[r4+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
L020266e4:
    [r5+12] = r10
    [r5+8] = r9
    r0 = [r5+24]
    r6 = 0
    b[r5+30] = r6
    r1 = r8 & 0xFFFFFF
    r0 = r0 & 0xFC000000
    r0 |= r1
    r0 |= 33554432
    [r5+24] = r0
    call L02041866  ; @call.xl
    r0 += r8
    [r5+20] = r0
    if (r5 == 0) goto L020267c2
    call storage_coordination_irq_enter  ; @call.xl
    csync
L02026716:
    testset b[r7]
    ifeq goto L02026716
    csync
    r0 = h[r4+86] (u)
    r9 = r0 + 1
    h[r4+86] = r9
    r1 = uextra(r9, p:0, l:16)
    h[r5+28] = r9
    if (r1 != 0) goto L02026740
    r9 = 1
    h[r5+28] = r9
    h[r4+86] = r9
L02026740:
    r6 = r9
L02026742:
    r1 = 0
L02026744:
    ifs (r1 > 1) goto L02026770
    r2 = r1 << 3
    r2 += r4  ; @add.rr
    r2 = r2 + 1876
    r3 = r2
L02026752:
    r3 = [r3+0]
    if (r3 == r2) goto L02026762
    r0 = r6.l (u)  #
    r7 = h[r3+28] (u)
    if (r0 != r7) goto L02026752
    goto L0202676a
L02026762:
    r0 = r6.l (u)
    r1 += 1  ; @add.ri.u5
    if (r0 != 0) goto L02026744
    r6 = 0
L0202676a:
    r6 += 1  ; @add.ri.u5
    h[r5+28] = r6
    goto L02026742
L02026770:
    r0 = uextra(r9, p:0, l:16)
    r1 = r6.l (u)
    if (r1 != r0) {
    h[r4+86] = r6
    }
    r7 = r4 + 1884
    call phase3_p13_get_min_precesion
    r3 = r0
    r1 = r7
L0202678a:
    r1 = [r1+0]
    if (r1 == r7) goto L020267a2
    r0 = [r1+24]
    r0 = r0 & 0xFFFFFF  #
    r2 = [r5+24]
    r2 = r2 & 0xFFFFFF
    if (r2 >= r0) goto L0202678a
    goto L020267a6
L020267a2:
    r1 = r4 + 1884
L020267a6:
    r0 = r5
    call phase3_p13_list_add_tail
    if (r3 > r8) {
    call phase3_p13_timer1_run
    }
    csync
    r0 = 0
    b[r4+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
L020267c2:
    r0 = r6.l (u)
    {pc, r10-r4} = [sp++]

; phase3_p10_bt_init_calls: 0x020267c6..0x02026818, module phase3-p10 (bt_init_calls)
.type phase3_p10_bt_init_calls,@function
phase3_p10_bt_init_calls:
    [--sp] = rets
    call L020521fc  ; @call.xl
    call L02053628  ; @call.xl
    call L02053614  ; @call.xl
    call L02053756  ; @call.xl
    call L02053770  ; @call.xl
    call L0205378c  ; @call.xl
    call L020537ba  ; @call.xl
    call L0204d704  ; @call.xl
    call L0205443e  ; @call.xl
    call L02054494  ; @call.xl
    call L0204d744  ; @call.xl
    call L0204d75a  ; @call.xl
    call L0204d76a  ; @call.xl
    pc = [sp++]
