; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_platform: 1 function, 0x01c041dc..0x01c04256

; storage_platform_interrupt: 0x01c041dc..0x01c04256, module storage-platform (interrupt)
.type storage_platform_interrupt,@function
storage_platform_interrupt:
    [--sp] = {psr, rets, reti}
    [--sp] = {r4-r0}
    r1 = cnum
    r0 = 32
    if (r1 == 0) goto L01c041ec
    r0 = 16
L01c041ec:
    r1 = 32436644
    [r1+0] = r0
    call storage_coordination_irq_enter
    csync
    r0 = 32432136
L01c04200:
    r1 = [r0+0]
    if ((r1 & 16384) == 0) goto L01c04200
    r0 = L01c3748d
    r2 = b[r0+0] (u)
    r1 = L01c1fc40
    r0 = L01c1fc48
    if (r2 == 0) goto L01c04242
    r4 = L01c1fc44
    r2 = 1
    b[r4+0] = r2
    csync
    csync
    r1 = [r1+0]
    if (r1 == 0) goto L01c04236
    r0 = [r0+0]
    call r1
    goto L01c04236
L01c04234:
    csync
L01c04236:
    r0 = b[r4+0] (u)
    if (r0 != 0) goto L01c04234
    r0 = 0
    b[r4+0] = r0
    csync
    goto L01c0424a
L01c04242:
    r1 = [r1+0]
    if (r1 == 0) goto L01c0424a
    r0 = [r0+0]
    call r1
L01c0424a:
    call storage_coordination_irq_leave
    {r4-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
