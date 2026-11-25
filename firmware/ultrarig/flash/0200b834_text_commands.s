; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; text_commands: 1 function, 0x0200b834..0x0200c77a

; text_commands_text_command: 0x0200b834..0x0200c77a, module text-commands (text_command)
; HyperRig MINI, product option: eight scenes (mini/product/scenes.c).
.type text_commands_text_command,@function
text_commands_text_command:
    [--sp] = {rets, r15-r4}
    sp += -288
    r6 = r1
    r4 = r0
    [sp+284] = r6
    r12 = L02035810
    r1 = r12 + 677
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200ba7c  ; @beq.ri.l
    r1 = r12 + 683
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200ba7c  ; @beq.ri.l
    r1 = r12 + 689
    r0 = r4
    call L02028308  ; @call.xl
    r5 = L01c24790
    r13 = L01c1f180
    if (r0 == 0) goto L0200ba86  ; @beq.ri.l
    r1 = r12 + 695
    r0 = r4
    call L02028308  ; @call.xl
    r14 = L01c26890
    if (r0 == 0) goto L0200badc
    r1 = r12 + 420
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bb08
    r1 = r12 + 1280
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bb78
    r1 = r12 + 1086
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bc92
    r1 = r12 + 1289
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bce0
    r1 = r12 + 701
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bd3a
    r1 = r12 + 425
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bd8c
    r1 = r12 + 907
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200be8c
    r1 = r12 + 707
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bf32
    r1 = r12 + 194
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bf6e
    r1 = r12 + 198
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200bfbc
    r1 = r12 + 435
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c06e
    r1 = r12 + 713
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c0c6
    r1 = r12 + 719
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c150
    r1 = r12 + 725
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c28c
    r1 = r12 + 731
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c36e
    r1 = r12 + 737
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c398
    r1 = r12 + 743
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c4e0
    r1 = r12 + 749
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c3ac
    r1 = r12 + 755
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c3ac
    r1 = r12 + 445
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c500
    r1 = r12 + 450
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c500
    r1 = r12 + 761
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c5d4
    r1 = r12 + 455
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c618
    r1 = r12 + 767
    r0 = r4
    call L02028308  ; @call.xl
    r4 = 0
    if (r0 != 0) goto L0200bfaa
    r0 = sp + 284
    r1 = 8
    call capture_command_slot_parse
    r5 = r0
    ifs (r5 < 0) goto L0200c708
    r1 = 1
    r4 = 1
    call ir_installation_load
    if (r0 != 0) goto L0200c70a
    r0 = r12 + 2046
    r1 = r5
    call link_and_print_print
    goto L0200bfaa
L0200ba7c:
    r0 = r4
    r1 = r6
    call command_services_slot_dump
    goto L0200bfa8
L0200ba86:
    r0 = sp + 284
    r1 = 32
    call capture_command_slot_parse
    r4 = r0
    ifs (r4 <= -1) goto L0200bb6c
    call status_snapshot_status_snapshot
    r6 = sp + 244
    r0 = r6
    call command_services_record_header
    r1 = [sp+284]
    r0 = r12 + 956  #
    r2 = b[r1+0] (u)
    if (r2 != 0) goto L0200bab2
    r1 = r0
L0200bab2:
    r0 = r6
    call record_helpers_copy_name
    r0 = r4  #
    r3 = [sp+248]
    r1 = r6
    r2 = r5
    call preset_storage_preparation_preset_write
    r2 = r0
    r0 = r4
    call preset_storage_preparation_invalidate
    if (r2 == 0) goto L0200bbac
    r0 = r2
    call capture_command_status_text
    r1 = r0
    r0 = r12 + 2236
    goto L0200bb72
L0200badc:
    r0 = sp + 284
    r1 = 32
    call capture_command_slot_parse
    r4 = r0
    call storage_platform_clock  ; @call.xl
    r6 = r0
    r1 = sp + 244
    r0 = r4
    call preset_preflight_preflight
    if (r0 == 0) goto L0200bbd8
    call capture_command_status_text
    r1 = r0
    r0 = r12 + 2250
    goto L0200bb72
L0200bb08:
    r0 = sp + 284
.if MINI_PRODUCT
    r1 = 8
.else
    r1 = 4
.endif
    call capture_command_slot_parse
    r4 = r0
    ifs (r4 < 0) goto L0200bba6
.if MINI_PRODUCT
    r0 = r4 * 0x104
    r1 = hyperrig_scene_base  ; @li.u32
    r0 += r1  ; @add.rr
    r1 = 11936
.else
    r0 = r4 * 0x104
    r0 += r14
    r1 = 11936
.endif
    r0 = b[r0+r1] (u)
    if (r0 == 0) goto L0200bba6
    call storage_platform_clock  ; @call.xl
    r6 = r0
    r0 = r4
    call scene_application_apply
    r5 = r0
    r1 = r6
    call scene_application_report
    r2 = r0
    r0 = 7
    r1 = r4
    call storage_coordination_notify
    r0 = r6
    call preset_loader_elapsed
    r6 = r0
    r7 = r12 + 2007
    call stereo_budget_suspended  ; @call.xl
    if (r0 != 0) goto L0200bb5e
    r7 = r12
