; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 5 functions, 0x0201e358..0x0201eba0

; phase3_p6_usb_check_dmo: 0x0201e358..0x0201e366, module phase3-p6 (usb_check_dmo)
.type phase3_p6_usb_check_dmo,@function
phase3_p6_usb_check_dmo:
    r0 = 92688
    r0 = [r0+0]
    r0 = uextra(r0, p:18, l:1)
    rts

; phase3_p6_sys_event_notify: 0x0201e366..0x0201e3ec, module phase3-p6 (sys_event_notify)
.type phase3_p6_sys_event_notify,@function
phase3_p6_sys_event_notify:
    [--sp] = {rets, r7-r4}
    sp += -4
    r7 = L01c1f180
    r3 = [r7+332]
    r4 = r2
    r5 = r1
    r6 = r0
    if (r3 == 0) goto L0201e3e2
L0201e37c:
    h[sp] = r6
    b[sp+2] = r5
    r0 = 12
    b[sp+3] = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r5 = L01c26890
    r0 = r5 + 68
L0201e39c:
    testset b[r0]
    ifeq goto L0201e39c
    csync
    r0 = [r7+332]
    if (r0 == 0) goto L0201e3c8
    r1 = [r0+24]
    r2 = [r0+28]
    r1 = r2 - r1
    if (r1 < 16) goto L0201e3c8
    r1 = sp + 0
    r2 = 4
    call L02006970
    r0 = [r7+332]
    r2 = 12
    r1 = r4
    call L02006970
L0201e3c8:
    csync
    r0 = 0
    b[r5+68] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r7 + 336
    call L020403ee  ; @call.xl
    goto L0201e3e8
L0201e3e2:
    call phase3_p5_event_pool_init
    if (r0 == 0) goto L0201e37c
L0201e3e8:
    sp += 4
    {pc, r7-r4} = [sp++]

; phase3_p6_device_event_notify: 0x0201e3ec..0x0201e3f8, module phase3-p6 (device_event_notify)
.type phase3_p6_device_event_notify,@function
phase3_p6_device_event_notify:
    [--sp] = rets
    r2 = r0
    r0 = 4
    r1 = 3
    call phase3_p6_sys_event_notify
    pc = [sp++]

; phase3_p6_usb_hotplug_detect: 0x0201e3f8..0x0201eb90, module phase3-p6 (usb_hotplug_detect)
.type phase3_p6_usb_hotplug_detect,@function
phase3_p6_usb_hotplug_detect:
    [--sp] = {rets, r15-r4}
    sp += -16
    r0 = sp + 4
    r13 = 0  #
    [sp] = r0
    r14 = 341
    r5 = L01c26890
    r11 = 5485
    r8 = 5468
    r9 = 1
    r7 = 5472
    r4 = 0
    goto L0201eb86
L0201e420:
    r0 = [r5+r14<<2]
    r0 = b[r0+0] (u)
    r0 = r0 & (1 << r4)
    if (r0 == 0) goto L0201eb02
    r0 = r4 * 0x64
    r15 = r0 + r5
    r0 = b[r15+r11] (u)
    if (r0 != 0) goto L0201eb02
    r10 = r15 + 5388
    r0 = r10
    call L02040614  ; @call.xl
    if (r0 != 0) goto L0201eb02
    r0 = [r5+r14<<2]
    r6 = b[r0+7] (u)
    if (r4 == 0) goto L0201e4b4
    if (r6 == 0) goto L0201e462
    r6 = b[r0+8] (u)
    if (r6 != 0) goto L0201e464
L0201e462:
    r6 = b[r0+5] (u)
L0201e464:
    r0 = 1
    call sdk_usb_phy_status
    if (r0 == 0) goto L0201e5e2
    r0 = 5568
    r0 = b[r5+r0] (u)
    r1 = r0 & 0xFFFFFF0F
    if (r1 > 6) goto L0201ea1e
    r2 = r1 << 1
    tbh [r2]
phase3_p6_case_table_0201e484:
    .short (L0201e492 - phase3_p6_case_table_0201e484) / 2, (L0201e492 - phase3_p6_case_table_0201e484) / 2, (L0201e508 - phase3_p6_case_table_0201e484) / 2, (L0201e54e - phase3_p6_case_table_0201e484) / 2, (L0201ea1e - phase3_p6_case_table_0201e484) / 2, (L0201e58c - phase3_p6_case_table_0201e484) / 2, (L0201e5e6 - phase3_p6_case_table_0201e484) / 2
