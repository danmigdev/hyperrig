; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 3 functions, 0x0203089a..0x02030906

; preset_application_chain_read: 0x0203089a..0x020308cc, module preset-application (chain_read), selection (chain_read)
.type preset_application_chain_read,@function
preset_application_chain_read:
    [--sp] = {rets, r4}
    r2 = r0
    r0 = 0
    if (r2 > 1) goto L020308ca
    r3 = L01c32db0
    r0 = r2 + r3
    r0 = b[r0+14] (u)
    if (r0 == 0) goto L020308ca
    r2 = r2 * 0xA
    r2 = r2 + r3
    r2 = r2 + 348
    r3 = 0
L020308bc:
    r4 = b[r2+r3] (u)
    b[r1+r3] = r4
    r3 = r3 + 1
    ifs (r3 < r0) goto L020308bc
L020308ca:
    {pc, r4} = [sp++]

; preset_application_effect_type: 0x020308cc..0x020308ea, module preset-application (effect_type), scene-application (effect_type), selection (effect_type)
.type preset_application_effect_type,@function
preset_application_effect_type:
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L020308e8
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r3 = r1 + r2
    r3 = b[r3+2] (u)
    if (r3 == 0) goto L020308e8
    r0 = b[r1+r2] (u)
L020308e8:
    rts

; preset_application_effect_enabled: 0x020308ea..0x02030906, module preset-application (effect_enabled), scene-application (effect_enabled), selection (effect_enabled)
.type preset_application_effect_enabled,@function
preset_application_effect_enabled:
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L02030904
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r1 = r1 + r2
    r2 = b[r1+2] (u)
    if (r2 == 0) goto L02030904
    r0 = b[r1+1] (u)
L02030904:
    rts
