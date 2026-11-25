; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 1 function, 0x0201dfd8..0x0201dfea

; phase3_p6_norflash_idle_query: 0x0201dfd8..0x0201dfea, module phase3-p6 (norflash_idle_query)
.type phase3_p6_norflash_idle_query,@function
phase3_p6_norflash_idle_query:
    r0 = L01c26890
    r1 = b[r0+67] (u)
    r0 = 1
    if (r1 == 0) goto L0201dfe8
    r0 = 0
L0201dfe8:
    rts
