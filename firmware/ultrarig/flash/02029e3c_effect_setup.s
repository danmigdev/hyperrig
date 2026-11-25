; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x02029e3c..0x02029e54

; effect_setup_object_extra: 0x02029e3c..0x02029e54, module effect-setup (object_extra)
.type effect_setup_object_extra,@function
effect_setup_object_extra:
    r2 = 960
    if (r0 != 34) {
    r2 = 0
    }
    r1 = 8448
    if (r0 != 31) {
    r1 = r2
    }
    r0 = r1
    rts
