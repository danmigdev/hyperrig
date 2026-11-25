; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; triplet_helpers: 1 function, 0x02015458..0x02015476

; triplet_helpers_brighter_triplet: 0x02015458..0x02015476, module triplet-helpers (brighter_triplet)
.type triplet_helpers_brighter_triplet,@function
triplet_helpers_brighter_triplet:
    [--sp] = {rets, r4}
    r2 = 0
    goto L02015470
L0201545e:
    r3 = b[r1+r2] (u)
    r4 = b[r0+r2] (u)
    if (r3 > r4) {
    b[r0+r2] = r3
    }
    r2 += 1  ; @add.ri.u5
L02015470:
    if (r2 != 3) goto L0201545e
    {pc, r4} = [sp++]
