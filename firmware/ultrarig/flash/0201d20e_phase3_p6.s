; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 3 functions, 0x0201d20e..0x0201d3d4

; phase3_p6_usr_timer_del_entry: 0x0201d20e..0x0201d252, module phase3-p6 (usr_timer_del_entry)
.type phase3_p6_usr_timer_del_entry,@function
phase3_p6_usr_timer_del_entry:
    [--sp] = {rets, r5, r4}
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r5 = L01c26890
    r0 = r5 + 70
L0201d224:
    testset b[r0]
    ifeq goto L0201d224
    csync
    r1_r0 = d[r3+0]
    call phase3_p13_list_del_entry
    r0 = r3
    call L0201d1f0
    r4 = r0
    csync
    r0 = 0
    b[r5+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 != 0) goto L0201d250
    r0 = r3
    call L0203d218  ; @call.xl
L0201d250:
    {pc, r5, r4} = [sp++]

; phase3_p6_timer1_isr: 0x0201d252..0x0201d3be, module phase3-p6 (timer1_isr)
.type phase3_p6_timer1_isr,@function
phase3_p6_timer1_isr:
    [--sp] = {psr, rets, reti}
    [--sp] = {r15-r0}
    r0 = 66816
    [r0+0] |= 0x4000
    r0 = 1548
    r14 = L01c26890
    r1 = b[r14+r0] (u)
    r0 = 2
    if (r1 != 0) goto L0201d276
    r0 = r1
L0201d276:
    r1 = r14 + 1360
    [r1+0] += r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r13 = r14 + 70
L0201d28a:
    testset b[r13]
    ifeq goto L0201d28a
    csync
    r15 = 0
    r8 = 2952790026
    r9 = 1342177270
    r10 = 1376
    r11 = 1
    r12 = 0
    goto L0201d392
L0201d2ac:
    r0 = r12 << 3
    r0 += r14
    r6 = r0 + 1876
    r5 = [r6+0]
    goto L0201d388
L0201d2ba:
    r0 = b[r4+27] (u)
    r5 = [r4+0]
    if ((r0 & 1) != 0) goto L0201d33e
    call L0204180e  ; @call.xl
    r1 = [r4+20]
    r0 += 1  ; @add.ri.u5
    r0 = r0 >> 1
    if (r1 <= r0) goto L0201d2e8
    r2 = r1 - r0
    if (r2 <= 1073741824) goto L0201d2e8
    r2 = r1 + r8
    if (r1 <= r9) {
    r2 = r0
    }
    [r4+20] = r2
L0201d2e8:
    call L0204180e  ; @call.xl
    r1 = [r4+20]
    r0 += 1  ; @add.ri.u5
    r0 = r0 >> 1
    ifs (r0 < r1) goto L0201d388
    r7 = r4 + 24
    csync
    b[r14+70] = r15
    call storage_coordination_irq_leave  ; @call.xl
    r1 = [r4+8]
    if (r1 == 0) goto L0201d316
    b[r14+r10] = r11
    r0 = [r4+12]
    call r1
    b[r14+r10] = r15
L0201d316:
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201d31e:
    testset b[r13]
    ifeq goto L0201d31e
    csync
    r0 = b[r7+3] (u)
    if ((r0 & 2) != 0) goto L0201d364
    call L02041866  ; @call.xl
    r1 = [r4+24]
    r1 = r1 & 0xFFFFFF
    r0 += r1  ; @add.rr
    [r4+20] = r0
    goto L0201d388
L0201d33e:
    csync
    r7 = r14
    b[++r7=70] = r15
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r4
    call phase3_p6_usr_timer_del_entry
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201d35a:
    testset b[r7]
    ifeq goto L0201d35a
    csync
    goto L0201d388
L0201d364:
    csync
    r7 = r14
    b[++r7=70] = r15
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r4
    call phase3_p6_usr_timer_del_entry
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201d380:
    testset b[r7]
    ifeq goto L0201d380
    csync
L0201d388:
    r4 = r5
    if (r4 != r6) goto L0201d2ba
    r12 = r12 + 1
L0201d392:
    if (r12 != 2) goto L0201d2ac
    call phase3_p13_get_min_precesion
    call phase3_p13_timer1_run
    csync
    r0 = 0
    b[r14+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r14 + 3908
    call L020403ee  ; @call.xl
    {r15-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti

; phase3_p6_sys_power_idle_query: 0x0201d3be..0x0201d3d4, module phase3-p6 (sys_power_idle_query)
.type phase3_p6_sys_power_idle_query,@function
phase3_p6_sys_power_idle_query:
    r0 = 464
    r1 = L01c1fa30
    r1 = b[r1+r0] (u)
    r0 = 1
    if (r1 == 0) goto L0201d3d2
    r0 = 0
L0201d3d2:
    rts
