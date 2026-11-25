; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; wet_mix: 1 function, 0x01c089e8..0x01c08a76

; wet_mix_wet_mix: 0x01c089e8..0x01c08a76, module wet-mix (wet_mix)
.type wet_mix_wet_mix,@function
wet_mix_wet_mix:
    [--sp] = {rets, r9-r4}
    sp += -28
    r9 = r0  #
    r3 = b[r0+0] (u)
    r4 = r2
    r6 = r1
    r1 = r3 + -17
    r0 = r0 + 312
    if (r1 >= 4) goto L01c08a06
    r0 = r0 + 148
    goto L01c08a16
L01c08a06:
    r1 = r3 + -9
    if (r1 >= 2) goto L01c08a12
    r0 += 32
    goto L01c08a16
L01c08a12:
    if (r3 != 3) goto L01c08a6a
L01c08a16:
    r0 = [r0+0]
    if (r0 == 0) goto L01c08a6a
    r8 = L01c31c94
    [sp+4] = r8
    [sp+12] = r8
    r1 = 0
    r1 = 0x8000 - r0  #
    [sp+16] = r1
    [sp+20] = r1
    [sp+24] = r0
    if (r4 == 0) goto L01c08a66
    r5 = sp + 0
L01c08a34:
    r7 = r4
    if (r4 >= 128) {
    r7 = 128
    }
    r0 = r8
    r1 = r6
    r2 = r7
    call dsp_stage_copy  ; @call.xl
    r0 = r9
    r1 = r6
    r2 = r7
    call effect_cases_effect_cases
    [sp] = r6
    [r5+8] = r7
    r0 = sp + 0
    call dsp_stage_mix  ; @call.xl
    r4 = r4 - r7
    r0 = r7 << 2
    r6 = r6 + r0
    if (r4 != 0) goto L01c08a34
L01c08a66:
    sp += 28
    {pc, r9-r4} = [sp++]
L01c08a6a:
    r0 = r9
    r1 = r6
    call effect_cases_effect_cases
    sp += 28
    {pc, r9-r4} = [sp++]
