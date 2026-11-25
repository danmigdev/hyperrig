; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 1 function, 0x02005964..0x020059bc

; link_and_print_link_resume: 0x02005964..0x020059bc, module link-and-print (link_resume)
.type link_and_print_link_resume,@function
link_and_print_link_resume:
    [--sp] = {rets, r7-r4}
    if (r0 == 0) goto L020059ba
    r0 = 5
    call L0203feb8  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r4 = L01c26890
    r0 = r4 + 2
L02005980:
    testset b[r0]
    ifeq goto L02005980
    csync
    r0 = r4 + 1716
    r5 = [r0+4]
    r6 = [r0+8]
    r7 = 0
    b[r0+2] = r7
    [r0+8] = r5
    r1 = 1
    b[r0+1] = r1
    call state_queries_toggle_update
    r3 = r0
    csync
    b[r4+2] = r7
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    call link_and_print_usb_restart
    r2 = r5 - r6
    if (r2 == 0) goto L020059ba
    r0 = 14
    r1 = 18
    call storage_coordination_notify
L020059ba:
    {pc, r7-r4} = [sp++]
