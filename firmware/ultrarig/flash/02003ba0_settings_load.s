; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; settings_load: 1 function, 0x02003ba0..0x02004084

; settings_load_settings_load: 0x02003ba0..0x02004084, module settings-load (settings_load)
.type settings_load_settings_load,@function
settings_load_settings_load:
    [--sp] = {rets, r14-r4}
    sp += -248
    call preset_storage_preparation_prepare
    r0 = sp + 160
    r1 = 0
    rep 22 {
    [r0++=4] = r1
    }
    call mode_and_settings_record_scan
    r9 = L01c1f180
    r0 = [r9+212]
    r1 = 776
    r8 = L01c26890
    r2 = 1
    b[r8+r1] = r2
    ifs (r0 < 0) goto L02003be6
    r0 = r0 << 7
    r0 = r0 + 0xFE000
    r1 = sp + 32
    r2 = 128
    call storage_control_read
    if (r0 == 0) goto L02003d1a
L02003be6:
    r1_r0 = 0
    call mode_and_settings_block_import
    r4 = sp + 0
    r0 = r4
    call mode_and_settings_block_export
    r1 = 32
    r0 = r4
    call capture_metadata_crc
    r4 = r0
L02003bfe:
    [r8+780] = r4
    r11 = -1
    r10 = 0
    r14 = L01c24790
    r12 = 1111968596
    r13 = 0
L02003c16:
    r6 = r13 << 7
    r4 = r13
    goto L02003c24
L02003c1e:
    r6 = r6 + 128
    r4 += 1  ; @add.ri.u5
L02003c24:
    if (r4 > 29) goto L02003c9e
    r2 = 4
    r0 = r6
    r1 = r14
    call mode_and_settings_record_read
    if (r0 != 0) goto L02003cb6
    r0 = [r14+0]
    if (r0 != r12) goto L02003c1e
    r2 = 40
    r0 = r6
    r1 = r14
    call mode_and_settings_record_read
    if (r0 != 0) goto L02003cb6
    r5 = [r14+4]
    if (r5 > 472) goto L02003c1e
    r0 = r5 + 167
    r0 = r0 >> 7
    if (r0 == 0) goto L02003c1e
    r13 = r4 + r0
    if (r13 > 30) goto L02003c1e
    r7 = r0 << 7
    r0 = r6
    r1 = r14
    r2 = r7
    call mode_and_settings_record_read
    if (r0 != 0) goto L02003cb6
    r0 = [r14+0]
    if (r0 != r12) goto L02003c1e
    r1 = [r14+4]
    if (r1 > 472) goto L02003c1e
    r0 = r1 + 40
    if (r0 > r7) goto L02003c1e
    r7 = [r14+8]
    r0 = r14 + 40
    call capture_metadata_crc
    if (r0 != r7) goto L02003c1e
    r10 = r5 + 40
    r11 = r4
    goto L02003c16
L02003c9e:
    ifs (r11 < 0) goto L02003cb6
    r0 = r11 << 7
    r1 = r10 + 127
    r2 = r1 & 0xFFFFFF80
    r1 = r14
    call mode_and_settings_record_read
    if (r0 == 0) goto L02003cb8
L02003cb6:
    r10 = 0
L02003cb8:
    r0 = 1228
    r0 = b[r8+r0] (u)
    if (r0 != 0) goto L02003da8
    call mode_and_settings_slots_clear
    r0 = 310
    r1 = 0
    [r8+r0<<2] = r1
    if (r10 < 352) goto L02003d9c
    r0 = r10 + -1
    if (r0 > 419) goto L02003d9c
    r0 = [r14+0]
    if (r0 != r12) goto L02003d9c
    r4 = [r14+12]
    r1 = [r14+4]
    r5 = [r14+8]
    r6 = r14 + 40
    r0 = r6
    call audio_pause_crc32
    r2 = r1 + 40
    if (r2 > r10) goto L02003d9c
    if (r0 != r5) goto L02003d9c
    if (r1 != 380) goto L02003d66
    if (r4 != 1282) goto L02003d66
    r0 = r8 + 6592
    r2 = 380
    goto L02003d7c
L02003d1a:
    r0 = sp + 32
    call mode_and_settings_page_check
    if (r0 == 0) goto L02003be6
    r0 = b[sp+39] (u)
    r2 = b[sp+38] (u)
    r3 = b[sp+37] (u)
    r1 = b[sp+36] (u)
    r5 = b[sp+41] (u)
    r4 = b[sp+40] (u)
    r6 = b[sp+43] (u)
    r7 = b[sp+42] (u)
    r2 <= insert(r0, p:8, l:8)
    r1 <= insert(r3, p:8, l:8)
    r1 <= insert(r2, p:16, l:16)
    r0 = sp + 32
    r0 += 40
    call mode_and_settings_block_import
