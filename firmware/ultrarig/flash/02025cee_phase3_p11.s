; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 2 functions, 0x02025cee..0x02025d0a

; phase3_p11_list_del_a: 0x02025cee..0x02025cfc, module phase3-p11 (list_del_a)
.type phase3_p11_list_del_a,@function
phase3_p11_list_del_a:
    {r2, r1} = [r0+]
    [r1+4] = r2
    [r2+0] = r1
    [r0+0] = r0
    [r0+4] = r0
    rts

; phase3_p11_list_del_b: 0x02025cfc..0x02025d0a, module phase3-p11 (list_del_b)
.type phase3_p11_list_del_b,@function
phase3_p11_list_del_b:
    {r2, r1} = [r0+]
    [r1+4] = r2
    [r2+0] = r1
    [r0+0] = r0
    [r0+4] = r0
    rts
