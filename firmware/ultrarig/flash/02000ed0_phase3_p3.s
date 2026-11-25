; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 1 function, 0x02000ed0..0x02000ee0

; phase3_p3_crc16_mutex_init: 0x02000ed0..0x02000ee0, module phase3-p3 (crc16_mutex_init)
.type phase3_p3_crc16_mutex_init,@function
phase3_p3_crc16_mutex_init:
    [--sp] = rets
    r0 = L01c25c90
    call L0203fb92  ; @call.xl
    pc = [sp++]
