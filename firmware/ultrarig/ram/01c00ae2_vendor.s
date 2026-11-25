; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c00ae2..0x01c00af8: vendor code (JieLi SDK or library, not reversed), as instructions
L01c00ae2:
    [--sp] = rets
    r0 = 0
    call storage_control_chip_select
    r0 = 117
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    pc = [sp++]
