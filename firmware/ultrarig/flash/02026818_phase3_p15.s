; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p15: 1 function, 0x02026818..0x02026826

; phase3_p15_bt_event_notify: 0x02026818..0x02026826, module phase3-p15 (bt_event_notify)
.type phase3_p15_bt_event_notify,@function
phase3_p15_bt_event_notify:
    [--sp] = rets
    r2 = r1
    r1 = r0.b0 (u)
    r0 = 16
    call phase3_p6_sys_event_notify
    pc = [sp++]
