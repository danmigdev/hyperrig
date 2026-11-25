; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dispatch_helpers: 6 functions, 0x0200e34e..0x0200e628

; dispatch_helpers_stereo_command: 0x0200e34e..0x0200e40e, module dispatch-helpers (stereo_command)
.type dispatch_helpers_stereo_command,@function
dispatch_helpers_stereo_command:
    [--sp] = {rets, r10-r4}
    sp += -28
    r6 = r1
    r5 = r0  #
    r1 = b[r6+0] (u)
    r9 = L01c26890
    r8 = L02036086  ; "ERR %s usage\x0a"
    if (r1 == 0) goto L0200e39c
    r1 = sp + 24
    r2 = 10
    r0 = r6
    call capture_command_decimal  ; @call.xl
    r1 = [sp+24]
    r2 = r1 + -1
L0200e378:
    r1 = b[++r2=1] (u)
    if (r1 == 32) goto L0200e378
    [sp+24] = r2
    if (r6 == r2) goto L0200e3e8
    if (r0 > 100) goto L0200e3e8
    if (r1 != 0) goto L0200e3e8
    r2 = 1
    if (r0 != 0) goto L0200e392
    r2 = r0
L0200e392:
    r1 = 0
    r0 = r2
    call stereo_budget_set_stereo  ; @call.xl
L0200e39c:
    r0 = sp + 20
    call stereo_budget_stereo_setting  ; @call.xl
    r10 = [sp+20]  ; @ld.w.sp.l
    r1 = L01c34488
    r5 = r0  #
    r4 = b[r1+0] (u)
    call effect_setup_total_cost  ; @call.xl
    r6 = r0
    call preset_application_services_budget  ; @call.xl
    r7 = r0
    call stereo_budget_suspended  ; @call.xl
    r0 = 8728  #
    [sp+16] = r0
    d[sp+8] = r7_r6
    r6 = r9 + r0  #
    [sp+4] = r4
    r2 = r8 + 4067
    r1 = 512
    [sp] = r10  ; @st.w.sp.l
    r0 = r6
    goto L0200e3f8
L0200e3e8:
    r0 = 8728
    r6 = r9 + r0
    r1 = 512
    r0 = r6
    r2 = r8
L0200e3f8:
    r3 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    sp += 28
    {pc, r10-r4} = [sp++]

; dispatch_helpers_audio_hold: 0x0200e40e..0x0200e4ee, module dispatch-helpers (audio_hold)
.type dispatch_helpers_audio_hold,@function
dispatch_helpers_audio_hold:
    [--sp] = {rets, r6-r4}
    r5 = L01c26890
    r1 = b[r5+19] (u)
    if (r0 == 0) goto L0200e46e
    if (r1 != 255) {  ; @if.ne.ri.s12
    r1 += 1  ; @add.ri.u5
    b[r5+19] = r1
    }
    if (r0 == 2) goto L0200e47e
    r0 = L01c1f180
    r1 = [r0+40]
    if (r1 == 0) goto L0200e47e
    r1 = [r5+280]
    if (r1 != 2) goto L0200e47e
    r1 = b[r0+2] (u)
    if (r1 == 0) goto L0200e47e
    r0 = b[r0+3] (u)
    if (r0 == 0) goto L0200e47e
    r0 = [r5+328]
    if (r0 == 0) goto L0200e450
    r0 = [r5+332]
    if (r0 != 0) goto L0200e47e
L0200e450:
    r0 = 0
    [r5+332] = r0
    r0 = 1
    [r5+328] = r0
    call storage_platform_clock  ; @call.xl
    r4 = r0
    call preset_application_rate
    r6 = r0 * 0x6
    goto L0200e490
L0200e46e:
    if (r1 == 0) goto L0200e4e6
    r0 = r1 + -1
    b[r5+19] = r0
    if ((r0 & 0xFF) == 0) goto L0200e4e6
L0200e47e:
    {pc, r6-r4} = [sp++]
L0200e480:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r4
    if (r0 >= r6) goto L0200e496
    call storage_coordination_poll_forward
L0200e490:
    r0 = [r5+332]
    if (r0 == 0) goto L0200e480
L0200e496:
    r6 = r5 + 332
    call storage_platform_clock  ; @call.xl
    [r6+4] += 1  ; @rmw.add.s12
    r0 = r0 - r4  #
    r1 = [r6+0]
    if (r1 != 0) goto L0200e4b2
    r1 = r5 + 340
    [r1+0] += 1  ; @rmw.add.s12
L0200e4b2:
    r1 = [r5+344]
    if (r0 > r1) {
    [r5+344] = r0
    }
    r4 = 0
    goto L0200e4cc
L0200e4c2:
    r0 = 1
    call L0203feb8  ; @call.xl
    r4 += 1  ; @add.ri.u5
