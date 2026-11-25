; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 2 functions, 0x0200d200..0x0200d5c0

; footswitch_events_preset_save: 0x0200d200..0x0200d2aa, module footswitch-events (preset_save)
; HyperRig MINI, product option: a preset may be packed.
.type footswitch_events_preset_save,@function
footswitch_events_preset_save:
    [--sp] = {rets, r6-r4}
    sp += -68
    r4 = r0
    r2 = -1
    if (r4 > 31) goto L0200d2a4
    call preset_storage_preparation_prepare
    r6 = L01c1f180
    r0 = [r6+92]
    ifs (r0 < 0) goto L0200d248
    call preset_storage_address
    r1 = 1363626836
    r3 = sp + 28
.if MINI_PRODUCT
    r2 = 1880
.else
    r2 = 1490
.endif
    call preset_application_header
    if (r0 == 0) goto L0200d248
    r0 = sp + 28
    r0 += 16  ; @add.ri.u5
    r1 = sp + 4
    rep 23 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = 0
    b[sp+27] = r0
    goto L0200d264
L0200d248:
; HyperRig MINI, product option: the name a saved preset gets, 1A to 11B.
.if MINI_PRODUCT
    r3 = 3
    r0 = r4 / r3 (u)
    r3 = r0 * 0x3
    r5 = r4 - r3
    r5 = r5 + 65
    r3 = r0 + 1
.else
    r0 = r4 & 0x3
    r5 = r0 + 65
    r0 = r4 >> 2
    r3 = r0 + 1
.endif
    r0 = sp + 4
    r2 = L0203a018  ; "Preset %d%c"
    r1 = 24
    [sp] = r5
    call L0200691e
L0200d264:
    r0 = [r6+88]
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    call command_services_effect_snapshot
    }
    r0 = r4
    call status_snapshot_status_snapshot
    r5 = sp + 28
    r0 = r5
    call command_services_record_header
    r1 = sp + 4
    r0 = r5
    call record_helpers_copy_name
    r1_r0 = r5_r4  #
    r3 = [sp+32]
    r2 = L01c24790
    call preset_storage_preparation_preset_write
    r2 = r0
    r0 = r4
    call preset_storage_preparation_invalidate
    if (r2 != 0) goto L0200d2a4
    [r6+92] = r4
    r2 = 0
L0200d2a4:
    r0 = r2
    sp += 68
    {pc, r6-r4} = [sp++]

; footswitch_events_switch_event: 0x0200d2aa..0x0200d5c0, module footswitch-events (switch_event)
.type footswitch_events_switch_event,@function
footswitch_events_switch_event:
    [--sp] = {rets, r13-r4}
    sp += -8
    r11 = r2
    r8 = r1
    r9 = r0
    r12 = L01c26890
    [r12+812] = r2
    r0 += -3
    r13 = uextra(r1, p:0, l:8)
    r1 = r13 + 1
    r2 = 0
    r0 = r0.b0 (u)
    r3 = 924
    r4 = 1
    goto L0200d2fe
L0200d2d4:
    r5 = 1
    r6 = 1
    if (r1 != r2) {
    r6 = 0
    }
    if (r0 >= 2) {  ; @if.ge.ri.s12
    r5 = 0
    }
    if (r13 == r2) goto L0200d2ec
    r5 &= r6
    if (r5 == 0) goto L0200d2fc
L0200d2ec:
    r5 = r12 + 1812
    [r5+r2<<2] = r11
    r5 = r2 + r12
    b[r5+r3] = r4
L0200d2fc:
    r2 += 1  ; @add.ri.u5
L0200d2fe:
    if (r2 != 4) goto L0200d2d4
    r1 = r13 + 4
    if (r0 >= 2) {  ; @if.ge.ri.s12
    r1 = r13
    }
    r10 = uextra(r9, p:0, l:8)
    r2 = r10 | 0x100
    r0 = 9
    call storage_coordination_notify
    r5_r4 = 0
    r6 = 1
    goto L0200d33a
L0200d320:
    r0 = b[r12+76] (u)
; HyperRig MINI, product option: the presets of the bank.
.if MINI_PRODUCT
    r0 = r0 * 0x3
    r7 = r5 + r0
.else
    r0 = r0 << 2
    r7 = r5 + r0
.endif
    r0 = r7
    call preset_storage_available
    r1 = r6 << r7
    if (r0 == 0) goto L0200d336
    r0 = r1
L0200d336:
    r4 |= r0
    r5 += 1  ; @add.ri.u5
L0200d33a:
; HyperRig MINI, product option: three switches.
.if MINI_PRODUCT
    if (r5 != 3) goto L0200d320
