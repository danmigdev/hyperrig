; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 2 functions, 0x020092e4..0x02009dd0

; preset_application_notify: 0x020092e4..0x020092fa, module preset-application (notify), scene-application (notify)
.type preset_application_notify,@function
preset_application_notify:
    [--sp] = rets
    r2 = r1
    r1 = 65535
    r1 <= insert(r0, p:16, l:16)
    r0 = 30
    call storage_coordination_notify
    pc = [sp++]

; preset_application_apply: 0x020092fa..0x02009dd0, module preset-application (apply)
.type preset_application_apply,@function
preset_application_apply:
    [--sp] = {rets, r15-r4}
    sp += -256
    r8 = r2
    r14 = r1
    r4 = r0
    call preset_application_asset_mode
    if (r0 != 0) goto L02009314
    r0 = 0
    r1 = 1
    call stereo_budget_set_stereo  ; @call.xl
L02009314:
    r7 = 0
    [r8+0] = r7
    [r14+0] = r7
    r9 = L01c1f180
    r0 = 255
    r5 = r9 + 9
    b[r5+10] = r0
    b[r5+9] = r0
    if (r4 >= 127) {  ; @if.ge.ri.s12
    r4 = -1
    }
    b[r5+11] = r4
    r0 = sp + 104
    r1 = sp + 76
    call preset_application_asset_layout
    r11 = L01c24790
    r12 = b[r11+1] (u)
    r10 = L01c26890
    r6 = [r10+280]
    r3 = b[r5+1] (u)
    r2 = b[r11+3] (u)
    r0 = 1
    r1 = 1
    if (r2 == r3) {
    r1 = 0
    }
    r3 = 1
    if (r2 >= 8) {  ; @if.ge.ri.s12
    r3 = 0
    }
    r13 = r3 & r1  #
    r2 = b[r5+0] (u)
    r4 = b[r11+2] (u)
    r1 = 1
    if (r4 == r2) {
    r1 = 0
    }
    if (r4 >= 15) {  ; @if.ge.ri.s12
    r0 = 0
    }
    r5 = r0 & r1
    if (r12 >= 16) {  ; @if.ge.ri.s12
    r12 = 16
    }
    if (r5 != 1) goto L02009402
    r0 = 0
    [sp+136] = r0
    r0 = 1
    call tempo_slot_services_priority_nest
    r0 = 0xDF000
    r1 = r4
    if (r4 >= 8) {  ; @if.ge.ri.s12
    r0 = 524280
    r1 = r4 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r0 += r1  ; @add.rr
    r1 = 1128745812
    r3 = sp + 140
    r2 = 8152
    call preset_application_header
    if (r0 == 0) goto L020093fc
    r1 = sp + 140
    r2 = sp + 136
    r0 = r4
    call preset_application_asset_resolve
    r4 = r0
    r0 = 0
    call tempo_slot_services_priority_nest
    if (r4 != 0) goto L02009402
    r0 = r10 + 1780  #
    r2 = [sp+144]
    r1 = [sp+136]
    r4 = 0
    r3 = 0
    [sp] = r4
    call preset_application_asset_matches
    r7 = 1
    if (r0 != 0) goto L02009402
    r7 = r0
    goto L02009402
L020093fc:
    r0 = 0
    call tempo_slot_services_priority_nest
L02009402:
    r0 = 0
    [sp+44] = r0
    r3 = 0
    [sp+40] = r6
    if (r13 == 0) goto L02009472
    r15 = r7
    r4 = b[r11+3] (u)
    r0 = b[r9+10] (u)
    r3 = 1
    r7 = 1
    if (r0 == r4) goto L0200946c
    r0 = 1
    r9 = 1
    call tempo_slot_services_priority_nest
    r1 = sp + 184
    r3 = sp + 180
    r2 = 8152
    r0 = r4
    call preset_application_asset_header
    r4 = r0
    r0 = 0
    r7 = 0
    call tempo_slot_services_priority_nest
    if (r4 == 0) goto L02009462
    r0 = r10 + 1796  #
    r3 = [sp+196]
    r2 = [sp+188]
    r1 = [sp+192]
    r4 = b[sp+180] (u)
    [sp] = r4
    call preset_application_asset_matches
    if (r0 != 0) goto L02009460
    r9 = r0
L02009460:
    r7 = r9
L02009462:
    r6 = [sp+40]
    r9 = L01c1f180
    r3 = 1
L0200946c:
    if (r7 != 0) goto L02009470
    r3 = r7
L02009470:
    r7 = r15
L02009472:
    r2 = b[r11+0] (u)
    r0 = 1
    r1 = 1
    if (r2 >= 4) {  ; @if.ge.ri.s12
    r1 = 0
    }
    r2 = 1346
    r2 = b[r11+r2] (u)
    if (r2 == 0) goto L0200948c
    r0 = 0
L0200948c:
    r15 = r1 | r0  #
    [sp+28] = r3
    r2 = r3 ^ 0x1
    r3 = r7 ^ 0x1
    if (r15 == 0) goto L020094aa
    call preset_application_asset_state416
    r1 = 1
    [sp+44] = r1
    if (r0 != 0) goto L020094aa
    [sp+44] = r0
L020094aa:
    r4 = r5 & r3
    r13 = r13 & r2
    r0 = 1
    if (r6 == 2) {  ; @if.eq.ri.s12
    r0 = 0
    }
    [sp+32] = r8  ; @st.w.sp.l
    r1 = r4 | r13  #
    [sp+36] = r4
    if (r1 != 0) goto L0200968a
    if (r0 != 0) goto L0200968a
    r0 = [sp+44]
    if (r0 != 0) goto L0200968a
    call preset_application_mode
    if (r15 != r0) goto L0200968a
    [sp+8] = r7
    [sp+4] = r15  ; @st.w.sp.l
    r5 = 0
    r0 = 0
    [sp+16] = r0
    [sp+20] = r0
    [sp+12] = r13  ; @st.w.sp.l
    goto L02009618
L020094ee:
    r1 = sp + 230
    r0 = r5
    call preset_application_chain_read  ; @call.xl
    r13 = 0  #
    [sp+24] = r0
    r0 = sp + 104
    r10 = [sp+20]  ; @ld.w.sp.l
    r8 = r0 + r10
    r0 = sp + 88
    r15 = r0 + r10
    r0 = r10 * 0x12
    r0 += r11
    r9 = r0 + 20
    r11 = [sp+16]  ; @ld.w.sp.l
    r7 = 1
    r6 = r5
    goto L020095e8
L02009522:
    ifs (r0 >= r12) goto L02009668
    r1 = b[r9+-8] (u)
    r0 = sp + 230
    if (r1 != r6) goto L02009668
    r4 = b[r0+r13] (u)
    r5 = b[r9+-7] (u)
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    if (r5 != r0) goto L02009648
    r5 = b[r8+r13] (u)
    r0 = r4
    call preset_application_placement  ; @call.xl
    if (r5 != r0) goto L02009648
    r0 = b[r9+-7] (u)
    if (r0 != 7) goto L020095a0
    r1 = 2
    r0 = r4
    call preset_application_parameter  ; @call.xl
    r1 = h[r9+0] (s)
    if (r0 != r1) goto L02009648
    r10 = r15
    r15 = r8
    r5 = r14
    r8 = 1
    r14 = 1
    ifs (r0 <= 0) {  ; @ifs.le.ri.s12
    r14 = 0
    }
    r0 = r4
    call ir_effect_lifecycle_owns  ; @call.xl
    if (r0 != 0) goto L02009590
    r8 = r0
L02009590:
    r0 = r14 ^ r8
    r14 = r5
    r8 = r15
    r15 = r10
    r10 = [sp+20]  ; @ld.w.sp.l
    if (r0 != 0) goto L02009648
L020095a0:
    r0 = b[r9+-6] (u)
    if (r0 == 0) goto L020095b0
    r0 = r4
    call preset_application_services_needs_resource  ; @call.xl
    if (r0 != 0) goto L02009648
L020095b0:
    r0 = L01c24790
    r3 = h[r0+8] (s)
    r1 = r9 + -4  #
    [sp] = r7
    r2 = 0
    r0 = r4
    call parameter_set_apply_set  ; @call.xl
    ifs (r0 < 0) goto L02009648
    r1 = r7 << r4
    b[r15+r13] = r4
    if (r0 == 0) goto L020095da
    r0 = r1
L020095da:
    r11 = r11 | r0  #
    r4 = [sp+36]
    r9 = r9 + 18
    r13 = r13 + 1
L020095e8:
    r0 = r10 + r13  #
    r1 = [sp+24]
    ifs (r13 < r1) goto L02009522
    [sp+16] = r11  ; @st.w.sp.l
    r6 += 1  ; @add.ri.u5
    r5 = r6  #
    [sp+20] = r0
    r8 = [sp+32]  ; @ld.w.sp.l
    r10 = L01c26890
    r6 = [sp+40]
    r9 = L01c1f180
    r13 = [sp+12]  ; @ld.w.sp.l
    r11 = L01c24790
L02009618:
    ifs (r5 <= 1) goto L020094ee
    r0 = [sp+20]
    if (r0 != r12) goto L02009b7c
    r0 = h[r11+8] (s)
    r7 = [sp+8]
    if (r0 == 0) goto L02009b84
    call preset_application_asset_clamp
    r4 = r0
    call preset_application_services_tempo  ; @call.xl
    if (r4 != r0) goto L02009b8a
    r15 = [sp+4]  ; @ld.w.sp.l
    goto L02009bae
L02009648:
    r8 = [sp+32]  ; @ld.w.sp.l
    r10 = L01c26890
    r6 = [sp+40]
    r15 = [sp+4]  ; @ld.w.sp.l
    r9 = L01c1f180
    r7 = [sp+8]
    r13 = [sp+12]  ; @ld.w.sp.l
    r4 = [sp+36]
    goto L02009684
L02009668:
    r8 = [sp+32]  ; @ld.w.sp.l
    r10 = L01c26890
    r6 = [sp+40]
    r15 = [sp+4]  ; @ld.w.sp.l
    r9 = L01c1f180
    r7 = [sp+8]
    r13 = [sp+12]  ; @ld.w.sp.l
L02009684:
    r11 = L01c24790
L0200968a:
    if (r6 != 2) goto L020096a6
    r0 = [sp+44]
    r1 = r4 | r0
    r0 = 1
    call storage_coordination_gate_core
    r0 = r11 + 1424
    r1 = 1
    call dsp_transition_request  ; @call.xl
L020096a6:
    b[r10+24] = r15
    r0 = [sp+44]
    if (r0 == 0) goto L020096fe
    call block_pool_maintain_wrapper
    if (r0 == 0) goto L020096fe
    call audio_pause_pause_audio
    r4 = 0
    goto L020096e0
L020096bc:
    r1 = sp + 66
    r0 = r4
    call preset_application_chain_read  ; @call.xl
    r5 = r0
    r6 = 0
    goto L020096da
L020096cc:
    r0 = sp + 66
    r0 = b[r0+r6] (u)
    call effect_ownership_remove  ; @call.xl
    r6 += 1  ; @add.ri.u5
L020096da:
    ifs (r6 < r5) goto L020096cc
    r4 += 1  ; @add.ri.u5
L020096e0:
    if (r4 != 2) goto L020096bc
    call effect_parameter_lifecycle_resource_flush  ; @call.xl
    call audio_pause_resume_audio
    call block_pool_maintain_wrapper
    r4 = [sp+36]
    if (r0 == 0) goto L020096fe
    r0 = -110
    [r14+0] = r0
L020096fe:
    r0 = [r14+0]
    r1 = r7 | r4
    if (r1 == 0) goto L02009716
    if (r0 != 0) goto L02009716
    r0 = b[r11+2] (u)
    call capture_loader_load
    [r14+0] = r0
L02009716:
    if (r0 != -111) goto L0200973c
    r1 = [r9+60]
    r0 = embedded_A2_capture
    if (r1 == r0) goto L02009734
    r1 = 4892
    r3_r2 = 0
    call capture_container_install
    if (r0 != 0) goto L0200973c
L02009734:
    r0 = 1
    r1 = 0
    call preset_application_services_clear_assets
L0200973c:
    if (r4 == 0) goto L02009784
    r0 = [r10+280]
    if (r0 == 0) goto L02009784
    r0 = b[r10+29] (u)
    if (r0 == 0) goto L02009784
    r5 = 1021
    r6 = [r10+r5<<2]
    call storage_platform_clock  ; @call.xl
    r4 = r0
    call preset_application_rate
    r7 = r0 * 0x14
    goto L02009768
L02009764:
    call storage_coordination_poll_forward
L02009768:
    r0 = [r10+524]
    if (r0 == 0) goto L02009778
    r0 = [r10+r5<<2]
    r0 = r0 - r6
    if (r0 > 2) goto L02009784
L02009778:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r4
    if (r0 < r7) goto L02009764
L02009784:
    r0 = [sp+28]
    r0 = r0 | r13
    if (r0 == 0) goto L0200979a
    r0 = b[r11+3] (u)
    r1 = 0
    call ir_installation_load
    [r8+0] = r0
L0200979a:
    call audio_pause_pause_audio
    r0 = 5
    call storage_control_activity
    r0 = L01c34458
    r1 = [r0+0]
    if (r1 == 0) goto L020097b2
    r0 = 2
    call r1
L020097b2:
    r0 = h[r11+8] (s)
    r1 = 1
    r2 = L01c34489
    b[r2+0] = r1
    if (r0 == 0) goto L020097c8
    call effect_setup_tempo  ; @call.xl
L020097c8:
    r9 = 0
    r6 = 0
    goto L0200980a
L020097ce:
    r1 = sp + 230
    r0 = r9
    call preset_application_chain_read  ; @call.xl
    r5 = r0
    r0 = sp + 240
    r7 = r0 + r6
    r4 = 0
    goto L020097fa
L020097e6:
    r0 = sp + 230
    r0 = b[r0+r4] (u)
    b[r7+r4] = r0
    call preset_application_services_detach_live  ; @call.xl
    r4 += 1  ; @add.ri.u5
L020097fa:
    r0 = r6 + r4
    ifs (r0 > 15) goto L02009804
    ifs (r4 < r5) goto L020097e6
L02009804:
    r9 = r9 + 1
    r6 = r0
L0200980a:
    if (r9 != 2) goto L020097ce
    r10 = 0
    r9 = 255
    goto L02009864
L02009816:
    r0 = sp + 120
    b[r0+r10] = r9
    r0 = r10 * 0x12
    r5 = r0 + r11
    r7 = 0
    goto L0200982a
L02009828:
    r7 += 1  ; @add.ri.u5
L0200982a:
    ifs (r7 >= r6) goto L02009860
    r0 = sp + 240
    r4 = b[r0+r7] (u)
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    r1 = b[r5+13] (u)
    if (r0 != r1) goto L02009828
    r0 = sp + 120
    b[r0+r10] = r4
    goto L02009858
L0200984c:
    r1 = sp + 240
    r1 += r7  ; @add.rr
    r7 = r0  #
    r2 = b[r1+1] (u)
    b[r1+0] = r2
L02009858:
    r0 = r7 + 1
    ifs (r0 < r6) goto L0200984c
    r6 += -1
L02009860:
    r10 = r10 + 1
L02009864:
    ifs (r10 < r12) goto L02009816
    r4 = 0
    r5 = L01c26890
    goto L02009882
L02009872:
    r0 = sp + 240
    r0 = b[r0+r4] (u)
    call tempo_slot_services_retire_slot  ; @call.xl
    r4 += 1  ; @add.ri.u5
L02009882:
    ifs (r4 < r6) goto L02009872
    r0 = 516
    r2 = 1
    b[r5+r0] = r2
    r0 = 0
    if (r15 == 0) goto L020098a0
    call preset_application_asset_state416
    if (r0 == 0) goto L0200989e
    r2 = 0
L0200989e:
    r0 = r2
L020098a0:
    call path_switch_switch_path
    if (r0 == 0) goto L020098b0
    r1 = [r14+0]
    if (r1 != 0) goto L020098b0
    [r14+0] = r0
L020098b0:
    r2 = b[r11+0] (u)
    r4 = 0
    r0 = 1
    r1 = 1
    if (r2 >= 3) {  ; @if.ge.ri.s12
    r1 = 0
    }
    r2 = 1344
    r2 = b[r11+r2] (u)
    if (r2 == 0) goto L020098cc
    r0 = 0
L020098cc:
    r8 = r14
    r0 |= r1
    call preset_band_controls_request_reserve
    r0 = L01c34458
    r0 = 516  #
    r1 = [r0+0]
    b[r5+r0] = r4
    if (r1 == 0) goto L020098ea
    r0 = 2
    call r1
L020098ea:
    r0 = 1
    r1 = L01c34489
    r9 = 0  #
    b[r1+0] = r0
    r14 = 0
    r10 = 0
    goto L02009a38
L020098fc:
    r0 = sp + 120
    r13 = b[r0+r14] (s)
    r0 = sp + 50
    b[r0+r14] = r9
    r0 = r14 * 0x12
    r15 = r0 + r11
    call storage_control_poll
    ifs (r13 < 0) goto L0200996a
    r7 = r15
    r0 = b[++r7=13] (u)
    if (r0 != 7) goto L0200995a
    r1 = 2
    r0 = r13
    call preset_application_parameter  ; @call.xl
    r2 = h[r15+20] (s)
    r1 = 0
    if (r0 != r2) goto L02009954
    r4 = 1
    r5 = 1
    ifs (r0 <= 0) {  ; @ifs.le.ri.s12
    r5 = 0
    }
    r0 = r13
    call ir_effect_lifecycle_owns  ; @call.xl
    if (r0 != 0) goto L0200994c
    r4 = r0
L0200994c:
    r0 = r5 ^ r4
    r1 = r0 ^ 0x1
L02009954:
    r0 = sp + 50
    b[r0+r14] = r1
L0200995a:
    r1 = b[r15+12] (u)
    r2 = 99
    r0 = r13
    call preset_application_services_move  ; @call.xl
    goto L020099c2
L0200996a:
    r2 = b[r15+13] (u)
    r0 = b[r15+12] (u)
    r1 = 99
    call effect_setup_create  ; @call.xl
    r13 = r0
    r0 |= 1
    if (r0 != -3) goto L0200999a
    call effect_parameter_lifecycle_resource_flush  ; @call.xl
    r2 = b[r15+13] (u)
    r0 = b[r15+12] (u)
    r1 = 99
    call effect_setup_create  ; @call.xl
    r13 = r0
L0200999a:
    ifs (r13 > -1) goto L020099b4
    if (r13 == -2) goto L020099b4
    r2 = b[r15+13] (u)
    r0 = b[r15+12] (u)
    r1 = 99
    call effect_setup_create_disabled  ; @call.xl
    r13 = r0
L020099b4:
    r0 = sp + 120
    b[r0+r14] = r13
    ifs (r13 < 0) goto L02009a30
    r7 = r15 + 13
L020099c2:
    r4 = 0
    goto L020099f2
L020099c6:
    r1 = r4  #
    r6 = b[r7+0] (u)
    r0 = r6
    call preset_application_parameter_order
    r5 = r0
    r0 = r6
    r1 = r5
    call preset_application_metadata  ; @call.xl
    if (r0 == 0) goto L020099f0
    r0 = r15 + 16
    r2 = h[r0+r5<<1] (s)
    r0 = r13
    r1 = r5
    call effect_parameter_lifecycle_parameter_commit  ; @call.xl
L020099f0:
    r4 += 1  ; @add.ri.u5
L020099f2:
    if (r4 != 7) goto L020099c6
    r0 = sp + 104
    r1 = b[r0+r14] (u)
    r0 = r13
    call preset_band_controls_set_group_quiet  ; @call.xl
    r1 = b[++r15=14] (u)
    r0 = r13
    call effect_enable_commit_unchecked  ; @call.xl
    if (r0 == 0) goto L02009a26
    call effect_parameter_lifecycle_resource_flush  ; @call.xl
    r1 = b[r15+0] (u)
    r0 = r13
    call effect_enable_commit_unchecked  ; @call.xl
    goto L02009a28
L02009a26:
    r0 = 0
L02009a28:
    r1 = 1
    if (r0 != 0) goto L02009a32
    r1 = r0
    goto L02009a32
L02009a30:
    r1 = 1
L02009a32:
    r10 += r1
    r14 = r14 + 1
L02009a38:
    ifs (r14 < r12) goto L020098fc
    r0 = L01c34458
    r1 = [r0+0]
    r4 = 0
    r0 = L01c34489
    b[r0+0] = r4
    if (r1 == 0) goto L02009a54
    r0 = 0
    call r1
L02009a54:
    r0 = 1
    call preset_band_controls_apply_band_flags
    r6 = sp + 76
    r9 = [sp+40]  ; @ld.w.sp.l
    goto L02009a82
L02009a62:
    r5 = 0
    r7 = r6
    goto L02009a7a
L02009a68:
    r3 = b[r7+1] (s)
    r2 = b[r7++=2] (s)
    r1_r0 = r5_r4
    call preset_band_controls_set_band_levels_now  ; @call.xl
    r5 += 1  ; @add.ri.u5
L02009a7a:
    if (r5 != 3) goto L02009a68
    r6 += 6  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02009a82:
    if (r4 != 2) goto L02009a62
    r0 = 1
    call preset_band_controls_apply_crossovers
    call effect_setup_total_cost  ; @call.xl
    r4 = r0
    call preset_application_services_budget  ; @call.xl
    if (r4 > r0) {
    call effect_parameter_lifecycle_resource_flush  ; @call.xl
    }
    r0 = L01c34458
    r1 = [r0+0]
    if (r1 == 0) goto L02009ab2
    r0 = 0
    call r1
L02009ab2:
; HyperRig MINI, product option: the cuts of the cabs are there at once, the sound being paused (mini/product/cab.c)
.if MINI_PRODUCT
    call hyperrig_cab_now
.endif
    r0 = 0
    r4 = 0
    call storage_control_activity
    call audio_pause_resume_audio
    r5 = r11 + 13
    goto L02009aec
L02009ac4:
    r0 = sp + 120
    r0 = b[r0+r4] (s)
    ifs (r0 < 0) goto L02009ae8
    r1 = b[r5+0] (u)
    if (r1 != 7) goto L02009ae8
    r1 = sp + 50
    r1 = b[r1+r4] (u)
    if (r1 != 0) goto L02009ae8
    call slot_ir_load_load_slot_ir
    r1 = 1
    if (r0 != 0) goto L02009ae6
    r1 = r0
L02009ae6:
    r10 += r1
L02009ae8:
    r5 += 18  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02009aec:
    ifs (r4 < r12) goto L02009ac4
    call ir_installation_refresh
    r1 = b[r11+5] (s)
    r0 = b[r11+4] (s)
    call preset_application_services_set_levels
    r1 = 1
    if (r9 != 2) {  ; @if.ne.ri.s12
    r0 = L01c1f7e0
    r1 = b[r0+0] (u)
    }
    r0 = r11 + 1424
    call dsp_transition_request  ; @call.xl
    r0 = 0
    r1 = L01c26890
    b[r1+24] = r0
    if (r9 == 2) {  ; @if.eq.ri.s12
    r1 = 0
    call storage_coordination_gate_core
    }
    r0 = [sp+32]
    r1 = [r0+0]
    r0 = [r8+0]
    call preset_application_services_select_assets
    r0 = sp + 120
    call scene_import_import_scenes
L02009b40:
    call preset_application_asset_mode
    if (r0 == 0) goto L02009b50
    r0 = 1
    r1 = 1
    call stereo_budget_set_stereo  ; @call.xl
L02009b50:
    r0 = 0
    call stereo_budget_update_suspension  ; @call.xl
    r1 = r0
    if (r1 == 0) goto L02009b76
    r0 = 3
    if (r1 != 1) {  ; @if.ne.ri.s12
    r0 = 4
    }
    if (r1 != 1) {  ; @if.ne.ri.s12
    r1 = 0
    } else {
    r1 = L01c341a8
    r1 = [r1+0]
    }
    call preset_application_notify
L02009b76:
    r0 = r10
    sp += 256
    {pc, r15-r4} = [sp++]
L02009b7c:
    r15 = [sp+4]  ; @ld.w.sp.l
    r7 = [sp+8]
    goto L0200968a
L02009b84:
    r15 = [sp+4]  ; @ld.w.sp.l
    goto L02009bb0
L02009b8a:
    r0 = h[r11+8] (s)
    r1 = 0
    [sp+224] = r1
    r1 = sp + 224
    call tempo_slot_services_tempo_fits  ; @call.xl
    r15 = [sp+4]  ; @ld.w.sp.l
    if (r0 == 0) goto L02009dcc
    r0 = [sp+224]
    r1 = [sp+16]
    r1 |= r0
    [sp+16] = r1
L02009bae:
    r4 = [sp+36]
L02009bb0:
    r0 = [sp+16]
    call preset_application_services_automation_fits  ; @call.xl
    if (r0 == 0) goto L0200968a
    if (r7 == 0) goto L02009bce
    r0 = b[r11+2] (u)
    call capture_loader_load
    [r14+0] = r0
    r7 = 0
L02009bce:
    r2 = [sp+28]
    if (r2 == 0) goto L02009be2
    r0 = b[r11+3] (u)
    r1 = 0
    call ir_installation_load
    r2 = 0
    [r8+0] = r0
L02009be2:
    r6 = 516
    r1 = b[r11+0] (u)
    r4 = 1
    b[r10+r6] = r4
    r5 = 0
    r0 = 1
    if (r1 >= 3) {  ; @if.ge.ri.s12
    r0 = 0
    }
    r1 = 1344  #
    [sp+8] = r7
    [sp+28] = r2
    r2 = b[r11+r1] (u)
    r1 = 1
    if (r2 == 0) goto L02009c0c
    r1 = 0
L02009c0c:
    r0 |= r1
    call preset_band_controls_request_reserve
    r0 = L01c1f7e0
    r9 = b[r0+0] (u)
    r0 = L01c1f180
    r7 = b[r0+8] (u)
    b[r10+r6] = r5
    r0 = 5
    call storage_control_activity
    r0 = L01c34489
    b[r0+0] = r4
    if (r7 != 0) goto L02009c3c
    r9 = 1
L02009c3c:
    r0 = h[r11+8] (s)
    if (r0 == 0) goto L02009c64
    call preset_application_asset_clamp
    r4 = r0
    call preset_application_services_tempo  ; @call.xl
    if (r4 == r0) goto L02009c64
    r0 = h[r11+8] (s)
    call tempo_slot_services_set_tempo  ; @call.xl
    r5 = r0
    if (r5 != -6) {
    r5 = 0
    }
L02009c64:
    r4 = r11 + 16
    r7_r6 = 0
    goto L02009c8e
L02009c6c:
    call storage_control_poll
    r0 = sp + 88
    r0 = b[r0+r7] (u)
    r3 = 0
    r1 = r4  #
    [sp] = r6
    r2 = r9
    call parameter_set_apply_set  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02009c8a
    r5 = -6
L02009c8a:
    r4 += 18  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L02009c8e:
    if (r5 != 0) goto L02009c94
    ifs (r7 < r12) goto L02009c6c
L02009c94:
    r10 = 0
    r0 = L01c34489
    b[r0+0] = r10
    if (r5 != 0) goto L02009dae  ; @bne.ri
    goto L02009cec
L02009ca6:
    r13 = r11 + 14
    r7 = 0
    goto L02009ce4
L02009cae:
    r4 = 1
    r6 = 1
    if (r10 != 0) {  ; @if.ne.ri.s12
    r6 = 0
    }
    r0 = b[r13++=18] (u)
    if (r0 != 0) goto L02009cc0
    r4 = r0
L02009cc0:
    r0 = sp + 88
    r5 = b[r0+r7] (u)
    r0 = r5
    call preset_application_effect_enabled  ; @call.xl
    if (r6 == r4) goto L02009ce2
    if (r0 == r4) goto L02009ce2
    r0 = r5
    r1 = r4
    call effect_enable_fast_unchecked  ; @call.xl
    if (r0 != 0) goto L02009dae
L02009ce2:
    r7 += 1  ; @add.ri.u5
L02009ce4:
    ifs (r7 < r12) goto L02009cae
    r10 = r10 + 1
L02009cec:
    ifs (r10 <= 1) goto L02009ca6
    r0 = r9
    call preset_band_controls_apply_band_flags
    r4 = 0
    r6 = sp + 76
    goto L02009d20
L02009cfc:
    r5 = 0
    r7 = r6
    goto L02009d18
L02009d02:
    r3 = b[r7+1] (s)
    r2 = b[r7++=2] (s)
    [sp] = r9  ; @st.w.sp.l
    r1_r0 = r5_r4
    call preset_band_controls_set_band_levels  ; @call.xl
    r5 += 1  ; @add.ri.u5
L02009d18:
    if (r5 != 3) goto L02009d02
    r6 += 6  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02009d20:
    if (r4 != 2) goto L02009cfc
    r0 = r9
    call preset_band_controls_apply_crossovers
    r0 = 0
    r5 = 0
    call storage_control_activity
    call preset_application_services_queued  ; @call.xl
    if (r0 == 0) goto L02009d68
    call effect_setup_total_cost  ; @call.xl
    r4 = r0
    call preset_application_services_budget  ; @call.xl
    if (r4 <= r0) goto L02009d68
    r0 = 1
    r1 = 0
    call storage_coordination_gate_core
    call audio_pause_pause_audio
    call effect_parameter_lifecycle_resource_flush  ; @call.xl
    call audio_pause_resume_audio
    r1_r0 = 0
    call storage_coordination_gate_core
L02009d68:
    call ir_installation_refresh
    r1 = b[r11+5] (s)
    r0 = b[r11+4] (s)
    call preset_application_services_set_levels
    r0 = r11 + 1424
    r1 = r9
    call dsp_transition_request  ; @call.xl
    goto L02009d94
L02009d86:
    r0 = sp + 88
    r0 = b[r0+r5] (u)
    r1 = sp + 120
    b[r1+r5] = r0
    r5 += 1  ; @add.ri.u5
L02009d94:
    ifs (r5 < r12) goto L02009d86
    r0 = [sp+32]
    r1 = [r0+0]
    r0 = [r14+0]
    call preset_application_services_select_assets
    r0 = sp + 120
    call scene_import_import_scenes
    r10 = 0
    goto L02009b40
L02009dae:
    r0 = 0
    call storage_control_activity
    r8 = [sp+32]  ; @ld.w.sp.l
    r10 = L01c26890
    r6 = [sp+40]
    r9 = L01c1f180
    r7 = [sp+8]
    r13 = [sp+12]  ; @ld.w.sp.l
L02009dcc:
    r4 = [sp+36]
    goto L0200968a
