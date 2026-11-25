; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 3 functions, 0x0202a7b2..0x0202a872

; effect_construction_onepole: 0x0202a7b2..0x0202a7f6, module effect-construction (onepole), effect-model-construction (onepole)
.type effect_construction_onepole,@function
effect_construction_onepole:
    [--sp] = rets
    r1 = 0
    ifs (r0 >= 1) goto L0202a7be
L0202a7ba:
    r0 = r1
    pc = [sp++]
L0202a7be:
    r1 = L01c1f7f0
    r0 = itof(r0)  #
    r1 = [r1+8]
    r2 = 3234402267
    r0 = r0 * r2 (f)
    r1 = utof(r1)
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r1 = 0x3F800000
    r0 = r1 - r0 (f)
    r1 = r1 + 0xF800000
    r0 = r0 * r1 (f)
    r1 = ftoi(r0) (trunc)
    goto L0202a7ba

; effect_construction_tempo_parameter: 0x0202a7f6..0x0202a814, module effect-construction (tempo_parameter), effect-model-construction (tempo_parameter)
.type effect_construction_tempo_parameter,@function
effect_construction_tempo_parameter:
    r1 = r0 + -11
    if (r1 > 4) goto L0202a80c
    r0 = 3
    tbb [r1]
construction_tempo_branches:
    .byte (L0202a80e - construction_tempo_branches) / 2, (L0202a808 - construction_tempo_branches) / 2, (L0202a80e - construction_tempo_branches) / 2, (L0202a80e - construction_tempo_branches) / 2, (L0202a810 - construction_tempo_branches) / 2
    .byte 0x00  ; alignment
L0202a808:
    r0 = 4
    rts
L0202a80c:
    r0 = -1
L0202a80e:
    rts
L0202a810:
    r0 = 2
    rts

; effect_construction_tempo_value: 0x0202a814..0x0202a872, module effect-construction (tempo_value), effect-model-construction (tempo_value)
.type effect_construction_tempo_value,@function
effect_construction_tempo_value:
    [--sp] = rets
    r2 = r0
    r0 = r1
    call effect_construction_tempo_parameter
    ifs (r0 < 0) goto L0202a82c
    r0 = h[r2+r0<<1] (s)
    r1 = r0 + -1
    if (r1 < 12) goto L0202a836
L0202a82c:
    r0 = h[r2+0] (s)
    r0 = itof(r0)
    pc = [sp++]
L0202a836:
    r1 = L0203b665
    r1 = b[r0+r1] (u)
    r2 = effect_support_tempo
    r0 = b[r0+r2] (u)
    r2 = L01c1f7f0
    r1 = utof(r1)  #
    r2 = [r2+12]
    r3 = 1086324736
    r1 = r1 * r3 (f)
    r0 = utof(r0)
    r2 = itof(r2)
    r0 = r2 * r0 (f)
    r0 = r0 / r1 (f)
    pc = [sp++]
