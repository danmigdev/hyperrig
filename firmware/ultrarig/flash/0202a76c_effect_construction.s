; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 1 function, 0x0202a76c..0x0202a7a8

; effect_construction_tempo_samples: 0x0202a76c..0x0202a7a8, module effect-construction (tempo_samples), effect-model-construction (tempo_samples)
.type effect_construction_tempo_samples,@function
effect_construction_tempo_samples:
    [--sp] = rets
    r2 = r0
    call effect_parameter_support_tempo_selector
    if (r0 == 0) goto L0202a7a4
    r0 = effect_support_tempo
    r0 = b[r2+r0] (u)
    r1 = L01c1f7f0
    r3 = L0203b665
    r2 = b[r2+r3] (u)
    r3 = [r1+12]
    r0 *= r3  #
    r1 = [r1+8]
    r1 *= r2
    r1 = r1 * 0x4B0
    r1 = r1 + r0
    r0 = r0 << 1
    r0 = r1 / r0 (u)
    pc = [sp++]
L0202a7a4:
    r0 = 0
    pc = [sp++]
