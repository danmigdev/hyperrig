; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 3 functions, 0x02025dfc..0x02025eaa

; phase3_p11_atomic_sub_return: 0x02025dfc..0x02025e40, module phase3-p11 (atomic_sub_return)
.type phase3_p11_atomic_sub_return,@function
phase3_p11_atomic_sub_return:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L02025e1e
    lockset
L02025e1e:
    csync
    [r2+0] += -1  ; @rmw.add.s12
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L02025e38
    lockclr
L02025e38:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]

; phase3_p11_thread_suspend: 0x02025e40..0x02025ea2, module phase3-p11 (thread_suspend)
.type phase3_p11_thread_suspend,@function
phase3_p11_thread_suspend:
    [--sp] = {rets, r5, r4}
    r2 = r1
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r4 = [r1+r0<<2]
    r5 = r4 + 1
    [r1+r0<<2] = r5
    r0 = L01c1fa20
    if (r4 != 0) goto L02025e72
    csync
L02025e6a:
    testset b[r0]
    ifeq goto L02025e6a
    csync
L02025e72:
    r3 += 21  ; @add.ri.u5
    b[r3+1] = r2
    if (r2 != 0) goto L02025e84
    r2 = b[r3+0] (u)
    r4 = r2 + -1
    if (r2 == 0) goto L02025e82
    r2 = r4
L02025e82:
    b[r3+0] = r2
L02025e84:
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L02025e9a
    csync
    r1 = 0
    b[r0+0] = r1
L02025e9a:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]

; phase3_p11_crc_get_16bit: 0x02025ea2..0x02025eaa, module phase3-p11 (crc_get_16bit)
.type phase3_p11_crc_get_16bit,@function
phase3_p11_crc_get_16bit:
    [--sp] = rets
    call L02001776
    pc = [sp++]
