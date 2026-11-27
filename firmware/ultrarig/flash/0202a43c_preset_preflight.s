; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_preflight: 2 functions, 0x0202a43c..0x0202a50a

; preset_preflight_needs_conversion: 0x0202a43c..0x0202a452, module preset-preflight (needs_conversion)
.type preset_preflight_needs_conversion,@function
preset_preflight_needs_conversion:
; HyperRig MINI, product option: the ids 6 and 24 are blocks of HyperRig and are not converted.
.if MINI_PRODUCT
    r0 = 0
    rts
.else
    r1 = 1
    r2 = 1
    if (r0 != 24) {
    r2 = 0
    }
    if (r0 != 6) {
    r1 = 0
    }
    r0 = r1 | r2
    rts
.endif

; preset_preflight_convert_effect: 0x0202a452..0x0202a50a, module preset-preflight (convert_effect)
.type preset_preflight_convert_effect,@function
preset_preflight_convert_effect:
    [--sp] = {rets, r9-r4}
; HyperRig MINI, product option: the ids 6 and 24 stay what they are here too; a block is converted when it is added, whatever the function above says.
.if MINI_PRODUCT
    goto L0202a508
.else
    if (r0 == 24) goto L0202a4f0
    if (r0 != 6) goto L0202a508
    r0 = 27
    if (r1 == 0) goto L0202a508
    r4 = h[r1+0] (s)
    r5 = r4
    ifs (r4 >= 100) {
    r5 = 100
    }
    r9 = 0
    r3 = 0
    ifs (r4 >= 0) {
    r3 = r5
    }
    r4 = h[r1+2] (s)
    ifs (r4 < 0) goto L0202a490
    r9 = 70
    ifs (r4 <= 100) {
    r2 = r4 * 0x7
    r4 = 10
    r9 = r2 / r4 (s)
    }
L0202a490:
    r4 = 2
    r4 = r3 / r4 (s)
    r5 = r4 + 40
    r4 = h[r1+4] (s)
    r8 = 10  #
    h[r1+0] = r5
    r7 = r3 / r8 (s)
    r6 = 9
    ifs (r3 <= 99) {
    r6 = r7
    }
    r7 = read_only_strings_and_tables
    r5 = b[++r7=r6] (u)
    r7 = b[r7+1] (u)
    r7 = r7 - r5
    r2 = -10
    r2 *= r6
    r2 = r2 + r3
    r2 *= r7
    r2 = r2 + 5
    r2 = r2 / r8 (s)
    r2 = r2 + r5
    r3 = r4  #
    h[r1+2] = r2
    h[r1+4] = r9
    r2 = 0
    h[r1+6] = r2
    ifs (r4 >= 100) {
    r3 = 100
    }
    r5 = 0
    ifs (r4 >= 0) {
    r5 = r3
    }
    h[r1+8] = r5
    h[r1+10] = r2
    r2 = 40
    goto L0202a506
L0202a4f0:
    r0 = 29
    if (r1 == 0) goto L0202a508
    r2 = h[r1+8] (s)
    ifs (r2 >= 28) {
    r2 = 27
    h[r1+8] = r2
    }
    r2 = 50
    h[r1+10] = r2
    r2 = 0
L0202a506:
    h[r1+12] = r2
.endif
L0202a508:
    {pc, r9-r4} = [sp++]
