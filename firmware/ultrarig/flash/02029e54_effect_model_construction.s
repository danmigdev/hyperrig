; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 4 functions, 0x02029e54..0x02029ed4

; effect_model_construction_object_duration: 0x02029e54..0x02029e7c, module effect-model-construction (object_duration)
.type effect_model_construction_object_duration,@function
effect_model_construction_object_duration:
    [--sp] = rets
    r2 = r0
    call effect_model_construction_object_record  ; @call.xl
    r3 = r0
    r0 = r2
    call effect_model_construction_object_mode  ; @call.xl
    r1 = r0
    r0 = 100
    if (r1 == 1) goto L02029e7a
    r0 = h[r3+52] (u)
    if (r0 != 0) goto L02029e7a
    r0 = b[r3+54] (u)
L02029e7a:
    pc = [sp++]

; effect_model_construction_object_limit: 0x02029e7c..0x02029e98, module effect-model-construction (object_limit)
.type effect_model_construction_object_limit,@function
effect_model_construction_object_limit:
    [--sp] = rets
    call effect_model_construction_object_duration
    r1 = L01c1f7f0
    r1 = [r1+8]
    r1 = r1 >> 1
    r0 *= r1
    r1 = 1000
    r0 = r0 / r1 (u)
    r0 += 81
    pc = [sp++]

; effect_model_construction_object_length: 0x02029e98..0x02029ec8, module effect-model-construction (object_length)
.type effect_model_construction_object_length,@function
effect_model_construction_object_length:
    r1 = model_object1_lengths
    r0 = h[r1+r0<<1] (u)
    r0 = utof(r0)
    r1 = 1062105986
    r0 = r0 * r1 (f)
    r1 = 1058642330
    r0 = r0 * r1 (f)
    r1 = 0x3F000000
    r0 = r0 + r1 (f)
    r0 = ftou(r0) (trunc)
    rts

; effect_model_construction_object_extra: 0x02029ec8..0x02029ed4, module effect-model-construction (object_extra)
.type effect_model_construction_object_extra,@function
effect_model_construction_object_extra:
    r0 = b[r0+56] (u)
    r1 = r0 >> 2
    r0 = r0 + r1
    r0 = r0 + 1
    rts
