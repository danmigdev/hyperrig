; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; triplet_helpers: 1 function, 0x02015326..0x02015348

; triplet_helpers_scale_triplet: 0x02015326..0x02015348, module triplet-helpers (scale_triplet)
.type triplet_helpers_scale_triplet,@function
triplet_helpers_scale_triplet:
    [--sp] = {rets, r4}
    if (r2 >= 256) {  ; @if.ge.ri.s12
    r2 = 256
    }
    r3 = 0
    goto L02015342
L02015334:
    r4 = b[r1+r3] (u)
    r4 *= r2
    r4 = r4 >> 8
    b[r0+r3] = r4
    r3 += 1  ; @add.ri.u5
L02015342:
    if (r3 != 3) goto L02015334
    {pc, r4} = [sp++]
