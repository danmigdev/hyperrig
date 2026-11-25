; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; main_task: 1 function, 0x02017b74..0x0201a864

; main_task_main_task: 0x02017b74..0x0201a864, module main-task (main_task)
.type main_task_main_task,@function
main_task_main_task:
    sp += -456
    call ram_callbacks_timer_start  ; @call.xl
    r0 = 2
    call clock_record_and_usb_link_record_refresh
    r0 = 1
    r1 = 191
    call L01c0100e  ; @call.xl
    r0 = 2
    r1 = 64
    call L01c00f72  ; @call.xl
    r0 = 22
    r1 = 0
    r2 = 6
    r3 = 0
    r4 = 0
    call storage_fault_masked_register  ; @call.xl
    r0 = 23
    r1 = 251
    call L01c0100e  ; @call.xl
    r0 = 23
    r1 = 223
    call L01c0100e  ; @call.xl
    r0 = 5
    r1 = 0
    r2 = 3
    r3 = 4
    r6 = 4
    call storage_fault_masked_register  ; @call.xl
    r0 = 5
    r1 = 4
    r2 = 2
    r3 = 3
    call storage_fault_masked_register  ; @call.xl
    r0 = 0
    r1 = 128
    call L01c00f72  ; @call.xl
    r0 = 17
    r1 = 64
    call L01c00f72  ; @call.xl
    r0 = 17
    r1 = 3
    r2 = 3
    r3 = 7
    call storage_fault_masked_register  ; @call.xl
    r0 = 17
    r1 = 1
    call L01c00f72  ; @call.xl
    r0 = 51
    r1 = 128
    call L01c00f72  ; @call.xl
    r0 = 21
    r1 = 4
    call L01c00f72  ; @call.xl
    r0 = 55
    call butterworth_table_butterworth_table
    call clock_record_and_usb_link_dsp_start
    call settings_load_settings_load
    r14 = L01c26890
    r5 = b[r14+39] (u)
    r0 = 15
    b[sp+299] = r0
    b[sp+298] = r4
    r0 = sp + 299
    r1 = sp + 298
    call flash_helpers_firmware_version
    r0 = r14 + 1692
    if (r5 != 0) goto L02017c4e
    r0 = r5
L02017c4e:
    r2 = b[sp+298] (u)
    r1 = b[sp+299] (u)
    call flash_helpers_serial_step
    r0 = 3
    call clock_record_and_usb_link_record_refresh
    r15 = L02035810
    r0 = r15 + 6360
    r1 = 43
    call record_helpers_checksum
    [sp+200] = r0
    [r14+128] = r0
    r9 = 29883864
    r0 = [r9+0]
    call flash_helpers_next_page
    [r9+0] = r0
    r5 = -1
    call storage_fault_record_count
    r4 = r0
    r3 = 7470824
L02017c96:
    r5 += 1  ; @add.ri.u5
    if (r5 >= r4) goto L02017caa
    r0 = [r6+r3<<2]
    r6 += 24  ; @add.ri.u5
    call storage_fault_tag
    if (r0 != 0) goto L02017c96
    goto L02017cc2
L02017caa:
    if (r4 == 0) goto L02017cc2
    r5 = r9 + -564
    goto L02017cbe
L02017cb2:
    r0 = [r5+0]
    call flash_helpers_next_page
    [r5++=24] = r0
    r4 += -1
L02017cbe:
    if (r4 != 0) goto L02017cb2
    goto L02017cce
L02017cc2:
    r0 = r9 + -568
    r1 = 3349479424
    [r0+0] = r1
L02017cce:
    r0 = [sp+200]
    call record_helpers_id_in_use
    r6 = [r9+0]
    r8 = r0
    r0 = r6 >> 20
    r10 = 0
    r3 = 1
    r1 = 3334
    r4 = 1
    if (r0 != r1) {
    r4 = 0
    }
    r0 = r6 & 0xFF000
    r5 = 1
    if (r0 != 4096) {
    r5 = 0
    }
    r0 = r6
    call storage_fault_tag
    if (r0 != 0) goto L02017d02
    r3 = r0
L02017d02:
    r7 = r5 & r3
    r5 = r4 & r7
    call phase3_p3_system_reset_reason_get
    if (r5 != 1) goto L02017d28
    r4 = [r9+12]
    r0 = r15 + 1014
    call record_helpers_pack_tag
    r10 = 1
    if (r4 != r0) {
    r10 = 0
    }
L02017d28:
    r0 = sp + 300
    call record_helpers_half_fields
    r12 = 0
    if (r5 == 0) goto L02017d50
    r2 = [r9+8]
    r0 = 1
    r1 = 1
    if ((r2 & 0xFF) == 0) {
    r1 = 0
    }
    r2 = r6 & 0xF
    if (r2 == 1) {  ; @if.eq.ri.s12
    r0 = 0
    }
    r12 = r0 | r1
L02017d50:
    r13 = b[r14+5] (u)
    r4 = 1
    if (r13 != 0) {  ; @if.ne.ri.s12
    r4 = 0
    }
    r5 = r6 & 0x8E0
    if (r7 != 0) goto L02017d64
    r5 = r7
L02017d64:
    r9 = [r14+116]
    r6 = [r14+120]
    r0 = 396
    call boundary_hooks_rate_level
    r11 = r0
    if ((r6 & 2048) == 0) goto L02017d86
    if (r4 != 0) goto L02017d86
    r4 = 1
    r10 = 1
    if (r7 != 0) goto L02017d96
    goto L02017db6
L02017d86:
    if (r7 == 0) goto L02017da8
    r0 = r5 & 0x800
    r0 = r0 | r10
    r4 = 1
    if (r0 != 0) goto L02017d96
    r4 = r0
L02017d96:
    if ((r5 & 0xE0) == 0) goto L02017db0
    r0 = r5 & 0xE0
    r0 = r0 >> 5
    r0 += -1
    r10 = 0
    goto L02017de2
L02017da8:
    r4 = 0
    r10 = 1
    goto L02017db2
L02017db0:
    r10 = 0
L02017db2:
    if (r13 == 0) goto L02017dc6
L02017db6:
    r0 = 1023
    if ((r6 & r0) == 0) goto L02017dc6
    r0 &= r6
    call boundary_hooks_rate_level_call
    goto L02017de2
L02017dc6:
    r0 = r4
    r4 = 0
    if (r0 == 0) goto L02017de0
    r0 = sp + 300
    r1 = r11
    call flash_helpers_record_level
    if (r0 >= 4) {  ; @if.ge.ri.s12
    r0 = 0
    }
    r4 = 1
    goto L02017de2
L02017de0:
    r0 = 0
L02017de2:
    r2 = r12 | r4
    r1 = 0
    if (r2 != 1) goto L02017e12
    r6 = umin(r0, r11)
    if (r6 == 0) goto L02017e12
    r7 = 2
    if (r4 != 0) goto L02017df8
    r7 = 1
L02017df8:
    r0 = 6
    if (r4 != 0) goto L02017dfe
    r0 = 3
L02017dfe:
    r2 = sp + 300
    r2 = b[r2+r6] (u)
    if (r4 == 0) goto L02017e16
    r3 = r0.b0 (u)
    if (r2 != r3) goto L02017e20
    r7 = 2
    goto L02017e2a
L02017e12:
    r7_r6 = 0
    goto L02017e2a
L02017e16:
    r2 += -2
    if (r2 >= 5) goto L02017e20
    r7 = 1
    goto L02017e2a
L02017e20:
    r1 = sp + 300
    b[r1+r6] = r0
    r1 = 1
L02017e2a:
    r5 = 1
    if (r9 > 1) goto L02017e42
    r0 = 1
    if (r8 == 0) {  ; @if.eq.ri.s12
    r0 = r8
    }
    r0 = r0 | r10
    r0 |= r4
    r5 = r0 ^ 0x1
L02017e42:
    b[r14+9] = r7
    b[r14+10] = r6
    if (r1 == 0) goto L02017e82
    r2 = b[sp+303] (u)
    r1 = b[sp+302] (u)
    r0 = b[sp+301] (u)
    call settings_store_select_save
    r1 = r6.b0 (u)
    r2 = r15 + 1006
    r3 = h[r2+r1<<1] (u)
    r2 = sp + 300
    r1 = b[r2+r1] (u)
    r0 = r0 << 8
    r0 = r0.l (u)
    r2 = r7.b0 (u)
    r2 |= r0
    r2 <= insert(r3, p:16, l:16)
    r1 += 100
    r0 = 23
    call storage_coordination_notify
L02017e82:
    b[r14+11] = r5
    b[r14+41] = r5
    r0 = sp + 300
    r1 = r11
    call flash_helpers_level_rate
    r4 = r0
    r1 = 0
    r9 = 0
    call cpu_clock_set_clock_rate
    r0 = b[r14+11] (u)
    r5 = L01c1f180
    if (r0 != 0) goto L02017fb6
    call ir_reload_and_leaves_get_rate
    if (r4 == r0) goto L02017f12
    call link_and_print_link_pause
    r6 = r0
    [r5+84] = r4
    call ir_reload_and_leaves_get_rate
    if (r0 != r4) goto L02017ee2
    r0 = 6
    r0 = r4 / r0 (u)  #
    [r5+44] = r4
    [r5+68] = r0
    call dsp_audio_path_input  ; @call.xl
    call audio_task_set_input  ; @call.xl
    r7 = 0
    goto L02017ef2
L02017ee2:
    r0 = 0
    call mode_and_settings_mode_service
    r1 = 1
    r0 = r4
    call cpu_clock_set_clock_rate
    r7 = r0
L02017ef2:
    r0 = r6
    call link_and_print_link_resume
    r0 = r7 << 16
    r0 = r0 & 0xFF0000
    r2 = r0 | r4
    r1 = r6 + 400
    r0 = 23
    call storage_coordination_notify
    r0 = b[r14+11] (u)
    if (r0 != 0) goto L02017fb6
L02017f12:
    call L0203d862  ; @call.xl
    r1 = 368
    [r14+r1<<2] = r0
    r1 = r15 + 1473
    r0 = boundary_hooks_ble_task
    call phase3_p3_task_create
    if (r0 == 0) goto L02017f38
    r0 = 32
    r1 = -2
    r2 = 0
    goto L02017fb2
L02017f38:
    r0 = 1456
    r1 = 1
    b[r14+r0] = r1
    r6 = 0
    r4 = 1440
    goto L02017f7c
L02017f4a:
    r0 = 1
    call L0203feb8  ; @call.xl
    r0 = 0
    call state_queries_ready_word
    r1 = r0
    call state_queries_tenfold_word
    r2 = b[r14+r4] (u)
    if (r2 != 0) goto L02017f76
    if (r1 != 0) goto L02017f6c
    if (r0 < 3000) goto L02017f76
L02017f6c:
    r0 = 1
    if (r1 == 0) goto L02017f72
    r0 = 0
L02017f72:
    call link_and_print_start_complete
L02017f76:
    call link_and_print_link_toggle
    r6 += 10  ; @add.ri.u5
L02017f7c:
    r0 = 0
    call state_queries_ready_word
    if (r0 == 0) goto L02017f92
    call state_queries_state_byte
    if (r6 > 2499) goto L02017f98
    if (r0 == 0) goto L02017f4a
    goto L02017f98
L02017f92:
    if (r6 <= 2499) goto L02017f4a
L02017f98:
    call link_and_print_link_report
    r0 = r4 + 16
    r0 = b[r14+r0] (u)
    if (r0 == 0) goto L02017fb6
    r0 = r4 + 20
    r1 = 1
    b[r14+r0] = r1
    r0 = 32
    r1 = -1
    r2 = r6
L02017fb2:
    call storage_coordination_notify
L02017fb6:
    r4 = 1456
    r0 = b[r14+r4] (u)
    call link_and_print_start_complete
    r0 = b[r14+r4] (u)
    if (r0 == 0) goto L02017fd4
    r0 = 16384
    call L0203c15c  ; @call.xl
    r9 = r0
L02017fd4:
    r0 = 613
    r0 = [r14+r0<<2]
    if (r0 != 0) goto L02018064
    call heap_access_heap_free
    r6 = r0
    call heap_access_heap_probe
    r4 = r0
    r0 = r6 - r4
    if (r6 <= r4) {
    r0 = 0
    }
    r7 = 0x8000 - r0
    if (r0 >= 32768) {
    r7 = 0
    }
    if (r4 == 0) goto L02018038
    r0 = r7 >> 14
    if (r0 != 0) goto L02018038
    call heap_access_lock_enter
    r0 = r4
    call heap_access_heap_allocate
    [sp+412] = r0
    call heap_access_lock_leave
    r6 = [sp+412]
    if (r6 == 0) goto L02018032
    call heap_access_heap_probe
    r8 = r0
    r0 = r6
    call heap_access_heap_release
    r0 = 16384
    if (r8 >= 16384) {
    r0 = r7
    }
    goto L02018036
L02018032:
    r0 = 16384
L02018036:
    r7 = r0
L02018038:
    r0 = r4 - r7
    r1 = -4096
    r6 = r0 & r1
    if (r4 <= r7) {
    r6 = 0
    }
    if (r6 < 32768) goto L02018064
    r0 = r6
    call L0203c15c  ; @call.xl
    r1 = r0
    if (r1 == 0) goto L02018064
    r0 = r14 + 2452
    r2 = r6
    call ir_reload_and_leaves_pool_setup
L02018064:
    r0 = r9
    call L0203d218  ; @call.xl
    r0 = [sp+200]
    call record_helpers_id_in_use
    [sp+224] = r0
    b[r14+12] = r0
    r4 = 29883864
    r2 = 3708  #
    r0 = [r4+0]
    r0 = r0 >> 20
    r1 = 1
    if (r0 == r2) goto L020180aa
    r2 = 2654  #
    r0 = [r4+0]
    r0 = r0 >> 20
    r1 = 2
    if (r0 == r2) goto L020180aa
    r2 = 3334  #
    r0 = [r4+0]
    r0 = r0 >> 20
    r1 = 3
    if (r0 != r2) {
    r1 = 0
    }
