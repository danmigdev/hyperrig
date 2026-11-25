; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 1 function, 0x020274e0..0x020274ea

; phase3_p12_setup_error_read_not_permitted: 0x020274e0..0x020274ea, module phase3-p12 (setup_error_read_not_permitted)
.type phase3_p12_setup_error_read_not_permitted,@function
phase3_p12_setup_error_read_not_permitted:
    [--sp] = rets
    r3 = 2
    call L02027294
    pc = [sp++]