; HyperRig MINI, product option: what is behind the lights in the same record (mini/product/midi.c).
.if MINI_PRODUCT
    r0 = sp + 32
    call hyperrig_settings_import  ; @call.xl
.endif
    r7 <= insert(r6, p:8, l:8)
    r4 <= insert(r5, p:8, l:8)
    r4 <= insert(r7, p:16, l:16)
    goto L02003bfe
L02003d66:
    if (r1 != 312) goto L02003d9c
    if (r4 != 1281) goto L02003d9c
    call mode_and_settings_slots_clear
    r0 = r8 + 6592
    r2 = 312
L02003d7c:
    r1 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = L01c25438
    r1 = r14
    r2 = r10
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 310
    [r8+r0<<2] = r10
L02003d9c:
    r0 = r8 + 1228
    r1 = [r0+8]
    [r0+16] = r1
    r1 = 1
    b[r0+0] = r1
L02003da8:
    r0 = [r9+204]
    ifs (r0 < 0) goto L0200406e
    r0 = r0 << 7
    r0 = r0 + 0xFE000
    r1 = sp + 32
    r2 = 128
    call storage_control_read
    if (r0 != 0) goto L0200406e
    r0 = b[sp+39] (u)
    r1 = b[sp+38] (u)
    r3 = b[sp+37] (u)
    r2 = b[sp+36] (u)
    r1 <= insert(r0, p:8, l:8)
    r2 <= insert(r3, p:8, l:8)
    r2 <= insert(r1, p:16, l:16)
    if (r2 < 20) goto L0200406e
    if (r2 >= 88) {  ; @if.ge.ri.s12
    r2 = 88
    }
    r0 = sp + 32
    r1 = r0 + 40
    r0 = sp + 160
    call effect_parameter_support_memmove  ; @call.xl
    r0 = [sp+180]
    r1 = b[sp+173] (u)
    r2 = b[sp+163] (u)
    r3 = b[sp+174] (u)
    [r8+784] = r0
    r2 <= insert(r1, p:8, l:24)
    h[r8+80] = r2
    r1 = 0
    if (r3 != 1) goto L02003e62
    r0 = b[sp+243] (u)
    r2 = r0 + -1
    r2 = r2.b0 (u)
    if (r2 > 14) goto L02003e62
    r1 = h[sp+234] (u)
    r2 = b[sp+237] (u)
    r3 = h[sp+178] (u)
    r4 = h[sp+230] (u)
    r5 = b[sp+175] (u)
    r6 = r8 + 1692
    h[r6+0] = r3
    h[r6+2] = r4
    b[r6+4] = r5
    r1 = r1.l (u)  #
    b[r6+5] = r1
    r3 = uextra(r1, p:8, l:4)
    b[r6+6] = r3
    r1 = r1 >> 12
    b[r6+7] = r1
    r1 = 0
    b[r6+8] = r1
    b[r6+9] = r0
    b[r6+10] = r2
    r1 = 1
L02003e62:
    r0 = b[sp+221] (u)
    b[r8+39] = r1
    if (r0 != 1) goto L02003e8a
    r0 = b[sp+222] (u)
    if (r0 >= 32) {  ; @if.ge.ri.s12
    r0 = -1
    }
    r1 = b[sp+223] (u)
    [r9+100] = r0
    if (r1 >= 4) {  ; @if.ge.ri.s12
    r1 = -1
    }
    [r9+104] = r1
L02003e8a:
    call audio_pause_pause_audio
    r0 = sp + 160
    r5 = r0 + 4
    r4 = 0
    goto L02003ea6
L02003e98:
    r1 = b[r5+r4] (s)
    r0 = r4
    call biquad_coefficients_stage  ; @call.xl
    r4 += 1  ; @add.ri.u5
L02003ea6:
    if (r4 != 5) goto L02003e98
    r0 = b[sp+161] (u)
    call slot_queries_set_flag  ; @call.xl
    call audio_pause_resume_audio
    r0 = b[sp+240] (u)
    if (r0 != 1) goto L02003ee4
    r0 = b[sp+242] (u)
    r1 = r0 + -1
    r1 = r1.b0 (u)
    if (r1 > 63) goto L02003ee4
    r1 = b[sp+241] (u)
    r2 = L01c1f7e0
    b[r2+0] = r0
    r0 = 1
    if (r1 != 0) goto L02003ee0
    r0 = r1
L02003ee0:
    b[r9+8] = r0
L02003ee4:
    r0 = b[sp+236] (u)
    if (r0 != 1) goto L02003efe
    r0 = h[sp+238] (s)
    r1 = r0 + 100
    r1 = r1.l (u)
    if (r1 <= 400) {  ; @if.le.ri.s12
    [r9+96] = r0
    }