L020180aa:
    r0 = 1
    r2 = 1
    [sp+216] = r2
    r2 = [sp+200]
    call storage_coordination_notify
    r0 = r14 + 108
    r3 = [r0+8]
    r2 = h[r0+4] (u)
    r2 <= insert(r3, p:16, l:16)  #
    r1 = [r0+0]
    r0 = 2
    call storage_coordination_notify
    r0 = r4 + -156
    r0 = [r0+0]
    r1 = 3334  #
    r0 = [r4+0]
    r0 = r0 >> 20
    if (r0 != r1) goto L0201811a
    r0 = [r4+0]
    if ((r0 & 256) != 0) goto L0201811a
    r0 = [r4+0]
    r2 = r0 & 0xF  #
    r1 = [r4+4]
    if (r2 == 4) goto L020180f8
    if (r2 != 8) goto L020180fe
    r2 = 0x5000000
    goto L02018110
L020180f8:
    r2 = 0x4000000
    goto L02018110
L020180fe:
    r0 = 0x3000000
    if (r2 != 2) {  ; @if.ne.ri.s12
    r0 = 0x1000000
    }
    r2 = [r4+8]
    r2 = r2.l (u)
    r2 |= r0
L02018110:
    r0 = 13
    call storage_coordination_notify
    [r4+0] |= 0x100
L0201811a:
    r4 = b[r14+11] (u)
    r0 = 4
    call clock_record_and_usb_link_record_refresh
    r9 = 0
    if (r4 == 0) goto L0201812c
    r0 = 0
    [sp+216] = r0
L0201812c:
    r8 = 432
    r11 = [r14+r8<<2]
    r0 = sp + 306
    r1 = r0 + 60
    r1 = r0 + 50  #
    [sp+196] = r1
    r1 = r0 + 40  #
    [sp+192] = r1
    r10 = 326  #
    [sp+188] = r1
    r1 = r0 + 30
    r13 = 321  #
    [sp+184] = r1
    r1 = r0 + 20
    r0 += 10  ; @add.ri.u5
    d[sp+176] = r1_r0
    r7 = 1
    r0 = 0
    r12 = 0  #
    [sp+228] = r0
    [sp+212] = r0
    [sp+220] = r0
    goto L0201a496
L0201816e:
    if (r3 < 1501) goto L02018196
    call state_queries_tenfold_word
    r1 = [r14+208]
    r0 = r0 - r1
    if (r0 < 1001) goto L02018196
    call state_queries_tenfold_word
    [r14+208] = r0
    r0 = 13
    r2 = 0x2000000
    r1 = r3
    call storage_coordination_notify
L02018196:
    r0 = r14 + 4076
    r2 = r14  #
    r1 = [r0+8]
    [++r2=352] = r1
    r1 = [r2+4]
    [r2+8] = r1
    r1 = [r0+0]
    [r2+12] = r1
    r1 = [r0+12]
    [r2+16] = r1
    r0 = [r0+16]
    [r2+20] = r0
    r0 = [r13+24]
    [r2+24] = r0
    r4 = 0
    r0 = [sp+216]
    if (r0 == 0) goto L02018268
    call state_queries_tenfold_word
    r1 = [r14+100]
    r2 = b[r14+13] (u)
    r5 = b[r14+1] (u)
    r3 = b[r14+3] (u)
    r6 = [sp+224]
    if (r6 == 0) goto L02018202
    if (r5 == 0) goto L02018202
    if (r0 < 3001) goto L02018268
    r1 = r0 - r1
    if (r2 == 0) goto L020181e8
    r4 = 6
    ifs (r1 > 299) goto L02018268
L020181e8:
    r0 = r0 >> 3
    r4 = 8
    if (r0 > 1874) goto L02018268
    r4 = 7
    if ((r3 & 0xFF) == 0) {
    r4 = 0
    }
    ifs (r1 <= 999) goto L0201821a
    goto L02018268
L02018202:
    r3 = [sp+224]
    if (r3 == 0) goto L0201821e
    if (r0 < 3001) goto L02018268
    r2 = r0 >> 3
    r4 = 1
    if (r2 > 624) goto L02018268
    r0 = r0 - r1
    ifs (r0 > 299) goto L02018268
L0201821a:
    r4 = 0
    goto L02018268
L0201821e:
    if (r0 < 3001) goto L02018268
    r1 = r0 - r1
    ifs (r1 < 1000) goto L02018234
    r3 = [sp+228]
    if (r3 != 0) goto L02018234
    r4 = 2
    if (r2 != 0) goto L02018268
L02018234:
    if (r5 == 0) goto L02018256
    r4 = 5
    r2 = 89999
    if (r0 > r2) goto L02018268
    r2 = 1
    ifs (r1 <= 999) {
    r2 = 0
    }
    r4 = r2 << 2
    r0 = r0 >> 5
    if (r0 <= 1874) goto L0201821a
    goto L02018268
L02018256:
    r4 = 3
    r2 = 3
    ifs (r1 < 8000) {
    r2 = 0
    }
    r0 = r0 >> 4
    if (r0 <= 1874) {
    r4 = r2
    }
L02018268:
    call state_queries_tenfold_word
    if (r4 == 0) goto L020182ae
    r1 = 1456
    r1 = b[r14+r1] (u)
    r1 ^= 1
    if ((r1 & 1) != 0) goto L020182ae
    r0 = r0 >> 5
    if (r0 > 1874) goto L0201828e
    r0 = 1464
    b[r14+r0] = r7
    goto L0201830a
L0201828e:
    r0 = 1468
    r0 = b[r14+r0] (u)
    if (r0 != 0) goto L020182ae
    r0 = 1468
    b[r14+r0] = r7
    call state_queries_tenfold_word
    r2 = r0
    r0 = 32
    r1 = -3
    call storage_coordination_notify
L020182ae:
    if (r4 == 0) goto L0201830a
    r0 = 4
    b[r14+6] = r0
    b[r14+7] = r4
    call state_queries_tenfold_word
    [r14+132] = r0
    r0 = r0 << 4
    r2 = r0 | r4
    r0 = 14
    r1 = 8
    call storage_coordination_notify
    call state_queries_tenfold_word
    r2 = r0 + -3000
    if (r2 >= 20) {  ; @if.ge.ri.s12
    r0 = 14
    r1 = 4
    call storage_coordination_notify
    }
    r0 = [r14+280]
    if (r0 != 0) goto L02018300
    call footswitch_events_startup_preset
    r2 = [r13+88]
    r1 = r0
    r0 = 3
    call storage_coordination_notify
    r0 = 2
    call mode_and_settings_mode_service
L02018300:
    r0 = 5
    call clock_record_and_usb_link_record_refresh
    r0 = 0
    [sp+216] = r0
L0201830a:
    r4 = [sp+224]
    r0 = [sp+212]
    r0 |= r4
    if (r0 != 0) goto L02018352
    r1 = b[r14+13] (u)
    r0 = b[r14+11] (u)
    r2 = 1021
    r2 = [r14+r2<<2]
    if (r2 < 3000) goto L02018352
    if (r1 == 0) goto L02018352
    if (r0 != 0) goto L02018352
    r0 = [sp+200]
    call footswitch_events_record_id
    r1 = 1
    [sp+212] = r1
    r4 = 1
    if (r0 == 0) goto L0201833c
    r4 = 0
L0201833c:
    b[r14+12] = r4
    r1 = 6
    if (r0 == 0) goto L02018346
    r1 = 7
L02018346:
    call state_queries_tenfold_word
    r2 = r0
    r0 = 14
    call storage_coordination_notify
L02018352:
    r0 = [sp+220]
    if (r0 != 0) goto L02018382
    if (r4 == 0) goto L02018382
    call state_queries_tenfold_word
    r1 = 0
    r1 = 20001  #
    [sp+220] = r1
    if (r0 < r1) goto L02018382
    r0 = 29883864
    [r0+24] = r9
    r0 = b[r14+11] (u)
    r1 = 1
    [sp+220] = r1
    if (r0 != 0) goto L02018382
    r0 = 6
    call clock_record_and_usb_link_record_refresh
L02018382:
    [sp+224] = r4
    call state_queries_tenfold_word
    r1 = 1019
    r2 = [r14+r1<<2]
    r1 += 17  ; @add.ri.u5
    r1 = [r14+r1<<2]
    r3 = [r14+280]
    if (r3 == 0) goto L02018406
    r4 = L01c2684c
    r4 = b[r4+0] (u)
    if (r4 == 0) goto L02018406
    r3 = 369
    r3 = [r14+r3<<2]
    r3 = r0 - r3
    if (r3 <= 249) goto L02018424
    r4 = 370
    r4 = [r14+r4<<2]
    r4 = r2 - r4
    r5 = r4 << 6
    r4 = 0
    if (r5 < 64) goto L020183e8
    r4 = 371
    r4 = [r14+r4<<2]
    r6 = 20
    r6 = r5 / r6 (u)
    r5 = r5 - r6
    r6 = r1 - r4
    r4 = 0
    if (r6 > r5) {
    r4 = 372
    r4 = [r14+r4<<2]
    r4 += r3  ; @add.rr
    }
L020183e8:
    r5 = r14 + 1476
    [r5+12] = r4
    r3 = 1
    if (r4 <= 1999) {
    r3 = 0
    }
    r4 = L01c26848
    b[r4+0] = r3
    [r5+] = {r2, r0}
    [r5+8] = r1
    goto L02018438
L02018406:
    r4 = 1
    if (r3 != 0) goto L0201840c
    r4 = r3
L0201840c:
    r5 = L01c2684c
    r4 = r14 + 1476  #
    b[r5+0] = r4
    [r4+] = {r2, r0}
    [r4+8] = r1
    [r4+12] = r9
    if (r3 == 0) goto L0201842e
L02018424:
    r0 = L01c26848
    r3 = b[r0+0] (u)
    goto L02018438
L0201842e:
    r3 = 0
    r0 = L01c26848
    b[r0+0] = r3
L02018438:
    r0 = b[r14+14] (u)
    if (r3 == r0) goto L02018456
    b[r14+14] = r3
    r0 = 1036
    r2 = [r14+r0<<2]
    r1 = r3 + 300
    r0 = 23
    call storage_coordination_notify
L02018456:
    r0 = 5
    b[r14+6] = r0
    call state_queries_tenfold_word
    r1 = 748
    r1 = b[r14+r1] (u)
    if (r1 == 0) goto L020184a8
    r1 = [r14+280]
    if (r1 != 2) goto L02018482
    r1 = [r14+752]
    r0 = r0 - r1
    r1 = 180001
    if (r0 < r1) goto L0201855a
L02018482:
    r2 = [r14+280]
    b[r14+17] = r9
    r0 = r15 + 1078
    r1 = r15 + 2222
    r3 = 748
    b[r14+r3] = r9
    if (r2 == 2) {  ; @if.eq.ri.s12
    r1 = r0
    }
    r0 = r15 + 4132
    call link_and_print_print
L020184a8:
    r0 = b[r14+212] (u)
    if (r0 == 0) goto L02018626
    call audio_measurement_measure_running  ; @call.xl
    if (r0 == 0) goto L020184ee
    call state_queries_tenfold_word
    r1 = [r14+216]
    r2 = [r14+220]
    r0 = r0 - r1
    r1 = r2 + 3000
    if (r0 > r1) goto L020184d6
    r0 = [r14+280]
    if (r0 != 0) goto L02018626
L020184d6:
    b[r14+212] = r9
    call audio_measurement_measure_stop  ; @call.xl
    r0 = 8728
    r4 = r14 + r0
    r2 = r15 + 5475
    goto L02018610
L020184ee:
    b[r14+212] = r9
    r0 = sp + 376
    call audio_measurement_measure_result  ; @call.xl
    if (r0 == 0) goto L02018604
    r5 = 0
    r4 = sp + 306
    goto L0201851a
L02018508:
    r0 = sp + 376
    r1 = [r0+r5<<2]
    r0 = r4
    call dispatch_helpers_tenths_text
    r4 += 10  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L0201851a:
    if (r5 != 7) goto L02018508
    r3 = [r14+220]
    r1 = 8728  #
    r0 = [sp+196]
    r4 = r14 + r1  #
    [sp+24] = r0
    r0 = [sp+192]
    [sp+20] = r0
    r0 = [sp+188]
    [sp+16] = r0
    r0 = [sp+184]
    [sp+12] = r0
    r0 = [sp+180]
    [sp+8] = r0
    r0 = [sp+176]
    [sp+4] = r0
    r0 = sp + 306
    r1 += -46
    r2 = r15 + r1  #
    [sp] = r0
    r1 = 512
    r0 = r4
    call L0200691e
    goto L0201861a
L0201855a:
    r0 = sp + 428
    r1 = sp + 416
    r2 = sp + 424
    call command_services_calibration_measure
    if (r0 == 0) goto L020184a8
    r1 = [r14+756]
    if (r0 == r1) goto L020184a8
    r1 = r14
    [++r1=756] = r0
    r0 = [sp+428]
    [r1+4] += 1  ; @rmw.add.s12
    r6 = -999
    r4 = r6
    if (r0 == 0) goto L020185ac
    r1 = 0
    call main_task_shift
    r1_r0 <<= 1
    r2 = r0 - 0x3C0000
    r4 = -1
    r3 = r1 + r4 + c
    r1_r0 = r3_r2
    call bond_records_and_prints_db_value
    r4 = r0
    ifs (r4 <= -999) {
    r4 = r6
    }
L020185ac:
    r1_r0 = d[sp+416]
    r2 = r0 | r1
    [r14+764] = r4
    if (r2 == 0) goto L020185ee
    r5 = [sp+424]
    if (r5 == 0) goto L020185ee
    call main_task_shift
    r6 = r0 - 0x2C0000
    r2 = -1
    r7 = r1 + r2 + c
    r1 = 0
    r0 = r5
    call main_task_shift
    r2 = r6 - r0
    r3 = r7 - r1 - !c
    r1_r0 = r3_r2
    call bond_records_and_prints_db_value
    r6 = r0
    ifs (r6 <= -999) {
    r6 = -999
    }
    r7 = 1
L020185ee:
    [r14+768] = r6
    r0 = [r14+772]
    ifs (r4 > r0) {
    [r14+772] = r4
    }
    call command_services_calibration_status
    goto L020184a8
L02018604:
    r0 = 8728
    r4 = r14 + r0
    r2 = r15 + 3600
L02018610:
    r1 = 512
    r0 = r4
    call L0200691e
