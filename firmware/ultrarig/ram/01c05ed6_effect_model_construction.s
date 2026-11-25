; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 1 function, 0x01c05ed6..0x01c05eec

; effect_model_construction_object_mode: 0x01c05ed6..0x01c05eec, module effect-model-construction (object_mode)
.type effect_model_construction_object_mode,@function
effect_model_construction_object_mode:
    r1 = r0
    r0 = 1
    r2 = 1
    if (r1 != 34) {
    r2 = 0
    }
    r2 = r2 << 1
    if (r1 != 33) {
    r0 = r2
    }
    rts