.else
    if (r5 != 4) goto L0200d320
.endif
    r7 = L01c1f180
    r1 = [r7+92]
    r0 = b[r12+52] (u)
    if (r0 == 0) goto L0200d362
    r0 = r9 | 0x2
    r0 = r0.b0 (u)
    if (r0 != 3) goto L0200d35e
    goto L0200d432
L0200d35a:
    b[r12+52] = r0
L0200d35e:
    sp += 8
    {pc, r13-r4} = [sp++]
L0200d362:
    r0 = r10 + -3
    r9 = L02035810
    if (r0 < 2) goto L0200d388
    if (r10 == 1) goto L0200d3ba
    if (r10 != 2) goto L0200d35e
    r0 = b[r12+77] (u)
    if (r0 != 0) goto L0200d35e
    r0 = b[r12+76] (u)
; HyperRig MINI, product option: the fourth switch is not there.
.if MINI_PRODUCT
    r0 = r0 * 0x3
    r8 += r0
    if (r13 > 2) goto L0200d35e
.else
    r0 = r0 << 2
    r8 += r0
.endif
    goto L0200d490
L0200d388:
    r0 = uextra(r8, p:0, l:8)
    r8 = 0
    r2 = 0
    if (r0 > 2) goto L0200d40a
    r2 = r9 + 56
    r0 = r9 + 53
    if (r10 != 3) {  ; @if.ne.ri.s12
    r0 = r2
    }
    r2 = b[r0+r13] (u)
    if (r2 != 3) goto L0200d3ea
    r0 = sp + 0
    call panel_inputs_switch_status
    r8 = b[sp+1] (u)
    r0 = b[sp] (u)
    goto L0200d412
L0200d3ba:
    r0 = b[r12+75] (u)
    if (r0 == 1) goto L0200d446
    r0 = b[r12+76] (u)
; HyperRig MINI, product option: the fourth switch is not there.
.if MINI_PRODUCT
    if (r13 > 2) goto L0200d35e
    r0 = r0 * 0x3
    r2 = r0 + r13
.else
    r0 = r0 << 2
    r2 = r0 + r13
.endif
    r0 = r4 & (1 << r2)
    if (r0 == 0) goto L0200d35e
    if (r2 != r1) goto L0200d5b4
    r2 = b[r12+77] (u)
    r1 = 1
    if (r2 == 0) goto L0200d3e0
    r1 = 0
L0200d3e0:
    r0 = 3
    if (r2 != 0) goto L0200d5ba
    r0 = 2
    goto L0200d5ba
L0200d3ea:
    r0 = r2 + -1
    if (r0 > 1) goto L0200d40a
; HyperRig MINI, product option: eleven banks: 32 presets, the last bank holds two.
.if MINI_PRODUCT
    r0 = 1
    if (r2 != 2) {
    r0 = 10
    }
    r1 = b[r12+76] (u)
    r0 = r0 + r1
    if (r0 > 10) {
    r0 = r0 + -11
    }
.else
    r0 = 1
    if (r2 != 2) {  ; @if.ne.ri.s12
    r0 = 7
    }
    r1 = b[r12+76] (u)
    r0 += r1  ; @add.rr
    r0 = r0 & 0x7
.endif
    b[r12+76] = r0
    goto L0200d35e
L0200d40a:
    r0 = 9
    if (r2 != 4) {  ; @if.ne.ri.s12
    r0 = 0
    }
L0200d412:
    r0 = r0.b0 (u)
    r0 += -1
    if (r0 > 9) goto L0200d35e
    r1 = r0 << 1
    tbh [r1]
switch_event_cases:
    .short (L0200d438 - switch_event_cases) / 2, (L0200d562 - switch_event_cases) / 2, (L0200d5a0 - switch_event_cases) / 2, (L0200d436 - switch_event_cases) / 2, (L0200d446 - switch_event_cases) / 2, (L0200d490 - switch_event_cases) / 2, (L0200d436 - switch_event_cases) / 2, (L0200d5a6 - switch_event_cases) / 2
    .short (L0200d5b0 - switch_event_cases) / 2, (L0200d432 - switch_event_cases) / 2
L0200d432:
    r0 = 0
    goto L0200d35a
L0200d436:
    goto L0200d35e
L0200d438:
    r0 = sextra(r8, p:0, l:8)
    call preset_loader_load
    r0 = 836
    goto L0200d598
