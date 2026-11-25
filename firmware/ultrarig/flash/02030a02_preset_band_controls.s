; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_band_controls: 3 functions, 0x02030a02..0x02030a9a

; preset_band_controls_group_flag: 0x02030a02..0x02030a7e, module preset-band-controls (group_flag)
.type preset_band_controls_group_flag,@function
preset_band_controls_group_flag:
    [--sp] = {rets, r10-r4}
    r5 = r2
    r6 = r1
    r2 = r0
    call biquad_coefficients_counter  ; @call.xl
    r4 = -1
    if (r2 > 15) goto L02030a2a
    if (r6 > 2) goto L02030a2a
    r0 = r2 * 0x1E0
    r1 = L01c2c220
    r7 = r0 + r1
    r0 = b[r7+2] (u)
    if (r0 != 0) goto L02030a2e
L02030a2a:
    r0 = r4
    {pc, r10-r4} = [sp++]
L02030a2e:
    r10 = b[r7+4] (u)
    r1 = 0
    r4 = 0
    r0 = r2
    call effect_ownership_lookup
    r9 = r0
    ifs (r0 > -1) goto L02030a46
    b[r7+4] = r6
    goto L02030a2a
L02030a46:
    call effect_ownership_groups
    r8 = r0  #
    b[r7+4] = r6
    r0 = r9
    call effect_ownership_groups
    ifs (r0 < 4) goto L02030a60
    b[r7+4] = r10
    r4 = -5
    goto L02030a2a
L02030a60:
    if (r5 != 0) goto L02030a2a
    ifs (r0 <= r8) goto L02030a2a
    call effect_setup_total_cost
    r1 = L01c32db0
    r1 = [r1+48]
    if (r0 > r1) {
    b[r7+4] = r10
    r4 = -4
    }
    goto L02030a2a

; preset_band_controls_set_group_checked: 0x02030a7e..0x02030a92, module preset-band-controls (set_group_checked)
.type preset_band_controls_set_group_checked,@function
preset_band_controls_set_group_checked:
    [--sp] = {rets, r4}
    r2 = 0
    call preset_band_controls_group_flag
    r4 = r0
    if (r4 == 0) goto L02030a8c
L02030a88:
    r0 = r4
    {pc, r4} = [sp++]
L02030a8c:
    call effect_ownership_refresh
    goto L02030a88

; preset_band_controls_set_group_quiet: 0x02030a92..0x02030a9a, module preset-band-controls (set_group_quiet)
.type preset_band_controls_set_group_quiet,@function
preset_band_controls_set_group_quiet:
    [--sp] = rets
    r2 = 1
    call preset_band_controls_group_flag
    pc = [sp++]