L0201861a:
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    call command_services_console_send
L02018626:
    r0 = 6
    b[r14+6] = r0
    call control_scan_control_scan
    r0 = 7
    b[r14+6] = r0
    r0 = b[r14+52] (u)
    if (r0 == 0) goto L0201865a
    r0 = [r14+1016]
    if (r0 == 0) goto L020186ae
    r1 = 1020
    r0 = b[r14+r1] (u)
    if (r0 == 0) goto L020186fe
    b[r14+r1] = r9
    r0 = [r14+1016]
    [r14+976] = r0
    goto L020186fe
L0201865a:
    r0 = 1012
    b[r14+r0] = r9
    r1 = [r14+1016]
    if (r1 == 0) goto L0201938e
    r2 = r0 + 8
    r0 = b[r14+r2] (u)
    if (r0 == 0) goto L020186be
    r0 = [r14+1008]
    r2 = 256
    r2 = [r14+r2<<2]
    r0 = r0 - r2
    if (r0 > 1) goto L02018698
    r0 = b[r14+53] (u)
    r0 += 1  ; @add.ri.u5
    r2 = r0.b0 (u)
    b[r14+53] = r0
    if (r2 < 10) goto L0201938e
L02018698:
    r4 = r14 + 2452
    r0 = r4
    call block_pool_contains
    if (r0 == 0) goto L02018836
    r0 = r4
    call block_pool_release
    goto L0201883e
L020186ae:
    r0 = 7168
    call heap_access_vendor_allocate_wrapper
    if (r0 == 0) goto L020186d6
    b[r14+54] = r9
    goto L020186f2
L020186be:
    r0 = r14 + 976
    [r0+0] = r9
    b[r14+r2] = r7
    r1 = [r0+32]
    [r0+48] = r1
    b[r14+53] = r9
    goto L0201938e
L020186d6:
    r0 = r14 + 2452
    r1 = 7168
    call block_pool_allocate
    r1 = 1
    if (r0 == 0) goto L020186e8
    r1 = 0
L020186e8:
    b[r14+54] = r1
    if (r0 == 0) goto L0201938e
L020186f2:
    r1 = r14 + 976
    [r1+40] = r0
    r2 = [r1+20]
    [r1+52] = r2
    [r1+0] = r0
L020186fe:
    r0 = [r14+996]
    r1 = 257
    r1 = [r14+r1<<2]
    r0 = r0 - r1
    if (r0 > 707) goto L0201871c
    r0 = 1012
    b[r14+r0] = r9
    goto L0201938e
L0201871c:
    r3 = [r14+988]
    r0 = [r13+24]
    r1 = 258
    r1 = [r14+r1<<2]
    r0 = r0 * 0xA
    if (r1 == 0) goto L02018748
    r2 = 259
    r2 = [r14+r2<<2]
    r1 = r0 - r1
    if (r1 > r2) {
    r2 = 259
    [r14+r2<<2] = r1
    }
L02018748:
    r1 = r14 + 1012
    [r1+20] = r0
    [r1+28] += 1  ; @rmw.add.s12
    r0 = b[r1+0] (u)
    if (r0 == 0) goto L020187fe
    r0 = 261
    r0 = [r14+r0<<2]
    r0 = r3 - r0
    if (r0 < 200) goto L0201938e
    r4 = r14 + 996  #
    [sp+208] = r3
    [r4+48] = r3
    [r4+76] += 1  ; @rmw.add.s12
    call storage_platform_clock  ; @call.xl
    r13 = [r4+0]
    r1 = 2047  #
    r2 = [r4+20]
    r15 = r2 + 2048  #
    [sp+204] = r0
    r2 = 0
    r3 = -1
    goto L020187a2
L0201878e:
    r0 = r13 + r3
    r0 &= r1
    r0 = h[r15+r0<<1] (s)
    r0 = abs(r0)
    r2 = smax(r0, r2)
    r3 += -1
L020187a2:
    if (r3 != -701) goto L0201878e
    r3 = r2 << 7
    ifs (r3 < 1) goto L0201884e
    r0 = 1000
    r5_r4 = r3 * r0 (s)
    r3 = 0
    goto L020187d2
L020187ba:
    r1 = 1122
    r0 = r5 * r1
    r5_r4 = r4 * r1 (u)
    r5 += r0  ; @add.rr
    r0 = 1000
    r5_r4 = r5_r4 / r0 (s)
    r3 += -10
L020187d2:
    ifs (r3 < -1439) goto L02018852
    r0 = 4194303999
    r6 = r4 - r0
    r7 = r5 - r9 - !c
    r1 = psr
    r0 = sextra(r1, p:0, l:1)
    r1 = sextra(r1, p:3, l:1)
    r0 ^= r1
    r0 = ~r0
    r1 = r6 | r7
    if ((r1 & r0) == 0) goto L020187ba
    goto L02018852
L020187fe:
    r0 = r14 + 1012
    r1 = 1048  #
    b[r0+0] = r7
    [r0+32] = r3
    b[r14+r1] = r9
    [r0+40] = r3
    [r0+44] = r3
    r2 = 0
    r3 = 0
    d[r0+612] = r3_r2
    d[r0+620] = r3_r2
    [r0+48] = r9
    [r0+52] = r9
    r0 = -1
    [r13+140] = r0
    r0 = r1 + 20
    b[r14+r0] = r9
    goto L0201938e
L02018836:
    r0 = r1
    call L0203d218  ; @call.xl
L0201883e:
    r0 = 1020
    [r14+1016] = r9
    b[r14+r0] = r9
    goto L0201938e
L0201884e:
    r3 = -1440
L02018852:
    r0 = 269
    [r14+r0<<2] = r3
    r0 = 1048
    r0 = b[r14+r0] (u)
    if (r0 == 0) goto L0201887c
    r4 = 0
    r3 = [sp+208]
    ifs (r2 > 17) goto L0201888e
    r0 = r14 + 1048
    b[r0+0] = r9
    [r0+4] = r3
    [r0+36] += 1  ; @rmw.add.s12
    goto L02018984
L0201887c:
    r3 = [sp+208]
    ifs (r2 < 33) goto L02018984
    r4 = 1
    r0 = r14 + 1048
    b[r0+0] = r4
    [r0+32] += 1  ; @rmw.add.s12
L0201888e:
    r0 = 1068
    r0 = b[r14+r0] (u)
    if (r0 == 0) goto L020188c6
    r0 = 264
    r0 = [r14+r0<<2]
    r0 = r3 - r0
    r1 = 12001
    ifs (r0 < r1) goto L020188c6
    r0 = r14 + 1060
    b[r0+8] = r9
    [r0+0] = r9
    [r0+28] += 1  ; @rmw.add.s12
    r0 = L01c1f180
    r1 = -1
    [r0+140] = r1
L020188c6:
    r2 = 0
    r3 = 0
    r5 = -1
    goto L020188e4
L020188ce:
    r0 = r13 + r5
    r1 = 2047
    r0 &= r1
    r0 = h[r15+r0<<1] (s)
    r0 = r0 >>> 1
    r3_r2 += r0 * r0 (s)
    r5 += -1
L020188e4:
    if (r5 != -121) goto L020188ce
    r0 = r14 + 1632
    r1_r0 = d[r0+0]
    if (r4 != 0) goto L02018952
    r4 = r14 + 1624
    r7_r6 = d[r4+0]
    r4 = r0 - r6
    r15 = r1 - r7 - !c  #
    [sp+172] = r4
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r13 = r4 ^ 0xFFFFFFFF  #
    r4 = [sp+172]
    r15 = r15 | r4
    r5_r4 = r1_r0
    if ((r15 & r13) == 0) {
    r5_r4 = r7_r6
    }
    r5_r4 <<= 2
    r6 = r4 + 0x8000
    r7 = r5 + r9 + c
    r4 = r2 - r6
    r5 = r3 - r7 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r4 |= r5
    if ((r4 & r6) == 0) goto L020189cc
    r4 = r14 + 1092
    [r4+0] += 1  ; @rmw.add.s12
L02018952:
    r4 = r14 + 1060
    d[r4+564] = r1_r0
    d[r4+572] = r3_r2
    r0 = [sp+208]
    r0 += 120
    [r4+36] = r0
    [r4+0] = r9
    [r4+4] = r9
    r0 = [r4+40]
    r13 = L01c1f180
    r1 = -1
    [r13+140] = r1
    r0 += 1  ; @add.ri.u5
    [r4+40] = r0
    [r4+44] = r0
    goto L0201938e
L02018984:
    r0 = 0
    r1 = 0
    r2 = r14 + 1068
    d[r2+556] = r1_r0
    d[r2+564] = r1_r0
    r0 = b[r2+0] (u)
    if (r0 == 0) goto L0201938e
    r0 = 263
    r0 = [r14+r0<<2]
    r0 = r3 - r0
    ifs (r0 <= 7200) goto L0201938e
    r0 = 1068
    b[r14+r0] = r9
    r0 = -1
    r1 = L01c1f180
    [r1+140] = r0
    r0 = 265
    [r14+r0<<2] = r9
    goto L0201938e
L020189cc:
    r4 = r14 + 1096
    d[r4+528] = r1_r0
    d[r4+536] = r3_r2
    r0 = [r4+0]
    r1 = [sp+208]
    r0 = r1 - r0
    ifs (r0 < 1288) goto L0201938e
    r4 = r1
    call storage_platform_clock  ; @call.xl
    r0 = 274
    r0 = [r14+r0<<2]
    r1 = r4 - r0
    r0 = 364  #
    [sp+172] = r1
    ifs (r1 <= 1495) {
    r0 += -52
    }
    r13 = [r14+1004]
    r1 = [r14+1016]
    r2 = r13 - r0
    r3 = r1 + 6144
    r1 = 0
    r6 = 0
    r5 = 511
    goto L02018a2e
L02018a1c:
    r4 = r2 + r1
    r4 &= r5
    r4 = h[r3+r4<<1] (s)
    r4 = abs(r4)
    r6 = smax(r4, r6)
    r1 += 1  ; @add.ri.u5
L02018a2e:
    ifs (r1 < r0) goto L02018a1c
    r4 = -1
L02018a34:
    r4 += 1  ; @add.ri.u5
    r1 = r6 >>> r4
    ifs (r1 > 1023) goto L02018a34
    r1 = 1
    r5 = 1
    if (r4 == 0) goto L02018a48
    r5 = 0
L02018a48:
    ifs (r6 <= 0) {  ; @ifs.le.ri.s12
    r1 = 0
    }
    r15 = r1 & r5
    r5 = -1
L02018a54:
    r1 = 0
    if (r15 == 0) goto L02018a6a
    r7 = r5 + 2
    r7 = r6 << r7
    r5 += 1  ; @add.ri.u5
    ifs (r7 < 1024) goto L02018a54
    goto L02018a6c
L02018a6a:
    r5 = 0
L02018a6c:
    r15 = 511
    r7 = L01c24790
    goto L02018a98
L02018a78:
    r6 = r2 + r1
    r6 = r6 & r15
    r6 = h[r3+r6<<1] (s)
    r7 = r6 << r5
    r6 >>>= r4
    if (r4 != 0) goto L02018a8c
    r6 = r7
L02018a8c:
    r7 = L01c24790
    h[r7+r1<<1] = r6
    r1 += 1  ; @add.ri.u5
L02018a98:
    ifs (r1 < r0) goto L02018a78
    r1 = [r14+1004]
    r2 = r0 - r13
    r1 += r2  ; @add.rr
    if (r1 <= 512) goto L02018abe
    r0 = r14 + 1108
    [r0+0] += 1  ; @rmw.add.s12
L02018ab2:
    r0 = r14 + 1120
    [r0+0] += 1  ; @rmw.add.s12
    goto L0201938e
L02018abe:
    r4 = 0
    [sp+452] = r4
    r0 = r0 << 1
    r0 += r7  ; @add.rr
    r5 = r0 + -280
    [sp+448] = r4
    r1 = 140
    r2 = 1
    r3 = 172
    r6 = 1
    r0 = r5
    call sort_and_format_normalized_differences
    r2 = sp + 452
    r3 = sp + 448
    r0 = 172
    r1 = 3
    call tuner_and_control_records_pitch_estimate
    r7 = r0
    r0 = 1
    if (r7 != 0) goto L02018af6
    r0 = r7
L02018af6:
    r15 = [sp+452]
    r1 = r4 + 0x3F000000
    r1 = r15 + r1 (f)
    r1 = ftoi(r1) (trunc)
    r2 = r1 + 2
    ifs (r2 <= 171) {  ; @ifs.le.ri.s12
    r6 = 0
    }
    if (r7 == 0) goto L02018b34
    r1 = r1 << 1
    r2 = r1 + 3
    ifs (r2 < 172) goto L02018b34
    r1 += -3
    ifs (r1 > 223) goto L02018b34
    r1 = 278
    r1 = [r14+r1<<2]
    r4 = 1
    r2 = 1028443341
    iff (r1 u<= r2) {
    r4 = 0
    }
L02018b34:
    r0 &= r6  #
    r2 = [sp+172]
    r6 = 0
    ifs (r2 <= 1495) {
    r6 = 2
    }
    r1 = r0 | r4
    if (r1 != 0) goto L02018b48
    r6 = r1
L02018b48:
    ifs (r2 < 1496) goto L02018ba8
    r6 = 0
    r1 = 1
    if (r7 == 0) goto L02018b56
    r1 = 0
L02018b56:
    r0 |= r1
    r0 |= r4
    if (r0 != 1) goto L02018bae
    [sp+444] = r9
    [sp+440] = r9
    r1 = 140
    r2 = 173
    r3 = 224
    r0 = r5
    call sort_and_format_normalized_differences
    r2 = sp + 444
    r3 = sp + 440
    r0 = 224
    r1 = 3
    call tuner_and_control_records_pitch_estimate
    if (r0 == 0) goto L02018bae
    r0 = [sp+444]
    if (r7 != 0) goto L02018b96
    r7 = 0
    r1 = 1126760448
    iff (r0 u<= r1) goto L02018bae
L02018b96:
    r1 = [sp+440]
    [sp+452] = r0
    [sp+448] = r1
    r7 = 1
    r15 = r0
    goto L02018bae
L02018ba8:
    r13 = 0
    if (r1 != 0) goto L02018cca
