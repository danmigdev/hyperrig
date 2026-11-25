; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 1 function, 0x02029fc8..0x0202a00a

; effect_construction_size: 0x02029fc8..0x0202a00a, module effect-construction (size), effect-model-construction (size)
.type effect_construction_size,@function
effect_construction_size:
    if (r0 != 12) {
    r2 = 6500
    } else {
    r2 = 4250
    }
    r3 = 0
    if (r0 == 11) {
    r2 = 10000
    }
    r0 = L01c1f7f0
    r0 = [r0+8]
    r1_r0 = r0 * r2 (u)
    r2 = 1000000
    r1_r0 = r1_r0 / r2 (u)
    r1 = r0 + 19
    r2 = 256
L02029ffa:
    r0 = r2
    if (r0 >= r1) goto L0202a008
    r2 = r0 << 1
    if (r0 < 2048) goto L02029ffa
L0202a008:
    rts