L0200bb5e:
    r0 = r12 + 5210  #
    [sp] = r7
    r1 = r4
    r2 = r5
    r3 = r6
    goto L0200bc8c
L0200bb6c:
    r0 = r12 + 4180
    r1 = 31
L0200bb72:
    call link_and_print_print
    goto L0200bfa8
L0200bb78:
    r0 = sp + 284
.if MINI_PRODUCT
    r1 = 8
.else
    r1 = 4
.endif
    call capture_command_slot_parse
    r4 = r0
.if MINI_PRODUCT
    ifs (r4 <= -1) goto L0200bd34
    r1 = [r13+92]
    call hyperrig_scene_fits  ; @call.xl
    if (r0 == 0) goto L0200bfa8
    r0 = r4
    call command_services_effect_snapshot
.else
    ifs (r4 <= -1) goto L0200bd34
    call command_services_effect_snapshot
.endif
    [r13+88] = r4
    r0 = [r13+92]
    ifs (r0 < 0) goto L0200bba2
    call command_services_save_slot
    if (r0 == 0) goto L0200be60
L0200bba2:
    r2 = -1
    goto L0200be64
L0200bba6:
    r0 = r12 + 3705
    goto L0200bfa4
L0200bbac:
    r2 = b[r5+3] (u)
    [r13+92] = r4
    r1 = -1
    r0 = -1
    if (r2 != 255) {  ; @if.ne.ri.s12
    r0 = r2
    }
    r3 = b[r5+1] (u)
    r2 = b[r5+2] (u)
    [sp+4] = r0
    if (r2 != 255) {  ; @if.ne.ri.s12
    r1 = r2
    }
    r0 = r12 + 6493  #
    [sp] = r1
    r2 = sp + 244
    r2 += 16  ; @add.ri.u5
    r1 = r4
    goto L0200bc8c
L0200bbd8:
    call storage_platform_clock  ; @call.xl
    r9 = r0
    call preset_application_rate
    r10 = r0
    call storage_platform_clock  ; @call.xl
    r1 = 1023
    r7 = [r14+r1<<2]
    r5 = r0
    r1 = sp + 240
    r2 = sp + 236
    r0 = r4
    call preset_application_apply
    r8 = r0
    [r13+92] = r4
    r0 = 5
    r1 = r4
    r2 = r8
    call storage_coordination_notify
    r0 = r9 - r6
    r1 = 1000
    r1 = r10 / r1 (u)
    r1 = r0 / r1 (u)
    r0 = r4
    r2 = r5
    r3 = r7
    call preset_loader_report
    r10 = r12 + 2539  #
    r6 = [sp+240]
    r13 = r12
    if (r6 != 0) goto L0200bc3a
    r10 = r13
L0200bc3a:
    r11 = [sp+236]  ; @ld.w.sp.l
    r7 = sp + 244
    r0 = r5
    call preset_loader_elapsed
    r9 = r0
    if (r6 == 0) goto L0200bc54
    r0 = r6
    call capture_command_status_text
    r13 = r0
L0200bc54:
    r5 = r7 + 16
    r7 = r12 + 2007
    call stereo_budget_suspended  ; @call.xl
    if (r0 != 0) goto L0200bc64
    r7 = r12
L0200bc64:
    r0 = r12 + 7  #
    [sp+24] = r7
    if (r6 != 0) goto L0200bc6e
    r0 = r12
L0200bc6e:
    r0 = r12 + 7828  #
    [sp+20] = r0
    [sp+16] = r13  ; @st.w.sp.l
    [sp+12] = r10  ; @st.w.sp.l
    [sp+8] = r9  ; @st.w.sp.l
    [sp+4] = r11  ; @st.w.sp.l
    r1 = r4  #
    [sp] = r6
    r2 = r5
L0200bc8a:
    r3 = r8
L0200bc8c:
    call link_and_print_print
    goto L0200bfa8
L0200bc92:
    r0 = sp + 284
.if MINI_PRODUCT
    r1 = 8
.else
    r1 = 4
.endif
    call capture_command_slot_parse
    r4 = r0
    ifs (r4 <= -1) goto L0200bd86
    r0 = r4 * 0x104
    r2 = [r13+88]
.if MINI_PRODUCT
    r3 = hyperrig_scene_base  ; @li.u32
    r0 += r3  ; @add.rr
    r3 = 11936
    r1 = 0
.else
    r0 += r14
    r3 = 11936
    r1 = 0
.endif
    b[r0+r3] = r1
    if (r2 == r4) {
    [r13+88] = 0xFFFFFFFF
    }
    r0 = [r13+92]
.if MINI_PRODUCT
    r2 = r4 << 4
    r3 = hyperrig_name_base  ; @li.u32
    r2 += r3  ; @add.rr
    r3 = 3248
.else
    r2 = r4 << 4
    r2 += r14
    r3 = 3248
.endif
    b[r2+r3] = r1
    ifs (r0 < 0) goto L0200bcdc
    call command_services_save_slot
    if (r0 == 0) goto L0200bf1c
