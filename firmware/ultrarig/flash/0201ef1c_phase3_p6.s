; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 1 function, 0x0201ef1c..0x0201ef24

; phase3_p6_sys_timer_del: 0x0201ef1c..0x0201ef24, module phase3-p6 (sys_timer_del)
.type phase3_p6_sys_timer_del,@function
phase3_p6_sys_timer_del:
    [--sp] = rets
    call L0201c622
    pc = [sp++]
