; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_commands: 1 function, 0x0200733e..0x02007348

; slot_commands_requested: 0x0200733e..0x02007348, module slot-commands (requested)
.type slot_commands_requested,@function
slot_commands_requested:
    r0 = L01c1f180
    r0 = b[r0+2] (u)
    rts
