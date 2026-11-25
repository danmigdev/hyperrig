; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x02029c22..0x02029c3e

; effect_setup_object_count: 0x02029c22..0x02029c3e, module effect-setup (object_count)
.type effect_setup_object_count,@function
effect_setup_object_count:
    [--sp] = rets
    call effect_model_construction_object_mode  ; @call.xl
    r2 = 13
    if (r0 != 1) {
    r2 = 20
    }
    r1 = 3
    if (r0 != 2) {
    r1 = r2
    }
    r0 = r1
    pc = [sp++]
