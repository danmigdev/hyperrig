; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_coordination: 2 functions, 0x01c00e2e..0x01c00e62

; storage_coordination_irq_enter: 0x01c00e2e..0x01c00e46, module storage-coordination (irq_enter)
.type storage_coordination_irq_enter,@function
storage_coordination_irq_enter:
    cli
    r0 = cnum
    r0 = r0 << 2
    r1 = L01c1fc54
    r0 += r1  ; @add.rr
    [r0+0] += 1  ; @rmw.add.s12
    csync
    rts

; storage_coordination_irq_leave: 0x01c00e46..0x01c00e62, module storage-coordination (irq_leave)
.type storage_coordination_irq_leave,@function
storage_coordination_irq_leave:
    r0 = cnum
    r1 = L01c1fc54
    r2 = [r1+r0<<2]
    r2 += -1
    [r1+r0<<2] = r2
    if (r2 != 0) goto L01c00e60
    csync
    sti
L01c00e60:
    rts
