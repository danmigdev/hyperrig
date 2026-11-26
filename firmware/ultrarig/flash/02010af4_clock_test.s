; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; clock_test: 1 function, 0x02010af4..0x020112f8

; HyperRig MINI, product option: no processor test
.if MINI_PRODUCT
.else
; clock_test_clock_test: 0x02010af4..0x020112f8, module clock-test (clock_test)
.type clock_test_clock_test,@function
clock_test_clock_test:
    [--sp] = {rets, r15-r4}
    sp += -336
    r4 = r0
    r1 = sp + 332
    r2 = 10
    r0 = 10
    r0 = r4  #
    [sp+196] = r0
    call L020285bc  ; @call.xl
    r1 = [sp+332]
    if (r1 == r4) goto L02010b22
    if (r0 == 0) goto L02010b1e
    if (r0 >= 60) {  ; @if.ge.ri.s12
    r0 = 60
    }
    goto L02010b20
L02010b1e:
    r0 = 1
L02010b20:
    [sp+196] = r0
L02010b22:
    r4 = r1 + -1
L02010b26:
    r0 = b[++r4=1] (u)
    if (r0 == 32) goto L02010b26
    [sp+332] = r4
    r13 = L02035810
    r1 = r13 + 405
    r2 = 4
    r0 = r4
    call capture_command_prefix  ; @call.xl
    r1 = 0
    [sp+116] = r1
    r5 = 1
    r6 = 1
    [sp+128] = r0
    if (r0 == 0) goto L02010b54
    r6 = 0
L02010b54:
    r1 = r13 + 641
    r2 = 5
    r0 = r4
    call capture_command_prefix  ; @call.xl
    [sp+124] = r0
    if (r0 == 0) goto L02010b68
    r5 = 0
L02010b68:
    r0 = r6 | r5
    [sp+120] = r0
    if (r0 != 1) goto L02010b88
    r0 = 4
    r1 = [sp+128]
    if (r1 == 0) goto L02010b7a
    r0 = 5
L02010b7a:
    r0 += r4  ; @add.rr
    r1 = 0
    r2 = 10
    call L020285bc  ; @call.xl
    [sp+116] = r0
L02010b88:
    call fault_record_radio_wait
    r5 = L01c26890
    if (r0 == 0) goto L0201119a
    r0 = 4096
    call L0203c15c  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L020111a6
    r0 = 8728
    r4 = r5 + r0
    r0 = 9278
    r2 = r13 + r0
    r1 = 512
    r0 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    call command_services_console_send
    r0 = 5
    call L0203feb8  ; @call.xl
    call link_and_print_link_pause
    r0 = 396  #
    [sp+84] = r0
    call boundary_hooks_rate_level
    r1 = [r5+280]
    r5 = r0  #
    [sp+80] = r1
    r4 = sp + 328
    r0 = r4
    call record_helpers_half_fields
    r0 = 1
    call fault_record_link_check
    r1_r0 = r5_r4  #
    [sp+208] = r5
    call flash_helpers_record_level
    r2 = r0  #
    [sp+112] = r0
    if (r0 < 4) goto L02010c18
    r0 = sp + 328
    r1 = [sp+208]
    call record_helpers_leading_ones
    r2 = r0
L02010c18:
    r0 = 0
    [sp+188] = r0
    r0 = 1
    [sp+108] = r0
    r0 = [sp+112]
    if (r0 >= 4) {  ; @if.ge.ri.s12
    r0 = 0
    [sp+108] = r0
    }
    r0 = sp + 328
    r1 = r0 | 0x3
    r1 = r0 | 0x2  #
    [sp+96] = r1
    r0 |= 1
    d[sp+88] = r1_r0
    r0 = r6 + 2048
    r10 = 511  #
    [sp+72] = r0
    r15 = 1664525
    r8 = 1013904223
    r0 = 0
    [sp+184] = r0
    [sp+168] = r0
    [sp+180] = r0
    [sp+176] = r0
    [sp+160] = r0
    [sp+164] = r0
    [sp+156] = r0
    [sp+172] = r0
    [sp+104] = r0
    [sp+212] = r0
    r3 = 1
    goto L02010fba
L02010c6e:
    r2 = [sp+220]
    if (r2 == 0) goto L02010c9c
    if (r11 == r5) goto L02010c9c
    r0 = sp + 328
    b[r0+r2] = r5
    r0 = [sp+96]
    r2 = b[r0+0] (u)
    r0 = [sp+92]
    r1 = b[r0+0] (u)
    r0 = [sp+88]
    r0 = b[r0+0] (u)
    call settings_store_select_save
    r1 = [sp+104]
    if (r0 == 0) goto L02010c94
    r1 = r0
