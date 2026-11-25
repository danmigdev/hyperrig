; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; triplet_helpers: 1 function, 0x0201582c..0x02015840

; triplet_helpers_percent_of: 0x0201582c..0x02015840, module triplet-helpers (percent_of)
.type triplet_helpers_percent_of,@function
triplet_helpers_percent_of:
    r2 = 0
    if (r0 == 0) goto L0201583c
    if (r1 == 0) goto L0201583c
    r0 *= r1
    r0 += 99
    r1 = 100
    r2 = r0 / r1 (u)
L0201583c:
    r0 = r2.b0 (u)
    rts
