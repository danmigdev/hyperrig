; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; boundary_hooks: 1 function, 0x0201c606..0x0201c622

; boundary_hooks_activity_note: 0x0201c606..0x0201c622, module boundary-hooks (activity_note)
.type boundary_hooks_activity_note,@function
boundary_hooks_activity_note:
    r0 = L01c1f180
    r1 = 300  #
    r0 = [r0+24]
    r0 = r0 * 0xA
    r2 = L01c26890
    [r2+r1<<2] = r0
    rts
