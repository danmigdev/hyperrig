; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 5 functions, 0x02007b88..0x02007cba

; preset_application_asset_mode: 0x02007b88..0x02007b9c, module preset-application (asset_mode), preset-assets (mode)
.type preset_application_asset_mode,@function
preset_application_asset_mode:
    r0 = 1347
    r1 = L01c24790
    r0 = b[r1+r0] (u)
    r0 = r0 >> 7
    r0 ^= 1
    rts

; preset_application_asset_layout: 0x02007b9c..0x02007c6a, module preset-application (asset_layout), preset-assets (layout)
.type preset_application_asset_layout,@function
preset_application_asset_layout:
    [--sp] = {rets, r11-r4}
    r10 = L01c24790
    r11 = b[r10+1] (u)
    r2 = 0
    r4 = r0
    rep 16 {
    b[r4++=1] = r2
    }
    r4 = r1
    rep 12 {
    b[r4++=1] = r2
    }
    if (r11 >= 16) {  ; @if.ge.ri.s12
    r11 = 16
    }
    r2 = b[r10+0] (u)
    if (r2 <= 3) goto L02007bf0
    r4 = r10 + 15
    r5 = 0
    goto L02007be0
L02007bce:
    r6 = b[r4++=18] (u)
    r2 = 0
    if (r6 <= 2) {  ; @if.le.ri.s12
    r2 = r6
    }
    b[r0+r5] = r2
    r5 += 1  ; @add.ri.u5
L02007be0:
    ifs (r5 < r11) goto L02007bce
    r0 = r10 + 1348
    rep 12 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    {pc, r11-r4} = [sp++]
L02007bf0:
    r4 = 0
    r8 = 1340
    r9 = 1341
    goto L02007c64
L02007bfc:
    r5 = r10 + 15
    r7_r6 = 0
    goto L02007c18
L02007c04:
    r2 = b[r5+-3] (u)
    if (r2 != r4) goto L02007c14
    r2 = b[r5+0] (u)
    if (r2 != 1) {  ; @if.ne.ri.s12
    r2 = r7
    }
    r7 = r2
L02007c14:
    r5 += 18  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02007c18:
    ifs (r6 < r11) goto L02007c04
    r5 = r10 + 15
    r6 = 0
    goto L02007c3e
L02007c24:
    if (r7 == 0) goto L02007c3a
    r2 = b[r5+-3] (u)
    if (r2 != r4) goto L02007c3a
    r3 = b[r5+0] (u)
    r2 = 2
    if (r3 != 1) {  ; @if.ne.ri.s12
    r2 = 1
    }
    b[r0+r6] = r2
L02007c3a:
    r5 += 18  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02007c3e:
    ifs (r6 < r11) goto L02007c24
    r2 = b[r10+0] (u)
    if (r2 <= 2) goto L02007c62
    r2 = r4 << 1
    r2 += r10
    r3 = b[r2+r8] (u)
    r5 = r4 * 0x6
    r6 = r1
    b[++r6=r5] = r3
    r2 = b[r2+r9] (u)
    b[r6+1] = r2
L02007c62:
    r4 += 1  ; @add.ri.u5
L02007c64:
    if (r4 != 2) goto L02007bfc
    {pc, r11-r4} = [sp++]

; preset_application_asset_matches: 0x02007c6a..0x02007c94, module preset-application (asset_matches), preset-assets (matches)
.type preset_application_asset_matches,@function
preset_application_asset_matches:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = b[r4+0] (u)
    r0 = 0
    if (r5 == 0) goto L02007c92
    r5 = [r4+4]
    if (r5 != r1) goto L02007c92
    r1 = [r4+8]
    if (r1 != r2) goto L02007c92
    r1 = [r4+12]
    if (r1 != r3) goto L02007c92
    r1 = [sp+12]
    r2 = b[r4+1] (u)
    r0 = 1
    if (r2 != r1) {
    r0 = 0
    }
L02007c92:
    {pc, r5, r4} = [sp++]

; preset_application_asset_state416: 0x02007c94..0x02007ca6, module preset-application (asset_state416), preset-assets (state416)
.type preset_application_asset_state416,@function
preset_application_asset_state416:
    r0 = L01c26890
    r1 = [r0+416]
    r0 = 1
    if (r1 != 0) goto L02007ca4
    r0 = r1
L02007ca4:
    rts

; preset_application_asset_clamp: 0x02007ca6..0x02007cba, module preset-application (asset_clamp), preset-assets (clamp)
.type preset_application_asset_clamp,@function
preset_application_asset_clamp:
    r1 = r0
    r0 = 400
    ifs (r1 >= 400) {  ; @ifs.ge.ri.s12
    r0 = 3000
    r0 = smin(r1, r0)
    }
    rts
