; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x01c05d02..0x01c05d40

; effect_setup_estimate_slot: 0x01c05d02..0x01c05d40, module effect-setup (estimate_slot)
.type effect_setup_estimate_slot,@function
effect_setup_estimate_slot:
    [--sp] = {rets, r6-r4}
    sp += -8
    r5 = r0
    call effect_processing_cost
    r4 = r0
    r0 = r5
    call dsp_stage_active
    r6 = L01c32db0
    r1 = r0  #
    r3 = b[r6+3] (u)
    r2 = 0
    if (r3 != 0) goto L01c05d2a
    r0 = L01c1f7f0
    r2 = b[r0+0] (u)
L01c05d2a:
    r3 = [r6+36]
    r0 = [r6+40]
    r6 = [r6+44]
    [sp+4] = r6
    r0 = r5  #
    [sp] = r0
    call effect_processing_extra_cost
    r0 = r0 + r4
    sp += 8
    {pc, r6-r4} = [sp++]
