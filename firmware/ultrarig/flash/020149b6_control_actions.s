; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; control_actions: 2 functions, 0x020149b6..0x02014c04

; control_actions_action: 0x020149b6..0x02014b3c, module control-actions (action)
; HyperRig MINI, product option: eight scenes.
.type control_actions_action,@function
control_actions_action:
    [--sp] = {rets, r9-r4}
    r6 = r1
    r5 = r0
    r0 = r6 * 0x3
    r1 = r5 * 0x9
    r0 += r1  ; @add.rr
    r1 = L01c1f180
    r8 = r0 + r1
    r4 = r8
    r0 = b[++r4=236] (u)
    r0 = r0 << 8
    r0 |= r6  #
    r1 = b[r4+1] (u)
    r1 = r1 << 16
    r2 = r0 | r1
    r0 = 9
    r1 = r5
    call storage_coordination_notify
    r7 = L01c26890
    r1 = r7 + 1828
    call control_actions_clock
    r1 = [r1+r5<<2]
    [r7+968] = r1
    r1 = r7 + 1844
    r2 = [r1+r5<<2]
    r1 = b[r4+0] (u)
    [r7+972] = r2
    if (r1 == 7) {  ; @if.eq.ri.s12
    [r7+928] = r2
    }
    r2 = r7 + 1812
    [r2+r5<<2] = r0
    r3 = r5 + r7
    r9 = 924
    r2 = 1
    b[r3+r9] = r2
    [r7+812] = r0
    if (r6 != 1) goto L02014a5c
    if (r1 == 7) {  ; @if.eq.ri.s12
    r2 = 0
    }
    r3 = r7 + 1608
    r3 = h[r3+r5<<1] (u)
    if (r3 == 0) goto L02014a5c
    if (r2 != 0) goto L02014a5c
    r1 = r5 + 1
    r2 = L01c26864
    r0 = r0 + 2500  #
    b[r2+0] = r1
    r1 = 377
    [r7+r1<<2] = r0
    {pc, r9-r4} = [sp++]
L02014a5c:
    r0 = [r7+956]
    if (r0 == 0) goto L02014a72
    r0 = r1 + -5
    r0 = r0.b0 (u)
    if (r0 < 2) goto L02014a72
    call scene_application_flush
    r1 = b[r4+0] (u)
L02014a72:
    r0 = r1 + -1
    if (r0 > 9) goto L02014b3a
    tbb [r0]
action_jump_table:
    .byte (L02014a86 - action_jump_table) / 2, (L02014a8e - action_jump_table) / 2, (L02014aa8 - action_jump_table) / 2, (L02014ab0 - action_jump_table) / 2, (L02014ab8 - action_jump_table) / 2, (L02014ac2 - action_jump_table) / 2, (L02014acc - action_jump_table) / 2, (L02014ad6 - action_jump_table) / 2
    .byte (L02014af6 - action_jump_table) / 2, (L02014b06 - action_jump_table) / 2
L02014a86:
    r0 = b[r4+1] (u)
; HyperRig MINI, product option: the taps of Scenes are the scenes of a group (mini/product/pairs.c).
.if MINI_PRODUCT
    r1 = r5
    r2 = r6
    call hyperrig_scene_of  ; @call.xl
.endif
L02014a88:
    call scene_application_select
    {pc, r9-r4} = [sp++]
L02014a8e:
    r0 = b[r4+1] (u)
    call preset_storage_available
    if (r0 == 0) goto L02014b3a
    r0 = b[r4+1] (u)
    call preset_loader_load
    if (r0 != 0) goto L02014b3a
    r0 = b[r8+238] (u)
.if MINI_PRODUCT
    if (r0 <= 7) goto L02014a88
.else
    if (r0 <= 3) goto L02014a88
.endif
    {pc, r9-r4} = [sp++]
L02014aa8:
    r0 = 1
    call selection_preset_step
    {pc, r9-r4} = [sp++]
L02014ab0:
    r0 = -1
    call selection_preset_step
    {pc, r9-r4} = [sp++]