L02003efe:
    r0 = b[sp+232] (u)
    if (r0 == 1) {  ; @if.eq.ri.s12
    r0 = b[sp+233] (u)
    call butterworth_table_butterworth_table
    }
    r0 = b[sp+224] (u)
    if (r0 == 1) {  ; @if.eq.ri.s12
    r2 = h[sp+228] (u)
    r1 = h[sp+226] (s)
    r0 = b[sp+225] (u)
    call dsp_dynamics_configure  ; @call.xl
    }
    r0 = sp + 160
    r0 += 9  ; @add.ri.u5
    r1 = 0
    goto L02003f44
L02003f32:
; HyperRig MINI v4, patch mini_panel_restore_fixed_map: Configuration restore uses its index as mapping value; a persisted G permutation cannot replace MINI wiring.
.if TARGET_MINI
    r2 = r1  ; @mov.rr
    nop  ; @nop
.else
    r2 = b[r0+r1] (u)
.endif
    if (r2 <= 4) {  ; @if.le.ri.s12
    r3 = r1 + r9
    b[r3+116] = r2
    }
    r1 += 1  ; @add.ri.u5
L02003f44:
    if (r1 != 4) goto L02003f32
    r0 = b[sp+220] (u)
    r0 += -1
    r0 = r0.b0 (u)
    r10 = sp + 160
    if (r0 > 1) goto L02003fc8
    r0 = -36
    goto L02003f8c
L02003f5e:
    r1 = sp + 160
    r1 += r0  ; @add.rr
    r2 = b[r1+60] (u)
    if (r2 != 8) goto L02003f8a
    r2 = b[++r1=62] (u)
    if (r2 == 255) goto L02003f8a
    r3 = sp + 160
    r3 += r0  ; @add.rr
    r5 = b[++r3=61] (s)
    ifs (r5 <= -1) {  ; @ifs.le.ri.s12
    b[r3+0] = r2
    r2 = r5 & 0x7F
    b[r1+0] = r2
    }
L02003f8a:
    r0 += 3  ; @add.ri.u5
L02003f8c:
    if (r0 != 0) goto L02003f5e
    r11 = r9 + 238
    r1 = sp + 160
    r1 += 24  ; @add.ri.u5
    r2 = 0
    goto L02003fc4
L02003f9c:
    r3 = 3
    r5 = r1
    r6 = r11
    goto L02003fba
L02003fa4:
    r7 = b[r5+0] (u)
    if (r7 > 10) goto L02003fb4
    r4 = b[r5+1] (u)
    r0 = b[r5+2] (u)
    b[r6+-2] = r7
    b[r6+-1] = r4
    b[r6+0] = r0
L02003fb4:
    r3 += -1
    r5 += 3  ; @add.ri.u5
    r6 += 3  ; @add.ri.u5
L02003fba:
    if (r3 != 0) goto L02003fa4
    r1 += 9  ; @add.ri.u5
    r11 = r11 + 9
    r2 += 1  ; @add.ri.u5
L02003fc4:
    if (r2 != 4) goto L02003f9c
L02003fc8:
    r0 = b[sp+244] (u)
    r1 = sp + 160
    r5 = r1 + 84
    if (r0 != 1) goto L0200400c
    r0 = b[sp+245] (u)
    call audio_pause_set_auxiliary
    r0 = b[sp+246] (u)
    r0 = r0 & 0xFFFFFF0F  #
    r2 = b[r5+0] (u)
    b[r9+11] = r0
    r1 = sp + 160
    if (r2 != 1) goto L0200400c
    r0 = b[sp+247] (u)
    r0 += -1
    r2 = r0.b0 (u)
    if (r2 > 2) goto L0200400c
    r2 = r1 + 86
    call audio_pause_set_selector
    goto L02004038
L0200400c:
    r0 = b[r10+60] (u)
    if (r0 == 0) goto L0200402a
    r0 = r9 + 236
    r1 = L02034fa8
    r2 = 36
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0200402c
    r0 = 2
    goto L0200402c
L0200402a:
    r0 = 0
L0200402c:
    call audio_pause_set_selector
    r0 = sp + 160
    r2 = r0 + 86
L02004038:
    r0 = h[sp+176] (s)
    r1 = r0 + -415
    if (r1 <= 51) {  ; @if.le.ri.s12
    r0 = itof(r0)
    [r9+144] = r0
    }
    r0 = b[r5+0] (u)
    if (r0 != 1) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r1 = b[r2+0] (s)
    r1 = r1 >> 31
    r0 &= r1
    b[r8+40] = r0
    if (r0 == 1) {  ; @if.eq.ri.s12
    r0 = 1536
    r1 = 1
    b[r8+r0] = r1
    }
L0200406e:
    r0 = r8 + 3988
    call mode_and_settings_device_record
    r0 = 736
    r1 = 1
    b[r8+r0] = r1
    sp += 248
    {pc, r14-r4} = [sp++]
