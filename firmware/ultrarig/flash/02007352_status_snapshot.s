; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; status_snapshot: 1 function, 0x02007352..0x020076f4

; status_snapshot_status_snapshot: 0x02007352..0x020076f4, module status-snapshot (status_snapshot)
; HyperRig MINI, product option: eight scenes (mini/product/scenes.c).
.type status_snapshot_status_snapshot,@function
status_snapshot_status_snapshot:
    [--sp] = {rets, r15-r4}
    sp += -32
    r6 = r0
.if MINI_PRODUCT
    call hyperrig_scene_fill  ; @call.xl
.endif
    r15 = L01c24790
    r1 = 0
    r2 = 1490
    r13 = 0
    r0 = r15
    call effect_enable_memset  ; @call.xl
    r9 = L01c1f180
    r1 = b[r9+9] (u)
    r0 = b[r9+18] (u)
    r2 = 5
    b[r15+0] = r2
    r2 = r6
    call status_snapshot_override_byte
    r1 = b[r9+10] (u)
    r2 = b[r9+19] (u)
    b[r15+2] = r0
    r0 = r2
    r2 = r6
    call status_snapshot_override_byte
    r1 = L01c26890
    r1 = h[r1+78] (u)
    b[r15+3] = r0
    h[r15+10] = r1
    r0 = 0
    call stereo_budget_stereo_setting  ; @call.xl
    if (r0 != 0) goto L020073be
    r0 = 1347
    r1 = 128
    b[r15+r0] = r1
L020073be:
    r11 = r15 + 1340
    r10 = r15 + 1348
    goto L02007406
L020073c8:
    r6 = 0
    r12 = r10
    goto L020073f6
L020073ce:
    r7 = 0
    r4 = r12
    r5 = r11
    goto L020073ec
L020073d6:
    r0 = r13
    r1 = r6
    r2 = r7
    call preset_band_controls_band_level  ; @call.xl
    b[r4++=1] = r0
    if (r6 != 0) goto L020073e8
    b[r5+0] = r0
L020073e8:
    r5 += 1  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L020073ec:
    if (r7 != 2) goto L020073d6
    r12 = r12 + 2
    r6 += 1  ; @add.ri.u5
L020073f6:
    if (r6 != 3) goto L020073ce
    r10 = r10 + 6
    r11 = r11 + 2
    r13 = r13 + 1
L02007406:
    if (r13 != 2) goto L020073c8
    r10 = r15 + 1484
    r5 = 0
    r7 = 10
    goto L02007442
L02007414:
    r6 = 0
    r4 = r10
    goto L0200742c
L0200741a:
    r0 = r5
    r1 = r6
    call slot_queries_group_value  ; @call.xl
    r0 = r0 / r7 (s)
    b[r4++=1] = r0
    r6 += 1  ; @add.ri.u5
L0200742c:
    ifs (r6 > 2) goto L0200743c
    r0 = r5
    call slot_queries_group_count  ; @call.xl
    ifs (r6 < r0) goto L0200741a
L0200743c:
    r10 = r10 + 3
    r5 += 1  ; @add.ri.u5
L02007442:
    if (r5 != 2) goto L02007414
    r10 = 0
    r5_r4 = 0
    goto L0200747e
L0200744c:
    r6 = 0
    r7 = r10
    goto L02007468
L02007452:
    r0 = r5
    r1 = r6
    call preset_band_controls_band_flag  ; @call.xl
    if (r0 == 0) goto L02007464
    r0 = r4.b0 (u)
    r4 = r0 | (1 << r7)
L02007464:
    r7 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02007468:
    ifs (r6 > 2) goto L02007478
    r0 = r5
    call slot_queries_group_count  ; @call.xl
    ifs (r6 < r0) goto L02007452
L02007478:
    r10 = r10 + 3
    r5 += 1  ; @add.ri.u5