L02010c94:
    r0 = [sp+104]
    if (r0 != 0) goto L02010c9a
    [sp+104] = r1
L02010c9a:
    r2 = [sp+220]
L02010c9c:
    if (r5 != 1) goto L020111c4
    r0 = [sp+212]
    r0 += r4  ; @add.rr
    [sp+212] = r0
    r4 = 0
    r0 = 1
    r1 = [sp+208]
    if (r2 >= r1) {
    r0 = 0
    }
    r1 = [sp+108]
    r0 &= r1
    if (r0 != 1) goto L020111cc
    r0 = sp + 328
    r1 = [sp+208]
    call flash_helpers_record_level
    r2 = r0
    r3 = 0
    r5 = 0
    if (r2 < 4) goto L02010fba
    goto L020111d0
L02010cd6:
    r0 = r1  #
    r1 = [sp+72]
    [++r0=684] = r1
    r2 = 0
    [r0+4] = r2
    r1 = 0
    [sp+228] = r1
    [r0+8] = r2
    call flash_helpers_move_interrupts
    call flash_helpers_park_request
    r0 = 2
    call L0203feb8  ; @call.xl
    call ram_callbacks_link_check  ; @call.xl
    r1 = 0
    [sp+76] = r0
    if (r0 != 0) goto L02010d06
    r1 = -2
L02010d06:
    [sp+224] = r1
    r0 = L01c1f180
    r0 = [r0+24]
    [sp+132] = r0
    call preset_application_rate
    r1 = 0
    r2 = [sp+76]
    if (r2 == 0) goto L02010e48
    r0 = r0 * 0x14
    [sp+100] = r0
    r0 = 0
    [sp+228] = r0
    r4 = 0
    goto L02010e32
L02010d2c:
    r13 = 0  #
    [sp+200] = r4
    [sp+204] = r1
    r1 = 0
    r0 = ram_callbacks_clock_job
    call ram_callbacks_post_job  ; @call.xl
    goto L02010dc8
L02010d42:
    r1 = 0
    r2 = 99537814
    goto L02010d56
L02010d4c:
    r2 *= r15
    r2 += r8
    [r6+r1<<2] = r2
    r1 += 1  ; @add.ri.u5
L02010d56:
    if (r1 != 512) goto L02010d4c
    r1 = 0
    r2 = 0
    r3 = 0
    r12 = 1
    r11 = 0
    goto L02010da4
L02010d6a:
    r7 = 0
    r4 = r12
    goto L02010d98
L02010d70:
    r9 = [r6+r7<<2]
    r14 = r4 & r10
    r5 = [r6+r14<<2]
    r3_r2 += r5 * r9 (u)
    r5 = r3 + r9
    r5 = r5 ^ r11
    r11 = r5 <> 27
    r5 = r11 ^ r9
    [r6+r7<<2] = r5
    r4 += 7  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L02010d98:
    if (r7 != 512) goto L02010d70
    r12 = r12 + 131
    r1 += 1  ; @add.ri.u5
L02010da4:
    if (r1 != 4) goto L02010d6a
    r1 = r2 ^ r3
    r2 = r1 ^ r11
    r1 = 1
    r3 = 1915855605
    if (r2 == r3) {
    r1 = 0
    }
    r2 = [sp+228]
    r2 += r1  ; @add.rr
    r13 = r13 + 1  #
    [sp+228] = r2
L02010dc8:
    if (r13 != 4) goto L02010d42
    r13 = L02035810
    if (r0 != 1) goto L02010e04
    call storage_platform_clock  ; @call.xl
    r1 = [sp+100]
    r0 += r1  ; @add.rr
    r1 = 0
    call ram_callbacks_wait_job  ; @call.xl
    if (r0 != 0) goto L02010e04
    r4 = 1
    goto L02010df8
L02010dee:
    r0 = 1
    call L0203feb8  ; @call.xl
    r4 += 1  ; @add.ri.u5
L02010df8:
    call audio_pause_queue_drained  ; @call.xl
    if (r0 != 0) goto L02010e04
    ifs (r4 <= 49) goto L02010dee
L02010e04:
    call phase3_p3_wdt_clear
    r0 = L01c1f180
    r4 = [sp+200]
    r1 = r4 & 0x3F  #
    r0 = [r0+24]
    r2 = L01c26890
    [r2+204] = r0
    if (r1 == 63) {  ; @if.eq.ri.s12
    r0 = 1
    call L0203feb8  ; @call.xl
    }
    r1 = [sp+204]
    r1 += 4  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02010e32:
    r0 = L01c1f180
    r0 = [r0+24]
    r2 = [sp+132]
    r0 = r0 - r2  #
    r2 = [sp+144]
    r0 = r0 * 0xA
    if (r0 < r2) goto L02010d2c
