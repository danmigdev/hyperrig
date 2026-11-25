; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; mode_and_settings: 3 functions, 0x02005130..0x020054a8

; mode_and_settings_link_rate: 0x02005130..0x02005194, module mode-and-settings (link_rate)
.type mode_and_settings_link_rate,@function
mode_and_settings_link_rate:
    r0 = 4172
    r1 = L01c26890
    r0 = b[r1+r0] (u)
    r0 |= 2
    if (r0 != 3) {  ; @if.ne.ri.s12
    r0 = -1
    rts
    }
    r0 = 1045
    r2 = 48000
    [r1+r0<<2] = r2
    r0 += 11  ; @add.ri.u5
    r0 = [r1+r0<<2]
    r2 = b[r0+5] (u)
    r0 = 0
    if (r2 != 0) goto L02005192
    r2 = 72100
    [r2+0] |= 0x2000000
    r2 = r2 + -6544
    [r2+0] |= 0x100
    r3 = 1055
    r1 = [r1+r3<<2]
    r3 = b[r1+12] (u)
    r3 = r3 & 0xFFFFFFE3
    b[r1+12] = r3
    r3 = b[r1+12] (u)
    r3 = r3 & 0xFFFFFF1F
    r3 |= 128
    b[r1+12] = r3
    [r2+0] &= 0xFFFFFDFF
L02005192:
    rts

; mode_and_settings_link_buffers: 0x02005194..0x020051fc, module mode-and-settings (link_buffers)
.type mode_and_settings_link_buffers,@function
mode_and_settings_link_buffers:
    [--sp] = {rets, r9-r4}
    r0 = 4172
    r8 = L01c26890
    r0 = b[r8+r0] (u)
    if (r0 == 0) goto L020051fa
    r0 = 2087
    r0 = h[r8+r0<<1] (u)
    r1 = 1055
    r6 = [r8+r1<<2]
    r4 = r0 << 3
    r7 = -4
    r5 = 0
    r9 = 1051
    goto L020051ee
L020051c2:
    r0 = r7 + 4
    if (r0 > 1) goto L020051ea
    r1 = b[r6+8] (u)
    r0 = r1 | (1 << r0)
    r0 = r5 + r8  #
    b[r6+8] = r0
    r0 = [r0+r9<<2]
    r1 = 0
    r2 = r4
    call effect_enable_memset  ; @call.xl
    r0 = h[r6+4] (u)
    r0 = r0 | (1 << r5)
    h[r6+4] = r0
L020051ea:
    r5 += 4  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L020051ee:
    if (r7 != 0) goto L020051c2
    r0 = 4172
    r1 = 2
    b[r8+r0] = r1
L020051fa:
    {pc, r9-r4} = [sp++]

; mode_and_settings_mode_service: 0x020051fc..0x020054a8, module mode-and-settings (mode_service)
.type mode_and_settings_mode_service,@function
mode_and_settings_mode_service:
    [--sp] = {rets, r12-r4}
    r8 = L01c1f180
    r9 = [r8+24]
    r7 = L01c26890
    r1 = 1
    b[r7+26] = r1
    r2 = 520
    r3 = b[r7+r2] (u)
    r11 = r0
    r4 = 0
    if (r3 != 0) goto L02005278
    b[r7+r2] = r1
    r0 = r7 + 3508
    call L0203fdba  ; @call.xl
    r0 = r7 + 3588
    call L0203fdba  ; @call.xl
    r0 = 1027
    r1 = 2
    [r7+r0<<2] = r1
    call ram_callbacks_timer_start  ; @call.xl
    r5 = L020361dd  ; "#C0tankg_audio"
    r0 = audio_task_task
    r1 = r5
    call phase3_p3_task_create
    r1 = r5 + 15
    r0 = flash_helpers_second_task
    call phase3_p3_task_create
    r0 = L01c340c0
    r1 = ram_callbacks_idle_watch
    [r0+0] = r1
    r4 = 1
L02005278:
    if (r11 != 2) goto L0200528c
    r0 = [r7+416]
    if (r0 == 0) goto L0200548a  ; @beq.ri.l
L02005286:
    r0 = 2
    b[r7+26] = r0
L0200528c:
    r0 = 3
    b[r7+26] = r0
    r10 = [r7+280]
    r0 = 0
    [r7+280] = r0
    [r7+524] = r0
    if (r10 == 0) goto L02005306
    r12 = 1021
    r5 = [r7+r12<<2]
    call storage_platform_clock  ; @call.xl
    r6 = r0
    call preset_application_rate
    r4 = r0 * 0xC
L020052bc:
    r0 = [r7+528]
    if (r0 == 6) goto L020052cc
    r0 = [r7+r12<<2]
    if (r0 == r5) goto L020052d4
L020052cc:
    call sample_leaves_capture_idle  ; @call.xl
    if (r0 != 0) goto L020052e0
L020052d4:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r6
    if (r0 < r4) goto L020052bc
L020052e0:
    r4 = 0
    r6 = r12
    goto L02005300
L020052e6:
    r0 = [r7+528]
    if (r0 == 6) goto L02005310
    r0 = [r7+r6<<2]
    if (r0 != r5) goto L02005310
    r0 = 1
    call L0203feb8  ; @call.xl
    r4 += 1  ; @add.ri.u5
