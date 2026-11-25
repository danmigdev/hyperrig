; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_reload_and_leaves: 1 function, 0x020057c6..0x0200580c

; ir_reload_and_leaves_get_rate: 0x020057c6..0x0200580c, module ir-reload-and-leaves (get_rate)
.type ir_reload_and_leaves_get_rate,@function
ir_reload_and_leaves_get_rate:
    r0 = 680
    r1 = L01c26890
    r0 = b[r1+r0] (u)
    if (r0 == 0) goto L020057e0
    r0 = L01c1f180
    r0 = [r0+44]
    rts
L020057e0:
    r0 = 65556
    r0 = [r0+0]
    r1 = r0 & 0xF
    r0 = 0
    if (r1 != 6) goto L0200580a
    r0 = 72108
    r1 = 16380  #
    r0 = [r0+0]
    r0 = r0 << 2
    r0 &= r1
    r0 += 8  ; @add.ri.u5
    r1 = 3
    r0 = r0 / r1 (u)
L0200580a:
    rts
