; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; triplet_helpers: 1 function, 0x0201565a..0x02015688

; triplet_helpers_blend_triplets: 0x0201565a..0x02015688, module triplet-helpers (blend_triplets)
.type triplet_helpers_blend_triplets,@function
triplet_helpers_blend_triplets:
    [--sp] = {rets, r7-r4}
    if (r3 >= 256) {  ; @if.ge.ri.s12
    r3 = 256
    }
    r4 = 0x100 - r3
    r5 = 0
    goto L02015682
L0201566c:
    r6 = b[r1+r5] (u)
    r7 = b[r2+r5] (u)
    r6 *= r4
    r7 *= r3
    r6 += r7  ; @add.rr
    r6 = r6 >> 8
    b[r0+r5] = r6
    r5 += 1  ; @add.ri.u5
L02015682:
    if (r5 != 3) goto L0201566c
    {pc, r7-r4} = [sp++]
