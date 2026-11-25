; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 2 functions, 0x0202ed38..0x0202ed7e

; effect_parameter_support_tempo: 0x0202ed38..0x0202ed70, module effect-parameter-support (tempo)
.type effect_parameter_support_tempo,@function
effect_parameter_support_tempo:
    [--sp] = rets
    r2 = r1
    r3 = r0
    call effect_parameter_support_tempo_selector
    if (r0 == 0) goto L0202ed6c
    r0 = effect_support_tempo
    r0 = b[r3+r0] (u)
    r1 = L0203b665
    r1 = b[r3+r1] (u)
    r0 *= r2
    r2 = 1200000
    r1 *= r2
    r1 = r1 + r0
    r0 = r0 << 1
    r0 = r1 / r0 (u)
    pc = [sp++]
L0202ed6c:
    r0 = 0
    pc = [sp++]

; effect_parameter_support_tempo_global: 0x0202ed70..0x0202ed7e, module effect-parameter-support (tempo_global)
.type effect_parameter_support_tempo_global,@function
effect_parameter_support_tempo_global:
    [--sp] = rets
    r1 = L01c1f7f0
    r1 = [r1+12]
    call effect_parameter_support_tempo
    pc = [sp++]
