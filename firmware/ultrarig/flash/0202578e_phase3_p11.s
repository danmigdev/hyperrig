; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 3 functions, 0x0202578e..0x02025896

; phase3_p11_low_power_exit_request: 0x0202578e..0x020257f8, module phase3-p11 (low_power_exit_request)
.type phase3_p11_low_power_exit_request,@function
phase3_p11_low_power_exit_request:
    [--sp] = {rets, r5, r4}
    r2 = L01c1fa30
    r0 = b[r2+93] (u)
    if ((r0 & 8) == 0) goto L020257f6
    r0 = b[r2+98] (u)
    if (r0 != 0) goto L020257f6
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    r4 = L01c1fa20
    if (r1 != 0) goto L020257d0
    csync
L020257c8:
    testset b[r4]
    ifeq goto L020257c8
    csync
L020257d0:
    r0 = b[r2+89] (u)
    if (r0 == 0) goto L020257da
    call L02025626
L020257da:
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L020257f0
    csync
    r0 = 0
    b[r4+0] = r0
L020257f0:
    call storage_coordination_irq_leave  ; @call.xl
L020257f6:
    {pc, r5, r4} = [sp++]

; phase3_p11_hw_dma_push: 0x020257f8..0x02025852, module phase3-p11 (hw_dma_push)
.type phase3_p11_hw_dma_push,@function
phase3_p11_hw_dma_push:
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
    if (r4 != 0) goto L0202582a
    csync
L02025822:
    testset b[r0]
    ifeq goto L02025822
    csync
L0202582a:
    r4 = [r3+4]
    [r3+4] = r2
    [r2+] = {r4, r3}
    [r4+0] = r2
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L0202584a
    csync
    r1 = 0
    b[r0+0] = r1
L0202584a:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]

; phase3_p11_atomic_set: 0x02025852..0x02025896, module phase3-p11 (atomic_set)
.type phase3_p11_atomic_set,@function
phase3_p11_atomic_set:
    [--sp] = {rets, r5, r4}
    r2 = r1
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r4 = [r0+r1<<2]
    r5 = r4 + 1
    [r0+r1<<2] = r5
    if (r4 != 0) goto L02025876
    lockset
L02025876:
    csync
    [r3+0] = r2
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0202588e
    lockclr
L0202588e:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
