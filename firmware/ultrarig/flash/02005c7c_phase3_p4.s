; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 1 function, 0x02005c7c..0x02005c9e

; phase3_p4_cdc_ready: 0x02005c7c..0x02005c9e, module phase3-p4 (cdc_ready)
.type phase3_p4_cdc_ready,@function
phase3_p4_cdc_ready:
    r0 = 412
    r1 = L01c26890
    r0 = [r1+r0<<2]
    if (r0 == 0) goto L02005c9a
    r0 = b[r0+104] (u)
    r1 = r0 & 0xFFFFFF12
    r0 = 1
    if (r1 == 18) goto L02005c9c
L02005c9a:
    r0 = 0
L02005c9c:
    rts