L0200bcdc:
    r2 = -1
    goto L0200bf20
L0200bce0:
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L0200be6a
    r0 = sp + 284
.if MINI_PRODUCT
    r1 = 8
.else
    r1 = 4
.endif
    call capture_command_slot_parse
    r4 = r0
    ifs (r4 <= -1) goto L0200bf2c
    r1 = [sp+284]
.if MINI_PRODUCT
    r0 = r4 << 4
    r5 = hyperrig_name_base  ; @li.u32
    r0 += r5  ; @add.rr
    r5 = r0 + 3248
.else
    r0 = r4 << 4
    r0 += r14
    r5 = r0 + 3248
.endif
    r0 = r5
    call scene_import_clean_name
    r0 = [r13+92]
    ifs (r0 < 0) goto L0200bf62
    call command_services_save_names
    r3 = [r13+92]
    if (r0 == 0) goto L0200bf60
    ifs (r3 < 0) goto L0200bf60
    if (r0 != -5) goto L0200bfb0
    r1 = r12 + 6026
    goto L0200bfb6
L0200bd34:
    r0 = r12 + 3383
    goto L0200bfa4
L0200bd3a:
    r0 = sp + 284
    r1 = 32
    call capture_command_slot_parse
    r5 = r0
    r2 = r12 + 2033
    ifs (r5 < 0) goto L0200bd80
    r1 = [sp+284]
    r0 = b[r1+0] (u)
    if (r0 == 0) goto L0200bd80
    r6 = sp + 244
    r0 = r6
    call record_helpers_copy_name
    r3_r2 = 0
    r0 = r5
    r1 = r6
    call preset_storage_preparation_preset_write
    r2 = r0
    r0 = r5
    call preset_storage_preparation_invalidate
    if (r2 == 0) goto L0200bf92
    r0 = r2
    call capture_command_status_text
    r2 = r0
L0200bd80:
    r0 = r12 + 1571
    goto L0200bf24
L0200bd86:
    r0 = r12 + 2020
    goto L0200bfa4
L0200bd8c:
    call audio_pause_pause_audio
    r4 = 0
    r6 = 1
    goto L0200bdec
L0200bd96:
    r1 = sp + 226
    r0 = r4
    call preset_application_chain_read  ; @call.xl
    r5 = r0
    r7 = 0
    goto L0200bdb8
L0200bda8:
    r0 = sp + 226
    r0 = b[r0+r7] (u)
    call effect_ownership_remove  ; @call.xl
    r7 += 1  ; @add.ri.u5
L0200bdb8:
    ifs (r7 < r5) goto L0200bda8
    r5 = 0
    goto L0200bde6
L0200bdc0:
    r2 = 0
    r3 = 1
    r1_r0 = r5_r4
    call preset_band_controls_set_band_flag  ; @call.xl
    r3_r2 = 0
    r1_r0 = r5_r4
    call preset_band_controls_set_band_levels_now  ; @call.xl
    r2 = 0
    r3 = 1
    r1_r0 = r5_r4  #
    [sp] = r6
    call preset_band_controls_set_crossover  ; @call.xl
    r5 += 1  ; @add.ri.u5
L0200bde6:
    if (r5 != 3) goto L0200bdc0
    r4 += 1  ; @add.ri.u5
L0200bdec:
    if (r4 != 2) goto L0200bd96
    call effect_parameter_lifecycle_resource_flush  ; @call.xl
    call audio_pause_resume_audio
    r0 = 1
    r4 = 1
    call path_switch_switch_path
    r0 = 1
    call preset_band_controls_request_reserve
.if MINI_PRODUCT
    r0 = hyperrig_scenes  ; @li.u32
    r1 = 0
    r2 = 2080
.else
    r0 = 11936
    r0 += r14
    r1 = 0
    r2 = 1040
.endif
    r5 = 0
    call effect_enable_memset  ; @call.xl
.if MINI_PRODUCT
    r0 = hyperrig_scene_names  ; @li.u32
    r1 = 0
    r2 = 128
.else
    r0 = r14 + 3248
    r1 = 0
    r2 = 64
.endif
    call effect_enable_memset  ; @call.xl
    r0 = -1
    [r13+88] = r0
    [r13+92] = r0
    h[r14+78] = r5
    r0 = 255
    b[r13+20] = r0
    call stereo_budget_end_suspension  ; @call.xl
    r0 = L01c1f7e0
    r0 = r12 + 1772  #
    r1 = b[r0+0] (u)
    call dsp_transition_request  ; @call.xl
    r0 = r12 + 1298
    call link_and_print_print
    goto L0200bfaa
L0200be60:
    r2 = [r13+92]
L0200be64:
    r0 = r12 + 4404
    goto L0200bf24
L0200be6a:
.if MINI_PRODUCT
    r4 = hyperrig_scene_names  ; @li.u32
    r5 = 0
.else
    r4 = r14 + 3248
    r5 = 0
.endif
    goto L0200be82
L0200be72:
    r0 = r12 + 3143
    r1 = r5
    r2 = r4
    call link_and_print_print
    r4 += 16  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L0200be82:
