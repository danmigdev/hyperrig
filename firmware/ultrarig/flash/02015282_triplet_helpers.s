; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; triplet_helpers: 1 function, 0x02015282..0x020152a8

; triplet_helpers_active_flag: 0x02015282..0x020152a8, module triplet-helpers (active_flag)
.type triplet_helpers_active_flag,@function
triplet_helpers_active_flag:
    r1 = 293
    r2 = L01c26890
    r1 = [r2+r1<<2]
    [r0+0] = r1
    r1 = b[r2+52] (u)
    r0 = 1068
    r0 = b[r2+r0] (u)
    r2 = 1
    if (r1 != 0) goto L020152a4
    r2 = r1
L020152a4:
    r0 &= r2
    rts