L0200e4cc:
    ifs (r4 > 19) goto L0200e4d6
    r0 = [r5+332]
    if (r0 == 0) goto L0200e4c2
L0200e4d6:
    r0 = [r5+332]
    if (r0 != 0) goto L0200e47e
    r0 = r5 + 348
    [r0+0] += 1  ; @rmw.add.s12
    {pc, r6-r4} = [sp++]
L0200e4e6:
    r0 = 0
    [r5+328] = r0
    {pc, r6-r4} = [sp++]

; dispatch_helpers_scope_buffer: 0x0200e4ee..0x0200e574, module dispatch-helpers (scope_buffer)
.type dispatch_helpers_scope_buffer,@function
dispatch_helpers_scope_buffer:
    [--sp] = {rets, r7-r4}
    r7 = L01c26890
    r5 = 0
    b[r7+18] = r5
    r4 = r0
    r0 = 1
    call dispatch_helpers_audio_hold
    r1 = [r7+312]
    if (r1 == 0) goto L0200e52a
    r6 = r7 + 2452
    r0 = r6
    call block_pool_contains
    if (r0 == 0) goto L0200e51c
    r0 = r6
    call block_pool_release
    goto L0200e524
L0200e51c:
    r0 = r1
    call L0203d218  ; @call.xl
L0200e524:
    r0 = 0
    [r7+312] = r0
L0200e52a:
    r0 = 0
    r1 = 0
    d[r7+316] = r1_r0
    [r7+324] = r5
    if (r4 == 0) goto L0200e566
    r6 = r4 << 1
    r0 = r6
    call heap_access_vendor_allocate_wrapper
    if (r0 == 0) goto L0200e548
    [r7+312] = r0
    goto L0200e558
L0200e548:
    r0 = r7 + 2452
    r1 = r6
    call block_pool_allocate
    [r7+312] = r0
    if (r0 == 0) goto L0200e570
L0200e558:
    r1 = 0
    r2 = r6
    call effect_enable_memset  ; @call.xl
    d[r7+316] = r5_r4
L0200e566:
    r0 = 0
    call dispatch_helpers_audio_hold
    r0 = r5
    {pc, r7-r4} = [sp++]
L0200e570:
    r5 += -100
    goto L0200e566

; dispatch_helpers_scope_arm: 0x0200e574..0x0200e5b8, module dispatch-helpers (scope_arm)
.type dispatch_helpers_scope_arm,@function
dispatch_helpers_scope_arm:
    r1 = L01c26890
    ifs (r0 < 1) goto L0200e592
    r0 = [r1+312]
    if (r0 == 0) goto L0200e5b4
    r0 = 0
    [r1+320] = r0
    r0 = 1
L0200e58c:
    b[r1+18] = r0
    goto L0200e5a8
L0200e592:
    if (r0 != 0) goto L0200e5a8
    r0 = b[r1+18] (u)
    if (r0 != 1) goto L0200e5a8
    r0 = 512
    [r1+324] = r0
    r0 = 2
    goto L0200e58c
L0200e5a8:
    r0 = b[r1+18] (u)
    if (r0 != 1) {  ; @if.ne.ri.s12
    r0 = 0
    }
    rts
L0200e5b4:
    r0 = -1
    rts

; dispatch_helpers_capabilities: 0x0200e5b8..0x0200e5f4, module dispatch-helpers (capabilities)
.type dispatch_helpers_capabilities,@function
dispatch_helpers_capabilities:
    [--sp] = {rets, r6-r4}
    r3 = L01c26890
    r4 = [r3+416]
    if (r4 == 0) goto L0200e5ec
    r4 = 0
    r5 = 1924
    goto L0200e5da
L0200e5ce:
    r6 = r4 + r3
    r6 = b[r6+r5] (u)
    b[r0+r4] = r6
    r4 += 1  ; @add.ri.u5
L0200e5da:
    if (r4 != 17) goto L0200e5ce
    r0 = [++r3=488]
    [r1+0] = r0
    r0 = [r3+4]
    [r2+0] = r0
    r0 = [r3+8]
    {pc, r6-r4} = [sp++]
L0200e5ec:
    call capture_dispatch_capabilities  ; @call.xl
    {pc, r6-r4} = [sp++]

; dispatch_helpers_tenths_text: 0x0200e5f4..0x0200e628, module dispatch-helpers (tenths_text)
.type dispatch_helpers_tenths_text,@function
dispatch_helpers_tenths_text:
    [--sp] = {rets, r4}
    sp += -8
    r2 = abs(r1)
    r3 = 10
    r3 = r2 / r3 (s)
    r3 = r3 * 0xA  #
    [sp] = r3
    r4 = r2 - r3
    r2 = L02035810
    r3 = r2 + 15
    [sp+4] = r4
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r3 = r2
    }
    r2 = r2 + 1158
    r1 = 10
    call L0200691e
    sp += 8
    {pc, r4} = [sp++]
