; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p14: 1 function, 0x02000570..0x020005ac

; phase3_p14_interrupt_init: 0x02000570..0x020005ac, module phase3-p14 (interrupt_init)
.type phase3_p14_interrupt_init,@function
phase3_p14_interrupt_init:
    [--sp] = rets
    call storage_platform_gate_disable
    r0 = cnum
    if (r0 == 0) goto L02000592
    r0 = 0
    r1 = 32436992
    r2 = 0
    goto L0200058c
L02000586:
    [r1+r2<<2] = r0
    r2 += 1  ; @add.ri.u5
L0200058c:
    if (r2 != 32) goto L02000586
    goto L020005a8
L02000592:
    r0 = 0
    r1 = 32436480
    r2 = 0
    goto L020005a4
L0200059e:
    [r1+r2<<2] = r0
    r2 += 1  ; @add.ri.u5
L020005a4:
    if (r2 != 32) goto L0200059e
L020005a8:
    call storage_platform_gate_enable
    pc = [sp++]