L02018bae:
    r0 = 1106247680
    iff (r15 u< r0) goto L02018bbc
    if (r7 != 0) goto L02018cbe
L02018bbc:
    r13 = [r14+996]
    r0 = [r14+1016]
    r1 = r13 + 1834
    r2 = r0 + 2048
    r4 = 0
    r3 = 0
    goto L02018be8
L02018bd2:
    r0 = r1 + r3
    r5 = 2047
    r0 &= r5
    r0 = h[r2+r0<<1] (s)
    r0 = abs(r0)
    r4 = smax(r0, r4)
    r3 += 1  ; @add.ri.u5
L02018be8:
    if (r3 != 214) goto L02018bd2
    r3 = -1
L02018bee:
    r3 += 1  ; @add.ri.u5
    r0 = r4 >>> r3
    ifs (r0 > 1023) goto L02018bee
    r0 = 1
    r5 = 1
    if (r3 == 0) goto L02018c02
    r5 = 0
L02018c02:
    [sp+160] = r6
    [sp+172] = r7
    ifs (r4 <= 0) {  ; @ifs.le.ri.s12
    r0 = 0
    }
    r0 &= r5
    r5 = -1
L02018c10:
    r6 = 0
    if (r0 == 0) goto L02018c24
    r7 = r5 + 2
    r7 = r4 << r7
    r5 += 1  ; @add.ri.u5
    ifs (r7 < 1024) goto L02018c10
    goto L02018c26
L02018c24:
    r5 = 0
L02018c26:
    r7 = L01c24790
    goto L02018c4a
L02018c2e:
    r0 = r1 + r6
    r0 &= r4
    r0 = h[r2+r0<<1] (s)
    r4 = r0 << r5
    r0 >>>= r3
    if (r3 != 0) goto L02018c40
    r0 = r4
L02018c40:
    r4 = r7 + 728
    h[r4+r6<<1] = r0
    r6 += 1  ; @add.ri.u5
L02018c4a:
    r4 = 2047
    if (r6 != 214) goto L02018c2e
    [sp+436] = r9
    [sp+432] = r9
    r0 = [r14+996]
    r1 = 0xD6 - r13
    r0 += r1  ; @add.rr
    if (r0 <= 2048) goto L02018c7a
    r0 = r14 + 1108
    [r0+0] += 1  ; @rmw.add.s12
    r6 = 0
    r0 = 1
    r13 = 0
    goto L02018cae
L02018c7a:
    r0 = r7 + 900
    r1 = 128
    r2 = 1
    r3 = 86
    call sort_and_format_normalized_differences
    r2 = sp + 436
    r3 = sp + 432
    r0 = 86
    r1 = 6
    call tuner_and_control_records_pitch_estimate
    if (r0 == 0) goto L02018e96
    r0 = [sp+436]
    r1 = 1178324224
    r13 = r1 / r0 (f)
    r0 = 1
    r6 = 1
L02018cae:
    r2 = [sp+172]
L02018cb0:
    r1 = 1
    if (r2 == 0) goto L02018cb6
    r1 = 0
L02018cb6:
    if (r0 != 0) goto L02018cba
    r6 = r0
L02018cba:
    if (r0 != 0) goto L02018cca
    if (r1 != 0) goto L02018cca
L02018cbe:
    r0 = 1169935616
    r13 = r0 / r15 (f)
    goto L02018cde
L02018cca:
    if (r6 == 0) goto L02018ab2
    if (r6 != 2) goto L02018cde
    r0 = r14 + 1116
    [r0+0] += 1  ; @rmw.add.s12
    goto L0201938e
L02018cde:
    r4 = r14 + 988
    r0 = r4 + 136
    [r0+0] += 1  ; @rmw.add.s12
    r0 = 1178324224
    r6 = r0
    r1 = 1137180672
    iff (r13 u>= r1) {
    r0 = r0 + 0x800000
    r6 = r0
    }
    r15 = r6 / r13 (f)
    r0 = r9 + 0x3F000000
    r0 = r15 + r0 (f)
    r7 = ftoi(r0) (trunc)
    r0 = 1008981770
    r0 = r15 * r0 (f)
    r0 = ftoi(r0) (trunc)
    [sp+44] = r0
    r0 += 2  ; @add.ri.u5
    r2 = r0 + r7
    r0 = r7 - r0  #
    [sp+60] = r2
    [sp+68] = r0
    r0 = 96
    iff (r13 u>= r1) {
    r0 = 192
    }
    r0 = 640  #
    [sp+172] = r0
    [sp+160] = r0
    iff (r13 u>= r1) {
    r0 += -128
    [sp+160] = r0
    }
    r0 = 1500
    [sp+152] = r0
    iff (r13 u>= r1) {
    r0 = 640
    [sp+152] = r0
    }
    r0 = 2048
    r5 = r1
    iff (r13 u>= r5) {
    r0 = 1024
    }
    [sp+144] = r0
    call storage_platform_clock  ; @call.xl
    call storage_platform_clock  ; @call.xl
    r1 = [r4+28]
    r0 = r1 + 2048
    iff (r13 u>= r5) {
    r0 = r1
    }
    r2 = r4 + 8
    iff (r13 u>= r5) {
    r2 = r4
    }
    r1 = 274
    r1 = [r14+r1<<2]
    [sp+128] = r2
    r3 = [r2+0]
    r4 = 1
    r2 = [sp+68]
    ifs (r2 < 2) goto L02019350
    [sp+136] = r3
    r2 = 1
    r3 = 1137180672
    iff (r13 u>= r3) {
    r2 = 0
    }
    r2 = r1 >> r2  #
    r1 = [sp+136]
    r1 = r1 - r2  #
    r3 = [sp+152]
    r1 = smin(r1, r3)  #
    r4 = [sp+60]
    r3 = r1 + -16
    r1 = 1066192077
    r1 = r15 * r1 (f)
    r1 = ftoi(r1) (trunc)
    r4 += r1  ; @add.rr
    r3 = r3 - r4  #
    r4 = [sp+160]
    r5 = smin(r3, r4)  #
    r4 = [sp+172]
    r3 = 1061997773
    r3 = r15 * r3 (f)
    r3 = ftoi(r3) (trunc)
    r3 = smax(r3, r4)
    r4 = 2
    ifs (r5 < r3) goto L02019350
    r4 = r1 + 16
    r3 = [sp+60]
    r3 += r5  ; @add.rr
    r3 += r4  #  ; @add.rr.p
    [sp+40] = r3
    [sp+56] = r4
    r4 = 7
    [sp+172] = r3
    ifs (r3 > 1536) goto L02019350
    [sp+36] = r6
    r15 = [sp+44]  ; @ld.w.sp.l
    r3 = r15 + r1  #
    r6 = [sp+136]
    r3 += r7  #  ; @add.rr.p
    r4 = [sp+152]
    r2 += -1
    r2 = r2 - r6
    r4 = ~r4
    r2 = smax(r2, r4)
    r2 += r3  #  ; @add.rr.p
    r3 = [sp+160]
    r2 += 18  ; @add.ri.u5
    r3 = ~r3
    r2 = smax(r2, r3)
    r2 += r6  ; @add.rr
    r2 += -17
    r2 = r2 - r7
    r2 = r2 - r15
    r3 = r2 - r1  #
    r1 = [sp+144]
    r2 = r1 + -1
    r1 = 0
    r6 = 0
    r15 = 4001
    goto L02018e5c
L02018e4a:
    r4 = r3 + r1
    r4 &= r2
    r4 = h[r0+r4<<1] (s)
    r4 = abs(r4)
    r6 = smax(r4, r6)
    r1 += 1  ; @add.ri.u5
L02018e5c:
    r4 = [sp+172]
    ifs (r1 < r4) goto L02018e4a
    [sp+64] = r5
    r1 = -1
L02018e66:
    r1 += 1  ; @add.ri.u5
    r4 = r6 >>> r1
    ifs (r4 > 4000) goto L02018e66
    r4 = 1
    r5 = 1
    if (r1 == 0) goto L02018e7a
    r5 = 0
L02018e7a:
    [sp+32] = r7
    ifs (r6 <= 0) {  ; @ifs.le.ri.s12
    r4 = 0
    }
    r5 &= r4
    r4 = -1
L02018e86:
    if (r5 == 0) goto L02018ea0
    r7 = r4 + 2
    r7 = r6 << r7
    r4 += 1  ; @add.ri.u5
    ifs (r7 < r15) goto L02018e86
    goto L02018ea2
L02018e96:
    r0 = 0
    r13 = 0  #
    r2 = [sp+172]
    r6 = [sp+160]
    goto L02018cb0
L02018ea0:
    r4 = 0
L02018ea2:
    r5 = r9 + 0x3FC00000
    r6 = r13 * r5 (f)
    r5 = 1167867904
    r7 = r5
    iff (r6 u<= r7) {
    r5 = r6
    }
    r6 = 1078530011
    r5 = r5 * r6 (f)  #
    r6 = [sp+36]
    r13 = r5 / r6 (f)
    r6 = r13 * r13 (f)
    r7 = 1018374052
    r7 = r6 * r7 (f)
    r5 = 1029508561
    r7 = r7 + r5 (f)
    r7 = r6 * r7 (f)
    r5 = 1040746633
    r7 = r7 + r5 (f)
    r7 = r6 * r7 (f)
    r5 = 1051372203
    r7 = r7 + r5 (f)
    r6 = r6 * r7 (f)
    r5 = r9 + 0x3F800000
    r15 = r5
    r6 = r6 + r5 (f)
    r5 = r13 * r6 (f)
    r6 = 1060439283
    r6 = r5 / r6 (f)
    r13 = r15 - r6 (f)
    r5 = r5 * r5 (f)
    r7 = r5 + r13 (f)
    r6 = r6 + r15 (f)  #
    [sp+160] = r7
    r6 = r5 + r6 (f)
    r6 = r15 / r6 (f)
    r7 = r5 * r6 (f)
    r7 = r7 + r7 (f)  #
    [sp+120] = r7
    r15 = 0  #
    [sp+112] = r7
    r7 = 3212836864
    r5 = r5 + r7 (f)
    r5 = r5 + r5 (f)
    [sp+152] = r5
    r5 = L01c24790
    goto L02018f7c
L02018f58:
    r5 = r3 + r15
    r5 &= r2
    r5 = h[r0+r5<<1] (s)
    r13 = r5 << r4
    r7 = r5 >>> r1
    if (r1 != 0) goto L02018f6e
    r7 = r13
L02018f6e:
    r5 = L01c24790
    h[r5+r15<<1] = r7
    r15 = r15 + 1
L02018f7c:
    r7 = [sp+172]
    ifs (r15 < r7) goto L02018f58
    r0 = [sp+128]
    r1 = [sp+172]
    r2 = [sp+136]
    r1 = r1 - r2  #
    r0 = [r0+0]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+144]
    if (r0 <= r1) goto L02018fa0
    r0 = r14 + 1128
    [r0+0] += 1  ; @rmw.add.s12
    r4 = 6
    goto L02019350
L02018fa0:
    r0 = r9 + 0x4E000000
    r1 = r0  #
    r0 = [sp+112]
    r0 = r0 * r1 (f)
    r2 = ftoi(r0) (trunc)
    r3 = r2 >>> 31
    d[sp+144] = r3_r2
    r13 = 0  #
    r0 = [sp+120]
    r0 = r0 * r1 (f)
    r2 = ftoi(r0) (trunc)
    r3 = r2 >>> 31
    d[sp+112] = r3_r2
    r15 = 1  #
    r0 = [sp+160]
    r0 = r0 * r6 (f)
    r0 = r0 * r1 (f)
    r2 = ftoi(r0) (trunc)
    r3 = r2 >>> 31
    d[sp+104] = r3_r2
    r0 = [sp+152]
    r0 = r0 * r6 (f)
    r4 = h[r5+0] (s)
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    r1 = r0 >>> 31
    d[sp+136] = r1_r0
    r5 = r4 >>> 31
    r0 = 0
    r5_r4 <<= 16  #
    [sp+48] = r0
    d[sp+160] = r5_r4
    r2 = 0
    r1_r0 = r5_r4  #
    [sp+52] = r2
    d[sp+96] = r5_r4
    d[sp+128] = r5_r4
    r7_r6 = r5_r4
    goto L020191b4
L02019018:
    r15 = L01c24790
    d[sp+152] = r5_r4
    r4 = h[r15+r13<<1] (s)
    r5 = r4 >>> 31
    r5_r4 <<= 16
    d[sp+120] = r3_r2
    r3_r2 = d[sp+128]
    r0 = r4 + r2
    d[sp+72] = r5_r4
    r1 = r5 + r3 + c
    d[sp+128] = r7_r6
    r7_r6 = d[sp+112]
    r4 = r0 * r7
    r3_r2 = r0 * r6 (u)
    r4 += r3  ; @add.rr
    r0 = r1 * r6
    r3 = r4 + r0
    r5_r4 = d[sp+144]
    r1_r0 = d[sp+128]
    r15 = r0 * r5
    r7_r6 = r5_r4
    r5_r4 = r0 * r6 (u)
    r15 += r5
    r1 *= r6
    r5 = r15 + r1
    r0 = r2 + r4
    r1 = r3 + r5 + c
    d[sp+88] = r1_r0
    r3_r2 = d[sp+136]
    r7_r6 = d[sp+152]
    r4 = r6 * r3
    r1_r0 = r3_r2
    r3_r2 = r6 * r0 (u)
    r4 += r3  ; @add.rr
    r5 = r7 * r0
    r3 = r4 + r5
    r7_r6 = d[sp+104]
    r5_r4 = d[sp+160]
    r15 = r4 * r7
    d[sp+160] = r5_r4
    r1_r0 = r7_r6
    r7_r6 = r4 * r0 (u)
    r15 += r7
    r5_r4 = d[sp+160]
    r5 *= r0
    r7 = r15 + r5
    r4 = r6 + r2
    r5 = r7 + r3 + c
    r1_r0 = d[sp+88]
    r2 = r0 - r4
    r3 = r1 - r5 - !c
    r3_r2 >>>= 29
    r5_r4 = d[sp+160]
    r0 = r2 + r4
    d[sp+88] = r3_r2
    r1 = r3 + r5 + c
    r3_r2 = d[sp+112]
    r6 = r0 * r3
    r5_r4 = r0 * r2 (u)
    r6 += r5  ; @add.rr
    r0 = r1 * r2
    r5 = r6 + r0
    r3_r2 = d[sp+152]
    r1_r0 = d[sp+144]
    r15 = r2 * r1
    r7_r6 = r2 * r0 (u)
    r15 += r7
    r1_r0 = d[sp+144]
    r1 = r3 * r0
    r7 = r15 + r1
    r0 = r4 + r6
    r1 = r5 + r7 + c
    r3_r2 = d[sp+120]
    r5_r4 = d[sp+136]
    r15 = r2 * r5
    r5_r4 = r2 * r4 (u)
    r15 += r5
    r7_r6 = d[sp+136]
    r7 = r3 * r6
    r5 = r15 + r7
    r3_r2 = d[sp+96]
    r7_r6 = d[sp+104]
    r15 = r2 * r7
    [sp+160] = r13  ; @st.w.sp.l
    r13 = r3 * r6
    r3_r2 = r2 * r6 (u)
    r6 = r3 + r15
    r3 = r6 + r13
    r13 = [sp+160]  ; @ld.w.sp.l
    r6 = r2 + r4
    r7 = r3 + r5 + c  #
    r2 = [sp+56]
    r4 = r0 - r6
    r5 = r1 - r7 - !c
    r1_r0 = r5_r4
    r1_r0 >>>= 29
    d[sp+80] = r1_r0
    ifs (r13 < r2) goto L02019188
    r5_r4 >>>= 43  #
    r2 = [sp+52]
    r0 = L01c24790
    h[r0+r2<<1] = r4
    r3 = [sp+48]
    r3 += r4  ; @add.rr
    [sp+48] = r3
    r2 += 1  ; @add.ri.u5
    [sp+52] = r2
