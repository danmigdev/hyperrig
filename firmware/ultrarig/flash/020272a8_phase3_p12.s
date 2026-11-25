; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 1 function, 0x020272a8..0x020272b0

; phase3_p12_setup_error_invalid_handle: 0x020272a8..0x020272b0, module phase3-p12 (setup_error_invalid_handle)
.type phase3_p12_setup_error_invalid_handle,@function
phase3_p12_setup_error_invalid_handle:
    [--sp] = rets
    r3 = 1
    call L02027294
    pc = [sp++]
