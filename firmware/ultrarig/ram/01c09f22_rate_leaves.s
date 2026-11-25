; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; rate_leaves: 1 function, 0x01c09f22..0x01c09f3a

; rate_leaves_step_toward: 0x01c09f22..0x01c09f3a, module rate-leaves (step_toward)
.type rate_leaves_step_toward,@function
rate_leaves_step_toward:
    if (r0 < r1) {
    r0 = r0 + 1
    r0 = r0.l (u)
    rts
    }
    r2 = 1
    if (r0 <= r1) {
    r2 = 0
    }
    r0 = r0 - r2
    r0 = r0.l (u)
    rts