.if MINI_PRODUCT
    if (r5 != 8) goto L0200be72
.else
    if (r5 != 4) goto L0200be72
.endif
    r0 = r12 + 2264
    goto L0200bfa4
L0200be8c:
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L0200c034
    r1 = r12 + 530
    r2 = 4
    r0 = r6
    call capture_command_prefix  ; @call.xl
    if (r0 == 0) goto L0200c002
L0200bea4:
    r1_r0 = 0
    goto L0200beda
L0200bea8:
    r2 = b[r6+r1] (s)
    r3 = r2 + -97
    r4 = r3 + 49
    r4 = r4.b0 (u)
    r2 += -87
    if (r4 > 9) goto L0200bec0
    r2 += 39
    goto L0200bed0
L0200bec0:
    r4 = r3.b0 (u)
    if (r4 <= 5) goto L0200bed0
    r3 += 32
    r3 = r3.b0 (u)
    if (r3 > 5) goto L0200bfa0
    r2 += 32
L0200bed0:
    ifs (r2 < 0) goto L0200bfa0
    r0 = r0 << 4
    r0 |= r2
    r1 += 1  ; @add.ri.u5
L0200beda:
    ifs (r1 <= 5) goto L0200bea8
    r1 = b[r6+6] (u)
    r2 = r1 + -10
    if (r2 > 22) goto L0200bef4
    r3 = 4194313
    r2 = r3 & (1 << r2)
    if (r2 != 0) goto L0200bef6
L0200bef4:
    if (r1 != 0) goto L0200bfa0
L0200bef6:
    r1 = r0 >> 19
    r1 = r1 << 11
    r0 = r0.l (u)
    r2 = r0 >> 5
    r2 = r2 & 0x7E0
    r1 |= r2
    r0 = uextra(r0, p:3, l:5)
    r4 = r1 | r0
    r0 = 65535
    if ((r4 & r0) == 0) {
    r4 = 2081
    }
    goto L0200c00c
L0200bf1c:
    r2 = [r13+92]
L0200bf20:
    r0 = r12 + 4278
L0200bf24:
    r1 = r4
L0200bf26:
    call link_and_print_print
    goto L0200bfa8
L0200bf2c:
    r0 = r12 + 4674
    goto L0200bfa4
.if MINI_PRODUCT
L0200bf32:
    r0 = [r13+88]
    call hyperrig_snaps  ; @call.xl
    goto L0200bfa8
    r0 = 12456
.else
L0200bf32:
    r0 = 12456
.endif
    r3 = b[r14+r0] (u)
    r0 = 12196
    r2 = b[r14+r0] (u)
    r0 = 11936
    r1 = b[r14+r0] (u)
    r0 = 12716
    r4 = b[r14+r0] (u)
    r0 = [r13+88]
    r0 = r12 + 4564  #
    [sp+4] = r0
    [sp] = r4
    goto L0200bc8c
L0200bf60:
    if (r0 == 0) goto L0200bf64
L0200bf62:
    r3 = -1
L0200bf64:
    r0 = r12 + 5022
    r1 = r4
    r2 = r5
    goto L0200bc8c
L0200bf6e:
    call storage_platform_clock  ; @call.xl
    r1 = [r13+24]
    r1 = r1 * 0xA
    call tap_tempo_tap_tempo
    r1 = 10
    r1 = r0 / r1 (s)
    r2 = r1 * 0xA
    r2 = r0 - r2
    r0 = r12 + 2569
    goto L0200bf26
L0200bf92:
    r0 = r12 + 3161
    r1 = sp + 244
    r2 = r1 + 16
    r1 = r5
    goto L0200bf26
L0200bfa0:
    r0 = r12 + 3179
L0200bfa4:
    call link_and_print_print
L0200bfa8:
    r4 = 1
L0200bfaa:
    r0 = r4
    sp += 288
    {pc, r15-r4} = [sp++]
L0200bfb0:
    call capture_command_status_text
    r1 = r0
L0200bfb6:
    r0 = r12 + 2919
    goto L0200bb72
L0200bfbc:
    call preset_application_services_tempo  ; @call.xl
    r1 = b[r6+0] (u)
    if (r1 == 0) goto L0200bff0
    r1 = sp + 216
    r2 = 10
    r0 = r6
    call capture_command_decimal  ; @call.xl
    r1 = [sp+216]
    if (r1 == r6) goto L0200c27a
    r1 = 0
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r1 = 30000
    r1 = smin(r0, r1)
    }
    r0 = r1
    call tempo_slot_services_tempo_command
L0200bff0:
    r1 = 10
    r1 = r0 / r1 (s)
    r2 = r1 * 0xA
    r2 = r0 - r2
    r0 = r12 + 1582
    goto L0200bf26
L0200c002:
    r0 = b[r6+4] (u)
    r0 |= 32
    r4 = 0
    if (r0 != 32) goto L0200bea4
L0200c00c:
    h[r14+78] = r4
    r1 = 32
    r0 = r6
    call L020282f4  ; @call.xl
    goto L0200c024
L0200c01c:
    r1 = b[r0+0] (u)
    if (r1 != 32) goto L0200c028
    r0 += 1  ; @add.ri.u5
