; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; triplet_helpers: 2 functions, 0x020150d4..0x02015130

; triplet_helpers_clamp_triplet: 0x020150d4..0x020150ee, module triplet-helpers (clamp_triplet)
.type triplet_helpers_clamp_triplet,@function
triplet_helpers_clamp_triplet:
    if (r1 >= 255) {  ; @if.ge.ri.s12
    r1 = 255
    }
    b[r0+0] = r1
    if (r2 >= 255) {  ; @if.ge.ri.s12
    r2 = 255
    }
    b[r0+1] = r2
    if (r3 >= 255) {  ; @if.ge.ri.s12
    r3 = 255
    }
    b[r0+2] = r3
    rts

; triplet_helpers_store_slot: 0x020150ee..0x02015130, module triplet-helpers (store_slot)
.type triplet_helpers_store_slot,@function
triplet_helpers_store_slot:
    [--sp] = {rets, r7-r4}
    if (r0 > 11) goto L0201512e
    r0 = r0 * 0x3
    r5 = L01c26890
    r4 = r0 + r5
    r0 = r4 + 2524
    r6 = b[r0+0] (u)
    if (r6 != r1) goto L0201511a
    r6 = b[r0+1] (u)
    if (r6 != r2) goto L0201511a
    r6 = r4 + 2526
    r7 = b[r6+0] (u)
    if (r7 == r3) goto L02015128
L0201511a:
    r6 = 876
    r7 = 1
    b[r5+r6] = r7
    r6 = r4 + 2526
L02015128:
    b[r0+0] = r1
    b[r0+1] = r2
    b[r6+0] = r3
L0201512e:
    {pc, r7-r4} = [sp++]
