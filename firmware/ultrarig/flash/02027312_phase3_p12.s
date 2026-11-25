; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 1 function, 0x02027312..0x0202731a

; phase3_p12_setup_error_atribute_not_found: 0x02027312..0x0202731a, module phase3-p12 (setup_error_atribute_not_found)
.type phase3_p12_setup_error_atribute_not_found,@function
phase3_p12_setup_error_atribute_not_found:
    [--sp] = rets
    r3 = 10
    call L02027294
    pc = [sp++]
