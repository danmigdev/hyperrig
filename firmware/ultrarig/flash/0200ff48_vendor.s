; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0200ff48..0x0200ff76: vendor code (JieLi SDK or library, not reversed), as instructions
L0200ff48:
    [--sp] = rets
    r3 = r0.b0 (u)
    r0 = 4
    r1 = 1
    r2 = 3
    call storage_fault_masked_register  ; @call.xl
    r0 = 4
    r1 = 5
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
    r0 = 4
    r1 = 0
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
    pc = [sp++]
