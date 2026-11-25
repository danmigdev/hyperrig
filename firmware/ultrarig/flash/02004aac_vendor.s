; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02004aac..0x02004b9c: vendor code (JieLi SDK or library, not reversed), as instructions
L02004aac:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = -22
    if (r4 > 1) goto L02004ad4
    r5 = 32922
    r0 = r5
    call storage_fault_read_register  ; @call.xl
    r0 = r0 | (1 << r4)
    r1 = r0.b0 (u)
    r0 = r5
    call storage_fault_write_register  ; @call.xl
    r0 = 0
L02004ad4:
    {pc, r5, r4} = [sp++]
L02004ad6:
    [--sp] = {rets, r4}
    r2 = r0
    if (r2 < 148) goto L02004ae6
    r1 = 1
    call L02004904
    {pc, r4} = [sp++]
L02004ae6:
    if (r2 != 16) goto L02004b00
    r0 = 32
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 154
    r1 = 1
    call storage_fault_write_register  ; @call.xl
    {pc, r4} = [sp++]
L02004b00:
    if (r2 < 144) goto L02004b0e
    r0 = r2 + 112
    r0 = r0.b0 (u)
    call L02004aac
    {pc, r4} = [sp++]
L02004b0e:
    call sdk_gpio2reg
    r3 = r0
    if (r3 == -1) goto L02004b46
    r0 = r2 >> 4
    r1 = L01c25ce0
    r4 = r0 + r1
    call storage_coordination_irq_enter  ; @call.xl
    csync
L02004b2a:
    testset b[r4]
    ifeq goto L02004b2a
    csync
    r0 = r2 & 0xF
    [r3+8] |= 1 << r0
    csync
    r0 = 0
    b[r4+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
L02004b46:
    {pc, r4} = [sp++]
L02004b48:
    r2 = r0 & 0xFFFFFFFE
    if (r2 == 150) goto L02004b72
    if (r2 != 148) goto L02004b9a
    r0 = r0 + -144
    r2 = 1
    r2 <<= r0
    r0 = 0x51000
    if (r1 == 0) {  ; @if.eq.ri.s12
    r1 = [r0+0]
    r1 = r1 & ~r2
    } else {
    r1 = [r0+0]
    r1 |= r2
    }
    [r0+0] = r1
    rts
L02004b72:
    r2 = 92684
    if (r0 == 151) goto L02004b8c
    if (r0 != 150) goto L02004b9a
    r0 = [r2+0]
    r3 = r0 & 0xFFFFFEFF
    r0 |= 256
    if (r1 == 0) goto L02004b96
    goto L02004b98
L02004b8c:
    r0 = [r2+0]
    r3 = r0 & 0xFFFFFDFF
    r0 |= 512
    if (r1 != 0) goto L02004b98
L02004b96:
    r0 = r3
L02004b98:
    [r2+0] = r0
L02004b9a:
    rts
