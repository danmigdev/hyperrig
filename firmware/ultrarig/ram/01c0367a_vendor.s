; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c0367a..0x01c0383e: vendor code (JieLi SDK or library, not reversed), as instructions
sdk___hw_nv_timer_is_runnig:
    [--sp] = {rets, r4}
    r4 = 4
    if (r0 != 0) goto L01c03682
    r4 = 2
L01c03682:
    r0 = 53
    call storage_fault_read_register
    r1 = r0
    r0 = 1
    if ((r1 & r4) == 0) {
    r0 = 0
    }
    {pc, r4} = [sp++]
L01c03694:
    [--sp] = {rets, r10-r4}
    call storage_fault_acquire
    r4 = 81416
    [r4+0] &= 0xFFFFFEFF
    [r4+0] |= 0x1
    r0 = 32
    call storage_fault_exchange
    r0 = 96
    call storage_fault_exchange
    r0 = 2
    call storage_fault_exchange
    r0 = 0
    call storage_fault_exchange
    r0 = 0
    call storage_fault_exchange
    r8 = r0
    r0 = 0
    call storage_fault_exchange
    r9 = r0
    r0 = 0
    call storage_fault_exchange
    r5 = r0
    r0 = 0
    call storage_fault_exchange
    r10 = -258
    [r4+0] &= r10
    r6 = r0
    call storage_fault_release
    call storage_fault_acquire
    [r4+0] &= 0xFFFFFEFF
    [r4+0] |= 0x1
    r0 = 128
    call storage_fault_exchange
    r0 = 68
    call storage_fault_exchange
    r0 = 0
    call storage_fault_exchange
    r2 = r0
    r0 = 0
    call storage_fault_exchange
    r7 = r0
    r0 = 0
    call storage_fault_exchange
    r3 = r0
    r0 = 0
    call storage_fault_exchange
    [r4+0] &= r10
    r1 = r8 << 24
    r1 <= insert(r9, p:16, l:8)
    r1 <= insert(r5, p:8, l:8)
    r1 |= r6
    r2 = r2 << 24
    r2 <= insert(r7, p:16, l:8)
    r2 <= insert(r3, p:8, l:8)
    r0 |= r2
    r3 = r0 - r1
    call storage_fault_release
    r0 = r3
    {pc, r10-r4} = [sp++]
L01c0374a:
    [--sp] = rets
    r0 = 89
    r1 = 254
    call L01c0100e
    r0 = 89
    r1 = 64
    call L01c00f72
    r0 = 89
    r1 = 16
    call L01c00f72
    pc = [sp++]
L01c03766:
    [--sp] = {rets, r7-r4}
    r6 = L01c1fa30
    r2 = [r6+460]
    r3_r2 = r2 * r1 (u)
    r1 = 1000000
    r5_r4 = r3_r2 / r1 (u)  #
    r1 = [r6+56]
    r2 = r0
    r0 = 0
    if (r4 < r1) goto L01c03810
    call storage_fault_acquire
    r3 = 81416
    [r3+0] &= 0xFFFFFEFF
    [r3+0] |= 0x1
    r0 = 0
    call storage_fault_exchange
    r0 = r2
    call storage_fault_exchange
    r0 = r6 + 468  #
    r2 = [r6+48]
    r1 = b[r0+1] (u)
    r6 = -1
    r1 = r6 << r1  #
    r7 = b[r0+2] (u)
    r2 = r4 - r2  #
    r0 = b[r0+3] (u)
    r1 += r2  ; @add.rr
    r2 = r6 << r7
    r1 += r2  ; @add.rr
    r0 = r6 << r0
    r2 = r1 + r0
    r0 = r2 >> 24
    call storage_fault_exchange
    r0 = uextra(r2, p:16, l:8)
    call storage_fault_exchange
    r0 = uextra(r2, p:8, l:8)
    call storage_fault_exchange
    r0 = r2.b0 (u)
    call storage_fault_exchange
    r0 = r4 >> 24
    call storage_fault_exchange
    r0 = uextra(r4, p:16, l:8)
    call storage_fault_exchange
    r0 = uextra(r4, p:8, l:8)
    call storage_fault_exchange
    r0 = r4.b0 (u)
    call storage_fault_exchange
    r0 = -258
    [r3+0] &= r0
    call storage_fault_release
    r0 = 1
L01c03810:
    {pc, r7-r4} = [sp++]
L01c03812:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = 19
    r1 = 209
    call storage_fault_write_register
    r0 = 20
    r1 = 209
    call storage_fault_write_register
    r0 = 49
    r1 = 68
    call storage_fault_write_register
    r0 = 89
    r1 = 89
    call storage_fault_write_register
    r0 = 72
    r1 = r4
    call L01c03766
    {pc, r4} = [sp++]
