; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 2 functions, 0x02026b38..0x02026b52

; phase3_p10_list_add_tail_b: 0x02026b38..0x02026b44, module phase3-p10 (list_add_tail_b)
.type phase3_p10_list_add_tail_b,@function
phase3_p10_list_add_tail_b:
    r2 = [r1+4]
    [r1+4] = r0
    [r0+] = {r2, r1}
    [r2+0] = r0
    rts

; phase3_p10_list_del_init: 0x02026b44..0x02026b52, module phase3-p10 (list_del_init)
.type phase3_p10_list_del_init,@function
phase3_p10_list_del_init:
    {r2, r1} = [r0+]
    [r1+4] = r2
    [r2+0] = r1
    [r0+0] = r0
    [r0+4] = r0
    rts
