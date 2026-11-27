; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; scene_application: 3 functions, 0x02009e14..0x0200a256

; scene_application_inner: 0x02009e14..0x0200a1d6, module scene-application (inner)
; HyperRig MINI, product option: the records of eight scenes.
.type scene_application_inner,@function
scene_application_inner:
    [--sp] = {rets, r15-r4}
    sp += -72
    r15 = L01c26890
    r1 = [r15+280]
    r6 = r0  #
    [sp+32] = r1
    r1 = L01c1f7e0
    r1 = b[r1+0] (u)
    [sp+12] = r1
    r1 = L01c1f180
    r5 = b[r1+8] (u)
    r4 = 0
    goto L02009e5e
L02009e3c:
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    r1 = r0
    r0 = 0
    if (r1 == 7) {  ; @if.eq.ri.s12
    r1 = 2
    r0 = r4
    call preset_application_parameter  ; @call.xl
    }
    r1 = sp + 40
    h[r1+r4<<1] = r0
    r4 += 1  ; @add.ri.u5
L02009e5e:
    if (r4 != 16) goto L02009e3c
    r0 = L01c34489
    r1 = 1
    b[r0+0] = r1
    if ((r5 & 0xFF) == 0) {
    r0 = 1
    [sp+12] = r0
    }
    r12 = r6 * 0x104  #
    [sp] = r6
.if MINI_PRODUCT
    r1 = hyperrig_scene_base  ; @li.u32
    r12 = r12 + r1
    r1 = L01c26890
    r12 = r12 - r1
.endif
    r1 = r12 + r15
    r0 = 11936  #
    [sp+4] = r1
    r0 += r1  ; @add.rr
    r13 = 0  #
    [sp+28] = r0
    r4 = 0
    r9 = 0
    r0 = 0
    r11 = 11958  #
    [sp+8] = r0
    r10 = 0  #
    [sp+20] = r0
    [sp+24] = r0
    goto L02009ff8
L02009e9e:
    r0 = [sp+28]
    r0 = b[r0+1] (u)
    call preset_band_controls_request_reserve
    [sp+8] = r0
L02009ea8:
    [sp+36] = r4
    r0 = 1
    [sp+16] = r0
    if (r9 == 0) {  ; @if.eq.ri.s12
    [sp+16] = r9  ; @st.w.sp.l
    }
    r4 = 0
    goto L02009fee
L02009eba:
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    r7 = r0
    if (r7 == 0) goto L02009fe2
    r0 = [sp+28]
    r1 = 1
    r14 = r1 << r4  #
    r0 = h[r0+2] (u)
    if ((r0 & r14) == 0) goto L02009fe2
    r5 = 1
    if ((r14 & r13) != 0) {
    r5 = 0
    }
    call storage_control_poll
    r0 = [sp+16]
    if ((r5 & r0) != 0) goto L02009f90
    r5 = 0
    goto L02009f8c
L02009eec:
    r0 = r7
    r1 = r5
    call preset_application_parameter_order
    r6 = r0
    r0 = r7
    r1 = r6
    call preset_application_metadata  ; @call.xl
    if (r0 == 0) goto L02009f8a
    r0 = r4
    r1 = r6
    call preset_application_parameter  ; @call.xl
    r1 = r4 * 0xE
    r1 += r12
    r2 = r6 << 1
    r1 += r2  ; @add.rr
    r8 = r1 + r15
    r2 = h[++r8=r11] (s)
    if (r0 == r2) goto L02009f8a
    r0 = r4
    r1 = r6
    call effect_parameter_lifecycle_parameter_probe  ; @call.xl
    if (r0 == 0) goto L02009f46
    if (r9 == 0) goto L02009f86
    r0 = [sp+36]
    if ((r0 & r14) != 0) goto L02009f8a
    r0 = r0 | r14
    [sp+36] = r0
    r0 = [sp+24]
    r0 += 1  ; @add.ri.u5
    [sp+24] = r0
    goto L02009f8a
L02009f46:
    r0 = [sp+32]
    if (r0 != 2) goto L02009f60
    r2 = h[r8+0] (s)
    r0 = r4  #
    r3 = [sp+12]
    r1 = r6
    call effect_parameter_lifecycle_parameter_fast_wrapper  ; @call.xl
    if (r0 != -6) goto L02009f8a
L02009f60:
    if (r7 == 7) goto L02009f6e
    if (r7 != 5) goto L02009f72
    r0 = -5
    if ((r6 & r0) != 0) goto L02009f72
L02009f6e:
    r10 = 1