L0200d446:
    r3 = sextra(r8, p:0, l:8)
    r0 = r3 & 0x3
    r0 += r9
    r1 = 1126
    r4 = b[r0+r1] (u)
    call panel_inputs_change_check
    if (r4 == 7) goto L0200d4ee
    if (r4 != 3) goto L0200d4be
    call preset_application_mode
    if (r0 == 0) goto L0200d4be
    call slot_commands_requested
    r1 = r0
    r0 = 1
    if (r1 == 0) goto L0200d476
    r0 = 0
L0200d476:
    call preset_band_controls_request_reserve
    if (r0 == 0) goto L0200d488
    r0 = 10
    r1 = 511
    r2 = 0
    call storage_coordination_notify
L0200d488:
    r0 = 97
    r1 = 0
    r2 = 0
    goto L0200d4e8
L0200d490:
    r6 = sextra(r8, p:0, l:8)
    r0 = r6
    call footswitch_events_preset_save
; HyperRig MINI, product option: the switch whose light answers.
.if MINI_PRODUCT
    r2 = 3
    r1 = r6 / r2 (u)
    r2 = r1 * 0x3
    r1 = r6 - r2
    b[r7+13] = r1
.else
    r1 = r8 & 0x3
    b[r7+13] = r1
.endif
    [r12+920] = r11
    r1 = 1
    if (r0 == 0) goto L0200d4aa
    r1 = 0
L0200d4aa:
    b[r12+49] = r1
    if (r0 != 0) goto L0200d35e
    r0 = 115
    r2 = 0
    r1 = r6
    call panel_inputs_event_queue
    goto L0200d35e
L0200d4be:
    r0 = r4 + r12
    r1 = 1590
    r4 = b[r0+r1] (s)
    ifs (r4 < 0) goto L0200d55c
    r0 = r4
    call preset_application_effect_enabled  ; @call.xl
    r1 = 1
    if (r0 == 0) goto L0200d4dc
    r1 = 0
L0200d4dc:
    r0 = r4
    call slot_commands_enable_command
    r0 = 101
    r2 = 0
    r1 = r4
L0200d4e8:
    call panel_inputs_event_queue
    goto L0200d55c
L0200d4ee:
    r1 = sp + 4
    r0 = r3
    call panel_inputs_switch_effect
    r1 = 1591
    r1 = b[r12+r1] (u)
    r2 = 1590
    r2 = b[r12+r2] (u)
    r9 = r0
    b[sp+2] = r1
    b[sp+3] = r2
    r7 = 0
    r8 = 1
    ifs (r0 >= 1) {  ; @ifs.ge.ri.s12
    r8 = 0
    }
    goto L0200d558
L0200d51e:
    r0 = sp + 2
    r6 = b[r0+r7] (s)
    ifs (r6 < 0) goto L0200d556
    r5 = 1
    r4 = 1
    ifs (r9 >= 1) {  ; @ifs.ge.ri.s12
    r4 = 0
    }
    r0 = r6
    call preset_application_effect_enabled  ; @call.xl
    if (r0 == 0) goto L0200d53e
    r5 = 0
L0200d53e:
    r0 = r4 ^ r5
    if (r0 != 0) goto L0200d556
    r0 = r6
    r1 = r8
    call slot_commands_enable_command
    r0 = 101
    r2 = 0
    r1 = r6
    call panel_inputs_event_queue
L0200d556:
    r7 += 1  ; @add.ri.u5
L0200d558:
    if (r7 != 2) goto L0200d51e
L0200d55c:
    call panel_inputs_change_mark
    goto L0200d35e
L0200d562:
    r4 = 0
    goto L0200d584
L0200d566:
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    if (r0 == 0) goto L0200d582
    r0 = r4
    call preset_application_effect_enabled  ; @call.xl
    if (r0 == 0) goto L0200d582
    r1 = 0
    r0 = r4
    call slot_commands_enable_command
L0200d582:
    r4 += 1  ; @add.ri.u5
L0200d584:
    if (r4 != 16) goto L0200d566
    call slot_commands_requested
    if (r0 == 0) goto L0200d594
    r0 = 0
    call preset_band_controls_request_reserve
L0200d594:
    r0 = 872
L0200d598:
    r1 = 1
    b[r12+r0] = r1
    goto L0200d35e
L0200d5a0:
    call footswitch_events_reload_preset
    goto L0200d35e
L0200d5a6:
    r0 = sextra(r8, p:0, l:8)
    call panel_inputs_analog_command
    goto L0200d35e
L0200d5b0:
    r0 = 1
    goto L0200d35a
L0200d5b4:
    r1 = 0
    r0 = 1
    r8 = r2
L0200d5ba:
    b[r12+77] = r1
    goto L0200d412
