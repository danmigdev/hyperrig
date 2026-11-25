; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 1 function, 0x01c06004..0x01c06028

; effect_model_construction_object_record: 0x01c06004..0x01c06028, module effect-model-construction (object_record)
.type effect_model_construction_object_record,@function
effect_model_construction_object_record:
    if (r0 == 31) goto L01c06018
    r1 = 1
    if (r0 == 32) goto L01c0601a
    r1 = 3
    if (r0 != 35) {
    r1 = 0
    }
    goto L01c0601a
L01c06018:
    r1 = 2
L01c0601a:
    r0 = r1 * 0x54
    r1 = model_object_records
    r0 = r0 + r1
    rts