L0200c024:
    if (r0 != 0) goto L0200c01c
    goto L0200c034
L0200c028:
    r1 = r12 + 430
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c12e
L0200c034:
    r0 = h[r14+78] (u)
    r1 = 0
    b[sp+224] = r1
    h[sp+222] = r1
    if (r0 == 0) goto L0200c064
    r1 = sp + 222
    call command_services_colour_bytes
    r4 = [r13+92]
    r3 = b[sp+224] (u)
    r2 = b[sp+223] (u)
    r1 = b[sp+222] (u)
    r0 = r12 + 5053  #
    [sp] = r4
    goto L0200bc8c
L0200c064:
    r1 = [r13+92]
    r0 = r12 + 4035
    goto L0200bb72
L0200c06e:
    r0 = sp + 284
    r1 = 32
    call capture_command_slot_parse
    r4 = r0
    ifs (r4 <= -1) goto L0200c280  ; @bles.ri.l
    r1 = 0
    r3_r2 = 0
    call preset_storage_preparation_preset_write
    r2 = r0
    r0 = r4
    call preset_storage_preparation_invalidate
    if (r2 != 0) goto L0200c284
    r0 = [r13+92]
    if (r0 == r4) {
    [r13+92] = 0xFFFFFFFF
    }
    r0 = b[r13+20] (s)
    if (r0 == r4) {
    r0 = 255
    b[r13+20] = r0
    }
    r1 = [r13+100]
    r0 = r12 + 1784
    if (r1 == r4) {
    r2 = 0xFFFFFFFF  ; @li.modimm
    r3 = r2
    d[r13+100] = r3_r2
    }
    goto L0200c288
L0200c0c6:
    call preset_storage_preparation_prepare
    r0 = 3
    call command_services_count_matches
    r8 = r0
    r0 = 1
    r4 = 1
    call command_services_count_matches
    r9 = r0
    r0 = 2
    call command_services_count_matches
    r10 = r0
    r0 = 4
    call command_services_count_matches
    r11 = r0
    r0 = 5
    call command_services_count_matches
    r1 = r14 + 3492
    r2 = [r1+0]
    r3 = [r1+8]
    r1 = [r1+12]
    r7 = [r13+208]
    r6 = [r13+220]
    r5 = 16
    [sp+32] = r5
    [sp+28] = r6
    r5 = 30
    [sp+24] = r5
    [sp+20] = r7
    r1 = r8  #
    [sp+16] = r1
    d[sp+8] = r3_r2
    r0 = 9808  #
    [sp+4] = r0
    r0 += r12
    [sp] = r11  ; @st.w.sp.l
    r2 = r9
    r3 = r10
    call link_and_print_print
    goto L0200bfaa
L0200c12e:
    r0 = [r13+92]
    ifs (r0 <= -1) goto L0200c392
    r1 = r4.l (u)
    call command_services_save_word
    if (r0 == -5) goto L0200c3a0
    if (r0 == 0) goto L0200c034
    call capture_command_status_text
    r1 = r0
    goto L0200c3a4
L0200c150:
    r10 = sp + 89
    r0 = sp + 244
    r11 = r0 + 16
    r15_r14 = 0
    goto L0200c26c
L0200c160:
    r1 = sp + 244
    r0 = r14
    call preset_preflight_preflight
    if (r0 != 0) goto L0200c268
    r0 = sp + 119
    r1 = sp + 107
    call preset_application_asset_layout
    r7 = r5 + 13
    r4 = 0
    r6 = 0
    goto L0200c1c0
L0200c17c:
    r1 = sp + 119
    r1 = b[r1+r4] (u)
    r2 = r12 + 11
    if (r1 != 2) {  ; @if.ne.ri.s12
    r2 = r12
    }
    r3 = r12 + 13
    if (r1 != 1) {  ; @if.ne.ri.s12
    r3 = r2
    }
    r2 = b[r7+-1] (u)
    r1 = b[r7++=18] (u)
    [sp+8] = r3
    [sp+4] = r1
    r1 = 113
    if (r2 != 0) goto L0200c1a6
    r1 = 112
L0200c1a6:
    r3 = r12 + 9  #
    [sp] = r1
    if (r4 != 0) goto L0200c1b0
    r3 = r12
L0200c1b0:
    r1 = 0x51 - r6
    r2 = r12 + 1307
    call L0200691e
    r6 += r0  ; @add.rr
    r4 += 1  ; @add.ri.u5
L0200c1c0:
    r0 = sp + 135
    r0 += r6  #  ; @add.rr.p
    r2 = b[r5+1] (u)
    ifs (r4 > 15) goto L0200c1d0
    ifs (r4 < r2) goto L0200c17c
