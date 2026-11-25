; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 1 function, 0x02025944..0x020259be

; phase3_p11_hw_dma_pop: 0x02025944..0x020259be, module phase3-p11 (hw_dma_pop)
.type phase3_p11_hw_dma_pop,@function
phase3_p11_hw_dma_pop:
    [--sp] = {rets, r5, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    r4 = L01c1fa20
    if (r1 != 0) goto L02025974
    csync
L0202596c:
    testset b[r4]
    ifeq goto L0202596c
    csync
L02025974:
    r3 = [r2+0]
    if (r3 == r2) goto L0202599c
    r0 = r3
    call L02025936
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02025994
    csync
    r0 = 0
    b[r4+0] = r0
L02025994:
    call storage_coordination_irq_leave  ; @call.xl
    goto L020259ba
L0202599c:
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L020259b2
    csync
    r0 = 0
    b[r4+0] = r0
L020259b2:
    call storage_coordination_irq_leave  ; @call.xl
    r3 = 0
L020259ba:
    r0 = r3
    {pc, r5, r4} = [sp++]