L02010e48:
    r14 = r1
    r4 = 1
    goto L02010e58
L02010e4e:
    r0 = 1
    call L0203feb8  ; @call.xl
    r4 += 1  ; @add.ri.u5
L02010e58:
    call audio_pause_queue_drained  ; @call.xl
    if (r0 != 0) goto L02010e64
    ifs (r4 <= 49) goto L02010e4e
L02010e64:
    r5 = 0
    r4 = L01c26890
    [r4+552] = r5
    r0 = 2
    call L0203feb8  ; @call.xl
    r7 = [r4+692]
    r0 = [r4+688]
    r0 = 1023  #
    [sp+204] = r0
    r0 = [r4+r0<<2]
    [sp+200] = r0
    r0 = [sp+76]
    if (r0 == 0) goto L02010fb6
    [sp+100] = r7
    r0 = 2
    call mode_and_settings_mode_service
    r0 = 1021
    r0 = [r4+r0<<2]
    [sp+144] = r0
    r0 = L01c1f180
    r12 = 0  #
    r0 = [r0+24]
    r9 = 0  #
    [sp+224] = r0
    r0 = [sp+192]
    r0 = r0 * 0x1F4
    [sp+132] = r0
    goto L02010f8c
L02010ebc:
    r0 = 0
    r1 = 99537814
    goto L02010ed0
L02010ec6:
    r1 *= r15
    r1 += r8
    [r6+r0<<2] = r1
    r0 += 1  ; @add.ri.u5
L02010ed0:
    if (r0 != 512) goto L02010ec6
    r13 = 0
    r0 = 0
    r1 = 0
    r11 = 1
    r2 = 0
    goto L02010f1c
L02010ee4:
    r7 = 0
    r5 = r11
    goto L02010f0e
L02010eea:
    r4 = [r6+r7<<2]
    r3 = r5 & r10
    r3 = [r6+r3<<2]
    r1_r0 += r3 * r4 (u)
    r3 = r1 + r4
    r2 ^= r3
    r2 = r2 <> 27
    r3 = r2 ^ r4
    [r6+r7<<2] = r3
    r5 += 7  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L02010f0e:
    if (r7 != 512) goto L02010eea
    r11 = r11 + 131
    r13 = r13 + 1
L02010f1c:
    if (r13 != 4) goto L02010ee4
    r3 = L01c1f180
    r3 = [r3+24]
    r4 = L01c26890
    [r4+204] = r3
    r0 ^= r1
    r0 ^= r2
    r5 = 1
    r1 = 1915855605
    if (r0 == r1) {
    r5 = 0
    }
    call phase3_p3_wdt_clear
    call fault_record_fault_age
    r13 = L02035810
    if (r0 >= 3001) goto L020112d4
    r0 = [sp+136]
    if (r0 == 0) goto L02010f74
    r0 = L01c1f180
    r0 = [r0+24]
    r1 = [sp+224]
    r0 = r0 - r1  #
    r1 = [sp+132]
    r0 = r0 * 0xA
    if (r0 >= r1) goto L020112ec
L02010f74:
    r7 = r12 + 1
    r0 = r12 & 0x3F
    r9 += r5
    r12 = r7
    if (r0 != 63) goto L02010f8c
    r0 = 1
    call L0203feb8  ; @call.xl
L02010f8c:
    r0 = L01c1f180
    r0 = [r0+24]
    r1 = [sp+224]
    r0 = r0 - r1  #
    r1 = [sp+140]
    r0 = r0 * 0xA
    if (r0 < r1) goto L02010ebc
    r0 = r4
    r1 = 1021
    r5 = [r0+r1<<2]
    r0 = 0
    [sp+224] = r0
    r0 = 1
    r7 = [sp+100]
    goto L020110b8
L02010fb6:
    r0 = 0
    goto L020110b0
L02010fba:
    r1 = 0
    r0 = [sp+120]
    [sp+220] = r2
    if (r0 == 0) goto L02010fe2
    r0 = r3  #
    r1 = [sp+116]
    if (r1 == 0) goto L02010fdc
    r0 = r13 + 1006
    r1 = h[r0+r2<<1] (u)
    r0 = 1
    r2 = [sp+116]
    if (r2 != r1) {
    r0 = 0
    }
    r2 = [sp+220]
L02010fdc:
    r1 = 1
    if (r0 != 0) goto L02010fe2
    r1 = r0