L0200c1d0:
    r8 = 0  #
    r1 = b[r5+0] (u)
    b[r0+0] = r15
    [sp+100] = r15  ; @st.w.sp.l
    r9 = 0
    d[sp+92] = r9_r8
    if (r1 < 5) goto L0200c210
    r0 = h[r5+10] (u)
    if (r0 == 0) goto L0200c210
    r1 = sp + 89
    call command_services_colour_bytes
    r4 = b[r10+1] (u)
    r0 = b[r10+2] (u)
    r3 = b[sp+89] (u)
    r2 = r12 + 3197  #
    [sp+4] = r0
    r0 = sp + 92
    r1 = 12
    [sp] = r4
    call L0200691e
    r1 = b[r5+0] (u)
    r2 = b[r5+1] (u)
L0200c210:
    r0 = 1346
    r0 = b[r5+r0] (u)
    r3 = r12 + 914
    if (r0 != 0) goto L0200c220
    r3 = r12
L0200c220:
    if (r1 <= 3) {  ; @if.le.ri.s12
    r3 = r12
    }
    r0 = b[r5+2] (u)
    r4 = b[r5+3] (u)
    r7 = b[r5+7] (u)
    [sp+20] = r3
    r3 = sp + 92
    [sp+16] = r3
    if (r1 <= 1) {  ; @if.le.ri.s12
    r7 = 0
    }
    r3 = r12 + 15  #
    [sp+12] = r7
    r1 = sp + 135
    if (r6 != 0) goto L0200c246
    r1 = r3
L0200c246:
    [sp+8] = r1
    [sp+4] = r11  ; @st.w.sp.l
    r3 = -1
    r1 = -1
    if (r4 != 255) {  ; @if.ne.ri.s12
    r1 = r4
    }
    [sp] = r1
    if (r0 != 255) {  ; @if.ne.ri.s12
    r3 = r0
    }
    r0 = r12 + 5686
    r1 = r14
    call link_and_print_print
L0200c268:
    r14 = r14 + 1
L0200c26c:
    if (r14 != 32) goto L0200c160
    r1 = [r13+92]
    r0 = r12 + 3878
    goto L0200bb72
L0200c27a:
    r0 = r12 + 3856
    goto L0200bfa4
L0200c280:
    call preset_storage_preparation_invalidate
L0200c284:
    r0 = r12 + 1423
L0200c288:
    r1 = r4
    goto L0200bb72
L0200c28c:
    r0 = sp + 284
    r1 = 15
    call capture_command_slot_parse
    r5 = r0
    ifs (r5 < 0) goto L0200c368
    r6 = [r13+64]
    if (r6 == 0) goto L0200c368
    r0 = r6 + 40
    if (r0 > 8192) goto L0200c368
    r8 = [r13+60]
    r0 = r6
    call L0203c15c  ; @call.xl
    r10 = r0
    if (r0 == 0) goto L0200c4fa
    r1 = r8
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 1128745812
    r0 = r10  #
    [sp+244] = r0
    r1 = r6  #
    [sp+248] = r6
    call preset_storage_checksum
    r3 = r14 + 696
    r2 = [r3+4]
    r1 = [r3+8]
    r3 = [r3+0]
    r0 = r3  #
    [sp+252] = r0
    call capture_command_pack
    r1 = [sp+284]
    [sp+256] = r0
    r0 = r12 + 1094  #
    r2 = b[r1+0] (u)
    if (r2 != 0) goto L0200c300
    r1 = r0
