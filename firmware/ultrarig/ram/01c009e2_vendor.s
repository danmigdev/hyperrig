; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c009e2..0x01c00a02: vendor code (JieLi SDK or library, not reversed), as instructions
L01c009e2:
    [--sp] = {rets, r4}
    r0 = 0
    call storage_control_chip_select
    r0 = 5
    call storage_control_send_byte
    call storage_control_receive_byte
    r4 = r0
    r0 = 1
    call storage_control_chip_select
    r0 = r4 & 0xFFFFFF01
    {pc, r4} = [sp++]