L0200747e:
    if (r5 != 2) goto L0200744c
    r0 = 90
    r1 = r15 + 1342
    b[r1+0] = r0
    b[r1+1] = r4
    call slot_commands_requested
    r5 = 0
    r2 = 1
    r3 = 1
    if (r0 == 0) goto L0200749a
    r3 = 0
L0200749a:
    b[r1+2] = r3
    call preset_application_mode
    if (r0 == 0) goto L020074a4
    r2 = 0
L020074a4:
    r0 = 1038  #
    b[r1+4] = r2
    r1 = L01c26890
    r0 = [r1+r0<<2]
    b[r15+4] = r0
    r0 = 1039
    r0 = [r1+r0<<2]
    b[r15+5] = r0
    call preset_application_services_tempo  ; @call.xl
    h[r15+8] = r0
    goto L020074e2
L020074d0:
    r0 = r5
    call audio_measurement_control_value  ; @call.xl
    r1 = r15 + 1424
    h[r1+r5<<1] = r0
    r5 += 1  ; @add.ri.u5
L020074e2:
    if (r5 != 6) goto L020074d0
    r1 = [r9+88]
    r0 = -1
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r0 = r1
    }
    b[r15+6] = r0
.if MINI_PRODUCT
    r0 = 11936
    r1 = hyperrig_scene_base  ; @li.u32
    r0 += r1  ; @add.rr
    r1 = 0
.else
    r0 = 11936
    r1 = L01c26890
    r0 += r1  ; @add.rr
    r1 = 0
.endif
    goto L0200752a
L02007506:
    r2 = b[r0+0] (u)
    if (r2 == 0) goto L02007524
    r2 = r1 + r15
    r2 = r2 + 1360
.if MINI_PRODUCT
    r3 = hyperrig_name_base  ; @li.u32
    r3 += r1  ; @add.rr
    r3 = r3 + 3248
.else
    r3 = L01c26890
    r3 += r1  ; @add.rr
    r3 = r3 + 3248
.endif
    rep 16 {
    r4 = b[r3++=1] (u)
    b[r2++=1] = r4
    }
L02007524:
    r0 = r0 + 260
    r1 += 16  ; @add.ri.u5
L0200752a:
    if (r1 != 64) goto L02007506
    r9 = 0
    goto L020075b4
L02007532:
    r1 = sp + 6
    r0 = r9
    call preset_application_chain_read  ; @call.xl
    r6 = r0
    r4 = 0
    goto L020075a4
L02007542:
    r5 = sp + 6
    r0 = b[r5+r4] (u)
    r2 = sp + 16
    b[r2+r1] = r0
    r2 = r1 + 1
    b[r15+1] = r2
    r1 = r1 * 0x12
    r7 = r1 + r15
    b[r7+12] = r9
    call preset_application_effect_type  ; @call.xl
    r1 = b[r5+r4] (u)
    r0 = r1  #
    b[r7+13] = r0
    call preset_application_effect_enabled  ; @call.xl
    r1 = b[r5+r4] (u)
    r0 = r1  #
    b[r7+14] = r0
    call preset_application_placement  ; @call.xl
    b[r7+15] = r0
    r5 = r7 + 16
    r7 = 0
    goto L0200759e
L0200758a:
    r0 = sp + 6
    r0 = b[r0+r4] (u)
    r1 = r7
    call preset_application_parameter  ; @call.xl
    h[r5+r7<<1] = r0
    r7 += 1  ; @add.ri.u5
L0200759e:
    if (r7 != 7) goto L0200758a
    r4 += 1  ; @add.ri.u5
L020075a4:
    ifs (r4 >= r6) goto L020075b0
    r1 = b[r15+1] (u)
    if (r1 < 16) goto L02007542
L020075b0:
    r9 = r9 + 1
L020075b4:
    if (r9 != 2) goto L02007532
.if MINI_PRODUCT
    r0 = 12182
    r1 = hyperrig_scene_base  ; @li.u32