L02010fe2:
    [sp+152] = r1
    r0 = [sp+196]
    [sp+192] = r0
    r0 = [sp+112]
    if (r0 > 3) goto L02011002
    r0 = [sp+196]
    r1 = [sp+208]
    if (r2 < r1) {
    r0 = 5
    }
    r1 = [sp+196]
    [sp+192] = r1
    if (r1 >= 5) {  ; @if.ge.ri.s12
    [sp+192] = r0
    }
L02011002:
    [sp+148] = r3
    r4 = 1
    r0 = [sp+124]
    if (r0 == 0) goto L0201100c
    r4 = 0
L0201100c:
    r0 = r13 + 1006
    r1 = L01c26890
    r1 = [r1+280]
    r0 = h[r0+r2<<1] (u)
    [sp+216] = r0
    if (r1 == 0) goto L02011028
    r0 = 0
    call mode_and_settings_mode_service
L02011028:
    r1 = 1
    r0 = [sp+216]
    call cpu_clock_set_clock_rate
    r2 = r0
    if (r2 != 0) goto L0201108a
    call ir_reload_and_leaves_get_rate
    r2 = -5
    r1 = [sp+216]
    if (r0 != r1) goto L0201108a
    r0 = [sp+152]
    r0 &= r4
    [sp+136] = r0
    r0 = [sp+192]
    r1 = r0 * 0x3E8
    r0 = 3
    r0 = r1 / r0 (u)  #
    [sp+140] = r1
    [sp+144] = r0
    if (r0 >= 2000) {  ; @if.ge.ri.s12
    r0 = 2000
    [sp+144] = r0
    }
    r1 = L01c26890
    r0 = [r1+280]
    if (r0 == 0) goto L02010cd6
    r0 = 1023
    r0 = [r1+r0<<2]
    r14 = 0  #
    [sp+200] = r0
    r0 = -1
    [sp+224] = r0
    r0 = 0
    [sp+228] = r0
    r7 = 0
    [sp+204] = r0
    goto L020110ae
L0201108a:
    r0 = 0
    [sp+228] = r0
    r0 = 1
    [sp+224] = r2
    if (r2 == 0) goto L02011096
    r0 = 0
L02011096:
    r1 = L01c26890
    r2 = 1023
    r1 = [r1+r2<<2]
    r14 = 0  #
    [sp+200] = r1
    r7 = 0
    r1 = 0
    [sp+204] = r1
L020110ae:
    r5 = 0
L020110b0:
    r1 = 0
    r12 = 0  #
    [sp+144] = r1
    r9 = 0
L020110b8:
    r1 = 1
    r2 = [sp+128]
    if (r2 == 0) goto L020110c0
    r1 = 0
L020110c0:
    r3 = 1023  #
    r2 = [sp+152]
    r1 &= r2  #
    r2 = [sp+228]
    r1 += r9
    r1 += r2  ; @add.rr
    r2 = L01c26890
    r2 = [r2+r3<<2]
    r3 = sp + 328
    r4 = [sp+220]
    r11 = b[r3+r4] (u)
    r3 = r1 + r7  #
    r1 = [sp+144]
    r1 = r5 - r1  #
    r4 = [sp+200]
    r2 = r2 - r4  #
    r4 = [sp+224]
    if (r4 == 0) goto L020110fa
    r5 = r11
    if (r5 >= 7) {  ; @if.ge.ri.s12
    r5 = 0
    }
    goto L02011110
L020110fa:
    r5 = 1
    if (r3 == 0) goto L02011100
    r5 = 2
L02011100:
    r4 = [sp+192]
    r4 = r4 * 0x12C
    if (r1 <= r4) {
    r5 = 2
    }
    if (r0 != 0) goto L02011110
    r5 = 2
L02011110:
    r0 = [sp+172]
    r0 += r3  ; @add.rr
    [sp+172] = r0
    r0 = [sp+184]
    r0 += r12
    [sp+184] = r0
    r0 = [sp+168]
    r0 += r9
    [sp+168] = r0
    r0 = [sp+180]
    r3 = [sp+204]
    r0 += r3  ; @add.rr
    [sp+180] = r0
    r0 = [sp+176]
    r0 += r14
    [sp+176] = r0
    r0 = [sp+160]
    r0 += r7  ; @add.rr
    [sp+160] = r0
    r0 = [sp+164]
    r3 = [sp+228]
    r0 += r3  ; @add.rr
    [sp+164] = r0
    r0 = [sp+156]
    r0 += r2  ; @add.rr
    [sp+156] = r0
    r0 = [sp+188]
    r0 += r1  ; @add.rr
    r1 = r13 + 410  #
    [sp+188] = r0
    r0 = r13 + 38  #
    r2 = [sp+216]
    [sp] = r2
    if (r5 != 1) {  ; @if.ne.ri.s12
    r0 = r1
    }
    r1 = r13 + 29  #
    r2 = [sp+224]
    if (r2 != 0) goto L02011166
    r1 = r0
