; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p1: 1 function, 0x02027f1c..0x02027f34

; phase3_p1_att_wrapper: 0x02027f1c..0x02027f34, module phase3-p1 (att_wrapper)
.type phase3_p1_att_wrapper,@function
phase3_p1_att_wrapper:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r5 = r1
    r6 = r0
    call boundary_hooks_activity_note
    r0 = r6
    r1 = r5
    r2 = r4
    call L02027598
    {pc, r6-r4} = [sp++]
