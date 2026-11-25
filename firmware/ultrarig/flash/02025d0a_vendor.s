; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02025d0a..0x02025db2: vendor code (JieLi SDK or library, not reversed), as instructions
L02025d0a:
    [--sp] = rets
    {r3, r1} = [r0+]
    r2 = [r0+8]
    [r1+4] = r3
    [r3+0] = r1
    [r0+0] = r0
    [r0+4] = r0
    r3 = [r2+0]
    r1 = 0
    if (r3 != r2) goto L02025d2c
    r0 = b[r0+20] (u)
    r1 = [r2+12]
    call r1
    r1 = r0
L02025d2c:
    r0 = r1
    pc = [sp++]
L02025d30:
    [--sp] = {rets, r6-r4}
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r5 = r4 + 16
L02025d3e:
    testset b[r5]
    ifeq goto L02025d3e
    csync
    r0 = [r4+0]
    goto L02025d54
L02025d4a:
    r6 = [r0++=16]
    call L02025896
    r0 = r6
L02025d54:
    if (r0 != r4) goto L02025d4a
    csync
    r0 = 0
    b[r5+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]
L02025d66:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = [r4+0]
    goto L02025d7a
L02025d6e:
    r1 = b[r0+21] (u)
    r5 = [r0+0]
    if (r1 == 0) goto L02025d7a
    r1 = [r0+16]
    call r1
L02025d7a:
    r0 = r5
    if (r0 != r4) goto L02025d6e
    r1 = r4
    goto L02025d92
L02025d84:
    r3 = b[r1+21] (u)
    r2 = b[r1+22] (u)
    if (r3 != 0) goto L02025da2
    r0 = smin(r0, r2)
L02025d92:
    r1 = [r1+0]
    if (r1 != r4) goto L02025d84
    r1 = r0.b0 (u)  #
    r2 = [r4+16]
    r0 = 0
    call r2
    {pc, r5, r4} = [sp++]
L02025da2:
    if (r2 != 0) goto L02025da6
    {pc, r5, r4} = [sp++]
L02025da6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02025db0:
    goto L02025db0
