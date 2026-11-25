; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 3 functions, 0x01c06490..0x01c06514

; effect_model_construction_pitch_curve: 0x01c06490..0x01c064d2, module effect-model-construction (pitch_curve)
.type effect_model_construction_pitch_curve,@function
effect_model_construction_pitch_curve:
    [--sp] = {rets, r4}
    r4 = r0 >>> 31
    r0 ^= r4
    r0 = r0 >>> 1
    r0 = r0 - r1
    ifs (r0 >= 0) {
    r0 = smin(r0, r2)
    r1 = r0 >>> 31
    } else {
    r0 = 0
    r1 = 0
    }
    r1_r0 = r0 * r3 (s)
    r1_r0 >>= 16
    ifs (r0 >= 1073741824) {
    r0 = 0x40000000
    }
    r3_r2 = r0 * r0 (s)
    r3_r2 <<= 2
    r3_r2 >>>= 32
    r0 = 0x60000000 - r0
    r1_r0 = r2 * r0 (s)
    r1_r0 >>= 29
    {pc, r4} = [sp++]

; effect_model_construction_pitch_increment: 0x01c064d2..0x01c064fe, module effect-model-construction (pitch_increment)
.type effect_model_construction_pitch_increment,@function
effect_model_construction_pitch_increment:
    r1 = [r0+308]
    if (r1 == 0) goto L01c064f6
    r2 = [r0+400]
    r1 = itof(r1)
    r3 = 0x57800000
    r1 = r3 / r1 (f)
    r1 = r1 * r2 (f)
    r1 = ftoi(r1) (trunc)
    [r0+296] = r1
    rts
L01c064f6:
    r1 = 0
    [r0+296] = r1
    rts

; effect_model_construction_pitch_limit_valid: 0x01c064fe..0x01c06514, module effect-model-construction (pitch_limit_valid)
.type effect_model_construction_pitch_limit_valid,@function
effect_model_construction_pitch_limit_valid:
    r0 = L01c1f7f0
    r0 = [r0+16]
    r1 = r0 + -20
    r0 = 1
    if (r1 >= 35) {
    r0 = 0
    }
    rts
