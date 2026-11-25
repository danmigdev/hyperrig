; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 1 function, 0x020331da..0x020331ec

; effect_model_construction_unsigned_quotient: 0x020331da..0x020331ec, module effect-model-construction (unsigned_quotient)
.type effect_model_construction_unsigned_quotient,@function
effect_model_construction_unsigned_quotient:
    [--sp] = {rets, r4}
    sp += -4
    r4 = 0
    [sp] = r4
    call effect_parameter_support_unsigned_divide  ; @call.xl
    sp += 4
    {pc, r4} = [sp++]
