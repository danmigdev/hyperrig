; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_fault: 6 functions, 0x01c00e86..0x01c00f72

; storage_fault_acquire: 0x01c00e86..0x01c00e9c, module storage-fault (acquire)
.type storage_fault_acquire,@function
storage_fault_acquire:
    [--sp] = rets
    call storage_coordination_irq_enter
    csync
    r0 = L01c1fa2c
L01c00e92:
    testset b[r0]
    ifeq goto L01c00e92
    csync
    pc = [sp++]

; storage_fault_exchange: 0x01c00e9c..0x01c00eb6, module storage-fault (exchange)
.type storage_fault_exchange,@function
storage_fault_exchange:
    r1 = 81416
    [r1+4] = r0
    [r1+0] |= 0x10
    csync
L01c00eaa:
    r0 = [r1+0]
    if ((r0 & 2) != 0) goto L01c00eaa
    r0 = [r1+4]
    r0 = r0.b0 (u)
    rts

; storage_fault_release: 0x01c00eb6..0x01c00ec8, module storage-fault (release)
.type storage_fault_release,@function
storage_fault_release:
    [--sp] = rets
    csync
    r0 = L01c1fa2c
    r1 = 0
    b[r0+0] = r1
    call storage_coordination_irq_leave
    pc = [sp++]

; storage_fault_read_register: 0x01c00ec8..0x01c00f0c, module storage-fault (read_register)
.type storage_fault_read_register,@function
storage_fault_read_register:
    [--sp] = {rets, r4}
    r2 = r0
    r4 = r2.l (s)
    call storage_fault_acquire
    r3 = 81416
    ifs (r4 >= 0) {  ; @ifs.ge.ri.s12
    [r3+0] &= 0xFFFFFEFF
    r0 = 1
    } else {
    r0 = 257
    }
    [r3+0] |= r0
    r0 = r2 >> 8
    r0 |= 128
    r0 = r0 & 0x83
    call storage_fault_exchange
    r0 = r2 & 0xFFFF00FF
    call storage_fault_exchange
    r0 = 94
    call storage_fault_exchange
    r1 = -258
    [r3+0] &= r1
    r3 = r0
    call storage_fault_release
    r0 = r3
    {pc, r4} = [sp++]

; storage_fault_write_register: 0x01c00f0c..0x01c00f4a, module storage-fault (write_register)
.type storage_fault_write_register,@function
storage_fault_write_register:
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
    call storage_fault_exchange
    r0 = r3 & 0xFFFF00FF
    call storage_fault_exchange
    r0 = r2
    call storage_fault_exchange
    r0 = -258
    [r4+0] &= r0
    call storage_fault_release
    {pc, r5, r4} = [sp++]

; storage_fault_masked_register: 0x01c00f4a..0x01c00f72, module storage-fault (masked_register)
.type storage_fault_masked_register,@function
storage_fault_masked_register:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = -1
    r0 <<= r2
    r2 = r3 & ~r0
    r5 = r2 << r1
    r0 = ~r0
    r6 = r0 << r1
    r0 = r4
    call storage_fault_read_register
    r0 = r0 & ~r6
    r0 |= r5
    r1 = r0.b0 (u)
    r0 = r4
    call storage_fault_write_register
    {pc, r6-r4} = [sp++]