L02019188:
    r15 = 1
    r5_r4 = d[sp+128]
    r3_r2 = d[sp+120]
    r7_r6 = d[sp+72]
    r13 = r13 + 1
    r1_r0 = d[sp+152]
    d[sp+160] = r1_r0
    d[sp+96] = r3_r2
    d[sp+128] = r5_r4
    r5_r4 = d[sp+88]
    r1_r0 = d[sp+80]
L020191b4:
    r3_r2 = r1_r0  #
    r0 = [sp+172]
    ifs (r13 < r0) goto L02019018
    r13 = [sp+52]  ; @ld.w.sp.l
    r0 = [sp+48]
    r1 = r0 / r13 (s)
    r0 = 0
    r2 = 0
    goto L020191f2
L020191cc:
    r3 = L01c24790
    r7 = r3
    r3 = h[r7+r2<<1] (u)
    r5 = r3 - r1
    r6 = r5 << 16
    r4 = r5.l (s)
    r3 = 0x0 - r4
    h[r7+r2<<1] = r5
    ifs (r6 >= 0) {  ; @ifs.ge.ri.s12
    r3 = r4
    }
    r0 = smax(r3, r0)
    r2 += 1  ; @add.ri.u5
L020191f2:
    r5 = [sp+64]
    ifs (r2 < r13) goto L020191cc
    r4 = 3
    r6 = [sp+32]
    ifs (r0 < 8) goto L02019350
    r1 = -1
L02019202:
    r1 += 1  ; @add.ri.u5
    r2 = r0 >>> r1
    ifs (r2 > 900) goto L02019202
    if (r1 == 0) goto L0201922c
    r0 = 0
    goto L02019228
L02019214:
    r2 = L01c24790
    r3 = r2
    r2 = h[r3+r0<<1] (s)
    r2 >>>= r1
    h[r3+r0<<1] = r2
    r0 += 1  ; @add.ri.u5
L02019228:
    ifs (r0 < r13) goto L02019214
L0201922c:
    r0 = [sp+44]
    r0 += r6  ; @add.rr
    r0 = r0 << 1
    r1 = L01c24790
    r0 += r1  ; @add.rr
    r0 += 4  ; @add.ri.u5
    r2 = 0
    r1 = 0
    goto L0201924c
L02019242:
    r3 = h[r0+r1<<1] (s)
    r3 *= r3
    r2 += r3  ; @add.rr
    r1 += 1  ; @add.ri.u5
L0201924c:
    ifs (r1 < r5) goto L02019242
    r3 = 0
    r1 = 0
    goto L02019266
L02019256:
    r4 = L01c24790
    r4 = h[r4+r1<<1] (s)
    r4 *= r4
    r3 += r4  ; @add.rr
    r1 += 1  ; @add.ri.u5
L02019266:
    ifs (r1 < r5) goto L02019256
    r1 = [sp+68]
    r4 = [sp+60]
    r7 = r4 - r1
    r1 = r7 + 3
    r4 = 7
    ifs (r1 > 56) goto L02019350
    r5 = L01c24790
    r4 = r5  #
    r6 = [sp+60]
    [sp+152] = r7
    goto L02019300
L02019286:
    r13 = 0  #
    r1 = [sp+60]
    r1 = r1 - r6
    [sp+160] = r1
    r1 = 0
    [sp+172] = r4
    r5 = [sp+64]
    goto L020192a6
L02019296:
    r7 = h[r0+r13<<1] (s)
    r15 = h[r4++=2] (s)
    r7 *= r15
    r1 += r7  ; @add.rr
    r13 = r13 + 1
L020192a6:
    ifs (r13 < r5) goto L02019296
    r7 = r3 + r2
    r4 = 0
    ifs (r7 > 0) {  ; @ifs.gt.ri.s12
    r4 = itof(r7)
    r1 = itof(r1)
    r1 = r1 + r1 (f)
    r4 = r1 / r4 (f)
    }
    r7 = 1397  #
    r5 = [sp+68]
    r1 = r6 - r5
    r1 = r1 << 2
    r1 += r14
    [r1+r7<<2] = r4
    ifs (r6 <= r5) goto L020192f4
    r1 = [sp+40]
    r1 = r1 - r6  #
    r5 = [sp+160]
    r4 = L01c24790
    r1 = h[r4+r1<<1] (s)
    r4 = h[r4+r5<<1] (s)
    r1 *= r1
    r1 += r3  ; @add.rr
    r3 = r4 * r4
    r3 = r1 - r3
L020192f4:
    r15 = 1  #
    r7 = [sp+152]
    r4 = [sp+172]
    r4 += 2  ; @add.ri.u5
    r6 += -1
L02019300:
    r1 = [sp+68]
    ifs (r6 >= r1) goto L02019286
    r2 = r14 + 5592  #
    r6 = [sp+36]
    r3 = 1
    r0 = 0
    goto L0201932c
L02019312:
    r1 = r0 << 2
    r1 += r14  #
    r5 = [r2++=4]
    r4 = 1397
    r4 = [r1+r4<<2]
    r1 = r3
    iff (r5 u<= r4) {
    r1 = r0
    }
    r3 += 1  ; @add.ri.u5
    r0 = r1
L0201932c:
    ifs (r3 <= r7) goto L02019312
    r4 = 4
    if (r0 == 0) goto L02019350
    if (r0 == r7) goto L02019350
    r1 = r0 << 2
    r1 += r14
    r2 = 1397
    r7 = [r1+r2<<2]
    r4 = 5
    r2 = r9 + 0x3F400000
    iff (r7 u>= r2) goto L0201a176
L02019350:
    r1 = 1
    if (r4 != 7) {  ; @if.ne.ri.s12
    r1 = 0
    }
    r0 = r14 + 1132
    [r0+0] += r1
    r1 = 1
    r2 = 1
    if (r4 != 2) {  ; @if.ne.ri.s12
    r1 = 0
    }
    [r0+4] += r1
    r1 = 1
    if (r4 != 4) {  ; @if.ne.ri.s12
    r1 = 0
    }
    [r0+8] += r1
    r1 = 1
    if (r4 != 3) {  ; @if.ne.ri.s12
    r1 = 0
    }
    if (r4 != 5) {  ; @if.ne.ri.s12
    r2 = 0
    }
    r1 |= r2
    [r0+12] += r1
L0201938e:
    r0 = 8
    b[r14+6] = r0
    call state_queries_tenfold_word
    r2 = L01c1f180
    r3 = [++r2=88]
    r13 = r0  #
    r1 = [r2+16]
    r6 = r1  #
    r5 = [r2+4]
    ifs (r5 >= 0) {  ; @ifs.ge.ri.s12
    r6 = r3
    }
    r0 = 1536
    r7 = b[r14+r0] (u)
    r3 = r7 << 10
    r3 += r6  #  ; @add.rr.p
    r0 = [r2+12]
    r4 = r0
    ifs (r5 >= 0) {  ; @ifs.ge.ri.s12
    r4 = r5
    }
    r5 = [r2+20]
    if (r4 != r5) goto L02019444
    r2 = [r2+24]
    if (r3 != r2) goto L02019444
    r2 = b[r14+40] (u)
    if (r4 != r0) goto L020193e2
    if (r6 != r1) goto L020193e2
    if (r7 == r2) goto L02019456
L020193e2:
    r0 = 2000
    if (r7 == r2) {
    r0 = 10000
    }
    r1 = [r14+788]
    r5 = r13 - r1
    if (r5 < r0) goto L02019456
    r0 = 150
    call storage_coordination_ready_threshold
    r1 = r5 >> 5
    if (r1 > 1874) goto L0201940a
    if (r0 == 0) goto L02019456
L0201940a:
    r0 = b[r14+40] (u)
    [sp+208] = r0
    r0 = L01c1f180
    r0 += 100
    r5 = [r0+4]
    r15 = [r0+0]
    [r0+] = {r6, r4}
    b[r14+40] = r7
    r0 = 0
    call settings_store_global_save
    if (r0 == 0) goto L02019456
    r0 = L01c1f180
    [r0+100] = r15
    [r0+104] = r5
    r0 = [sp+208]
    b[r14+40] = r0
    goto L02019452
L02019444:
    r0 = L01c1f180
    [r0+108] = r4
    [r0+112] = r3
L02019452:
    [r14+788] = r13
L02019456:
    call state_queries_tenfold_word
    r1 = [r14+224]
    r4 = r0
    r0 = r4 - r1
    r15 = L02035810
    r5 = L01c1f180
    r6 = 1
    ifs (r0 < 0) goto L02019486
    if (r1 == 0) goto L0201947a
    call flash_helpers_record_tick
L0201947a:
    r0 = 60000
    r0 += r4  ; @add.rr
    [r14+224] = r0
L02019486:
    call state_queries_tenfold_word
    r1 = [r5+232]
    r2 = [r14+792]
    r4 = r0
    if (r1 == r2) goto L020194ae
    [r14+792] = r1
    r0 = 310
    r0 = [r14+r0<<2]
    if (r0 == 0) goto L020194ae
    r0 = 1248
    b[r14+r0] = r6
L020194ae:
    r0 = [r14+796]
    r0 = r4 - r0
    ifs (r0 < 0) goto L020194fa
    r0 = r14 + 1228
    r2 = [r0+8]
    r3 = [r0+16]
    r1 = 1
    if (r2 == r3) {
    r1 = 0
    }
    r2 = 1248
    r2 = b[r14+r2] (u)
    r1 |= r2
    if ((r1 & 1) == 0) goto L020194f2
    r0 = b[r0+0] (u)
    if ((r0 & 1) == 0) goto L020194f2
    r1 = 308  #
    r0 = [r5+24]
    r1 = [r14+r1<<2]
    r0 = r0 - r1
    r0 = r0 * 0xA
    if (r0 >= 2000) goto L020195f4
L020194f2:
    r0 = 800
    b[r14+r0] = r9
L020194fa:
    r4 = h[r14+82] (u)
    if (r4 == 0) goto L0201974c
    r0 = b[r14+60] (u)
    if (r0 == 0) goto L0201974c
    call console_helpers_now_ms
    r1 = r14 + 1292
    r15 = [r1+0]
    r2 = b[r14+59] (u)
    r13 = r0  #
    r3 = [r1+40]
    r6 = 0
    r0 = 1
    if (r15 != r3) {
    r0 = 0
    }
    if (r15 == 0) goto L0201955c
    r0 |= r2
    if (r0 != 0) goto L0201955c
    r0 = r13 - r15
    r6 = 3
    r2 = 9999
    ifs (r0 > r2) goto L0201955c
    r1 = [r1+36]
    r1 = r13 - r1
    r6 = 2
    ifs (r1 <= 249) {  ; @ifs.le.ri.s12
    r6 = 1
    }
    r0 = r0 + -300
    r0 = r0 >> 2
    if (r0 >= 1175) {
    r6 = 1
    }
L0201955c:
    r0 = b[r14+64] (u)
    r7 = r6 + -1
    if (r0 == 0) goto L020195b6
    if (r7 < 2) goto L020195b6
    r0 = b[r14+59] (u)
    if (r0 != 0) goto L02019588
    r0 = 300
    r0 = [r14+r0<<2]
    r0 = r13 - r0
    ifs (r0 > 1499) goto L02019588
    r0 = b[r14+62] (u)
    if (r0 == 0) goto L020195b6
L02019588:
    b[r14+64] = r9
    r0 = L02035810
    r3 = r0 + 1174
    r0 = 11
    r1 = 2
    r2 = r4
    call L0204c744  ; @call.xl
    r0 = 20
    r1 = 3
    r3 = 251
    r2 = 2120
    r2 = r4  #
    [sp] = r2
    call L0204c744  ; @call.xl
L020195b6:
    if (r6 == 2) {  ; @if.eq.ri.s12
    r0 = r14 + 1328
    [r0+0] = r13
    [r0+8] += 1  ; @rmw.add.s12
    call L020522c0  ; @call.xl
    }
    if (r7 < 2) goto L0201974c
    if (r6 != 3) goto L0201970a
    r5 = r14 + 1332
    [r5+0] = r15
    r2 = [r5+4]
    r0 = 32
    r1 = -12
    call storage_coordination_notify
    r0 = r4
    call console_helpers_ble_drop
    r0 = r13 | 0x1
    [r5+8] = r0
    goto L0201974c
L020195f4:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r14 + 58
L02019600:
    testset b[r0]
    ifeq goto L02019600
    csync
    r0 = 309
    r6 = [r14+r0<<2]
    r0 = 1248
    r0 = b[r14+r0] (u)
    [sp+208] = r6
    if (r0 != 0) goto L0201965a
    r0 = 310
    r5 = [r14+r0<<2]
    r0 = L01c25438
    r13 = r0 + 40
    if (r5 != 0) goto L02019632
    r13 = r5
