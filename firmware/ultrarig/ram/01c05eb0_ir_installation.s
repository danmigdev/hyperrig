; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_installation: 1 function, 0x01c05eb0..0x01c05ec6

; ir_installation_gain_clamp: 0x01c05eb0..0x01c05ec6, module ir-installation (gain_clamp)
.type ir_installation_gain_clamp,@function
ir_installation_gain_clamp:
    r1 = 4294907296
    ifs (r0 >= r1) {
    r1 = 20000
    r1 = smin(r0, r1)
    }
    r0 = r1
    rts
