; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; control_actions: 1 function, 0x0200c996..0x0200c9a4

; control_actions_clock: 0x0200c996..0x0200c9a4, module control-actions (clock)
.type control_actions_clock,@function
control_actions_clock:
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 * 0xA
    rts