L02019632:
    if (r5 == 0) goto L0201964a
    r0 = r14 + 6592
    r2 = 380
    r1 = r13
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0201a13e
L0201964a:
    r7 = r14 + 6592
    r0 = r7
    call bond_records_and_prints_bond_count
    if (r0 == 0) goto L0201a10a
L0201965a:
    r6 = r14 + 6592
    r1 = 380
    r0 = r6
    call audio_pause_crc32
    r2 = 1111968596
    r3 = r1
    r1 = L01c25438
    r5 = r1
    d[r5+0] = r3_r2
    r0 = 1282  #
    [r5+8] = r0
    [r5+12] = r0
    r0 = r5 + 16
    r1 = r15 + 833
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = r5 + 22
    rep 9 {
    h[r0++=2] = r9
    }
    r0 = r5 + 40
    r2 = r3
    r1 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r3 = r14 + 1240
    [r3+0] = 0x1A4
    r6 = 1
    b[r3+8] = r6
    csync
    b[r14+58] = r9
    call storage_coordination_irq_leave  ; @call.xl
    r1 = 800
    r0 = b[r14+r1] (u)
    r13 = [r3+0]
    r5 = 1
    if (r0 == 0) {  ; @if.eq.ri.s12
    b[r14+r1] = r6
    [r14+804] = r4
    r0 = r4
    } else {
    r0 = [r14+804]
    }
    r1 = [r14+280]
    r7 = r4 - r0
    if (r1 == 0) goto L02019872
    r0 = 150
    call storage_coordination_ready_threshold
    r1 = 1
    if (r0 == 0) goto L020196f4
    r1 = 0
L020196f4:
    if (r0 != 0) goto L020196f8
    r6 = r0
L020196f8:
    r0 = r7 >> 4
    if (r0 > 1874) goto L02019872
    if (r1 == 0) goto L02019872
    r0 = r4 + 500
    goto L020198ce
L0201970a:
    r0 = 335
    r0 = [r14+r0<<2]
    if (r0 == 0) goto L0201971e
    r0 = r13 - r0
    ifs (r0 < 2000) goto L0201974c
L0201971e:
    r2 = b[r14+59] (u)
    r0 = 300
    r0 = [r14+r0<<2]
    r1 = b[r14+62] (u)
    if (r1 != 0) goto L02019744
    r1 = 30000
    if (r2 != 0) goto L0201973a
    r1 = 15000
L0201973a:
    r0 = r13 - r0
    ifs (r0 >= r1) goto L0201a156
L02019744:
    r0 = 335
    [r14+r0<<2] = r9
L0201974c:
    r0 = 9
    b[r14+6] = r0
    call preset_storage_preparation_prepare
    r0 = 716
    r0 = b[r14+r0] (u)
    r13 = 321
    r6 = 18
    r7 = 3440
    if (r0 == 0) goto L020198f6
    r0 = 2
    call command_services_count_matches
    r1 = 776
    r2 = b[r14+r1] (u)
    r1 = 0
    if (r2 == 0) goto L020197a8
    r2 = L01c1f180
    r1 = [r2+208]
    r1 = 0x1E - r1
    if (r1 > 2) goto L02019798
    r4 = 1
    if (r0 != 0) goto L020197b4
    r4 = r0
    goto L020197b4
L02019798:
    r1 = [r2+220]
    r2 = 0x10 - r1
    r1 = 1
    if (r2 >= 2) {  ; @if.ge.ri.s12
    r1 = 0
    }
L020197a8:
    r4 = 1
    if (r0 != 0) goto L020197ae
    r4 = r0
L020197ae:
    if (r0 != 0) goto L020197b4
    if (r1 == 0) goto L020198f6
L020197b4:
    r0 = 150
    call storage_coordination_ready_threshold
    if (r0 == 0) goto L020198f6
    r0 = [r14+280]
    if (r0 == 0) goto L020197ee
    r0 = 1019
    r0 = [r14+r0<<2]
    r1 = [r14+408]
    r0 = r0 - r1
    r1 = 1331
    r0 *= r1
    r1 = 299999
    if (r0 > r1) goto L020197ee
    r0 = 5000
    call storage_coordination_ready_threshold
    if (r0 == 0) goto L020198f6
L020197ee:
    if (r4 == 0) goto L020198d4
    r0 = 3496
    r0 = b[r14+r0] (u)
    r4 = r0 + 1
    r1 = 0
L020197fc:
    if (r1 > 17) goto L020198f6
    r0 = r4 + r1
    r2 = r0 / r6 (u)
    r2 = r2 * 0x12
    r0 = r0 - r2
    r2 = r0 + r14
    r2 = b[r2+r7] (u)
    r1 += 1  ; @add.ri.u5
    if (r2 != 2) goto L020197fc
    r1 = r14 + 3500
    [r1+0] += 1  ; @rmw.add.s12
    call preset_storage_preparation_erase_block
    r15 = r0
    r5 = 0
    r1 = 0
    goto L02019858
L0201982e:
    r0 = r4 + r5
    r1 = r0 / r6 (u)
    r1 = r1 * 0x12
    r0 = r0 - r1
    r1 = r0 + r14
    r2 = b[r1+r7] (u)
    r1 = 0
    if (r2 > 5) goto L02019856
    r3 = 38
    r2 = r3 & (1 << r2)
    if (r2 == 0) goto L02019856
    call preset_storage_block
    r1 = r0
L02019856:
    r5 += 1  ; @add.ri.u5
L02019858:
    if (r5 > 17) goto L0201985e
    if (r1 == 0) goto L0201982e
L0201985e:
    r0 = uextra(r15, p:0, l:8)
    r2 = r0 | 0x100
    if (r15 == 0) {  ; @if.eq.ri.s12
    r2 = 257
    }
    r0 = 19
    goto L020198f2
L02019872:
    r0 = 776
    r0 = b[r14+r0] (u)
    if (r0 != 0) goto L02019888
    call mode_and_settings_record_scan
    r0 = 776
    b[r14+r0] = r5
L02019888:
    r1 = r7 >> 5
    r0 = 1
    if (r1 <= 1874) {
    r0 = 0
    }
    r5 = r0 | r6
    r0 = L01c25438
    r1 = r13
    call settings_store_block_write
    r7 = r0
    if (r5 != 1) goto L020198ba
    if (r7 != -9) goto L020198ba
    r0 = L01c25438
    r1 = r13
    call settings_store_compaction
    r7 = r0
L020198ba:
    r0 = 32
    r1 = -8
    r2 = r7
    call storage_coordination_notify
    if (r7 == 0) goto L0201a0f4
    r0 = r4 + 2000
L020198ce:
    [r14+796] = r0
    goto L020194fa
L020198d4:
    r0 = 88
    r1 = L01c1f180
    [r1+228] = r0
    r1_r0 = 0
    call settings_store_compaction
    r0 = r0.b0 (u)
    r2 = r0 | 0x200
    r0 = 19
    r1 = 0xFE000
L020198f2:
    call storage_coordination_notify
L020198f6:
    r0 = 10
    b[r14+6] = r0
    r0 = 11
    b[r14+6] = r0
    r0 = L01c3443c
    r0 = [r0+0]
    if (r0 == 0) goto L020199a2
    [sp+408] = r9
    [sp+404] = r9
    r0 = sp + 408
    r1 = sp + 404
    call slot_queries_pending_request  ; @call.xl
    r4 = r0
    ifs (r4 < 0) goto L020199a2
    call preset_application_effect_type  ; @call.xl
    r1 = [sp+408]
    r6 = r0
    if (r1 == 3) goto L02019954
    if (r1 != 1) goto L0201995c
    call audio_pause_pause_audio
    r1 = [sp+404]
    r0 = r4
    call slot_queries_slot_set_mode  ; @call.xl
    if (r0 == 0) goto L02019978
    call audio_pause_resume_audio
    goto L020199a2
L02019954:
    r2 = [sp+404]
    r1 = 3
    goto L0201996e
L0201995c:
    r1 = 0
    r0 = r4
    call slot_commands_enable_command
    if (r0 != 0) goto L020199a2
    r2 = [sp+404]
    r1 = [sp+408]
L0201996e:
    r0 = r4
    call slot_queries_post_request  ; @call.xl
    goto L0201998c
L02019978:
    r2 = [sp+404]
    r1 = [sp+408]
    r0 = r4
    call slot_queries_post_request  ; @call.xl
    call audio_pause_resume_audio
L0201998c:
    r0 = [sp+408]
    r1 = r6 << 8
    r2 = [sp+404]
    r1 |= r4
    r0 = r0 << 16
    r1 |= r0
    r0 = 30
    call storage_coordination_notify
L020199a2:
    call stereo_budget_poll_budget  ; @call.xl
    r15 = L02035810
    r7 = 1
    if (r0 == 0) goto L020199c6
    r0 = L01c341a8
    r2 = [r0+0]
    r0 = 30
    r1 = 458751
    call storage_coordination_notify
L020199c6:
    r0 = 12
    b[r14+6] = r0
    r0 = b[r14+136] (u)
    if (r0 == 0) goto L020199da
    call state_queries_both_set
    if (r0 != 0) goto L020199e2
    goto L02019ff4
L020199da:
    r0 = [sp+228]
    if (r0 == 0) goto L02019ff4
L020199e2:
    call state_queries_tenfold_word
    r1 = [r14+188]
    r5 = r0
    if (r1 == 0) goto L02019ff4
    r0 = [r14+228]
    r0 = r5 - r0
    if (r0 >= r1) goto L02019a68
    r0 = 952
    r0 = b[r14+r0] (u)
    if (r0 != 0) goto L02019a10
    r0 = b[r14+50] (u)
    if (r0 == 0) goto L02019ff4
L02019a10:
    call flash_helpers_link_ready
    if (r0 == 0) goto L02019ff4
    r4 = r14 + 2868
    r0 = 64
    b[r4+0] = r0
    r0 = 75
    b[r4+1] = r0
    r0 = 32
    r0 = 872  #
    b[r4+2] = r0
    r0 = b[r14+r0] (u)
    if (r0 != 0) goto L02019e9a
    r0 = 952
    r0 = b[r14+r0] (u)
    if ((r0 & 0x1) != 0) goto L02019e9a
    r0 = L01c34468
    r1 = [r0+0]
    r0 = [r14+948]
    if (r1 != r0) goto L02019e9a
    r5 = 32
    r0 = r14 + 2871
    r1 &= 2147483647
    call sort_and_format_decimal_digits
    r1 = r0
    goto L02019eaa
L02019a68:
    [r14+228] = r5
    call console_reports_level_record
    r1 = 6588
    r0 = b[r14+r1] (u)
    if (r0 == 0) goto L02019c58
    r0 = 1583
    r0 = [r14+r0<<2]
    r1 = 1073
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1584
    r0 = [r14+r0<<2]
    r1 = 1074
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1588
    r0 = [r14+r0<<2]
    r1 = 1078
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1602
    r0 = [r14+r0<<2]
    r1 = 1092
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1603
    r0 = [r14+r0<<2]
    r1 = 1093
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1604
    r0 = [r14+r0<<2]
    r1 = 1094
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1605
    r0 = [r14+r0<<2]
    r1 = 1095
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1589
    r0 = [r14+r0<<2]
    r1 = 1079
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1590
    r0 = [r14+r0<<2]
    r1 = 1080
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1591
    r0 = [r14+r0<<2]
    r1 = 1081
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1592
    r0 = [r14+r0<<2]
    r1 = 1082
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1593
    r0 = [r14+r0<<2]
    r1 = 1083
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1594
    r0 = [r14+r0<<2]
    r1 = 1084
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1598
    r0 = [r14+r0<<2]
    r1 = 1088
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1599
    r0 = [r14+r0<<2]
    r1 = 1089
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1600
    r0 = [r14+r0<<2]
    r1 = 1090
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1587
    r0 = [r14+r0<<2]
    r1 = 1077
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1597
    r0 = [r14+r0<<2]
    r1 = 1087
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1607
    r0 = [r14+r0<<2]
    r1 = 1097
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1608
    r0 = [r14+r0<<2]
    r1 = 1098
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1609
    r0 = [r14+r0<<2]
    r1 = 1099
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1610
    r0 = [r14+r0<<2]
    r1 = 1100
    r1 = [r14+r1<<2]
    if (r1 != r0) goto L02019c48
    r0 = 1612
    r0 = [r14+r0<<2]
    r1 = 1102
    r1 = [r14+r1<<2]
    if (r1 == r0) goto L02019c5c
L02019c48:
    r1 = 3292
    r0 = h[r14+r1<<1] (u)
    r0 += 1  ; @add.ri.u5
    h[r14+r1<<1] = r0
    goto L02019c5c
L02019c58:
    b[r14+r1] = r7
L02019c5c:
    r0 = r14 + 6324
    r1 = r14 + 4284
    rep 32 {
    r2 = [r1++=4]
    [r0++=4] = r2
    }
    r0 = 6589
    r0 = b[r14+r0] (u)
    if (r0 == 0) goto L02019d8c
    r0 = 3293
    r0 = h[r14+r0<<1] (u)
    r1 = 3292
    r1 = h[r14+r1<<1] (u)
    if (r1 != r0) goto L02019d8c
    r0 = 1645
    r0 = [r14+r0<<2]
    r0 = r5 - r0
    if (r0 > 1999) goto L02019d8c
    r0 = 6590
    r0 = b[r14+r0] (u)
    if (r0 < 2) goto L02019cc2
    r0 = 1096
    r0 = [r14+r0<<2]
    r2 = 1638
    r2 = [r14+r2<<2]
    r1 = r0 >>> 31
    r3 = r2 >>> 31
    call sort_and_format_wide_distance
    if (r0 > 9) goto L02019d8c
