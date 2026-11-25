; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201d056..0x0201d1ea: vendor code (JieLi SDK or library, not reversed), as instructions
L0201d056:
    r0 = 29883724
    r0 = h[r0+28] (u)
    rts
L0201d060:
    [--sp] = {rets, r8-r4}
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r5 = 32669696
    r0 = r5 + 1
L0201d074:
    testset b[r0]
    ifeq goto L0201d074
    csync
    r6 = 0x10800
    [r6+0] = 0x4000
    r7 = 0
    r8 = 1  #
    [r6+4] = r7
    r2 = L0201d0f6
    r0 = 62
    r1 = 5
    r3 = 1
    call storage_platform_register
    r0 = L02035b57  ; "timer"
    call L020009ee
    r1 = 1000000
    r0 = r0 / r1 (s)
    r0 *= r4
    [r6+8] = r0
    [r6+0] = r8
    csync
    b[r5+1] = r7
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r8-r4} = [sp++]
L0201d0c4:
    [--sp] = rets
sdk_timer4_unset:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = 32669696
    r1 = r0 + 1
L0201d0d6:
    testset b[r1]
    ifeq goto L0201d0d6
    csync
    r1 = 0
    r2 = 0x10800
    [r2+0] = r1
    [r2+0] |= 0x4000
    csync
    b[r0+1] = r1
    call storage_coordination_irq_leave  ; @call.xl
    pc = [sp++]
L0201d0f6:
    [--sp] = {psr, rets, reti}
    [--sp] = {r6-r0}
    sp += -16
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r3 = 32669696
    r0 = r3 + 1
L0201d10e:
    testset b[r0]
    ifeq goto L0201d10e
    csync
    r0 = 0x10800
    [r0+0] |= 0x4000
    csync
    r6 = 0
    b[r3+1] = r6
    call storage_coordination_irq_leave  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r5 = L01c25ed8
L0201d138:
    testset b[r5]
    ifeq goto L0201d138
    csync
    r4 = [r3+4]
    if (r4 == 0) goto L0201d162
    r0 = b[r4+17] (u)
    if (r0 == 0) goto L0201d14e
    r0 = [r3+12]
    call r0
L0201d14e:
    r0 = b[r4+16] (u)
    r1 = [r4+0]
    if (r0 == 0) goto L0201d176
    r0 = [r4+4]
    call r1
    csync
    r0 = 0
    b[r5+0] = r0
    goto L0201d166
L0201d162:
    csync
    b[r5+0] = r6
L0201d166:
    call storage_coordination_irq_leave  ; @call.xl
L0201d16c:
    sp += 16
    {r6-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
L0201d176:
    [sp] = r1
    r0 = 1
    [sp+4] = r0
    r0 = [r4+4]
    [sp+8] = r0
    r4 = [r4+8]
    csync
    r0 = 0
    b[r5+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 == 0) goto L0201d16c
    r3 = sp + 0
    r1 = 0x300000
    r2 = 3
    r0 = r4
    call L02040bae  ; @call.xl
    if (r0 == 0) goto L0201d16c
    if (r0 == 21) goto L0201d16c
    r0 = L02035d46  ; "app_core"
    r3 = sp + 0
    r1 = 0x300000
    r2 = 3
    call L02040bae  ; @call.xl
    goto L0201d16c
L0201d1bc:
    r1 = 1544
    r0 = L01c26890
    r1 = b[r0+r1] (u)
    if (r1 == 0) goto L0201d1e0
    r1 = 66816
    r3 = 385  #
    r2 = [r1+4]
    [r0+r3<<2] = r2
    [r1+0] = 0x0
L0201d1e0:
    rts
L0201d1e2:
    [--sp] = rets
    call phase3_p13_timer1_resume
    pc = [sp++]
