; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_reload_and_leaves: 1 function, 0x02017af8..0x02017b1a

; ir_reload_and_leaves_percent: 0x02017af8..0x02017b1a, module ir-reload-and-leaves (percent)
.type ir_reload_and_leaves_percent,@function
ir_reload_and_leaves_percent:
    if (r1 == 0) goto L02017b16
    r2 = 42949672
    if (r0 > r2) {
    r2 = 100
    r1 = r1 / r2 (u)
    r1 += 1  ; @add.ri.u5
    } else {
    r0 = r0 * 0x64
    }
    r0 = r0 / r1 (u)
    rts
L02017b16:
    r0 = 0
    rts