L02009f72:
    r0 = 1
    [sp+20] = r0
    if (r6 != 6) {  ; @if.ne.ri.s12
    r0 = r10
    }
    if (r7 != 37) {  ; @if.ne.ri.s12
    r0 = r10
    }
    r10 = r0
    goto L02009f8a
L02009f86:
    r13 = r13 | r14
L02009f8a:
    r5 += 1  ; @add.ri.u5
L02009f8c:
    if (r5 != 7) goto L02009eec
L02009f90:
    r5 = 1
    r6 = 1
    if (r9 != 0) {  ; @if.ne.ri.s12
    r6 = 0
    }
    r0 = r12 + r4
    r7 = r0 + r15
    r0 = r4
    call preset_application_effect_enabled  ; @call.xl
    r1 = 11942
    r1 = b[r7+r1] (u)
    if (r1 == 0) goto L02009fb6
    r5 = 0
L02009fb6:
    if (r0 == r1) goto L02009fe2
    r0 = r6 ^ r5
    if (r0 != 0) goto L02009fe2
    r0 = [sp+32]
    if (r0 != 2) goto L02009fd4
    r0 = r4
    call effect_enable_fast  ; @call.xl
    if (r0 == 0) goto L02009fe2
    if (r0 != -6) goto L02009fe6
L02009fd4:
    r0 = 1
    [sp+20] = r0
    r1 = [sp+32]
    if (r1 != 2) {  ; @if.ne.ri.s12
    r0 = r10
    }
    r10 = r0
L02009fe2:
    r4 += 1  ; @add.ri.u5
    goto L02009fee
L02009fe6:
    r0 = [sp+24]
    r0 += 1  ; @add.ri.u5
    [sp+24] = r0
    goto L02009fe2
L02009fee:
    if (r4 != 16) goto L02009eba
    r9 = r9 + 1  #
    r4 = [sp+36]
L02009ff8:
    if (r9 == 1) goto L02009e9e
    if (r9 != 2) goto L02009ea8
    r9 = r4  #
    r6 = [sp+4]
    r0 = 11962
    r5 = r6 + r0
    r4 = 0
    goto L0200a038
L0200a00e:
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    if (r0 != 7) goto L0200a034
    r0 = [sp+28]
    r0 = h[r0+2] (u)
    r0 = r0 & (1 << r4)
    if (r0 == 0) goto L0200a034
    r0 = sp + 40
    r0 = h[r0+r4<<1] (u)
    r1 = h[r5+0] (u)
    if (r1 != r0) {
    r10 = 1
    }
L0200a034:
    r5 += 14  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L0200a038:
    if (r4 != 16) goto L0200a00e
    r5 = 1
    r7 = 1
    r0 = [sp+32]
    if (r0 != 2) {  ; @if.ne.ri.s12
    r7 = 0
    }
    if (r10 == 0) {  ; @if.eq.ri.s12
    r5 = r10
    }
    if ((r7 & r5) != 0) {
    r0 = 1
    r1 = 0
    call storage_coordination_gate_core
    }
    r0 = [sp+20]
    if (r0 == 0) goto L0200a138
    [sp+32] = r7
    [sp+36] = r5
    call audio_pause_pause_audio
    r8 = 0
    r10 = 1
    r13 = 11942
    r14 = r11
    goto L0200a12a
L0200a074:
    r0 = r8
    call preset_application_effect_type  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L0200a126
    r11 = r10 << r8  #
    r0 = [sp+28]
    r0 = h[r0+2] (u)
    if ((r0 & r11) == 0) goto L0200a126
    call storage_control_poll
    r7 = 0
    goto L0200a0f6
L0200a094:
    r0 = r5
    r1 = r7
    call preset_application_parameter_order
    r6 = r0
    r0 = r5
    r1 = r6
    call preset_application_metadata  ; @call.xl
    if (r0 == 0) goto L0200a0f4
    r0 = r8
    r1 = r6
    call preset_application_parameter  ; @call.xl
    r1 = r8 * 0xE
    r1 += r12
    r2 = r6 << 1
    r1 += r2  ; @add.rr
    r4 = r1 + r15
    r2 = h[++r4=r14] (s)
    if (r0 == r2) goto L0200a0f4
    r0 = r8
    r1 = r6
    call effect_parameter_lifecycle_parameter_probe  ; @call.xl
    if (r0 == 0) goto L0200a0e6
    if ((r9 & r11) != 0) goto L0200a0f4
    r9 = r9 | r11  #
    r0 = [sp+24]
    r0 += 1  ; @add.ri.u5
    [sp+24] = r0
    goto L0200a0f4
L0200a0e6:
    r2 = h[r4+0] (s)
    r0 = r8
    r1 = r6
    call effect_parameter_lifecycle_parameter_commit  ; @call.xl
