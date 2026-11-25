; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; boundary_hooks: 1 function, 0x0201cada..0x0201cc12

; boundary_hooks_sm_handler: 0x0201cada..0x0201cc12, module boundary-hooks (sm_handler)
.type boundary_hooks_sm_handler,@function
boundary_hooks_sm_handler:
    [--sp] = {rets, r7-r4}
    r3 = r2
    if (r0 != 4) goto L0201cb76
    call boundary_hooks_activity_note
    r0 = b[r3+0] (u)
    r5 = L01c26890
    if (r0 == 223) goto L0201cb3c
    if (r0 != 208) goto L0201cb76
    r1 = 2
    r0 = r3
    call L0204cb74  ; @call.xl
    r4 = r0
    call L0204cb82  ; @call.xl
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r5 + 58
L0201cb16:
    testset b[r0]
    ifeq goto L0201cb16
    csync
    call console_helpers_now_ms
    r1 = 1536
    r1 = b[r5+r1] (u)
    r7_r6 = 0
    if (r1 != 0) goto L0201cb7a
    if (r3 == 0) goto L0201cb78
    call console_helpers_key_left
    r6 = 1
    if (r0 != 0) goto L0201cb7a
    r6 = r0
    goto L0201cb7a
L0201cb3c:
    r4 = b[r3+11] (u)
    call L0204cb82  ; @call.xl
    r2 = r4
    r2 <= insert(r0, p:8, l:16)
    r0 = 32
    r1 = -5
    call storage_coordination_notify
    r0 = r4 + -1
    if (r0 > 16) goto L0201cb76
    tbb [r0]
boundary_hooks_pairing_status_cases:
    .byte (L0201cbb2 - boundary_hooks_pairing_status_cases) / 2, (L0201cbcc - boundary_hooks_pairing_status_cases) / 2, (L0201cb6e - boundary_hooks_pairing_status_cases) / 2, (L0201cb6e - boundary_hooks_pairing_status_cases) / 2, (L0201cb6e - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2
    .byte (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cb76 - boundary_hooks_pairing_status_cases) / 2, (L0201cbda - boundary_hooks_pairing_status_cases) / 2
    .byte (L0201cb6e - boundary_hooks_pairing_status_cases) / 2
    .byte 0x00  ; alignment
L0201cb6e:
    r0 = r5 + 1324
    [r0+0] += 1  ; @rmw.add.s12
L0201cb76:
    {pc, r7-r4} = [sp++]
L0201cb78:
    r6 = 1
L0201cb7a:
    csync
    b[r5+58] = r7
    call storage_coordination_irq_leave  ; @call.xl
    r2 = r6
    r2 <= insert(r3, p:8, l:16)
    r0 = 32
    r1 = -6
    call storage_coordination_notify
    if (r6 == 0) goto L0201cba0
    r0 = r4
    call L020522e2  ; @call.xl
    {pc, r7-r4} = [sp++]
L0201cba0:
    r0 = r5 + 1308
    [r0+0] += 1  ; @rmw.add.s12
    r0 = r4
    call L020535be  ; @call.xl
    {pc, r7-r4} = [sp++]
L0201cbb2:
    r0 = r5 + 1292
    [r0+24] += 1  ; @rmw.add.s12
    r1 = L01c1f180
    r1 = [r1+24]
    r1 = r1 * 0xA
    r1 |= 1
    [r0+0] = r1
    {pc, r7-r4} = [sp++]
L0201cbcc:
    r0 = r5 + 1292
    [r0+28] += 1  ; @rmw.add.s12
    [r0+0] = 0x0
    {pc, r7-r4} = [sp++]
L0201cbda:
    r3 = r5 + 1272
    [r3+40] += 1  ; @rmw.add.s12
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r5 + 58
L0201cbee:
    testset b[r0]
    ifeq goto L0201cbee
    csync
    r0 = 1532
    r1 = 0
    b[r5+r0] = r1
    csync
    b[r5+58] = r1
    call storage_coordination_irq_leave  ; @call.xl
    [r3+0] += 1  ; @rmw.add.s12
    {pc, r7-r4} = [sp++]
