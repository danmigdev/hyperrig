; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c00fdc..0x01c01058: vendor code (JieLi SDK or library, not reversed), as instructions
L01c00fdc:
    [--sp] = {rets, r4}
    r4 = 81416
    r2 = r0  #
    r1 = [r4+0]
    r0 = uextra(r1, p:2, l:2)
    r3 = r0 + 1
    if (r2 == 0) goto L01c0100a
    call storage_fault_acquire
    [r4+0] &= 0xFFFFFFF3
    r0 = r2 << 2
    r0 += 12  ; @add.ri.u5
    r0 = r0 & 0xC
    [r4+0] |= r0
    csync
    call storage_fault_release
L01c0100a:
    r0 = r3.b0 (u)
    {pc, r4} = [sp++]
L01c0100e:
    [--sp] = {rets, r5, r4}
    r2 = r1
    r3 = r0
    r5 = r3.l (s)
    call storage_fault_acquire
    r4 = 81416
    ifs (r5 >= 0) {  ; @ifs.ge.ri.s12
    [r4+0] &= 0xFFFFFEFF
    r0 = 1
    } else {
    r0 = 257
    }
    [r4+0] |= r0
    r0 = uextra(r3, p:8, l:2)
    r0 |= 64
    call storage_fault_exchange
    r0 = r3 & 0xFFFF00FF
    call storage_fault_exchange
    r0 = r2
    call storage_fault_exchange
    r0 = -258
    [r4+0] &= r0
    call storage_fault_release
    {pc, r5, r4} = [sp++]
