; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201e274..0x0201e2c6: vendor code (JieLi SDK or library, not reversed), as instructions
L0201e274:
    [--sp] = rets
    if (r0 == 0) goto L0201e282
    r0 = 0x16800
    [r0+0] |= 0x40
    pc = [sp++]
L0201e282:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0201e2a0
    lockset
L0201e2a0:
    csync
    r1 = 0x11800
    [r1+0] |= 0x1000
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0201e2be
    lockclr
L0201e2be:
    call storage_coordination_irq_leave  ; @call.xl
    pc = [sp++]