.else
    r0 = 12182
    r1 = L01c26890
.endif
    r0 += r1  ; @add.rr
    r0 = 11958  #
    [sp] = r0
    r1 += r0  ; @add.rr
    r3 = r15 + 1436
    r12 = r15 + 306
    r5 = 0
    r9 = 11942
    r11 = 304
    goto L020076ec
L020075e0:
.if MINI_PRODUCT
    r13 = r5 * 0x104
    r0 = hyperrig_scene_base  ; @li.u32
.else
    r13 = r5 * 0x104
    r0 = L01c26890
.endif
    r4 = r13 + r0
    r0 = 11936
    r0 = b[r4+r0] (u)
    if (r0 == 0) goto L020076d8
    r8 = r3
    r0 = b[r15+7] (u)
    r2 = 11937
    r2 = b[r4+r2] (u)
    r0 = r0 | (1 << r5)
    b[r15+7] = r0
    r0 = 1
    r7 = r0 << r5
    if (r2 != 0) goto L02007624
    r2 = 1345
    r0 = b[r15+r2] (u)
    r0 |= r7
    b[r15+r2] = r0
L02007624:
    r0 = 11940
    r0 = b[r4+r0] (u)
    r2 = 11941
    r2 = b[r4+r2] (u)
    r3 = 12194
    r6 = b[r4+r3] (u)
    r14 = r13 + r15
    r3 = 302
    b[r14+r3] = r0
    r0 = r3 + 1
    b[r14+r0] = r2
    r3 = r8
    if (r6 == 0) goto L02007670
    r2 = 1347
    r0 = b[r15+r2] (u)
    r0 |= r7
    b[r15+r2] = r0
    r7 = 6
    r2 = r3  #
    r0 = [sp]
    goto L0200766e
L02007668:
    r6 = h[r0++=2] (u)
    h[r2++=2] = r6
    r7 += -1
L0200766e:
    if (r7 != 0) goto L02007668
L02007670:
    r0 = 11938
    r4 += r0  ; @add.rr
    r7 = 0
    r8 = r12
    goto L020076d0
L0200767c:
    r0 = sp + 16
    r0 = b[r0+r7] (u)
    r2 = h[r4+0] (u)
    r2 = r2 & (1 << r0)
    if (r2 == 0) goto L020076ca
    r2 = r14
    r6 = h[++r2=300] (u)
    r6 = r6 | (1 << r7)
    r2 = r13 + r0  #
    h[r2+0] = r6
.if MINI_PRODUCT
    r6 = hyperrig_scene_base  ; @li.u32
    r2 += r6  ; @add.rr
    r2 = b[r2+r9] (u)
.else
    r6 = L01c26890
    r2 += r6  ; @add.rr
    r2 = b[r2+r9] (u)
.endif
    r6 = r7 << 4
    r6 += r13
    r6 += r15
    b[r6+r11] = r2
    r0 = r0 * 0xE
    r0 += r1  ; @add.rr
    r2 = 0
    r10 = r8
    goto L020076c6
L020076bc:
    r6 = h[r0+r2<<1] (u)
    h[r10++=2] = r6
    r2 += 1  ; @add.ri.u5
L020076c6:
    if (r2 != 7) goto L020076bc
L020076ca:
    r8 = r8 + 16
    r7 += 1  ; @add.ri.u5
L020076d0:
    r0 = b[r15+1] (u)
    ifs (r7 < r0) goto L0200767c
L020076d8:
    r1 = r1 + 260  #
    r0 = [sp]
    r12 = r12 + 260
    r0 = r0 + 260
    [sp] = r0
    r3 += 12  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L020076ec:
.if MINI_PRODUCT
    if (r5 != 4) goto L020075e0
    r0 = sp + 16
    call hyperrig_snapshot_more  ; @call.xl
    sp += 32
.else
    if (r5 != 4) goto L020075e0
    sp += 32
.endif
    {pc, r15-r4} = [sp++]