L02014ab8:
    r0 = r7 + 956
    [r0+0] += 1  ; @rmw.add.s12
    {pc, r9-r4} = [sp++]
L02014ac2:
    r0 = r7 + 956
    [r0+0] += -1  ; @rmw.add.s12
    {pc, r9-r4} = [sp++]
L02014acc:
    r1_r0 = d[r7+968]
    call tap_tempo_tap_tempo
    {pc, r9-r4} = [sp++]
L02014ad6:
    r0 = r4
    call selection_effect_resolve
    r5 = r0
    ifs (r5 <= -1) goto L02014b22
    call preset_application_effect_enabled  ; @call.xl
    r1 = 1
    if (r0 == 0) goto L02014aee
    r1 = 0
L02014aee:
    r0 = r5
    call slot_commands_enable_command
    {pc, r9-r4} = [sp++]
L02014af6:
    r1 = b[r7+52] (u)
    r0 = 1
    if (r1 == 0) goto L02014b00
    r0 = 0
L02014b00:
    b[r7+52] = r0
    {pc, r9-r4} = [sp++]
L02014b06:
    call slot_commands_requested
    r1 = r0
    r0 = 1
    if (r1 == 0) goto L02014b12
    r0 = 0
L02014b12:
    call preset_band_controls_request_reserve
    if (r0 == 0) goto L02014b3a
    r0 = 10
    r1 = 511
    r2 = 0
    goto L02014b36
L02014b22:
    r2 = b[r8+238] (u)
    if (r2 != 255) {  ; @if.ne.ri.s12
    r0 = b[r4+1] (u)
    r1 = r0 | 0x300
    } else {
    r1 = 768
    }
    r0 = 10
L02014b36:
    call storage_coordination_notify
L02014b3a:
    {pc, r9-r4} = [sp++]

; control_actions_tick: 0x02014b3c..0x02014c04, module control-actions (tick)
.type control_actions_tick,@function
control_actions_tick:
    [--sp] = {rets, r15-r4}
    r6 = L01c26890
    r3 = b[r6+74] (u)
    r8 = r0
    if (r3 == 0) goto L02014bfe
    r10 = L01c1f180
    r4 = r10 + 239
    r9 = 0
    r7 = 1567
    r11 = 808
    r12 = 60000
    r13 = 804
    r5 = 0
    goto L02014bf8
L02014b6e:
    r0 = r5 + r10
    r0 = b[r0+116] (u)
    r14 = r0 + r6
    r0 = b[r14+r7] (u)
    if (r0 == 0) goto L02014bbe
    r0 = r5 + r6
    r1 = r0 + 932
    r2 = b[r1+0] (u)
    if (r2 != 0) goto L02014bbe
    r2 = r5 << 1
    r2 += r6  ; @add.rr
    r3 = h[r2+r13<<1] (u)
    r3 += r8
    r15 = r3 >> 5
    if (r15 >= 1875) {
    r3 = r12
    }
    h[r2+r13<<1] = r3
    if (r3 < 1000) goto L02014bbe
    r2 = b[r4+0] (u)
    if (r2 == 0) goto L02014bbe
    r2 = 1
    r1 = 964  #
    b[r1+0] = r2
    b[r0+r1] = r9
    r1 = 1
    r0 = r5
    call control_actions_action
L02014bbe:
    r0 = r5 + r6
    r0 = r0 + 964
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L02014bf4
    r1 = b[r14+r7] (u)
    if (r1 != 0) goto L02014bf4
    r1 = r5 << 1
    r1 += r6  ; @add.rr
    r2 = h[r1+r11<<1] (u)
    r2 += r8
    r3 = r2 >> 5
    if (r3 >= 1875) {
    r2 = r12
    }
    h[r1+r11<<1] = r2
    if (r2 >= 301) {
    b[r0+0] = r9
    r1 = 0
    r0 = r5
    call control_actions_action
    }
L02014bf4:
    r4 += 9  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L02014bf8:
    if (r5 != 4) goto L02014b6e
    {pc, r15-r4} = [sp++]
L02014bfe:
    call panel_inputs_switch_scan
    {pc, r15-r4} = [sp++]
