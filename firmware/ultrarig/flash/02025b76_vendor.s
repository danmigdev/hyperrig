; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02025b76..0x02025c62: vendor code (JieLi SDK or library, not reversed), as instructions
L02025b76:
    [--sp] = rets
    r0 = r0.l (u)
    call phase3_p6_sys_timer_del
    pc = [sp++]
L02025b80:
    [--sp] = {rets, r4}
    r2 = r0
    r3 = [r2+-8]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r3 += 16  ; @add.ri.u5
L02025b90:
    testset b[r3]
    ifeq goto L02025b90
    csync
    r4 = 0
    b[r2+-2] = r4
    r0 = b[r2+-1] (u)
    r1 = r0 + 1
    b[r2+-1] = r1
    if (r0 != 0) goto L02025bae
    r0 = r2 + -16  #
    r1 = [r2+-8]
    call sdk_list_add_tail_0202502c
L02025bae:
    csync
    b[r3+0] = r4
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]
L02025bba:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r3 = [r1+r0<<2]
    r4 = r3 + 1
    [r1+r0<<2] = r4
    r0 = L01c1fa20
    if (r3 != 0) goto L02025bea
    csync
L02025be2:
    testset b[r0]
    ifeq goto L02025be2
    csync
L02025bea:
    r4 = 0
    r3 = r2 + 8
    b[r3+14] = r4
    r2 = b[r3+13] (u)
    r4 = 1
    if (r2 == 255) {  ; @if.eq.ri.s12
    r4 = 0
    }
    r2 += r4  ; @add.rr
    b[r3+13] = r2
    r2 = cnum
    r4 = [r1+r2<<2]
    r4 += -1
    [r1+r2<<2] = r4
    if (r4 != 0) goto L02025c14
    csync
    r1 = 0
    b[r0+0] = r1
L02025c14:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+0]
    r0 = [r0+20]
    call r0
    {pc, r4} = [sp++]
L02025c22:
    [--sp] = {rets, r5, r4}
    r4 = r0
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02025c3e
    r1 = 0
    r2 = r4
    call effect_enable_memset  ; @call.xl
    r0 = r5
    {pc, r5, r4} = [sp++]
L02025c3e:
    r0 = rets
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02025c4c:
    goto L02025c4c
L02025c4e:
    [--sp] = rets
    call L02025c22
    if (r0 == 0) goto L02025c56
    pc = [sp++]
L02025c56:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02025c60:
    goto L02025c60
