; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x0202f46c..0x0202f4e8

; effect_setup_tempo: 0x0202f46c..0x0202f4e8, module effect-setup (tempo)
.type effect_setup_tempo,@function
effect_setup_tempo:
    [--sp] = {rets, r6-r4}
    r1 = 400
    ifs (r0 >= 400) {
    r1 = 3000
    r1 = smin(r0, r1)
    }
    r5 = L01c1f7f0
    [r5+12] = r1
    r4 = 0
    r6 = L01c2c220
    goto L0202f4d6
L0202f490:
    r0 = b[r6+0] (u)
    if (r0 != 5) goto L0202f4a2
    r2 = h[r6+78] (s)
    r0 = r2
    call effect_parameter_support_tempo_selector
    if (r0 != 0) goto L0202f4c0
L0202f4a2:
    r2 = r6
    r0 = b[r2++=70] (u)
    call effect_construction_tempo_parameter
    r1 = r0
    ifs (r1 < 0) goto L0202f4da
    r2 = h[r2+r1<<1] (s)
    if (r2 == 0) goto L0202f4da
    r0 = r4
    call effect_parameter_lifecycle_parameter_commit
    goto L0202f4da
L0202f4c0:
    r0 = r2
    call effect_parameter_support_tempo_global
    r2 = r0
    r1 = 0
    r0 = r4
    call effect_parameter_lifecycle_parameter_commit
    r0 = b[r6+2] (u)
    if (r0 == 0) goto L0202f4da
    goto L0202f4a2
L0202f4d6:
    r0 = b[r6+2] (u)
    if (r0 != 0) goto L0202f490
L0202f4da:
    r4 = r4 + 1
    r6 = r6 + 480
    if (r4 != 16) goto L0202f4d6
    r0 = [r5+12]
    {pc, r6-r4} = [sp++]