L02005300:
    ifs (r4 <= 19) goto L020052e6
    goto L02005310
L02005306:
    if (r4 == 0) goto L02005310
    r0 = 2
    call L0203feb8  ; @call.xl
L02005310:
    r0 = 4
    r1 = r7 + 24
    r0 = r7 + 524  #
    b[r1+2] = r0
    r4 = 0
    [r0+8] = r4
    [r0+12] = r4
    [r0+16] = r4
    [r0+20] = r4
    [r7+384] = r4
    [r7+380] = r4
    b[r1+3] = r4
    b[r1+4] = r4
    [r0+0] = r4
    r0 = r7 + 3508  #
    [r0+24] = r4
    call L02040804  ; @call.xl
    if (r11 != 2) goto L02005382
    r0 = [r7+416]
    if (r0 != 0) goto L0200534e
    call audio_task_warmup  ; @call.xl
L0200534e:
    call flash_helpers_move_interrupts
    call flash_helpers_park_request
    r0 = 2
    call L0203feb8  ; @call.xl
    r0 = 1028
    r0 = [r7+r0<<2]
    if (r0 == 0) goto L02005386
    call ram_callbacks_link_check  ; @call.xl
    if (r0 == 0) goto L02005386
    r0 = 1028
    r0 = [r7+r0<<2]
    r1 = 1029
    r1 = [r7+r1<<2]
    goto L02005388
L02005382:
    [r7+552] = r4
L02005386:
    r1_r0 = 0
L02005388:
    call ram_callbacks_link_words  ; @call.xl
    r0 = 5
    b[r7+26] = r0
    if (r11 == 0) goto L02005436
    r0 = 556
    r0 = b[r7+r0] (u)
    if ((r0 & 1) != 0) goto L02005436
; HyperRig MINI v4, patch mini_codec_pre_and_post_trampoline: Retain r6=1; codec-pre failure skips IRQ/ALNK setup. Local post trampoline restores RETS/r4 and skips success flags on failure.
.if TARGET_MINI
    r6 = 1  ; @li.u8
    call hyperrig_mini_g_audio_pre_current_clock  ; @call.l
    if (r0 != 0) goto L02005436  ; @bnez
    goto L020053c6  ; @goto.s
L020053ae:
    [--sp] = {rets, r4}  ; @push.rets_rl
    call hyperrig_mini_g_audio_post  ; @call.l
    {rets, r4} = [sp++]  ; @pop.rets_rl
    if (r0 != 0) goto L02005436  ; @bnez
    rts  ; @rts
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
.else
    r0 = 32
    r1 = 1
    r6 = 1
    call phase3_p5_gpio_direction_output
L020053ae:
    r0 = 33
    r1 = 1
    call phase3_p5_gpio_direction_output
    r0 = 37
    r1 = 1
    call phase3_p5_gpio_direction_output
    r0 = 9
    r1 = 0
    call phase3_p5_gpio_direction_output
.endif
L020053c6:
    r0 = 65556
    [r0+0] |= 0x200
    r0 = 2
    r1 = r7 + 1748
    b[r1+0] = r0
    b[r1+1] = r6
    b[r1+2] = r4
    r0 = 3
    b[r1+3] = r0
    b[r1+4] = r6
    h[r1+12] = r4
    r0 = r1 + 5
    rep 6 {
    b[r0++=1] = r4
    }
    r0 = 128
    h[r1+14] = r0
    call mode_and_settings_first_callbacks
    call mode_and_settings_second_callbacks
    r2 = interrupt_and_stack_calls_timer_interrupt
    r0 = 11
    r1 = 6
    r3 = 0
    call storage_platform_register
    call audio_link_start_link_start
    r1 = 1033
    [r7+r1<<2] = r0
    call mode_and_settings_link_rate
    r1 = 1034
    [r7+r1<<2] = r0
; HyperRig MINI v4, patch mini_codec_post_call: Call the local post trampoline, which invokes original G channel-start through the C binding then MINI PA9 sequence.
.if TARGET_MINI
    call L020053ae  ; @call.l
.else
    call mode_and_settings_link_buffers
.endif
    r0 = 556
    b[r7+r0] = r6
    r0 = [r8+24]
    [r7+560] = r0
    b[r7+29] = r6
L02005436:
    r1 = 1026
    r0 = 0
    [r7+r1<<2] = r0
    r1 += -1
    [r7+r1<<2] = r0
    r1 = [r8+24]
    [r7+560] = r1
    if (r11 != 0) {  ; @if.ne.ri.s12
    [r8+48] = r0
    r0 = r7 + 412
    [r0+0] += 1  ; @rmw.add.s12
    }
    [r7+280] = r11
    if (r10 != r11) {
    r0 = 4
    r1 = r11
    r2 = r10
    call storage_coordination_notify
    }
    r0 = [r8+24]
    r0 = r0 - r9
    r0 = r0 * 0xA
    [r7+564] = r0
    r5 = 0
    b[r7+26] = r5
L02005486:
    r0 = r5
    {pc, r12-r4} = [sp++]
L0200548a:
    call clock_record_and_usb_link_dsp_start
    r5 = r0
    if (r5 == 0) goto L02005286  ; @beq.ri.l
    r0 = 0
    b[r7+26] = r0
    r0 = 29
    r1 = 4
    r2 = r5
    call storage_coordination_notify
    goto L02005486