L02019cc2:
    r0 = 1071
    r0 = [r14+r0<<2]
    r2 = 1613
    r2 = [r14+r2<<2]
    r1 = r0 >>> 31
    r3 = r2 >>> 31
    call sort_and_format_wide_distance
    if (r0 > 9) goto L02019d8c
    r0 = 1072
    r0 = [r14+r0<<2]
    r2 = 1614
    r2 = [r14+r2<<2]
    r1 = r0 >>> 31
    r3 = r2 >>> 31
    call sort_and_format_wide_distance
    if (r0 > 9) goto L02019d8c
    r0 = 1091
    r0 = [r14+r0<<2]
    r2 = 1633
    r2 = [r14+r2<<2]
    r1 = r0 >>> 31
    r3 = r2 >>> 31
    call sort_and_format_wide_distance
    if (r0 > 9) goto L02019d8c
    r0 = 1076
    r1 = [r14+r0<<2]
    r0 += -1
    r0 = [r14+r0<<2]
    call ir_reload_and_leaves_percent
    r1 = 1618
    r1 = [r14+r1<<2]
    r2 = 1617
    r2 = [r14+r2<<2]
    r4 = r0
    r0 = r2
    call ir_reload_and_leaves_percent
    r2 = r0
    r1 = 0
    r3 = 0
    r0 = r4
    call sort_and_format_wide_distance
    if (r0 > 1) goto L02019d8c
    r0 = 1086
    r1 = [r14+r0<<2]
    r0 += -1
    r0 = [r14+r0<<2]
    call ir_reload_and_leaves_percent
    r1 = 1628
    r1 = [r14+r1<<2]
    r2 = 1627
    r2 = [r14+r2<<2]
    r4 = r0
    r0 = r2
    call ir_reload_and_leaves_percent
    r2 = r0
    r1 = 0
    r3 = 0
    r0 = r4
    call sort_and_format_wide_distance
    if (r0 < 2) goto L02019ff4
L02019d8c:
    call flash_helpers_link_ready
    if (r0 == 0) goto L02019e94
    r0 = 6590  #
    [sp+208] = r5
    r0 = b[r14+r0] (u)
    r0 = 3292  #
    [sp+204] = r0
    r13 = h[r14+r0<<1] (u)
    r3 = r14 + 2928
    r0 = 64
    r7 = r14 + 4284  #
    b[r3+2] = r0
    r0 = 76
    r1 = 9999  #
    b[r3+3] = r0
    r5 = 32
    b[r3+4] = r5
    r0 = [r7+0]
    call sort_and_format_bounded_minimum
    r1 = r0
    r0 = r3 + 5
    call pool_callbacks_digits_text
    r3 = r0
    r1 = 9999  #
    b[r3++=1] = r5
    r0 = [r7+4]
    call sort_and_format_bounded_minimum
    r1 = r0
    r0 = r3
    call pool_callbacks_digits_text
    b[r0++=1] = r5
    r1 = [r7+16]
    r4 = 999999
    r1 = umin(r1, r4)
    call pool_callbacks_digits_text
    r6 = 47
    b[r0++=1] = r6
    r1 = [r7+20]
    r1 = umin(r1, r4)
    call pool_callbacks_digits_text
    b[r0++=1] = r5
    r1 = [r7+56]
    r1 = umin(r1, r4)
    call pool_callbacks_digits_text
    b[r0++=1] = r6
    r1 = [r7+60]
    r1 = umin(r1, r4)
    call pool_callbacks_digits_text
    r3 = r0
    r0 = 1091  #
    b[r3++=1] = r5
    r0 = [r14+r0<<2]
    r1 = 0
    call sort_and_format_bounded_minimum
    r1 = r0
    r0 = r3
    call pool_callbacks_digits_text
    r1 = r13  #
    b[r0++=1] = r5
    call pool_callbacks_digits_text
    r3 = r0  #
    r0 = [sp+204]
    if (r0 < 2) goto L02019e62
    r0 = 1096  #
    b[r3++=1] = r5
    r0 = [r14+r0<<2]
    r1 = 9999
    call sort_and_format_bounded_minimum
    r1 = r0
    r0 = r3
    call pool_callbacks_digits_text
    r3 = r0
L02019e62:
    r4 = [sp+208]
    r0 = 10
    r0 = r14 + 2930  #
    b[r3++=1] = r0
    r1 = r3 - r0
    call flash_helpers_link_send
    if (r0 == 0) goto L02019fe6
    r0 = r14 + 6452
    rep 32 {
    r1 = [r7++=4]
    [r0++=4] = r1
    }
    r0 = r14 + 6580
    r1 = h[r0+4] (u)
    h[r0+6] = r1
    [r0+0] = r4
    r7 = 1
    r0 = r14 + 236  #
    b[r0+9] = r7
    goto L02019fec
L02019e94:
    r0 = r14 + 232
    goto L02019ff0
L02019e9a:
    r5 = 32
    r0 = 2871
    r1 = 45
    b[r14+r0] = r1
    r1 = r14 + 2872
L02019eaa:
    r13 = r14 + 2722
    r7 = 0
    r15 = 0
    goto L02019f6a
L02019eb4:
    b[r1+0] = r5
    r0 = b[r13+-2] (u)
    b[r1+1] = r0
    r2 = b[r13+-2] (u)
    r0 = r1 + 2
    if (r2 == 97) goto L02019f00
    if (r2 == 101) goto L02019f14
    if (r2 == 115) goto L02019f38
    if (r2 == 113) goto L02019f3e
    if (r2 != 112) goto L02019f5e
    r1 = b[r13+-1] (u)
    call sort_and_format_decimal_digits
    r1 = 46
    b[r0++=1] = r1
    r1 = b[r13+0] (u)
    call sort_and_format_decimal_digits
    r6 = r0
    r0 = 61
    b[r6++=1] = r0
    r1 = b[r13+0] (u)
    r0 = b[r13+-1] (u)
    call preset_application_parameter  ; @call.xl
    goto L02019f56
L02019f00:
    r2 = 61
    b[r0+0] = r2
    call slot_commands_requested
    r2 = 49
    if (r0 != 0) goto L02019f0e
    r2 = 48
L02019f0e:
    b[r1+3] = r2
    r0 = r1 + 4
    goto L02019f5e
L02019f14:
    r1 = b[r13+-1] (u)
    call sort_and_format_decimal_digits
    r6 = r0
    r0 = 61
    b[r6+0] = r0
    r0 = b[r13+-1] (u)
    call preset_application_effect_enabled  ; @call.xl
    r1 = 49
    if (r0 != 0) goto L02019f32
    r1 = 48
L02019f32:
    b[r6+1] = r1
    r0 = r6 + 2
    goto L02019f5e
L02019f38:
    r1 = b[r13+-1] (u)
    goto L02019f5a
L02019f3e:
    r1 = b[r13+-1] (u)
    call sort_and_format_decimal_digits
    r6 = r0
    r0 = 61
    b[r6++=1] = r0
    r0 = b[r13+-1] (u)
    call audio_measurement_control_value  ; @call.xl
L02019f56:
    r1 = r0
    r0 = r6
L02019f5a:
    call sort_and_format_decimal_digits
L02019f5e:
    r13 = r13 + 3
    r7 += 1  ; @add.ri.u5
    r15 = r15 + 1
    r1 = r0
L02019f6a:
    r0 = b[r14+50] (u)
    ifs (r15 >= r0) goto L02019f78
    r0 = r1 - r4
    ifs (r0 <= 46) goto L02019eb4
L02019f78:
    b[r14+51] = r7
    r0 = 10
    r0 = r4  #
    b[r1++=1] = r0
    r1 = r1 - r4
    call flash_helpers_link_send
    r15 = L02035810
    r7 = 1
    r13 = 321
    if (r0 == 0) goto L02019ff4
    r0 = b[r14+51] (u)
    r1 = b[r14+50] (u)
    r2 = r14 + 2720
    r3 = r0 * 0x3
    r4 = r0
    goto L02019fba
L02019faa:
    r5 = r2 + r3
    r6 = r2
    rep 3 {
    r7 = b[r5++=1] (u)
    b[r6++=1] = r7
    }
    r7 = 1
    r2 += 3  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02019fba:
    ifs (r4 < r1) goto L02019faa
    r0 = r1 - r0
    b[r14+50] = r0
    if ((r0 & 0xFF) != 0) goto L02019ff4
    r0 = L01c34468
    r1 = 952  #
    r0 = [r0+0]
    b[r14+r1] = r9
    r1 += -80
    b[r14+r1] = r9
    [r14+948] = r0
    goto L02019ff4
L02019fe6:
    r0 = r14 + 232
    r7 = 1
L02019fec:
    r13 = 321
L02019ff0:
    [r0+0] += 1  ; @rmw.add.s12
L02019ff4:
    call state_queries_tenfold_word
    r1 = [r14+240]
    r0 = r0 - r1
    if (r0 < 500) goto L0201a0e0
    call state_queries_tenfold_word
    r1 = L01c2685c
    r4 = b[r1+0] (u)
    [r14+240] = r0
    r0 = 0
    if (r4 > 15) goto L0201a0d8
    if (r4 == 10) goto L0201a0d8
    r0 = r4 * 0x14
    r5 = r0 + r15
    r0 = 3062
    r6 = [r5+r0<<2]
    r0 = r6
    call L02040ab8  ; @call.xl
    if (r0 == 0) goto L0201a0c4
L0201a036:
    call L02040cd0  ; @call.xl
    ifs (r0 < 0) goto L0201a0d6
    r1 = 3064
    r1 = [r5+r1<<2]
    r2 = L01c26854
    r5 = h[r2+0] (u)
    r2 = 65535
    r2 = umin(r1, r2)
    r3 = umin(r2, r0)
    if (r5 == 0) goto L0201a07c
    r6 = L01c26858
    r6 = b[r6+0] (u)
    if (r6 == r4) goto L0201a07c
    r6 = L01c26850
    r5 *= r3  #
    r6 = h[r6+0] (u)
    r6 *= r2
    if (r5 >= r6) goto L0201a094
L0201a07c:
    r5 = L01c26858
    b[r5+0] = r4
    r5 = L01c26850
    h[r5+0] = r3
    r5 = L01c26854
    h[r5+0] = r2
L0201a094:
    r3 = r3 << 2
    if (r3 >= r2) goto L0201a0d6
    r2 = 373
    r2 = [r14+r2<<2]
    r3 = r7 << r4
    if ((r2 & r3) != 0) goto L0201a0d6
    r2 |= r3
    r3 = 373
    [r14+r3<<2] = r2
    r1 = r1 << 16
    r2 = r1 | r0
    r0 = 31
    r1 = r4
    call storage_coordination_notify
    goto L0201a0d6
L0201a0c4:
    r0 = b[r6++=3] (u)
    if (r0 != 35) goto L0201a0d6
    r0 = r6
    call L02040ab8  ; @call.xl
    if (r0 != 0) goto L0201a036
L0201a0d6:
    r0 = r4 + 1
L0201a0d8:
    r1 = L01c2685c
    b[r1+0] = r0
L0201a0e0:
    call phase3_p3_wdt_clear
    r0 = 13
    b[r14+6] = r0
    r0 = 1
    call L0203feb8  ; @call.xl
    goto L0201a496
L0201a0f4:
    r0 = 311  #
    r1 = [sp+208]
    [r14+r0<<2] = r1
    r0 = 1248
    b[r14+r0] = r9
    goto L020194f2
L0201a10a:
    r6 = 1
    if (r5 == 0) goto L0201a110
    r6 = 0
L0201a110:
    r0 = r7
    call bond_records_and_prints_bit_count
    if (r0 != 0) goto L0201a136
    if (r6 != 0) goto L0201a136
    r0 = r13
    call bond_records_and_prints_bond_count
    r6 = [sp+208]
    if (r0 != 0) goto L0201965a
    r0 = r13
    call bond_records_and_prints_bit_count
    if (r0 != 0) goto L0201965a
    goto L0201a13e
L0201a136:
    r6 = [sp+208]
    if (r0 != 0) goto L0201965a
L0201a13e:
    csync
    b[r14+58] = r9
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 311
    [r14+r0<<2] = r6
    goto L020194f2
L0201a156:
    r0 = r13 | 0x1
    r1 = r14 + 1340
    [r1+0] = r0
    [r1+4] += 1  ; @rmw.add.s12
    r0 = 32
    r1 = -9
    call storage_coordination_notify
    r0 = r4
    call console_helpers_ble_drop
    goto L0201974c
L0201a176:
    r2 = 1396
    r2 = [r1+r2<<2]
    r3 = 1398
    r4 = [r1+r3<<2]
    r1 = r9 + 0xC0000000
    r1 = r7 * r1 (f)
    r1 = r2 + r1 (f)
    r3 = r1 + r4 (f)
    r1 = 0
    r5 = 2961797215
    iff (r3 < r5) {
    r1 = r2 - r4 (f)
    r2 = r9 + 0x3F000000
    r1 = r1 * r2 (f)
    r1 = r1 / r3 (f)
    }
    r2 = r14 + 1148
    [r2+0] += 1  ; @rmw.add.s12
    r2 = r9 + 0x3F000000
    r3 = r2
    r5 = 265
    iff (r1 u<= r3) {
    r2 = r1
    }
    r1 = r3 + 0x80000000
    r3 = r1
    iff (r2 u>= r3) {
    r1 = r2
    }
    r2 = [sp+68]
    r0 += r2  ; @add.rr
    r0 = itof(r0)
    r0 = r0 + r1 (f)
    r13 = r6 / r0 (f)
    call storage_platform_clock  ; @call.xl
    r0 = L01c1f180
    r0 = [r0+144]
    r0 = r13 / r0 (f)  #
    [sp+172] = r7
    r1 = 8388607
    r1 &= r0
    r1 = r1 | 0x3F800000
    r0 = uextra(r0, p:23, l:8)
    r2 = 1068827891
    iff (r1 > r2) {
    r2 = r9 + 0x3F000000
    r1 = r1 * r2 (f)
    r0 += -126
    } else {
    r0 += -127
    }
    r2 = r9 + 0x3F800000
    r7 = r2
    r2 = r1 + r7 (f)
    r3 = 3212836864
    r1 = r1 + r3 (f)
    r1 = r1 / r2 (f)
    r2 = r1 * r1 (f)
    r3 = 1041385765
    r3 = r2 * r3 (f)
    r6 = 1045220557
    r3 = r3 + r6 (f)
    r3 = r2 * r3 (f)
    r6 = 1051372203
    r3 = r3 + r6 (f)
    r2 = r2 * r3 (f)
    r2 = r2 + r7 (f)
    r1 = r1 + r1 (f)
    r1 = r1 * r2 (f)
    r6 = [r14+r5<<2]
    r0 = itof(r0)
    r2 = 1060205080
    r0 = r0 * r2 (f)
    r0 = r0 + r1 (f)
    r1 = r5
    r2 = 1155032957
    r5 = r0 * r2 (f)
    if (r6 == 0) goto L0201a2d6
    r0 = r6
    call sort_and_format_median_word
    r0 = r5 - r0 (f)
    r1 = r7 + 0x28C0000
    iff (r0 > r1) goto L0201a2f6
    r1 = r1 + 0x80000000
    iff (r0 < r1) goto L0201a2f6
    r0 = 266
    [r14+r0<<2] = r9
    r3 = 506
    ifs (r6 >= 5) goto L0201a340
    r0 = r6 << 2
    r6 += 1  ; @add.ri.u5
    r1 = 265
    [r14+r1<<2] = r6
    r0 += r14
    r0 = r0 + 2004
    r7 = r7 + 0x3480000
    goto L0201a360
