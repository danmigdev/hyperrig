; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 2 functions, 0x020282ac..0x020282bc

; phase3_p12_atoi: 0x020282ac..0x020282b4, module phase3-p12 (atoi)
.type phase3_p12_atoi,@function
phase3_p12_atoi:
    r1 = 0
    r2 = 10
    goto capture_command_decimal  ; @goto.l

; phase3_p12_atoi_r: 0x020282b4..0x020282bc, module phase3-p12 (atoi_r)
.type phase3_p12_atoi_r,@function
phase3_p12_atoi_r:
    r2 = 0
    r3 = 10
    goto capture_command_decimal_core  ; @goto.l
