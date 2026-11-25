; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_band_controls: 6 functions, 0x02008c28..0x02008d90

; preset_band_controls_reserve_allowance: 0x02008c28..0x02008c46, module preset-band-controls (reserve_allowance)
.type preset_band_controls_reserve_allowance,@function
preset_band_controls_reserve_allowance:
    r0 = L01c1f180
    r1 = [r0+56]
    r0 = L01c224a0
    r2 = 122000
    r1 += r2  #  ; @add.rr.p
    r0 = [r0+0]
    if (r0 != 0) goto L02008c44
    r0 = r1
L02008c44:
    rts

; preset_band_controls_reserve_fits: 0x02008c46..0x02008c6c, module preset-band-controls (reserve_fits)
.type preset_band_controls_reserve_fits,@function
preset_band_controls_reserve_fits:
    [--sp] = {rets, r4}
    call dsp_audio_path_cached  ; @call.xl
    r4 = r0
    r3 = 0
    call preset_band_controls_reserve_allowance
    if (r4 <= r0) goto L02008c68
    r4 = r4 - r0
    call effect_setup_total_cost  ; @call.xl
    r3 = 1
    if (r0 > r4) {
    r3 = 0
    }
L02008c68:
    r0 = r3
    {pc, r4} = [sp++]

; preset_band_controls_set_reserve_mode: 0x02008c6c..0x02008ca2, module preset-band-controls (set_reserve_mode)
.type preset_band_controls_set_reserve_mode,@function
preset_band_controls_set_reserve_mode:
    [--sp] = {rets, r4}
    r4 = L01c1f180
    r3 = r0  #
    r1 = b[r4+5] (u)
    r0 = r3.b0 (u)
    if (r1 == r0) goto L02008ca0
    if (r3 == 0) goto L02008c84
    call preset_band_controls_reserve_allowance
    goto L02008c90
L02008c84:
    r1 = [r4+52]
    r0 = [r4+56]
    r2 = L01c224a0
    [r2+0] = r1
L02008c90:
    [r4+52] = r0
    b[r4+5] = r3
    call dsp_audio_path_input  ; @call.xl
    call audio_task_set_input  ; @call.xl
L02008ca0:
    {pc, r4} = [sp++]

; preset_band_controls_request_reserve: 0x02008ca2..0x02008cee, module preset-band-controls (request_reserve)
.type preset_band_controls_request_reserve,@function
preset_band_controls_request_reserve:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = L01c1f180
    if (r4 == 0) goto L02008cb2
    r0 = b[r5+2] (u)
    if (r0 == 0) goto L02008cd0
L02008cb2:
    r0 = 1
    if (r4 != 0) goto L02008cb8
    r0 = r4
L02008cb8:
    b[r5+2] = r0
    r1 = b[r5+2] (u)
    r4 = 0
    r0 = 0
    if (r1 == 0) goto L02008cca
    r1 = b[r5+3] (u)
    r0 = 1
    if (r1 != 0) goto L02008cca
    r0 = r1
L02008cca:
    call preset_band_controls_set_reserve_mode
L02008ccc:
    r0 = r4
    {pc, r5, r4} = [sp++]
L02008cd0:
    r0 = b[r5+3] (u)
    if (r0 == 0) goto L02008cb2
    r0 = 516
    r1 = L01c26890
    r0 = b[r1+r0] (u)
    if ((r0 & 1) != 0) goto L02008cb2
    call preset_band_controls_reserve_fits
    if (r0 != 0) goto L02008cb2
    r4 = -4
    goto L02008ccc

; preset_band_controls_apply_band_flags: 0x02008cee..0x02008d4c, module preset-band-controls (apply_band_flags)
.type preset_band_controls_apply_band_flags,@function
preset_band_controls_apply_band_flags:
    [--sp] = {rets, r11-r4}
    r11 = r0
    r8 = 0
    r9 = 1342
    r7 = L01c24790
    r10 = 1343
    r5 = 0
    goto L02008d46
L02008d06:
    r6 = 0
    r4 = r8
    goto L02008d3c
L02008d0c:
    r0 = b[r7+0] (u)
    r2 = 0
    if (r0 < 4) goto L02008d2c
    r0 = b[r7+r9] (u)
    if (r0 != 90) goto L02008d2c
    r0 = b[r7+r10] (u)
    r2 = 1
    r1 = r2 << r4
    if ((r0 & r1) == 0) {
    r2 = 0
    }
L02008d2c:
    r0 = r5
    r1 = r6
    r3 = r11
    call preset_band_controls_set_band_flag  ; @call.xl
    r4 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02008d3c:
    if (r6 != 3) goto L02008d0c
    r8 = r8 + 3
    r5 += 1  ; @add.ri.u5
L02008d46:
    if (r5 != 2) goto L02008d06
    {pc, r11-r4} = [sp++]

; preset_band_controls_apply_crossovers: 0x02008d4c..0x02008d90, module preset-band-controls (apply_crossovers)
.type preset_band_controls_apply_crossovers,@function
preset_band_controls_apply_crossovers:
    [--sp] = {rets, r9-r4}
    sp += -4
    r4 = r0
    r8 = L01c24d5c
    r5 = 0
    r9 = 1
    goto L02008d88
L02008d60:
    r6 = 0
    r7 = r8
    goto L02008d7e
L02008d66:
    r1 = r6  #
    r0 = b[r7++=1] (u)
    r2 = r0 * 0xA
    [sp] = r9  ; @st.w.sp.l
    r0 = r5
    r3 = r4
    call preset_band_controls_set_crossover  ; @call.xl
    r6 += 1  ; @add.ri.u5
L02008d7e:
    if (r6 != 3) goto L02008d66
    r8 = r8 + 3
    r5 += 1  ; @add.ri.u5
L02008d88:
    if (r5 != 2) goto L02008d60
    sp += 4
    {pc, r9-r4} = [sp++]