L0201a2d6:
    r0 = 501
    [r14+r0<<2] = r5
    [r14+r1<<2] = r15
    r0 = r1 + 1
    [r14+r0<<2] = r9
    r0 += 22  ; @add.ri.u5
    [r14+r0<<2] = r5
    r0 = r5
    r7 = r7 + 0x3480000
    goto L0201a386
L0201a2f6:
    r0 = r14 + 1064
    [r0+92] += 1  ; @rmw.add.s12
    r1 = [r0+0]
    r1 += 1  ; @add.ri.u5
    [r0+0] = r1
    r2 = [sp+208]
    ifs (r1 < 3) goto L0201938e
    r0 = 501
    [r14+r0<<2] = r5
    r0 = r14 + 1060
    [r0+0] = r15
    [r0+4] = r9
    r1 = 288
    [r14+r1<<2] = r5
    [r0+100] += 1  ; @rmw.add.s12
    r0 = -1
    r1 = L01c1f180
    [r1+140] = r0
    r0 = r5
    r7 = r7 + 0x3480000
    goto L0201a388
L0201a340:
    r0 = -16
    r7 = r7 + 0x3480000
    goto L0201a35a
L0201a348:
    r1 = r0 + r14
    r2 = [r1+r3<<2]
    r4 = 505
    [r1+r4<<2] = r2
    r0 += 4  ; @add.ri.u5
L0201a35a:
    if (r0 != 0) goto L0201a348
    r0 = r14 + 2020
L0201a360:
    r0 = r6  #
    [r0+0] = r5
    call sort_and_format_median_word
    r2 = 288
    r1 = [r14+r2<<2]
    r0 = r0 - r1 (f)
    r3 = 1053609165
    r0 = r0 * r3 (f)
    r0 = r1 + r0 (f)
    [r14+r2<<2] = r0
L0201a386:
    r2 = [sp+208]
L0201a388:
    r1 = 264
    [r14+r1<<2] = r2
    r1 = r0 - r5 (f)
    r2 = 974613402
    r1 = r1 * r2 (f)
    r2 = r9 + 0x3F800000
    r1 = r1 + r2 (f)
    r1 = r13 * r1 (f)
    r2 = 1167867904
    r2 = r0 + r2 (f)
    r6 = L01c1f180
    r3 = [r6+140]
    r2 = r2 / r7 (f)
    r4 = r9 + 0x3F000000
    r2 = r2 + r4 (f)
    r2 = ftoi(r2) (trunc)
    r2 += 19  ; @add.ri.u5
    ifs (r3 < 0) goto L0201a40a
    if (r2 == r3) goto L0201a40a
    r4 = r3 + -69
    r4 = itof(r4)
    r5 = r7 + 0x80000000
    r4 = r4 * r5 (f)
    r4 = r0 + r4 (f)
    r5 = 1113587712
    r13 = [sp+204]  ; @ld.w.sp.l
    iff (r4 u>= r5) {
    r3 = r2
    }
    r5 = r5 + 0x80000000
    iff (r4 u<= r5) {
    r3 = r2
    }
    r2 = r3
    goto L0201a40e
L0201a40a:
    r13 = [sp+204]  ; @ld.w.sp.l
L0201a40e:
    [r6+140] = r2
    r3 = r14 + 1068
    b[r3+0] = r15
    r4 = r14 + 1164
    r1 = r1 * r7 (f)  #
    [r4+0] = r2
    r5 = r9 + 0x3F000000
    r1 = r1 + r5 (f)
    r1 = ftoi(r1) (trunc)
    r2 += -69
    r2 = itof(r2)  #
    [r4+4] = r1
    r2 = r2 * r7 (f)
    r0 = r0 - r2 (f)
    r1 = r5 + 0x80000000
    r2 = 0
    iff (r0 u>= r2) {
    r1 = r5
    }
    r2 = r5 + 0x2200000
    r0 = r0 * r2 (f)
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    [r4+8] = r0
    r0 = [sp+172]
    r0 = r0 * r7 (f)
    r0 = ftoi(r0) (trunc)
    [r4+12] = r0
    r0 = [r3+8]
    [r4+16] = r0
    r0 = [r3+32]
    [r3+36] = r0
    r0 = [r4+20]
    r0 += 1  ; @add.ri.u5
    [r4+20] = r0
    [r4+24] = r0
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r13  #
    r1 = [r4+28]
    if (r0 > r1) {
    r1 = 298
    [r14+r1<<2] = r0
    }
    goto L0201938e
L0201a496:
    r5 = r11
    r0 = 3
    b[r14+6] = r0
    call link_and_print_link_report
    call link_and_print_link_toggle
    r11 = [r14+r8<<2]
    call phase3_p4_cdc_ready
    r4 = r0
    if (r5 != r11) {
    r4 = 0
    }
    r0 = [sp+228]
    if (r4 == r0) goto L0201a516
    [r14+180] = r9
    r0 = b[r14+136] (u)
    if (r0 != 0) goto L0201a4de
    call ir_reload_and_leaves_buffer_free
    r0 = [r14+184]
    if (r0 == 0) goto L0201a4da
    call L0203d218  ; @call.xl
    [r14+184] = r9
L0201a4da:
    [r14+188] = r9
L0201a4de:
    r0 = L01c1f180
    r12 = 0  #
    b[r0+1] = r7
    r0 = 0
    if (r4 == 0) goto L0201a4f2
    b[r14+148] = r9
    r0 = 1
L0201a4f2:
    r1 = L01c26844
    r1 = r4  #
    b[r1+0] = r0
    r0 = 14
    r2 = 0
    call storage_coordination_notify
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 * 0xA
    [r14+100] = r0
    [sp+228] = r4
L0201a516:
    r0 = b[r14+1] (u)
    if (r0 == 0) goto L0201a52c
    r0 = 0
    call L02001e72
    r0 = b[r0+20] (u)
    r2 = 1
    if (r0 == 4) goto L0201a52e
L0201a52c:
    r2 = 0
L0201a52e:
    r4 = 320
    r0 = b[r14+3] (u)
    if (r2 == r0) goto L0201a556
    b[r14+3] = r2
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 * 0xA
    [r14+100] = r0
    r0 = 14
    r1 = 9
    call storage_coordination_notify
L0201a556:
    r0 = b[r14+4] (u)
    r1 = [sp+228]
    if (r1 == 0) goto L0201a678
    if (r0 == 0) goto L0201a678
    b[r14+4] = r9
    goto L0201a62a
L0201a56a:
    r0 = sp + 234
    r1 = r6
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 412
    r0 = [r14+r0<<2]
    r0 += 24  ; @add.ri.u5
    call L0204074c  ; @call.xl
    r7 = 0
    goto L0201a614
L0201a58c:
    r0 = sp + 234
    r0 = b[r0+r7] (u)
    if (r0 == 13) goto L0201a59c
    if (r0 != 10) goto L0201a5ce
L0201a59c:
    if (r12 == 0) goto L0201a5ec
    r5 = 0
    [r14+180] = r5
    b[r14+136] = r5
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 3288
    r1 = 512
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    goto L0201a610
L0201a5ce:
    r1 = [r14+180]
    r5 = 1
    if (r1 > 198) goto L0201a610
    r2 = r1 + 1
    [r14+180] = r2
    r1 += r14
    r2 = 4988
    b[r1+r2] = r0
    r5 = r12
    goto L0201a610
L0201a5ec:
    r1 = [r14+180]
    if (r1 == 0) goto L0201a60e
    r0 = r14 + 4988
    r5 = 0
    b[r1+r0] = r5
    b[r14+136] = r5
    b[r14+6] = r13
    call tuner_and_control_records_console_line
    [r14+180] = r5
    goto L0201a610
L0201a60e:
    r5 = 0
L0201a610:
    r7 += 1  ; @add.ri.u5
    r12 = r5
L0201a614:
    if (r7 >= r4) goto L0201a620
    r0 = [r14+r8<<2]
    if (r11 == r0) goto L0201a58c
L0201a620:
    r7 = 1
    r13 = 321
    r4 = 320
L0201a62a:
    r2 = [r14+r8<<2]
    call phase3_p4_cdc_ready
    if (r11 != r2) goto L0201a678
    if (r0 == 0) goto L0201a678
    r0 = 412
    r0 = [r14+r0<<2]
    if (r0 == 0) goto L0201a678
    r13 = 1
    r6 = [r0++=24]
    call L02040614  ; @call.xl
    r0 = r6
    call L02005d84
    r4 = r0
    if (r4 >= 64) {  ; @if.ge.ri.s12
    r4 = 64
    }
    if (r4 != 0) goto L0201a56a
    r0 = 412
    r0 = [r14+r0<<2]
    r0 += 24  ; @add.ri.u5
    call L0204074c  ; @call.xl
    r13 = 321
    r4 = 320
L0201a678:
    r0 = 315
    r0 = [r14+r0<<2]
    r1 = [r14+192]
    if (r0 == r1) goto L0201a80c
    r1 = r14 + 136
    [r1+56] = r0
    [r1+60] = r9
    b[r14+200] = r9
    r0 = b[r1+0] (u)
    if (r0 == 0) goto L0201a80c
    call ir_reload_and_leaves_buffer_free
    r0 = [r14+184]
    if (r0 == 0) goto L0201a6b0
    call L0203d218  ; @call.xl
    [r14+184] = r9
L0201a6b0:
    [r14+188] = r9
    r0 = L01c1f180
    b[r0+1] = r7
    call state_queries_both_set
    if (r0 != 0) goto L0201a80c
    b[r14+136] = r9
    goto L0201a80c
L0201a6ca:
    r0 = 1023
    r0 &= r1
    r0 += r14
    r2 = 10912
    r0 = b[r0+r2] (u)
    r1 += 1  ; @add.ri.u5
    [r14+r10<<2] = r1
    if (r0 == 13) goto L0201a704
    if (r0 == 10) goto L0201a704
    if (r0 != 0) goto L0201a7a2
    [r14+196] = r9
    b[r14+200] = r9
    b[r14+136] = r7
    r0 = 8728
    r4 = r14 + r0
    r2 = r15 + 2404
    goto L0201a722
L0201a704:
    r0 = b[r14+200] (u)
    if (r0 == 0) goto L0201a73e
    b[r14+200] = r9
    [r14+196] = r9
    b[r14+136] = r7
    r0 = 8728
    r4 = r14 + r0
    r2 = r15 + 3288
L0201a722:
    r1 = 512
    r0 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    r4 = 320
    call command_services_console_send
    goto L0201a80c
L0201a73e:
    r0 = [r14+196]
    if (r0 == 0) goto L0201a80c
    r0 += r14
    r1 = 5188
    b[r0+r1] = r9
    b[r14+136] = r7
    r0 = 2
    b[r14+6] = r0
    r0 = 13049
    r3 = r15 + r0
    call console_helpers_key_window
    r4 = r0
    r0 = r3
    call tuner_and_control_records_word_listed
    if (r0 != 0) goto L0201a778
    r0 = r15 + 2660
    call tuner_and_control_records_name_listed
    if (r0 == 0) goto L0201a7c2
L0201a778:
    if (r4 != 0) goto L0201a790
    r0 = 12468
    r0 += r15
    call tuner_and_control_records_word_listed
    if (r0 != 0) goto L0201a790
    r0 = r15 + 1640
    call tuner_and_control_records_name_listed
    if (r0 == 0) goto L0201a7c6
L0201a790:
    r0 = r14 + 5188
    call tuner_and_control_records_console_line
L0201a798:
    r4 = 320
    [r14+196] = r9
    goto L0201a80c
L0201a7a2:
    r1 = [r14+196]
    if (r1 > 198) goto L0201a7bc
    r2 = r1 + 1
    [r14+196] = r2
    r1 += r14
    r2 = 5188
    b[r1+r2] = r0
    goto L0201a80c
L0201a7bc:
    b[r14+200] = r7
    goto L0201a80c
L0201a7c2:
    r5 = 0
    goto L0201a7c8
L0201a7c6:
    r5 = 2
L0201a7c8:
    r4 = r14 + 5188
    r1 = 32
    r0 = r4
    call L020282f4  ; @call.xl
    if (r0 == 0) goto L0201a7dc
    b[r0+0] = r9
L0201a7dc:
    r0 = r15 + 2868
    r2 = r15 + 1916
    if (r5 != 2) {  ; @if.ne.ri.s12
    r2 = r0
    }
    r0 = 8728
    r6 = r14 + r0
    r1 = 512
    r0 = r6
    r3 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    goto L0201a798
L0201a80c:
    r1 = [r14+r10<<2]
    r0 = [r14+r13<<2]
    r2 = r0 - r1
    ifs (r2 < 1) goto L0201a832
    r2 = [r14+r4<<2]
    r2 = r2 - r0
    ifs (r2 < 0) goto L0201a832
    [r14+r10<<2] = r0
    [r14+196] = r9
    b[r14+200] = r9
    goto L0201a80c
L0201a832:
    r0 = [r14+r4<<2]
    if (r1 != r0) goto L0201a6ca
    r13 = L01c1f180
    r0 = [r13+24]
    [r14+204] = r0
    call fault_record_fault_age
    r3 = r0
    if (r3 < 3001) goto L0201816e
    call fault_record_fault_word
    r2 = r0
    r0 = 2
    r1 = r3
    call fault_record_fatal_record
L0201a862:
    goto L0201a862
