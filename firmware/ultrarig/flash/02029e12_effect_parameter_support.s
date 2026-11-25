; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 2 functions, 0x02029e12..0x02029e3c

; effect_parameter_support_size_base: 0x02029e12..0x02029e32, module effect-parameter-support (size_base)
.type effect_parameter_support_size_base,@function
effect_parameter_support_size_base:
    r1 = L01c1f7f0
    r1 = [r1+8]
    r0 *= r1
    r1 = 1000
    r0 = r0 / r1 (u)
    r0 = r0 + 128
    r1 = 16777152
    r0 &= r1
    rts

; effect_parameter_support_size_extra: 0x02029e32..0x02029e3c, module effect-parameter-support (size_extra)
.type effect_parameter_support_size_extra,@function
effect_parameter_support_size_extra:
    [--sp] = rets
    call effect_parameter_support_size_base
    r1 = r0 >> 5
    r0 = r0 + r1
    pc = [sp++]
