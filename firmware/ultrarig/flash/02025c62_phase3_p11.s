; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 1 function, 0x02025c62..0x02025c6e

; phase3_p11_list_add_tail: 0x02025c62..0x02025c6e, module phase3-p11 (list_add_tail)
.type phase3_p11_list_add_tail,@function
phase3_p11_list_add_tail:
    r2 = [r1+4]
    [r1+4] = r0
    [r0+] = {r2, r1}
    [r2+0] = r0
    rts