L0201e492:
    r0 = r5 + 5575
    b[r0+9] = r9
    r1 = b[r0+0] (u)
    r1 += 1  ; @add.ri.u5
    b[r0+0] = r1
    r0 = 1
    call sdk_usb_check_dpo
    if (r0 == 0) goto L0201e62a
    r0 = 5572
    b[r5+r0] = r13
    goto L0201e638
L0201e4b4:
    if (r6 == 0) goto L0201e4ba
    r1 = b[r0+8] (u)
    if (r1 != 0) goto L0201e4bc
L0201e4ba:
    r6 = b[r0+5] (u)
L0201e4bc:
    r0 = 0
    call sdk_usb_phy_status
    if (r0 == 0) goto L0201ea16
    r0 = b[r5+r8] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 > 6) goto L0201ea1e
    r1 = r0 << 1
    tbh [r1]
phase3_p6_case_table_0201e4da:
    .short (L0201e4e8 - phase3_p6_case_table_0201e4da) / 2, (L0201e4e8 - phase3_p6_case_table_0201e4da) / 2, (L0201e738 - phase3_p6_case_table_0201e4da) / 2, (L0201e768 - phase3_p6_case_table_0201e4da) / 2, (L0201e78a - phase3_p6_case_table_0201e4da) / 2, (L0201e7c2 - phase3_p6_case_table_0201e4da) / 2, (L0201e818 - phase3_p6_case_table_0201e4da) / 2
L0201e4e8:
    r0 = r5 + 5475
    b[r0+9] = r9
    r1 = b[r0+0] (u)
    r1 += 1  ; @add.ri.u5
    b[r0+0] = r1
    r0 = 0
    call sdk_usb_check_dpo
    if (r0 == 0) goto L0201e876
    b[r5+r7] = r13
    goto L0201e884
L0201e508:
    r1 = r5 + 5572
    b[r1+12] = r9
    r2 = 90208
    r2 = b[r2+0] (u)
    r2 = r2 >> 2
    r12 = r6 & r2  #
    r3 = b[r1+1] (u)
    r2 = r3 + 1
    if ((r12 & 0x1) != 0) {
    r2 = 0
    }
    r2 = r2.b0 (u)  #
    b[r1+1] = r2
    r1 = [r5+r14<<2]
    r1 = b[r1+4] (u)
    if (r2 <= r1) goto L0201ea1e
    r0 = r0 & 0xFFFFFFF0
    r0 |= 1
    r1 = 5568
    b[r5+r1] = r0
    r0 = r1 + 5
    b[r5+r0] = r13
    goto L0201e5e2
L0201e54e:
    r0 = 5584
    b[r5+r0] = r9
    r0 = 1
    call sdk_usb_read_sofpnd
    if (r0 == 0) goto L0201e94c
    r0 = 1
    call L0201e274
    r1 = 5568
    r0 = b[r5+r1] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x5
    b[r5+r1] = r0
    r0 = 1
    call L02001916
    r0 = 1
    r1 = 2
    call L0201e0f4
    goto L0201e9e2