L0200c300:
    r9 = sp + 244
    r0 = r9
    call record_helpers_copy_name
    r0 = r10 + r6
    r2 = r0 + -4
    if (r6 <= 3) {  ; @if.le.ri.s12
    r2 = r10
    }
    r1 = r6  #
    r0 = [sp+252]
    call preset_application_asset_identity
    r8 = r0
    r0 = 0xDF000
    r1 = r5
    ifs (r5 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 = r5 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r0 += r1  #  ; @add.rr.p
    [sp] = r6
    r2 = sp + 244
    r1 = 8192
    r3 = r10
    call capture_journal_rewrite
    r4 = r0
    r0 = r10
    call L0203d218  ; @call.xl
    if (r4 == 0) goto L0200c532
    r0 = r4
    call capture_command_status_text
    r1 = r0
    r0 = r12 + 2278
    goto L0200bb72
L0200c368:
    r0 = r12 + 1593
    goto L0200bfa4
L0200c36e:
    r0 = sp + 284
    r1 = 15
    call capture_command_slot_parse
    r4 = r0
    ifs (r4 < 0) goto L0200c4e8
    call capture_loader_load
    r3 = r0
    if (r3 != 0) goto L0200c4ea
    r2 = [r14+280]
    r0 = r12 + 3900
    goto L0200bf24
L0200c392:
    r0 = r12 + 7322
    goto L0200bfa4
L0200c398:
    r0 = r6
    call capture_command_command
    goto L0200bfa8
L0200c3a0:
    r1 = r12 + 6026
L0200c3a4:
    r0 = r12 + 2554
    goto L0200bb72  ; @goto.l
L0200c3ac:
    r14 = b[r4+0] (u)
    r10 = 15
    if (r14 != 67) {  ; @if.ne.ri.s12
    r10 = 8
    }
    r15 = sp + 244
    r9 = r15 + 16
    r8 = 0
    r7 = 0
    goto L0200c4b8
L0200c3ca:
    [sp+84] = r8  ; @st.w.sp.l
    if (r14 != 67) goto L0200c418
    r0 = 0xDF000
    r1 = r7
    ifs (r7 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 = r7 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r0 += r1  ; @add.rr
    r3 = sp + 244
    r2 = 8192
    r1 = 1128745812
    call preset_application_header
    if (r0 == 0) goto L0200c4b6
    [sp+56] = r8  ; @st.w.sp.l
    r1 = sp + 244
    r2 = sp + 56
    r0 = r7
    call preset_application_asset_resolve
    if (r0 == 0) goto L0200c440
    r5 = [r15+12]
    goto L0200c450
L0200c418:
    r1 = sp + 244
    r3 = sp + 84
    r2 = 8192
    r0 = r7
    call preset_application_asset_header
    if (r0 == 0) goto L0200c4b6
    r0 = [sp+84]
    r1 = 48
    if (r0 != 0) goto L0200c432
    r1 = 24
L0200c432:
    r2 = [r15+4]
    r0 = r12 + 4058  #
    [sp] = r1
    r1 = r7
    goto L0200c4b0
L0200c440:
    r0 = r7  #
    r2 = [sp+56]
    r1 = sp + 244
    r3 = 0
    call capture_metadata_lookup
    r5 = r0
L0200c450:
    [sp+52] = r8  ; @st.w.sp.l
    r1 = sp + 52
    r0 = r5
    call capture_loader_aux
    r6 = r0
    r0 = r5
    call capture_loader_gain_value
    r1 = r0 * 0x5
    r0 = sp + 72
    r2 = 0
    call link_and_print_tenths
    r5 = sp + 60
    r2 = 0
    r0 = r5  #
    r1 = [sp+52]
    call link_and_print_tenths
    r11 = [r15+4]
    if (r6 == 0) {  ; @if.eq.ri.s12
    r6 = r12
    r5 = r12
    } else {
    r6 = r12 + 415
    }
    r1 = sp + 244
    r0 = r7
    call capture_loader_signature
    r1 = r12 + 440
    if (r0 != 0) goto L0200c49e
    r1 = r12
L0200c49e:
    r0 = r12 + 5084  #
    [sp+12] = r1
    r2 = r11  #
    [sp+8] = r5
    [sp+4] = r6
    r1 = sp + 72
    r1 = r7  #
    [sp] = r1
L0200c4b0:
    r3 = r9
    call link_and_print_print
L0200c4b6:
    r7 += 1  ; @add.ri.u5
L0200c4b8:
    ifs (r7 < r10) goto L0200c3ca
    r1 = r13 + 10
    r0 = r13 + 9
    if (r14 != 67) {  ; @if.ne.ri.s12
    r0 = r1
    }
    r0 = b[r0+0] (u)
    r2 = -1
    if (r0 != 255) {  ; @if.ne.ri.s12
    r2 = r0
    }
    r0 = r12 + 4702
    r1 = r4
    r3 = r10
    goto L0200bc8c
L0200c4e0:
    r0 = r6
    call calibration_commands_calibration_command
    goto L0200bfa8
L0200c4e8:
    r3 = -1
L0200c4ea:
    r0 = r3
    call capture_command_status_text
    r1 = r0
    r0 = r12 + 3402
    r2 = r3
    goto L0200bf26
L0200c4fa:
    r0 = r12 + 4303
    goto L0200bfa4
L0200c500:
    r7 = b[r4+0] (u)
    r1 = 15
    if (r7 != 67) {  ; @if.ne.ri.s12
    r1 = 8
    }
    r0 = sp + 284
    call capture_command_slot_parse
    r5 = r0
    r0 = 1
    if (r7 == 67) {  ; @if.eq.ri.s12
    r0 = 0
    }
    ifs (r5 < 0) goto L0200c568
    if (r0 == 0) goto L0200c568
    r1 = 0
    r0 = r5
    call link_and_print_ir_select
    if (r0 == 0) goto L0200c56c
L0200c52c:
    r0 = r12 + 7599
    goto L0200c288
L0200c532:
    b[r13+9] = r5
    r0 = 255
    b[r13+18] = r0
    r0 = [r9+4]
    r4 = 1
    r1 = r14 + 1780
    r3 = r6  #
    b[r1+0] = r4
    [r1+4] = r8
    [r1+8] = r0
    r0 = 0
    [r1+12] = r0
    r0 = r12 + 4204  #
    b[r1+1] = r0
    r1 = sp + 244
    r2 = r1 + 16
    r1 = r5
    call link_and_print_print
    goto L0200bfaa
L0200c568:
    ifs (r5 < 0) goto L0200c5ce
L0200c56c:
    r0 = 0xEF000
    r1 = r5
    if (r7 != 67) goto L0200c586
    r0 = 0xDF000
    ifs (r5 >= 8) {  ; @ifs.ge.ri.s12
    r1 = r5 + -8
    r0 = 0xCF000
    }
L0200c586:
    r1 = r1 << 13
    r6 = r0 + r1
    if (r6 < 782336) goto L0200c5c4
    r0 = r6 + 4096
    if (r0 > 1044480) goto L0200c5c4
    call storage_coordination_wait_ready
    r1 = 1
    r0 = r6
    call capture_journal_erase
    r0 = 19
    r2 = 0
    r1 = r6
    call storage_coordination_notify
    if (r7 != 67) goto L0200c65e
    r0 = b[r13+9] (u)
    if (r0 == r5) {
    r0 = 255
    b[r13+9] = r0
    }
    goto L0200c66c
L0200c5c4:
    r0 = 19
    r2 = -1
    r1 = r6
    call storage_coordination_notify
L0200c5ce:
    r0 = r12 + 1102
    goto L0200c288
L0200c5d4:
    r0 = sp + 284
    r1 = 8
    call capture_command_slot_parse
    r11 = r0
    call ir_reload_and_leaves_ir_reload
    r0 = sp + 48
    r1 = sp + 44
    call ir_installation_query
    r5 = r0
    ifs (r11 < 0) goto L0200c610
    if (r5 == 0) goto L0200c610
    r9 = 4096
    if (r11 != 7) {  ; @if.ne.ri.s12
    r9 = 8192
    }
    r8 = [sp+48]  ; @ld.w.sp.l
    r6 = r8 << 1
    r0 = r6 + 40
    if (r0 <= r9) goto L0200c696
L0200c610:
    r0 = 9119
    r0 += r12
    goto L0200bfa4
L0200c618:
    r0 = -1
    r1 = r12 + 815  #
    [sp+40] = r0
    r0 = -2
    r0 = r6  #
    [sp+36] = r0
    r2 = sp + 40
    r3 = sp + 36
    call L0200b7c2
    if (r0 != 2) goto L0200c690
    r0 = [sp+40]
    call preset_application_effect_type  ; @call.xl
    if (r0 != 7) goto L0200c690
    r1 = [sp+36]
    r0 = r1 + 1
    if (r0 >= 9) goto L0200c690
    r0 = [sp+40]
    call slot_commands_choose_slot_ir
    r3 = r0
    if (r3 == 0) goto L0200c718
    call capture_command_status_text
    r1 = r0
    r0 = r12 + 3215
    r2 = r3
    goto L0200bf26
L0200c65e:
    r0 = b[r13+10] (u)
    if (r0 == r5) {
    r0 = 255
    b[r13+10] = r0
    }
L0200c66c:
    r1 = r13 + 19
    r0 = r13 + 18
    if (r7 != 67) {  ; @if.ne.ri.s12
    r0 = r1
    }
    r2 = r5.b0 (u)  #
    r1 = b[r0+0] (u)
    if (r1 == r2) {
    r1 = 255
    b[r0+0] = r1
    }
    r0 = r12 + 1433
    r1 = r4
    r2 = r5
    goto L0200bf26
L0200c690:
    r0 = r12 + 2724
    goto L0200bfa4
L0200c696:
    r0 = [r14+168]
    if (r0 == 0) {  ; @if.eq.ri.s12
    r0 = 1229409108
    } else {
    r0 = 1246186324
    }
    r0 = r5  #
    [sp+244] = r0
    r1 = r6  #
    [sp+248] = r6
    call preset_storage_checksum
    r2 = [sp+44]
    r1 = [sp+284]
    r0 = r12 + 35  #
    [sp+252] = r0
    [sp+256] = r2
    r2 = b[r1+0] (u)
    if (r2 != 0) goto L0200c6cc
    r1 = r0
L0200c6cc:
    r10 = sp + 244
    r0 = r10
    call record_helpers_copy_name
    r0 = r11  #
    r1 = [sp+252]
    call link_and_print_ir_select
    if (r0 != 0) goto L0200c52c
    r0 = r11 << 13  #
    [sp] = r6
    r0 = r0 + 0xEF000
    r2 = sp + 244
    r1 = r9
    r3 = r5
    call capture_journal_rewrite
    if (r0 == 0) goto L0200c722
    call capture_command_status_text
    r1 = r0
    r0 = r12 + 2292
    goto L0200bb72
L0200c708:
    r0 = -1
L0200c70a:
    call capture_command_status_text
    r1 = r0
    r0 = r12 + 2306
    goto L0200bb72
L0200c718:
    r0 = r12 + 2584  #
    r2 = [sp+36]
    r1 = [sp+40]
    goto L0200bf26
L0200c722:
    r2 = [r10+8]
    b[r13+10] = r11
    [r14+744] = r2
    r0 = 255
    b[r13+19] = r0
    r3 = [r10+12]
    r4 = [r10+4]
    r0 = r14 + 1796  #
    r5 = [sp+244]
    r1 = 1
    b[r0+0] = r1
    [r0+4] = r2
    [r0+8] = r4
    r2 = 1246186324
    [r0+12] = r3
    if (r5 != r2) {
    r1 = 0
    }
    b[r0+1] = r1
    call ir_installation_refresh
    r0 = [r14+168]
    r1 = 48
    if (r0 != 0) goto L0200c768
    r1 = 24
L0200c768:
    r0 = r12 + 5722  #
    [sp] = r1
    r2 = sp + 244
    r2 += 16  ; @add.ri.u5
    r1 = r11
    goto L0200bc8a
