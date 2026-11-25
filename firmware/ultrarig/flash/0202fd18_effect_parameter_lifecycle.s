; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_lifecycle: 1 function, 0x0202fd18..0x0202fe58

; effect_parameter_lifecycle_parameter_probe: 0x0202fd18..0x0202fe58, module effect-parameter-lifecycle (parameter_probe), effect-parameters (probe), effect-resource-ownership (parameter_probe)
.type effect_parameter_lifecycle_parameter_probe,@function
effect_parameter_lifecycle_parameter_probe:
    [--sp] = {rets, r10-r4}
    sp += -24
    r5 = r2
    r7_r6 = r1_r0
    r3 = 0
    if (r6 > 15) goto L0202fd56
    r0 = r6 * 0x1E0
    r1 = L01c2c220
    r4 = r0 + r1
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L0202fd56
    r2 = b[r4+0] (u)
    r0 = r2
    call effect_parameter_support_capability  ; @call.xl
    r9 = r0
    if (r0 == r7) goto L0202fd52
    r0 = r7 + -4
    if (r0 > 2) goto L0202fd56
    if (r2 != 25) goto L0202fd56
L0202fd52:
    r0 = b[r4+1] (u)
    if (r0 != 0) goto L0202fd5c
L0202fd56:
    r0 = r3
    sp += 24
    {pc, r10-r4} = [sp++]
L0202fd5c:
    r0 = r2
    r1 = r7
    call preset_application_metadata
    if (r0 == 0) goto L0202fd56
    r8 = r4 + 70
    r2 = 0
L0202fd6c:
    r3 = h[r8+r2<<1] (u)
    r1 = sp + 10
    h[r1+r2<<1] = r3
    r2 = r2 + 1
    if (r2 != 7) goto L0202fd6c
    r10 = h[r0+0] (s)
    ifs (r10 <= r5) {
    r0 = h[r0+2] (s)
    r10 = smin(r0, r5)
    }
    r0 = sp + 10
    h[r0+r7<<1] = r10
    r1 = sp + 9
    r2 = sp + 8
    call effect_parameter_support_pack  ; @call.xl
    r1 = 1
    r0 = r6
    call effect_setup_slot_cost
    r8 = r0
    r5 = L01c32db0
    if (r9 != r7) goto L0202fe28
    r0 = r4
    call dsp_stage_active  ; @call.xl
    r1 = r0  #
    r3 = b[r5+3] (u)
    r7 = 0
    r9 = L01c1f7f0
    r2 = 0
    if (r3 != 0) goto L0202fdcc
    r2 = b[r9+0] (u)
L0202fdcc:
    r3 = [r5+36]
    r0 = [r5+40]
    r6 = [r5+44]
    [sp+4] = r6
    r0 = r4  #
    [sp] = r0
    call effect_processing_extra_cost  ; @call.xl
    r6 = r0
    r0 = 1
    r2 = 65535
    r1 = 1
    if ((r10 & r2) != 0) {
    r1 = 0
    }
    r2 = b[r4+0] (u)
    if (r2 != 14) {
    r0 = 0
    }
    r0 ^= r1  #
    r2 = b[r5+3] (u)
    r1 = r0 ^ 0x1
    if (r2 != 0) goto L0202fe06
    r7 = b[r9+0] (u)
L0202fe06:
    r3 = [r5+36]
    r0 = [r5+40]
    r2 = [r5+44]
    r2 = r7  #
    [sp+4] = r2
    r0 = r4  #
    [sp] = r0
    call effect_processing_extra_cost  ; @call.xl
    r3 = 0
    if (r0 <= r6) goto L0202fd56
    r1 = r8 - r6
    r0 = r0 + r1
    goto L0202fe3c
L0202fe28:
    r1 = b[sp+8] (u)
    r0 = b[sp+9] (u)
    r2 = r6
    call effect_parameter_support_time_rule  ; @call.xl
    r0 = r0 + 1750
L0202fe3c:
    if (r0 > r8) goto L0202fe44
L0202fe40:
    r3 = 0
    goto L0202fd56
L0202fe44:
    r4 = r0 - r8
    call effect_setup_total_cost
    r0 = r0 + r4  #
    r1 = [r5+48]
    r3 = -4
    if (r0 > r1) goto L0202fd56
    goto L0202fe40