L0201e58c:
    r0 = 5584
    b[r5+r0] = r9
    r0 = 90124
    r1 = h[r0+0] (u)
    r0 = 1
    call sdk_usb_check_dpo
    if (r0 == 0) goto L0201e71c
    call phase3_p6_usb_check_dmo
    if (r0 == 0) goto L0201e71c
    r0 = 2785
    r0 = h[r5+r0<<1] (u)
    if (r1 != r0) goto L0201e71c
    r0 = r5 + 5568
    r2 = b[r0+4] (u)
    r2 += 1  ; @add.ri.u5
    r2 = r2.b0 (u)  #
    b[r0+4] = r2
    h[r0+2] = r1
    r1 = [r5+r14<<2]
    r1 = b[r1+2] (u)
    if (r2 <= r1) goto L0201ea1e
    r1 = b[r0+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= 1
    b[r0+0] = r1
    b[r0+4] = r13
L0201e5e2:
    r0 = 1
    goto L0201ea18
L0201e5e6:
    r0 = 5584
    b[r5+r0] = r9
    r0 = 1
    call sdk_usb_check_dpo
    if (r0 == 0) goto L0201e72e
    call phase3_p6_usb_check_dmo
    if (r0 == 0) goto L0201e72e
    r2 = 5574
    r0 = b[r5+r2] (u)
    r0 += 1  ; @add.ri.u5
    r1 = r0.b0 (u)
    b[r5+r2] = r0
    if (r1 < 21) goto L0201ea1e
    r0 = r5 + 5568
    b[r0+6] = r13
    r1 = b[r0+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= 1
    b[r0+0] = r1
    goto L0201ea1e
L0201e62a:
    r0 = r5 + 5572
    r1 = b[r0+0] (u)
    r1 += 1  ; @add.ri.u5
    b[r0+0] = r1
    b[r0+3] = r13
L0201e638:
    r0 = 1
    call sdk_usb_read_dp_se
    if ((r6 & 8) == 0) goto L0201e64c
    r12 = 1
    if (r0 != 0) goto L0201e65e
    r12 = r0
    goto L0201e65e
L0201e64c:
    if (r0 != 0) goto L0201e65a
    r0 = 1
    call sdk_usb_read_dm_se
    if (r0 == 0) goto L0201eb64
L0201e65a:
    r12 = 1
L0201e65e:
    if ((r6 & 4) != 0) goto L0201e66c
    if (r12 != 0) goto L0201e682
    r1 = r5 + 5573
    goto L0201e68e
L0201e66c:
    r0 = 161
    call storage_fault_read_register  ; @call.xl
    r1 = r5 + 5573
    if (r12 == 0) goto L0201e68e
    r0 = r0 & 0xFFFFFF20
    if (r0 != 0) goto L0201e68e
L0201e682:
    r1 = r5 + 5573
    r0 = b[r1+0] (u)
    r0 += 1  ; @add.ri.u5
    b[r1++=2] = r0
L0201e68e:
    b[r1+0] = r13
    r1 = [r5+r14<<2]
    r0 = 5573
    r2 = b[r5+r0] (u)
    r0 = b[r1+3] (u)
    if (r2 <= r0) goto L0201e6cc
    if (r0 == 0) goto L0201e6cc
    r0 = r5 + 5568
    r1 = b[r0+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= 2
    b[r0+0] = r1
    b[r0+5] = r13
    r0 = 1
    call L0201e03e
    if ((r6 & 0x1) != 0) {
    r0 = 5585
    b[r5+r0] = r9
    }
    goto L0201e9e2
L0201e6cc:
    r2 = 5572  #
    r1 = b[r1+1] (u)
    r2 = b[r5+r2] (u)
    if (r2 <= r1) goto L0201e856
    if (r1 == 0) goto L0201e856
    r0 = r6 & 0xFFFFFF08
    r1 = 0
    r2 = 5572
    b[r5+r2] = r1
    r2 += 2  ; @add.ri.u5
    b[r5+r2] = r1
    if (r0 == 0) goto L0201e9c2
    r1 = 5568
    r0 = b[r5+r1] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x5
    b[r5+r1] = r0
    r0 = 1
    call L0201e03e
    r0 = 1
    r1 = 10
    call L0201e0f4
    goto L0201e9e2
L0201e71c:
    r0 = 5572
    b[r5+r0] = r13
    r0 = 2785
    h[r5+r0<<1] = r1
    goto L0201ea1e
L0201e72e:
    r0 = 5574
    b[r5+r0] = r13
    goto L0201ea1e
L0201e738:
    r0 = r7 + 12
    b[r5+r0] = r9
    r2 = r6 & 0xFFFFFF08
    r3 = 0
    goto L0201e748
L0201e746:
    r3 += 1  ; @add.ri.u5
L0201e748:
    ifs (r3 > 9) goto L0201e9ec
    r0 = 0
    call sdk_usb_read_dp_se
    if (r2 != 0) goto L0201e75e
    if (r0 != 0) goto L0201e760
    r0 = 0
    call sdk_usb_read_dm_se
L0201e75e:
    if (r0 == 0) goto L0201e746
L0201e760:
    r0 = r7 + 1
    b[r5+r0] = r13
    goto L0201ea1e
L0201e768:
    r0 = r7 + 12
    b[r5+r0] = r9
    r0 = 0
    call sdk_usb_read_sofpnd
    if (r0 == 0) goto L0201eb06
    r0 = 0
    call L0201e274
    r0 = 148
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    goto L0201e934
L0201e78a:
    r0 = 0
    call sdk_usb_check_dpo
    r1 = b[r5+r7] (u)
    r1 += 1  ; @add.ri.u5
    if (r0 == 0) goto L0201e79a
    r0 = r1
L0201e79a:
    b[r5+r7] = r0
    r1 = [r5+r14<<2]
    r0 = r0.b0 (u)  #
    r1 = b[r1+2] (u)
    r1 = r1 << 1
    if (r0 <= r1) goto L0201ea1e
    r0 = r5 + 5468
    r1 = b[r0+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= 1
    b[r0+0] = r1
    b[r0+4] = r13
    goto L0201ea1e
L0201e7c2:
    r0 = r7 + 12
    b[r5+r0] = r9
    r0 = 149
    r1 = 1
    call phase3_p5_gpio_set_pull_up
    r0 = 0
    call sdk_usb_read_dm_se
    r1 = r0
    r0 = 0
    call sdk_usb_read_dp_se
    if (r1 == 0) goto L0201e996
    if (r0 == 0) goto L0201e996
    r0 = b[r5+r7] (u)
    r0 += 1  ; @add.ri.u5
    b[r5+r7] = r0
    r1 = [r5+r14<<2]
    r0 = r0.b0 (u)  #
    r1 = b[r1+2] (u)
    if (r0 <= r1) goto L0201ea1e
    r0 = 68
    if ((r6 & 0x8) == 0) {
    r0 = b[r5+r8] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 |= 1
    }
    b[r5+r8] = r0
    b[r5+r7] = r13
    goto L0201ea16
L0201e818:
    r1 = r5 + 5474
    b[r1+10] = r9
    r0 = 0
    call sdk_usb_read_dp_se
    r2 = b[r1+0] (u)
    r2 += 1  ; @add.ri.u5
    if (r0 == 0) goto L0201e82e
    r2 = 0
L0201e82e:
    r0 = r2.b0 (u)  #
    b[r1+0] = r2
    if (r0 < 21) goto L0201ea1e
    r0 = r5 + 5468
    r1 = b[r0+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= 1
    b[r0+0] = r1
    b[r0+6] = r13
    r0 = 0x51000
    [r0+0] |= 0x8
    [r0+0] &= 0xFFFFF6FF
    goto L0201ea1e
L0201e856:
    r2 = 5575
    r2 = b[r5+r2] (u)
    r0 = umax(r1, r0)
    if (r2 <= r0) goto L0201e9e2
    r0 = 5575
    b[r5+r0] = r13
    r0 = 17
    r1 = 5568
    goto L0201e9de
L0201e876:
    r0 = r5 + 5472
    r1 = b[r0+0] (u)
    r1 += 1  ; @add.ri.u5
    b[r0+0] = r1
    b[r0+3] = r13
L0201e884:
    r0 = 0
    call sdk_usb_read_dp_se
    if ((r6 & 8) == 0) goto L0201e898
    r12 = 1
    if (r0 != 0) goto L0201e8a8
    r12 = r0
    goto L0201e8a8
L0201e898:
    if (r0 != 0) goto L0201e8a4
    r0 = 0
    r12 = 0
    call sdk_usb_read_dm_se
    if (r0 == 0) goto L0201e8a8
L0201e8a4:
    r12 = 1
L0201e8a8:
    if ((r6 & 4) != 0) goto L0201e8b6
    if (r12 != 0) goto L0201e8cc
    r1 = r5 + 5473
    goto L0201e8d8
L0201e8b6:
    r0 = 161
    call storage_fault_read_register  ; @call.xl
    r1 = r5 + 5473
    if (r12 == 0) goto L0201e8d8
    r0 = r0 & 0xFFFFFF20
    if (r0 != 0) goto L0201e8d8
L0201e8cc:
    r1 = r5 + 5473
    r0 = b[r1+0] (u)
    r0 += 1  ; @add.ri.u5
    b[r1++=2] = r0
L0201e8d8:
    b[r1+0] = r13
    r1 = [r5+r14<<2]
    r0 = r7 + 1
    r2 = b[r5+r0] (u)
    r0 = b[r1+3] (u)
    if (r2 <= r0) goto L0201e910
    if (r0 == 0) goto L0201e910
    r0 = r5 + 5468
    r1 = b[r0+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= 2
    b[r0+0] = r1
    b[r0+5] = r13
    r0 = 0
    call L0201e03e
    if ((r6 & 0x1) != 0) {
    b[r5+r11] = r9
    }
    goto L0201eb7e
L0201e910:
    r3 = r7  #
    r1 = b[r1+1] (u)
    r2 = b[r5+r3] (u)
    if (r2 <= r1) goto L0201e9aa
    if (r1 == 0) goto L0201e9aa
    r0 = r6 & 0xFFFFFF08
    r1 = 0
    b[r5+r3] = r1
    r2 = r3 + 2
    b[r5+r2] = r1
    if (r0 == 0) goto L0201eb68
L0201e934:
    r0 = b[r5+r8] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x5
    b[r5+r8] = r0
    r0 = 0
    call L0201e03e
    goto L0201eb7e
L0201e94c:
    r1 = 5574
    r0 = b[r5+r1] (u)
    r0 += 1  ; @add.ri.u5
    b[r5+r1] = r0
    r1 = [r5+r14<<2]
    r2 = 2000  #
    r1 = b[r1+6] (u)
    r1 = r2 / r1 (u)
    r0 = r0.b0 (u)
    if (r0 <= r1) goto L0201e9e2
    r12 = r5 + 5568
    b[r12+6] = r13
    r0 = 1
    call L02001916
    r0 = 1
    r1 = r6
    call L0201e0f4
    r0 = b[r12+0] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x6
    b[r12+0] = r0
    goto L0201e9e2
L0201e996:
    b[r5+r7] = r13
    r0 = 2735
    r1 = 65535
    h[r5+r0<<1] = r1
    goto L0201ea1e
L0201e9aa:
    r2 = r3 + 3
    r2 = b[r5+r2] (u)
    r0 = umax(r1, r0)
    if (r2 <= r0) goto L0201eb7e
    r0 = r3 + 3
    b[r5+r0] = r13
    r0 = 17
    goto L0201eb7a
L0201e9c2:
    r0 = 1
    call L0201e03e
    r0 = 1
    call phase3_p6_usb_otg_sof_check_init
    r1 = 5568
    r0 = b[r5+r1] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x3
L0201e9de:
    b[r5+r1] = r0
L0201e9e2:
    r0 = 5584
    b[r5+r0] = r13
    goto L0201ea1e
L0201e9ec:
    r1 = r7 + 1
    r0 = b[r5+r1] (u)
    r0 += 1  ; @add.ri.u5
    b[r5+r1] = r0
    r1 = [r5+r14<<2]
    r0 = r0.b0 (u)  #
    r1 = b[r1+4] (u)
    if (r0 <= r1) goto L0201ea1e
    r0 = r5 + 5468
    r1 = b[r0+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= 1
    b[r0+0] = r1
    b[r0+5] = r13
L0201ea16:
    r0 = 0
L0201ea18:
    r1 = r6
    call L0201e0f4
L0201ea1e:
    r12 = r15 + 5468
    r1 = b[r12+0] (u)
    r0 = r1 >> 4
    r1 = r1 & 0xFFFFFF0F
    if (r0 == r1) goto L0201eafa
    r3 = [r5+r14<<2]
    r2 = b[r3+7] (u)
    if (r2 == 0) goto L0201ea48
    r2 = r3
    r6 = b[++r2=8] (u)
    if (r6 == 0) goto L0201ea48
    r3 += 7  ; @add.ri.u5
    if (r4 != 0) goto L0201ea4a
    r2 = r3
    goto L0201ea4a
L0201ea48:
    r2 = r3 + 5
L0201ea4a:
    r8 = 0  #
    r2 = b[r2+0] (u)
    r9 = 0
    d[sp+4] = r9_r8
    r1 += -1
    r8 = 5468  #
    r3 = [sp]
    r6 = L02035906  ; "otg"
    r9 = 1  #
    [r3+8] = r6
    if (r1 > 5) goto L0201eaea
    tbb [r1]
phase3_p6_case_table_0201ea6e:
    .byte (L0201ea74 - phase3_p6_case_table_0201ea6e) / 2, (L0201ea8e - phase3_p6_case_table_0201ea6e) / 2, (L0201eaea - phase3_p6_case_table_0201ea6e) / 2, (L0201eaea - phase3_p6_case_table_0201ea6e) / 2, (L0201eaac - phase3_p6_case_table_0201ea6e) / 2, (L0201ead6 - phase3_p6_case_table_0201ea6e) / 2
L0201ea74:
    r0 = r0 & 0xF
    r1 = r0 + -4
    b[sp+4] = r9
    if (r1 < 2) goto L0201eaba
    if (r0 == 2) goto L0201ea9c
    if (r0 == 6) goto L0201eada
    goto L0201eaea
L0201ea8e:
    b[sp+4] = r13
    r0 = r7 + 12
    b[r15+r0] = r9
    if ((r2 & 1) == 0) goto L0201eaea
L0201ea9c:
    r6 = r15 + 5476
    r0 = L02035906  ; "otg"
    r1 = r0 + 724
    goto L0201eac8
L0201eaac:
    b[sp+4] = r13
    r0 = r7 + 12
    b[r15+r0] = r9
    if ((r2 & 2) == 0) goto L0201eaea
L0201eaba:
    r6 = r15 + 5476
    r0 = L02035906  ; "otg"
    r1 = r0 + 304
L0201eac8:
    r0 = r6
    r2 = r4
    call phase3_p13_sprintf
    r0 = [sp]
    [r0+4] = r6
    goto L0201eae4
L0201ead6:
    b[sp+4] = r13
L0201eada:
    r0 = r6  #
    r1 = [sp]
    r0 = r0 + 731
    [r1+4] = r0
L0201eae4:
    r0 = sp + 4
    call phase3_p6_device_event_notify
L0201eaea:
    r0 = b[r12+0] (u)
    r1 = r0 & 0xFFFFFF0F
    r1 <= insert(r0, p:4, l:28)
    b[r12+0] = r1
L0201eafa:
    r0 = r10
    call L0204074c  ; @call.xl
L0201eb02:
    r4 += 1  ; @add.ri.u5
    goto L0201eb86
L0201eb06:
    r1 = r7 + 2
    r0 = b[r5+r1] (u)
    r0 += 1  ; @add.ri.u5
    b[r5+r1] = r0
    r1 = [r5+r14<<2]
    r2 = 2000  #
    r1 = b[r1+6] (u)
    r1 = r2 / r1 (u)
    r0 = r0.b0 (u)
    if (r0 <= r1) goto L0201eb7e
    r12 = r5 + 5468
    b[r12+6] = r13
    r0 = 0
    call L02001916
    r0 = 0
    call L0201e03e
    r0 = 0
    r1 = r6
    call L0201e0f4
    r0 = 149
    r1 = 1
    call phase3_p5_gpio_direction_output
    r0 = 0x51000
    [r0+0] |= 0x900
    r0 = b[r12+0] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x6
    b[r12+0] = r0
    goto L0201eb7e
L0201eb64:
    r12 = 0
    goto L0201e65e
L0201eb68:
    r0 = 0
    call phase3_p6_usb_otg_sof_check_init
    r0 = b[r5+r8] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x3
L0201eb7a:
    b[r5+r8] = r0
L0201eb7e:
    r0 = r7 + 12
    b[r5+r0] = r13
    goto L0201ea1e
L0201eb86:
    if (r4 != 2) goto L0201e420
    sp += 16
    {pc, r15-r4} = [sp++]

; phase3_p6_sys_timer_add_to_task: 0x0201eb90..0x0201eba0, module phase3-p6 (sys_timer_add_to_task)
.type phase3_p6_sys_timer_add_to_task,@function
phase3_p6_sys_timer_add_to_task:
    [--sp] = {rets, r4}
    sp += -4
    r4 = 0
    [sp] = r4
    call L0201c816
    sp += 4
    {pc, r4} = [sp++]
