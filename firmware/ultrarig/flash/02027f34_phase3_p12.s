; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 3 functions, 0x02027f34..0x02027f40

; phase3_p12_bt_sleep_suspend: 0x02027f34..0x02027f38, module phase3-p12 (bt_sleep_suspend)
.type phase3_p12_bt_sleep_suspend,@function
phase3_p12_bt_sleep_suspend:
    r0 = 0
    rts

; phase3_p12_bt_sleep_resume: 0x02027f38..0x02027f3c, module phase3-p12 (bt_sleep_resume)
.type phase3_p12_bt_sleep_resume,@function
phase3_p12_bt_sleep_resume:
    r0 = 0
    rts

; phase3_p12_bt_sleep_release: 0x02027f3c..0x02027f40, module phase3-p12 (bt_sleep_release)
.type phase3_p12_bt_sleep_release,@function
phase3_p12_bt_sleep_release:
    r0 = 0
    rts