L0200a0f4:
    r7 += 1  ; @add.ri.u5
L0200a0f6:
    if (r7 != 7) goto L0200a094
    r0 = r12 + r8
    r4 = r0 + r15
    r0 = r8
    call preset_application_effect_enabled  ; @call.xl
    r1 = b[r4+r13] (u)
    if (r0 == r1) goto L0200a126
    r0 = r8
    call effect_enable_commit  ; @call.xl
    r1 = 1
    if (r0 != 0) goto L0200a120
    r1 = r0
L0200a120:
    r0 = [sp+24]
    r0 += r1  ; @add.rr
    [sp+24] = r0
L0200a126:
    r8 = r8 + 1
L0200a12a:
    if (r8 != 16) goto L0200a074
    call audio_pause_resume_audio
    r6 = [sp+4]
    r5 = [sp+36]
    r7 = [sp+32]
L0200a138:
    r4 = 0
    r0 = L01c34489
    r5 &= r7  #
    b[r0+0] = r4
    r8 = [sp]  ; @ld.w.sp.l
    r7 = [sp+24]
    goto L0200a17c
L0200a14c:
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    if (r0 != 7) goto L0200a17a
    r1 = 2
    r0 = r4
    call preset_application_parameter  ; @call.xl
    r1 = sp + 40
    r1 = h[r1+r4<<1] (s)
    if (r0 == r1) goto L0200a17a
    r0 = r4
    call slot_ir_load_load_slot_ir
    r1 = 1
    if (r0 != 0) goto L0200a178
    r1 = r0
L0200a178:
    r7 += r1  ; @add.rr
L0200a17a:
    r4 += 1  ; @add.ri.u5
L0200a17c:
    if (r4 != 16) goto L0200a14c
    if (r5 == 0) goto L0200a188
    r1_r0 = 0
    call storage_coordination_gate_core
L0200a188:
    r0 = 11941
    r1 = b[r6+r0] (s)
    r0 += -1
    r0 = b[r6+r0] (s)
    call preset_application_services_set_levels
    r0 = 12194
    r0 = b[r6+r0] (u)
    if (r0 == 0) goto L0200a1b2
    r0 = 12182  #
    r1 = [sp+12]
    r0 += r6  ; @add.rr
    call dsp_transition_request  ; @call.xl
L0200a1b2:
    r0 = [sp+8]
    if (r0 == 0) goto L0200a1c6
    r0 = [sp+28]
    r0 = b[r0+1] (u)
    call preset_band_controls_request_reserve
    r1 = 1
    if (r0 != 0) goto L0200a1c4
    r1 = r0
L0200a1c4:
    r7 += r1  ; @add.rr
L0200a1c6:
    r0 = L01c1f180
    [r0+88] = r8
    r0 = r7
    sp += 72
    {pc, r15-r4} = [sp++]

; scene_application_apply: 0x0200a1d6..0x0200a228, module scene-application (apply)
; HyperRig MINI, product option: a scene knows every block (mini/product/scenes.c).
.type scene_application_apply,@function
scene_application_apply:
    [--sp] = {rets, r5, r4}
    r5 = r0
.if MINI_PRODUCT
    call hyperrig_scene_fill  ; @call.xl
    r0 = r5
    call hyperrig_scene_capture  ; @call.xl
    r0 = r5
.endif
    call scene_application_inner
    r4 = r0
    call stereo_budget_update_suspension  ; @call.xl
    if (r0 == 1) goto L0200a1f8
    if (r0 != 2) goto L0200a224
    r0 = 4
    r1 = 0
    call preset_application_notify
    goto L0200a224
L0200a1f8:
    r0 = L01c341a8
    r1 = [r0+0]
    r0 = 3
    call preset_application_notify
    r0 = r5
    call scene_application_inner
    r5 = r0
    if (r4 == 0) goto L0200a222
    ifs (r5 < r4) goto L0200a222
    call stereo_budget_end_suspension  ; @call.xl
    r0 = 5
    r1 = r5
    call preset_application_notify
L0200a222:
    r4 = r5
L0200a224:
    r0 = r4
    {pc, r5, r4} = [sp++]

; scene_application_report: 0x0200a228..0x0200a256, module scene-application (report)
.type scene_application_report,@function
scene_application_report:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    call storage_platform_clock  ; @call.xl
    r2 = r0 - r4
    call preset_application_rate
    r1 = 10
    r0 = r0 / r1 (u)
    r0 = r2 / r0 (u)
    r1 = 8388607
    r1 = umin(r0, r1)
    r0 = r5.b0 (u)
    r0 <= insert(r1, p:8, l:24)
    {pc, r5, r4} = [sp++]