L02011166:
    r0 = r13 + 9  #
    [sp+4] = r1
    r3 = r13  #
    r1 = [sp+148]
    if (r1 != 0) goto L02011174
    r3 = r0
L02011174:
    r0 = sp + 232
    r1 = [sp+212]
    r0 += r1  ; @add.rr
    r1 = 0x60 - r1
    r2 = r13 + 1054
    call L0200691e
    r4 = r0  #
    r0 = [sp+224]
    if (r0 == 0) goto L02010c6e
    r5 = 0
    r4 = 1
    r3 = r0
    goto L020111d0
L0201119a:
    r0 = 8728
    r4 = r5 + r0
    r2 = r13 + 6964
    goto L020111b0
L020111a6:
    r0 = 8728
    r4 = r5 + r0
    r2 = r13 + 4537
L020111b0:
    r1 = 512
    r0 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    goto L020112cc
L020111c4:
    r5 = 1
    r3 = 0
    r4 = 0
    goto L020111d0
L020111cc:
    r3 = 0
    r5 = 0
L020111d0:
    r12 = r3
    r0 = r6
    call L0203d218  ; @call.xl
    r0 = sp + 328
    r1 = [sp+208]
    call flash_helpers_level_rate
    r1 = 0
    call cpu_clock_set_clock_rate
    if (r4 != 0) goto L020111ee
    r12 = r0
L020111ee:
    r8 = L01c26890
    r1 = [r8+280]
    r9 = [sp+180]  ; @ld.w.sp.l
    r10 = [sp+176]  ; @ld.w.sp.l
    r11 = [sp+172]  ; @ld.w.sp.l
    r0 = [sp+80]
    if (r0 != r1) {
    call mode_and_settings_mode_service
    }
    r0 = 0
    call fault_record_link_check
    r0 = [sp+84]
    call link_and_print_link_resume
    r4 = sp + 328
    r0 = r4  #
    r1 = [sp+208]
    call fault_record_step_state
    r7 = r0
    r0 = r4
    call flash_helpers_level_rate
    r6 = r0
    r0 = r6 << 16
    r1 = r7 + 200
    r2 = r0 | r11
    r0 = 23
    call storage_coordination_notify
    call ir_reload_and_leaves_get_rate
    r4 = r0
    r0 = r7
    call fault_record_state_name
    r2 = r0
    call ir_reload_and_leaves_get_rate
    r1 = sp + 232
    r3 = r12 | r5  #
    [sp+68] = r1
    r1 = r13 + 38  #
    [sp+64] = r6
    [sp+60] = r0
    r0 = [sp+104]
    [sp+56] = r0
    r0 = [sp+156]
    [sp+52] = r0
    r0 = [sp+188]
    [sp+48] = r0
    r6 = [sp+184]
    [sp+44] = r6
    r0 = [sp+168]
    [sp+40] = r0
    [sp+36] = r9  ; @st.w.sp.l
    r0 = [sp+160]
    [sp+32] = r0
    [sp+28] = r10  ; @st.w.sp.l
    r0 = [sp+164]
    r0 = r13 + 410  #
    [sp+24] = r0
    [sp+20] = r12  ; @st.w.sp.l
    [sp+16] = r2
    if (r3 != 0) goto L02011296
    r0 = r1
L02011296:
    r0 = r10 + r6  #
    [sp+12] = r0
    [sp+8] = r11  ; @st.w.sp.l
    r0 += r9
    r0 = 8728  #
    [sp+4] = r0
    r5 = r8 + r0
    r0 = 11004
    r2 = r13 + r0  #
    r0 = [sp+196]
    r1 = 512  #
    [sp] = r0
    r0 = r5
    r3 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
L020112cc:
    call command_services_console_send
    sp += 336
    {pc, r15-r4} = [sp++]
L020112d4:
    call fault_record_fault_age
    r2 = r0
    call fault_record_fault_word
    r3 = r0
    r0 = 2
    r1 = r2
    r2 = r3
    call fault_record_fatal_record
L020112ea:
    goto L020112ea
L020112ec:
    r0 = 1
    r1 = 0
    r2 = 0
    call fault_record_fatal_record
L020112f6:
    goto L020112f6
.endif
