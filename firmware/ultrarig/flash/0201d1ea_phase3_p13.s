; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 1 function, 0x0201d1ea..0x0201d1f0

; phase3_p13_list_del_entry: 0x0201d1ea..0x0201d1f0, module phase3-p13 (list_del_entry)
.type phase3_p13_list_del_entry,@function
phase3_p13_list_del_entry:
    [r0+4] = r1
    [r1+0] = r0
    rts
