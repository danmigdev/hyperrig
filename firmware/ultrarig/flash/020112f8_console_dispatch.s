; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_dispatch: 1 function, 0x020112f8..0x02014104

; console_dispatch_console_dispatch: 0x020112f8..0x02014104, module console-dispatch (console_dispatch)
.type console_dispatch_console_dispatch,@function
console_dispatch_console_dispatch:
    [--sp] = {rets, r15-r4}
    sp += -596
    r5 = r1
    r6 = r0
    r15 = L02035810
    r1 = r15 + 310
    call L02028308  ; @call.xl
    r14 = L01c26890
    if (r0 == 0) goto L0201170a
    r1 = r15 + 74
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0201174c
    r1 = r15 + 315
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011870
    r1 = r15 + 1022
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011902
    r1 = r15 + 78
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011968
    r1 = r15 + 581
    r0 = r6
    call L02028308  ; @call.xl
    r8 = L01c1f180
    if (r0 == 0) goto L02011a7a
    r1 = r15 + 82
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011b56
    r1 = r15 + 587
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011baa
    r1 = r15 + 320
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011c48
    r1 = r15 + 325
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011ccc
    r1 = r15 + 86
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011d9e
    r1 = r15 + 335
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011eb8
    r1 = r15 + 90
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011f86
    r1 = r15 + 345
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011fe8
    r1 = r15 + 94
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012062
    r1 = r15 + 599
    r0 = r6
    call L02028308  ; @call.xl
    r9 = L01c1f7e0
    if (r0 == 0) goto L02012168
    r1 = r15 + 605
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020121dc
    r1 = r15 + 98
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0201220c
    r1 = r15 + 102
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012262
    r1 = r15 + 106
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012332
    r1 = r15 + 1226
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012400
    r1 = r15 + 350
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012430
    r1 = r15 + 110
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020124ee
    r1 = r15 + 611
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012524
    r1 = r15 + 617
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012596
    r1 = r15 + 1038
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020125dc
    r1 = r15 + 114
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0201263a
    r1 = r15 + 623
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0201270c
    r1 = r15 + 629
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020127b4
    r1 = r15 + 635
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012876
    r1 = r15 + 122
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020128c2
    r1 = r15 + 126
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0201290c
    r1 = r15 + 130
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012a28
    r1 = r15 + 134
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012ad4
    r1 = r15 + 138
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012b7a
    r1 = r15 + 142
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012bec
    r1 = r15 + 360
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012c82
    r1 = r15 + 146
    r0 = r6  #
    [sp+96] = r1
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012cc8
    r1 = r15 + 150
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013074
    r1 = r15 + 365
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013140
    r1 = r15 + 154
    r0 = r6
    call L02028308  ; @call.xl
    r9 = L01c34468
    if (r0 == 0) goto L02013192
    r1 = r15 + 158
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020131d8
    r1 = r15 + 872
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013230
    r1 = r15 + 370
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013272
    r1 = r15 + 282
    r0 = r6
    call L02028308  ; @call.xl
    r9 = 71936
    if (r0 == 0) goto L0201328e
    r1 = r15 + 385
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020135ce
    r1 = r15 + 390
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020136e2
    r1 = r15 + 395
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020136f4
    r7 = r15 + 641
    r1_r0 = r7_r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013796
    r1 = r15 + 1235
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013738
    r1 = r15 + 1244
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013738
    r1 = r15 + 1014
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013a32
    r1 = r15 + 900
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013db8
    r1 = r15 + 659
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020140c8
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L02011a58
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1102
    goto L02012424
L0201170a:
    call bond_records_and_prints_boot_clear
    r1 = b[r14+11] (u)
    r0 = r15 + 575
    if (r1 != 0) goto L0201171a
    r0 = r15
L0201171a:
    r0 = r15 + 1208  #
    [sp+8] = r0
    r0 = r15 + 1868  #
    [sp+4] = r0
    r1 = 8728
    r5 = r14 + r1
    r2 = r15 + 2885
    r3 = r15 + 3966
L02011736:
    r1 = 512
L0201173a:
    [sp] = r0
L0201173c:
    r0 = r5
L0201173e:
    call L0200691e
L02011742:
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    goto L02011a54
L0201174c:
    r1 = 0
    r2 = 10
    r8 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r14 + 55
L02011768:
    testset b[r0]
    ifeq goto L02011768
    csync
    r0 = 299
    r10 = [r14+r0<<2]
    r0 = r2 + 1
    r1 = 1
    if (r10 >= r2) {
    r1 = r0
    }
    if (r10 < 129) goto L02011794
    r12 = r10 + -127
    if (r12 <= r1) goto L02011794
    r8 = r12 - r1
    goto L02011796
L02011794:
    r12 = r1
L02011796:
    r1 = 0
    r9 = 8248
    r11 = L01c2a0d0
    r7 = 0
    r5 = r12
    goto L020117d4
L020117a8:
    if (r6 > r10) goto L020117dc
    r2 = r1 + r14
    [++r2=r9] = r6
    r6 = r6 << 4
    r6 = r6 & 0x7F0
    r3 = [++r6=r11]
    r4 = h[r6+4] (u)
    r0 = [r6+8]
    r6 = [r6+12]
    [r2+4] = r3
    [r2+8] = r4
    [r2+12] = r0
    r2 = r5  #
    [r2+16] = r6
    r1 += 20  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L020117d4:
    r6 = r12 + r7
    ifs (r7 <= 23) goto L020117a8
L020117dc:
    csync
    r4 = 0
    b[r14+55] = r4
    r9 = 1
    if (r6 > r10) {
    r9 = 0
    }
    if (r1 == 0) goto L020117f2
    r10 = r2
L020117f2:
    r0 = 8264
    r5 = r14 + r0
    call storage_coordination_irq_leave  ; @call.xl
    r11 = 10868
    r12 = 8728
    goto L0201184e
L0201180a:
    r1_r0 = d[r5+-12]
    r3 = [r5+-16]
    if (r1 <= 33) {  ; @if.le.ri.s12
    r2 = r15 + r11
    r1 = [r2+r1<<2]
    } else {
    r1 = r15 + 17
    }
    r2 = [r5+-4]
    r6 = [r5++=20]
    r6 = r14 + r12  #
    [sp+12] = r6
    r2 = r15 + 3642  #
    [sp+8] = r2
    d[sp] = r1_r0
    r1 = 512
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    r4 += 1  ; @add.ri.u5
L0201184e:
    ifs (r4 < r7) goto L0201180a
    call state_queries_tenfold_word
    r0 = r12  #
    [sp+8] = r0
    d[sp] = r9_r8
    r6 = r14 + r0
    r2 = r15 + 3621
    r1 = 512
    r0 = r6
    r3 = r10
    goto L02011a48
L02011870:
    call state_queries_tenfold_word
    r1 = r14 + 108
    r2 = [r1+4]
    [sp+116] = r2
    r2 = [r1+0]
    [sp+120] = r2
    r1 = [r1+8]
    [sp+124] = r1
    [sp+128] = r0
    call phase3_p3_system_reset_reason_get
    r1 = b[r14+13] (u)
    [sp+112] = r1
    r1 = 32436468
    r1 = [r1+0]
    [sp+108] = r1
    r1 = b[r14+5] (u)
    r2 = b[r14+11] (u)
    [sp+104] = r2
    if (r1 != 0) {  ; @if.ne.ri.s12
    r1 = [r14+120]
    r13 = uextra(r1, p:12, l:4)
    } else {
    r13 = 0
    }
    r1 = 363
    r7 = [r14+r1<<2]
    r1 = L01c26854
    r11 = h[r1+0] (u)
    r4 = r14 + 132
    r8 = [r4+0]
    r2 = b[r14+7] (u)
    r1 = L01c344b0
    r10 = [r1+0]
    r9 = b[r14+12] (u)
    r1 = [r4+8]
    r6 = [r4+12]
    r4 = b[r14+14] (u)
    if (r11 == 0) goto L020119dc
    r3 = L01c26858
    r5 = 3062  #
    r3 = b[r3+0] (u)
    r3 = r3 * 0x14
    r3 += r15
    r12 = [r3+r5<<2]
    goto L020119e0
L02011902:
    r1 = sp + 580
    r2 = 0
    r4 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r3 = [sp+580]
    r5 = r0
    r1 = sp + 576
    r2 = 0
    r0 = r3
    call capture_command_decimal  ; @call.xl
    r3 = [sp+576]
    r6 = r0
    r1 = 0
    r2 = 0
    r0 = r3
    call capture_command_decimal  ; @call.xl
    r1 = [r14+184]
    r7 = r0
    if (r1 == 0) goto L02011950
    r0 = r1
    call L0203d218  ; @call.xl
    [r14+184] = r4
    [r14+244] = r4
L02011950:
    if (r5 == 0) goto L02011afa
    if (r5 <= 4096) goto L02011b08
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 3663
    goto L0201215a
L02011968:
    r1 = sp + 572
    r2 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r6 = [sp+572]
    r9 = r0
L0201197c:
    r0 = r6
    r1 = b[r0+0] (u)
    r6 = r0 + 1
    if (r1 == 32) goto L0201197c
    r11 = [r14+184]
    [sp+572] = r0
    r10 = r11 + r9
    r8 = 0
    r3 = -1
    r4 = 0
    goto L020119d6
L0201199a:
    r1 = r6
    r0 = b[++r1=r3] (u)
    if (r0 == 0) goto L02011a5e
    r7 = b[r1+1] (u)
    if (r7 == 0) goto L02011a5e
    r1 = [r14+244]
    r2 = r9 + r4
    r1 = r1 << 1
    if (r2 >= r1) goto L02011a5e
    r0 = r0.b0 (s)
    call bond_records_and_prints_hex_value
    r5 = r0
    r0 = r7.b0 (s)
    call bond_records_and_prints_hex_value
    r1 = r0 | r5
    ifs (r1 < 0) goto L02011a5e
    r1 = r5 << 4
    r0 += r1  ; @add.rr
    b[r10+r4] = r0
    r3 += 2  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L020119d6:
    if (r11 != 0) goto L0201199a
    goto L02011a60
L020119dc:
    r12 = r15 + 15
L020119e0:
    r3 = 373
    r3 = [r14+r3<<2]
    r5 = L01c26850
    r5 = h[r5+0] (u)
    [sp+76] = r3
    [sp+72] = r11  ; @st.w.sp.l
    [sp+68] = r5
    [sp+64] = r12  ; @st.w.sp.l
    [sp+60] = r8  ; @st.w.sp.l
    [sp+56] = r2
    [sp+52] = r10  ; @st.w.sp.l
    [sp+48] = r9  ; @st.w.sp.l
    [sp+44] = r7
    [sp+40] = r1
    [sp+36] = r6
    [sp+32] = r4
    [sp+28] = r13  ; @st.w.sp.l
    r1 = [sp+104]
    [sp+24] = r1
    r1 = [sp+108]
    [sp+20] = r1
    r1 = [sp+112]
    d[sp+12] = r1_r0
    r1 = 512  #
    r0 = [sp+116]
    [sp+8] = r0
    r0 = [sp+120]
    r0 = 8728  #
    [sp+4] = r0
    r6 = r14 + r0
    r0 = 12044
    r2 = r15 + r0  #
    r0 = [sp+124]
    r0 = r6  #
    [sp] = r0
    r3 = [sp+128]
L02011a48:
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
L02011a54:
    call command_services_console_send
L02011a58:
    sp += 596
    {pc, r15-r4} = [sp++]
L02011a5e:
    r8 = r4
L02011a60:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 2138
L02011a6c:
    r1 = 512
    [sp] = r8  ; @st.w.sp.l
L02011a74:
    r0 = r5
    r3 = r9
    goto L0201173e
L02011a7a:
    r1 = 0
    r2 = 16
    r6 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r2 = [r14+184]
    r5 = r0
    if (r2 == 0) goto L02011b32
    r7 = [r14+244]
    r1 = r7 << 1
    r0 = r2
    call record_helpers_checksum
    r6 = r0
    if (r5 != r6) goto L02011b32
    r0 = 20
    r1 = 768
    r2 = r7
    call storage_coordination_notify
    r0 = r14 + 244
    r3_r2 = d[r0+4]
    r4 = r14 + 152  #
    r1 = [r0+0]
    r0 = [r4+32]
    call ir_installation_attach
.if MINI_PRODUCT
    call hyperrig_ir_heard  ; @call.xl
.endif
    r0 = 0
    r1 = 1796  #
    [r4+32] = r0
    b[r14+r1] = r0
    r1 = [r4+16]
    r0 = 255
    b[r8+10] = r0
    b[r8+19] = r0
    r0 = 48
    if (r1 != 0) goto L02011ae0
    r0 = 24
L02011ae0:
    {r4, r3} = [r4+]
    r0 = 8728  #
    [sp+4] = r0
    r5 = r14 + r0
    r2 = r15 + 5758
L02011af2:
    r1 = 512  #
    [sp] = r4
    goto L0201173c
L02011afa:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 2124
    goto L0201215a
L02011b08:
    if (r7 == 0) goto L02011b12
    if (r7 == 24) goto L02011b12
    if (r7 != 48) goto L02011cbe
L02011b12:
    r0 = 60000
    r0 += r6  ; @add.rr
    r1 = 80001
    if (r0 < r1) goto L02011bfe
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 5650
    goto L0201215a
L02011b32:
    r0 = 8728  #
    [sp] = r5
    r7 = r14 + r0
    r2 = r15 + 4618
    r1 = 512
    r0 = r7
    r3 = r6
L02011b48:
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r7
    goto L02011a54
L02011b56:
    r0 = -1
    [sp+568] = r0
    r0 = 0
    [sp+564] = r0
    r1 = r15 + 815
    r2 = sp + 568
    r3 = sp + 564
    r0 = r5
    call L0200b7c2
    call audio_pause_pause_audio
    r1 = [sp+564]
    r0 = [sp+568]
    call preset_band_controls_set_group_checked  ; @call.xl
    r5 = r0
    call audio_pause_resume_audio
    if (r5 == 0) goto L02011ca8
    r0 = r5
    call dispatch_helpers_error_text
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1652
L02011ba4:
    r1 = 512
    goto L0201173c
L02011baa:
    r0 = 0
    b[sp+563] = r0
    r1 = -1
    d[sp+552] = r1_r0
    [sp+548] = r0
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02011ea6
    r0 = sp + 548
    r1 = r15 + 1929  #
    [sp+4] = r0
    r0 = sp + 552
    r2 = sp + 563
    r3 = sp + 556
    r0 = r5  #
    [sp] = r0
    call L0200b7c2
    if (r0 != 4) goto L02012418
    r2 = b[sp+563] (u)
    if (r2 != 80) goto L02011e26
    r1 = [sp+556]
    ifs (r1 >= 0) goto L02011e36
    goto L02012418  ; @goto.l
L02011bfe:
    r8 = r5 << 1
    r0 = r8
    call L0203c15c  ; @call.xl
    r9 = r0
    if (r0 == 0) goto L02011d90
    r1 = 0
    r2 = r8
    call effect_enable_memset  ; @call.xl
    [r14+184] = r9
    [r14+244] = r5
    [r14+248] = r6
    r0 = 1
    if (r7 != 48) {  ; @if.ne.ri.s12
    r0 = 0
    }
    [r14+252] = r0
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 2419
L02011c3e:
    r1 = 512
L02011c42:
    r0 = r6
    r3 = r5
    goto L02011a48
L02011c48:
    r0 = 0
    b[sp+547] = r0
    r1 = -1
    d[sp+536] = r1_r0
    [sp+532] = r1
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201214a
    r0 = sp + 532
    r1 = r15 + 1929  #
    [sp+4] = r0
    r0 = sp + 536
    r2 = sp + 547
    r3 = sp + 540
    r0 = r5  #
    [sp] = r0
    call L0200b7c2
    ifs (r0 < 3) goto L02012418
    r1 = b[sp+547] (u)
    if (r1 != 80) goto L02011f18
    r7 = [sp+540]
    if (r7 > 2) goto L02012418
    r2 = [sp+536]
    r3 = 20000
    if (r2 <= r3) goto L02011f36
    goto L02012418
L02011ca8:
    r3 = [sp+568]
    r0 = [sp+564]
    r1 = 8728
    r5 = r14 + r1
    r2 = r15 + 2152
    goto L02011736
L02011cbe:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 4228
    goto L0201215a
L02011ccc:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02011cdc
    r0 = r5
    call phase3_p12_atoi  ; @call.xl
    call audio_pause_set_auxiliary
L02011cdc:
    r0 = 2567
    r9 = [r14+r0<<2]
    r0 += -1
    r0 = [r14+r0<<2]
    r12 = 0  #
    [sp+128] = r0
    r4 = 0
    r13 = 0
    r5 = 9752
    goto L02011d06
L02011cf8:
    r0 = r14 + r5
    r0 = [r0+r4<<2]
    r13_r12 += r0 * r0 (s)
    r4 += 1  ; @add.ri.u5
L02011d06:
    if (r4 != 128) goto L02011cf8
    r13_r12 >>= 7
    r4 = 0
    r5 = r4 + 0x40000000
L02011d14:
    r7_r6 = r5_r4
    r0 = r6 - r12
    r1 = r7 - r13 - !c
    r2 = psr
    r0 |= r1
    r1 = sextra(r2, p:1, l:1)
    r5_r4 >>= 2
    if ((r1 & r0) != 0) goto L02011d14
    r10 = 0
    r11 = 0
    goto L02011d6a
L02011d36:
    r4 = r6 + r10
    r5 = r7 + r11 + c
    r0 = r12 - r4
    r0 = r13 - r5 - !c
    r0 = psr
    if ((r0 & 2) != 0) goto L02011d54
    r11_r10 >>= 1
    goto L02011d66
L02011d54:
    r12 = r12 - r4
    r13 = r13 - r5 - !c
    r11_r10 >>= 1
    r10 += r6
    r11 = r11 + r7 + c
L02011d66:
    r7_r6 >>= 2
L02011d6a:
    r0 = r6 | r7
    if (r0 != 0) goto L02011d36
    r3 = b[r8+4] (u)
    [sp+8] = r10  ; @st.w.sp.l
    [sp+4] = r9  ; @st.w.sp.l
    r0 = 8728
    r5 = r14 + r0  #
    r0 = [sp+128]
    r2 = r15 + 7431
    r1 = 512
    goto L0201173a
L02011d90:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 4456
    goto L0201215a
L02011d9e:
    r1 = r15 + 330
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02011fa6
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02011faa
    r0 = 0
    [sp+528] = r0
    [sp+524] = r0
    r1 = r15 + 593
    r2 = sp + 528
    r3 = sp + 524
    r0 = r5
    call L0200b7c2
    if (r0 != 2) goto L02012418
    r4 = [sp+528]
    r6 = [sp+524]
    call dispatch_helpers_buffer_release
    r0 = r4 + -1
    r3 = r15 + 779
    if (r0 > 3) goto L0201237c
    r0 = r6 + -128
    if (r0 > 8064) goto L0201237c
    r5 = r6 << 2
    r0 = r5
    call heap_access_vendor_allocate_wrapper
    if (r0 != 0) goto L02011e14
    r0 = r14 + 2452
    r1 = r5
    call block_pool_allocate
    if (r0 == 0) goto L02012378
L02011e14:
    r1 = r14 + 456
    [r1+0] = r0
    [r1+8] = r6
    [r1+4] = 0x0
    b[r14+25] = r4
    goto L02011faa
L02011e26:
    if (r2 != 81) goto L02012418
    r1 = [sp+556]
    ifs (r1 <= -1) goto L02012418
L02011e36:
    ifs (r1 > 2) goto L02012418
    r0 = 1
    if (r2 != 81) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r3 = [sp+548]
    r2 = [sp+552]
    call preset_band_controls_set_band_levels_now  ; @call.xl
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02011ea6
    r5 = b[sp+563] (s)
    r0 = 1
    if (r5 != 81) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r6 = [sp+556]
    r2 = 0
    r1 = r6
    call preset_band_controls_band_level  ; @call.xl
    r1 = b[sp+563] (u)
    r7 = r0
    r0 = 1
    if (r1 != 81) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r1 = [sp+556]
    r2 = 1
    call preset_band_controls_band_level  ; @call.xl
    r0 = 8728  #
    [sp+8] = r0
    r7 = r14 + r0  #
    [sp+4] = r7
    r2 = r15 + 3307
L02011e9a:
    r1 = 512  #
    [sp] = r6
    r0 = r7
    r3 = r5
    goto L02011b48
L02011ea6:
    call dispatch_helpers_mix_list
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1483
    goto L0201215a
L02011eb8:
    r7 = [r14+456]
    r8 = [r14+460]
    r1 = 0
    r2 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r5 = r0
    if (r7 == 0) goto L02011fd2  ; @beq.ri
    if (r5 >= r8) goto L02011fd2
    r0 = 8728
    r6 = r14 + r0
    r1 = r15 + 1217
    r0 = r6
    r2 = r5
    call phase3_p13_sprintf
    r6 += r0  ; @add.rr
    r4 = r5 + 24
    goto L02011f06
L02011ef0:
    if (r5 >= r4) goto L02011f0a
    r2 = [r7+r5<<2]
    r1 = r15 + 340
    r0 = r6
    call phase3_p13_sprintf
    r6 += r0  ; @add.rr
    r5 += 1  ; @add.ri.u5
L02011f06:
    if (r5 < r8) goto L02011ef0
L02011f0a:
    r0 = 10
    r0 = 8728  #
    b[r6++=1] = r0
    r0 += r14
    r1 = r6 - r0
    goto L02011a54
L02011f18:
    r2 = [sp+536]
    r3 = 20000
    if (r2 > r3) goto L02012418
    if (r1 != 81) goto L02012418
    r7 = [sp+540]
    if (r7 >= 3) goto L02012418
L02011f36:
    r8 = [sp+532]
    r3 = 1
    r9 = -2
    r4 = 1
    if ((r8 & r9) != 0) {
    r4 = 0
    }
    if (r0 != 3) {  ; @if.ne.ri.s12
    r3 = 0
    }
    r3 |= r4
    if (r0 != 4) goto L0201202e
    if (r3 == 0) goto L0201202e
    r6 = 1
    if (r1 != 81) {  ; @if.ne.ri.s12
    r6 = 0
    }
    r0 = r6
    call slot_queries_group_count  ; @call.xl
    r3 = 16
    ifs (r7 >= r0) {
    r3 = 1
    }
    r1_r0 = r7_r6
    r2 = r8
    call preset_band_controls_set_band_flag  ; @call.xl
    r2 = [sp+536]
    r7 = [sp+540]
    r1 = b[sp+547] (u)
    goto L02012034
L02011f86:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201201a
    r0 = r5
    call phase3_p12_atoi  ; @call.xl
    call preset_band_controls_request_reserve
    if (r0 == 0) goto L0201201a
L02011f98:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 7712
    goto L02012424
L02011fa6:
    call dispatch_helpers_buffer_release
L02011faa:
    r0 = [r14+464]
    r3 = b[r14+25] (u)
    r1 = 30
    if (r3 != 1) {  ; @if.ne.ri.s12
    r1 = 26
    }
    r2 = [r14+460]
    r1 = 8728  #
    [sp+8] = r1
    r5 = r14 + r1  #
    [sp+4] = r2
    r2 = r15 + 6149
    goto L02011736
L02011fd2:
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 5832
L02011fde:
    r1 = 512
    [sp] = r8  ; @st.w.sp.l
    goto L02011c42
L02011fe8:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L020120d6
    call audio_pause_pause_audio
    r0 = r5
    call phase3_p12_atoi  ; @call.xl
    call path_switch_switch_path
    r5 = r0
    call audio_pause_resume_audio
    if (r5 == -110) goto L020121f6
    if (r5 == 0) goto L020120d6
    if (r5 == -4) goto L02011f98
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 5795
    goto L02011c3e
L0201201a:
    r0 = 8728
    r5 = r14 + r0
    call slot_commands_requested
    r3 = r0
    r2 = r15 + 1030
    goto L02011ba4
L0201202e:
    if (r3 == 0) goto L02012418
L02012034:
    r0 = 0
    r1 = r1.b0 (u)  #
    [sp] = r0
    r0 = 1
    if (r1 != 81) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r3 = 16
    r1 = r7
    call preset_band_controls_set_crossover  ; @call.xl
    if (r0 == 0) goto L020120fc
    call dispatch_helpers_error_text
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1942
    goto L02011ba4
L02012062:
    r0 = -1
    [sp+508] = r0
    r0 = 0
    [sp+504] = r0
    r1 = r15 + 815
    r2 = sp + 508
    r3 = sp + 504
    r0 = r5
    call L0200b7c2
    if (r0 == 2) {  ; @if.eq.ri.s12
    r1 = [sp+504]
    r0 = [sp+508]
    call biquad_coefficients_stage  ; @call.xl
    }
    r0 = 0
    call biquad_pipeline_parameter  ; @call.xl
    r8 = r0
    r0 = 1
    call biquad_pipeline_parameter  ; @call.xl
    r6 = r0
    r0 = 2
    call biquad_pipeline_parameter  ; @call.xl
    r7 = r0
    r0 = 3
    call biquad_pipeline_parameter  ; @call.xl
    r5 = r0
    r0 = 4
    call biquad_pipeline_parameter  ; @call.xl
    r0 = 8728  #
    [sp+12] = r0
    r5 = r14 + r0  #
    [sp+8] = r5
    r2 = r15 + 3478  #
    [sp+4] = r7
    goto L02012142
L020120d6:
    call preset_application_mode
    r5 = r0
    r1 = sp + 514
    r0 = 0
    call preset_application_chain_read  ; @call.xl
    r1 = 8728
    r6 = r14 + r1
    r2 = r15 + 1676
L020120f4:
    r1 = 512  #
    [sp] = r0
    goto L02011c42
L020120fc:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201214a
    r8 = b[sp+547] (s)
    r7 = 1
    r0 = 1
    if (r8 != 81) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r6 = [sp+540]
    r1 = r6
    call slot_queries_group_value  ; @call.xl
    r1 = b[sp+547] (u)
    r5 = r0
    if (r1 != 81) {  ; @if.ne.ri.s12
    r7 = 0
    }
    r1 = [sp+540]
    r0 = r7
    call preset_band_controls_band_flag  ; @call.xl
    r0 = 8728  #
    [sp+8] = r0
    r5 = r14 + r0  #
    [sp+4] = r5
    r2 = r15 + 3089
L02012142:
    r1 = 512  #
    [sp] = r6
    goto L0201231c
L0201214a:
    call dispatch_helpers_crossover_list
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1343
L0201215a:
    r1 = 512
    r0 = r5
    call L0200691e
    goto L02011742
L02012168:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L020122c6
    r2 = sp + 480
    r0 = r2 + 20
    [sp+12] = r0
    r0 = r2 + 16
    [sp+8] = r0
    r0 = r2 + 12
    [sp+4] = r0
    r0 = r2 + 8
    r1 = r15 + 3107  #
    [sp] = r0
    r8 = r2 + 4
    r0 = r5
    r3 = r8
    call L0200b7c2
    r5 = r0
    r7 = 0
    goto L020121aa
L02012198:
    r0 = r7
    call audio_measurement_control_value  ; @call.xl
    r1 = sp + 468
    h[r1+r7<<1] = r0
    r7 += 1  ; @add.ri.u5
L020121aa:
    if (r7 != 6) goto L02012198
    if (r5 == 2) goto L0201229a
    if (r5 != 6) goto L02012418
    r5 = 0
    goto L020121d6
L020121bc:
    r0 = sp + 480
    r1 = [r0+r5<<2]
    r0 = r5
    call dsp_transition_clamp  ; @call.xl
    r1 = sp + 468
    h[r1+r5<<1] = r0
    r5 += 1  ; @add.ri.u5
L020121d6:
    if (r5 != 6) goto L020121bc
    goto L020122b8
L020121dc:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201226e
    r0 = r5
    call phase3_p12_atoi  ; @call.xl
    r5 = r0
    r0 = r5 + -1
    r0 = r0 >> 3
    if (r0 < 625) goto L02012272
    goto L02012418
L020121f6:
    r0 = 8728
    r5 = r14 + r0
    r0 = 8968
    r3 = r15 + r0
    r2 = r15 + 1955
    goto L02011ba4
L0201220c:
    r0 = 0
    [sp+452] = r0
    [sp+448] = r0
    [sp+444] = r0
    r0 = sp + 464
    r1 = sp + 460
    r2 = sp + 456
    call dsp_dynamics_get  ; @call.xl
    r0 = sp + 444
    r1 = r15 + 1325  #
    [sp] = r0
    r2 = sp + 452
    r3 = sp + 448
    r0 = r5
    call L0200b7c2
    r2 = r0
    ifs (r2 < 1) goto L020123cc
    r1 = [sp+452]
    r0 = 1
    if (r1 != 0) goto L02012254
    r0 = r1
L02012254:
    [sp+464] = r0
    if (r2 != 1) goto L0201238a
    r1 = [sp+460]
    goto L0201239e
L02012262:
    r0 = r6
    r1 = r5
    call dispatch_helpers_stereo_command
    goto L02011a58  ; @goto.l
L0201226e:
    r5 = 1000
L02012272:
    r0 = [r14+280]
    if (r0 == 0) goto L02012324
    r0 = b[r14+212] (u)
    if (r0 != 0) goto L0201228c
    r0 = r5
    call audio_measurement_measure_start  ; @call.xl
    if (r0 == 0) goto L020124a6  ; @beq.ri.l
L0201228c:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 2676
    goto L0201215a
L0201229a:
    r0 = [sp+480]
    if (r0 > 5) goto L02012418
    r1 = [r8+0]
    call dsp_transition_clamp  ; @call.xl
    r1 = [sp+480]
    r2 = sp + 468
    h[r2+r1<<1] = r0
L020122b8:
    r1 = b[r9+0] (u)
    r0 = sp + 468
    call dsp_transition_request  ; @call.xl
L020122c6:
    r0 = 0
    call audio_measurement_control_value  ; @call.xl
    r8 = r0
    r0 = 1
    call audio_measurement_control_value  ; @call.xl
    r9 = r0
    r0 = 2
    call audio_measurement_control_value  ; @call.xl
    r7 = r0
    r0 = 3
    call audio_measurement_control_value  ; @call.xl
    r5 = r0
    r0 = 4
    call audio_measurement_control_value  ; @call.xl
    r6 = r0
    r0 = 5
    call audio_measurement_control_value  ; @call.xl
    r0 = 8728  #
    [sp+16] = r0
    r1 = 512  #
    [sp+12] = r6
    r5 = r14 + r0  #
    [sp+8] = r5
    r2 = r15 + 7889  #
    [sp+4] = r7
    [sp] = r9  ; @st.w.sp.l
L0201231c:
    r0 = r5
    r3 = r8
    goto L0201173e
L02012324:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 6191
    goto L0201215a
L02012332:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02012362
    r1 = sp + 436
    r2 = 10
    r0 = r5
    call capture_command_decimal  ; @call.xl
    r1 = [sp+436]
    r1 += -1
L0201234a:
    r2 = b[++r1=1] (u)
    if (r2 == 32) goto L0201234a
    [sp+436] = r1
    if (r5 == r1) goto L02012418
    if (r2 != 0) goto L02012418
    call butterworth_table_butterworth_table
    if (r0 != 0) goto L02012418
L02012362:
    r0 = 3245
    r3 = [r14+r0<<2]
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1494
    goto L02011ba4
L02012378:
    r3 = r15 + 2208
L0201237c:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1664
    goto L02011ba4
L0201238a:
    r1 = [sp+448]
    [sp+460] = r1
    ifs (r2 >= 3) {  ; @ifs.ge.ri.s12
    r2 = [sp+444]
    [sp+456] = r2
    }
L0201239e:
    r2 = r1 + 200
    if (r2 > 200) goto L02012418
    r2 = [sp+456]
    r3 = r2 + -10
    if (r3 >= 1991) goto L02012418
    call dsp_dynamics_configure  ; @call.xl
    r0 = sp + 464
    r1 = sp + 460
    r2 = sp + 456
    call dsp_dynamics_get  ; @call.xl
L020123cc:
    r0 = sp + 440
    r1 = 0
    call dsp_dynamics_meter  ; @call.xl
    r3 = [sp+464]
    r0 = [sp+460]
    r1 = [sp+456]
    r2 = [sp+440]
    [sp+12] = r2
    r2 = 48
    [sp+8] = r2
    r1 = 8728  #
    [sp+4] = r1
    r5 = r14 + r1
    r2 = r15 + 6317
    goto L02011736
L02012400:
    r1 = 0
    r2 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r5 = r0
    r0 = r5 + -1
    r0 = r0 >> 8
    if (r0 < 375) goto L020124bc
L02012418:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 2166
L02012424:
    r1 = 512
L02012428:
    r0 = r5
    r3 = r6
    goto L0201173e
L02012430:
    r1 = sp + 432
    r2 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r12 = [r14+312]
    r1 = [r14+316]
    r7 = [sp+432]
    r9 = r0
L0201244c:
    r0 = r7
    r2 = b[r0+0] (u)
    r7 = r0 + 1
    if (r2 == 32) goto L0201244c
    [sp+432] = r0
    r10 = r12 + r9
    r11 = r1 << 1
    r8 = 0
    r4 = -1
    r3 = 0
    goto L020124a0
L0201246a:
    r1 = r7
    r0 = b[++r1=r4] (u)
    if (r0 == 0) goto L020124dc
    r6 = b[r1+1] (u)
    if (r6 == 0) goto L020124dc
    r1 = r9 + r3
    if (r1 >= r11) goto L020124dc
    r0 = r0.b0 (s)
    call bond_records_and_prints_hex_value
    r5 = r0
    r0 = r6.b0 (s)
    call bond_records_and_prints_hex_value
    r1 = r0 | r5
    ifs (r1 < 0) goto L020124dc
    r1 = r5 << 4
    r0 += r1  ; @add.rr
    b[r10+r3] = r0
    r4 += 2  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L020124a0:
    if (r12 != 0) goto L0201246a
    goto L020124de
L020124a6:
    r0 = 1
    b[++r14=212] = r0
    call state_queries_tenfold_word
    [r14+4] = r0
    [r14+8] = r5
    goto L02011a58
L020124bc:
    r0 = r5
    call dispatch_helpers_scope_buffer
    if (r0 == 0) goto L02012586
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 5510
    r3 = r5 << 1
    r1 = 512
    r0 = r6
    goto L02011a48
L020124dc:
    r8 = r3
L020124de:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 2434
    goto L02011a6c
L020124ee:
    r1 = r15 + 59
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020125c4
    r1 = r15 + 214
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020126c4
    r1 = r15 + 330
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020126be
    r0 = b[r5+0] (u)
    if (r0 != 0) goto L02012418  ; @bne.ri
    goto L020126ca
L02012524:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201260a
    r0 = -1
    [sp+428] = r0
    [sp+424] = r0
    r1 = r15 + 815
    r2 = sp + 428
    r3 = sp + 424
    r0 = r5
    call L0200b7c2
    ifs (r0 < 1) goto L02012418
    r1 = [sp+428]
    if (r1 > 170) goto L02012418
    r2 = [sp+424]
    if (r0 != 2) goto L0201255c
    if (r2 >= 2) goto L02012418
L0201255c:
    r1 = r1 * 0x3E8
    r1 = r1 + 1331
    r3 = 2662
    r1 = r1 / r3 (s)
    ifs (r1 <= 1) {  ; @ifs.le.ri.s12
    r1 = 1
    }
    b[r9+0] = r1
    if (r0 != 2) goto L0201260e
    r0 = 1
    if (r2 != 0) goto L02012580
    r0 = r2
L02012580:
    b[r8+8] = r0
    goto L0201260e
L02012586:
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 2692
    goto L02011c3e
L02012596:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L020125a8
    r0 = r5
    call phase3_p12_atoi  ; @call.xl
    call slot_queries_set_flag  ; @call.xl
L020125a8:
    call slot_queries_flag  ; @call.xl
    r5 = r0
    call slot_queries_slots_counted  ; @call.xl
    r1 = 8728
    r6 = r14 + r1
    r2 = r15 + 3326
    goto L020120f4
L020125c4:
    r0 = 1
    call dispatch_helpers_scope_arm
    ifs (r0 > -1) goto L020126ca
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 6721
    goto L0201215a
L020125dc:
    r1 = 0
    r2 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r5 = r0
    r4 = r5 + -1
    call ir_reload_and_leaves_buffer_free
    if (r4 < 8192) goto L020126ec
    r0 = 8192
    r1 = 8728
    r6 = r14 + r1
    r2 = r15 + 5146
    goto L020120f4
L0201260a:
    r1 = b[r9+0] (u)
L0201260e:
    r0 = r1.b0 (u)
    r3 = 0
    if (r0 >= 2) {  ; @if.ge.ri.s12
    r1 = 2662
    r1 *= r0
    r2 = 1000
    r3 = r1 / r2 (u)
    }
    r1 = b[r8+8] (u)
    r1 = 8728  #
    [sp+4] = r1
    r5 = r14 + r1
    r2 = r15 + 4991
    goto L02011736
L0201263a:
    r1 = sp + 420
    r2 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r4 = [sp+420]
    r9 = r0
L0201264e:
    r0 = r4
    r1 = b[r0+0] (u)
    r4 = r0 + 1
    if (r1 == 32) goto L0201264e
    r10 = [r14+256]
    [sp+420] = r0
    r8 = r10 + r9
    r6 = 0
    r3 = -1
    goto L020126a4
L0201266a:
    r1 = r4
    r0 = b[++r1=r3] (u)
    if (r0 == 0) goto L020126a8
    r7 = b[r1+1] (u)
    if (r7 == 0) goto L020126a8
    r1 = [r14+260]
    r2 = r9 + r6
    if (r2 >= r1) goto L020126a8
    r0 = r0.b0 (s)
    call bond_records_and_prints_hex_value
    r5 = r0
    r0 = r7.b0 (s)
    call bond_records_and_prints_hex_value
    r1 = r0 | r5
    ifs (r1 < 0) goto L020126a8
    r1 = r5 << 4
    r0 += r1  ; @add.rr
    b[r8+r6] = r0
    r3 += 2  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L020126a4:
    if (r10 != 0) goto L0201266a
L020126a8:
    r0 = 8728  #
    [sp] = r6
    r5 = r14 + r0
    r2 = r15 + 2180
    r1 = 512
    goto L02011a74
L020126be:
    r0 = 0
    call dispatch_helpers_scope_buffer
L020126c4:
    r0 = 0
    call dispatch_helpers_scope_arm
L020126ca:
    r1_r0 = d[r14+316]
    r3 = b[r14+18] (u)
    d[sp] = r1_r0
    r1 = 8728
    r5 = r14 + r1
    if (r3 != 1) {  ; @if.ne.ri.s12
    r3 = 0
    }
    r2 = r15 + 4814
    goto L02011ba4
L020126ec:
    call block_pool_maintain_wrapper
    if (r0 == 0) goto L02012844
    r0 = 8728
    r5 = r14 + r0
    r0 = 8968
    r3 = r15 + r0
    r2 = r15 + 2708
    goto L02011ba4
L0201270c:
    r1 = 0
    r2 = 16
    r6 = 0
    r0 = r5
    call L020285bc  ; @call.xl
    r5 = [r14+256]
    r1 = [r14+260]
    r7 = r0
    if (r5 == 0) goto L0201272e
    r0 = r5
    call record_helpers_checksum
    r6 = r0
L0201272e:
    if (r7 != r6) goto L02012830
    if (r1 == 0) goto L02012830
    call state_queries_tenfold_word
    r6 = r0
    r3_r2 = 0
    r4 = 0
    r0 = r5
    call capture_container_install
    r5 = r0
    call state_queries_tenfold_word
    r7 = r0
    call ir_reload_and_leaves_buffer_free
    r0 = 20
    r1 = 512
    r2 = r5
    call storage_coordination_notify
    r7 = r7 - r6
    if (r5 != 0) goto L02012768
    r0 = 1
    r1 = 0
    call preset_application_services_clear_assets
L02012768:
    [sp+396] = r4
    [sp+392] = r4
    r6 = sp + 403
    r1 = sp + 396
    r2 = sp + 392
    r0 = r6
    call dispatch_helpers_capabilities
    r0 = [sp+396]
    r1 = [sp+392]
    r2 = [r14+280]
    r3 = [r14+416]
    r3 = r15 + 190  #
    [sp+20] = r7
    d[sp+12] = r3_r2
    d[sp+4] = r1_r0
    r0 = 8728
    r7 = r14 + r0
    r0 = 8544
    r2 = r15 + r0
    goto L02011e9a
L020127b4:
    r0 = 0
    [sp+368] = r0
    [sp+364] = r0
    r0 = sp + 375
    r1 = sp + 368
    r2 = sp + 364
    call dispatch_helpers_capabilities
    r1 = r14 + 696
    r5 = r0  #
    r4 = [r1+8]
    {r7, r1} = [r1+]
    r1 = r1 * 0x5
    r0 = sp + 352
    call dispatch_helpers_tenths_text
    r6 = sp + 340
    r1_r0 = r7_r6
    call dispatch_helpers_tenths_text
    r1 = [sp+364]
    r0 = [sp+368]
    r2 = [r14+416]
    if (r4 == 0) {  ; @if.eq.ri.s12
    r2 = r15
    r6 = r15
    } else {
    r2 = r15 + 415
    }
    [sp+24] = r6
    [sp+20] = r2
    r2 = sp + 352
    r2 = r15 + 190  #
    [sp+16] = r2
    [sp+12] = r2
    [sp+8] = r5
    r1 = 8728  #
    [sp+4] = r1
    r5 = r14 + r1
    r2 = r15 + 8144
    r3 = sp + 375
    goto L02011736
L02012830:
    r0 = 8728  #
    [sp] = r7
    r5 = r14 + r0
    r2 = r15 + 4646
    r1 = 512
    goto L02012428
L02012844:
    r0 = r5 + 7
    r6 = r0 & 0xFFFFFFF8
    r0 = r6
    call L0203c15c  ; @call.xl
    [r14+256] = r0
    if (r0 == 0) goto L020128fe
    r1 = 0
    r2 = r6
    call effect_enable_memset  ; @call.xl
    [r14+260] = r5
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 2449
    goto L02011c3e
L02012876:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02012a14
    r1 = r15 + 118
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020128ca
    r1 = r15 + 355
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020128ca
    r1 = r15 + 190
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020128ca
    r1 = r15 + 851
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020128ca
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 5946
    goto L0201215a
L020128c2:
    call auth_memory_report_memory_report
    goto L02011a58
L020128ca:
    r1 = r15 + 355
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012a62
    r1 = r15 + 190
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020128fa
    r1 = r15 + 851
    r0 = r5
    call L02028308  ; @call.xl
    r6 = 0
    if (r0 != 0) goto L02012a64
L020128fa:
    r6 = 2
    goto L02012a64
L020128fe:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 4483
    goto L0201215a
L0201290c:
    r0 = 0
    [sp+336] = r0
    r1 = 0
    d[sp+328] = r1_r0
    d[sp+320] = r1_r0
    r0 = 99
    [sp+316] = r0
    r6 = sp + 320
    r1 = r15 + 1688  #
    [sp] = r6
    r2 = sp + 336
    r3 = sp + 316
    r0 = r5
    call L0200b7c2
    r0 = r6
    call dispatch_helpers_effect_number
    r3 = [sp+316]
    r6 = r0
    r0 = 32
    r2 = 0
    r1 = r6
    call audio_pause_breadcrumb
    call audio_pause_pause_audio
    r0 = 33
    r3_r2 = 0
    r1 = r6
    call audio_pause_breadcrumb
    r0 = b[sp+336] (u)
    call dispatch_helpers_path_letter
    r1 = [sp+316]
    r2 = r6
    call effect_setup_create  ; @call.xl
    r5 = r0
    if (r5 != -3) goto L02012994
    call effect_parameter_lifecycle_resource_flush  ; @call.xl
    r0 = b[sp+336] (u)
    call dispatch_helpers_path_letter
    r1 = [sp+316]
    r2 = r6
    call effect_setup_create  ; @call.xl
    r5 = r0
L02012994:
    r2 = r5
    ifs (r5 <= -1) {  ; @ifs.le.ri.s12
    r2 = 0
    }
    r0 = 34
    r1 = r6
    r3 = r5
    call audio_pause_breadcrumb
    call audio_pause_resume_audio
    ifs (r5 < 0) goto L02012b4e
    r0 = 35
    r3 = 0
    r1 = r6
    r2 = r5
    call audio_pause_breadcrumb
    r0 = r5
    call dispatch_helpers_bank_bit_clear
    r0 = 36
    r3 = 0
    r1 = r6
    r2 = r5
    call audio_pause_breadcrumb
    r0 = r5
    call preset_application_effect_type  ; @call.xl
    call console_reports_type_name  ; @call.xl
    r1 = 8728  #
    [sp] = r0
    r6 = r14 + r1
    r2 = r15 + 2194
    r1 = 512
    r0 = r6
    r3 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    r0 = r15 + 23
    call dispatch_helpers_cpu_line
    r1_r0 = 0
    r3_r2 = 0
    call audio_pause_breadcrumb
    goto L02011a58
L02012a14:
    r3 = [r14+280]
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 2464
    goto L02011ba4
L02012a28:
    call audio_pause_pause_audio
    r1 = 0
    r2 = 10
    r0 = r5
    call capture_command_decimal  ; @call.xl
    r5 = r0
    call effect_ownership_remove  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L02012bd6
    call audio_pause_resume_audio
    r0 = r6
    call dispatch_helpers_error_text
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1712
    goto L02011ba4
L02012a62:
    r6 = 1
L02012a64:
    r0 = [r14+280]
    if (r6 == 0) goto L02012a8a
    if (r6 != r0) goto L02012a8a
    r1 = r15 + 851
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02012a8a
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 3989
    goto L02012424
L02012a8a:
    r1 = r15 + 851
    r0 = r5
    call L02028308  ; @call.xl
    r1 = r0
    r0 = 1
    if (r1 != 0) goto L02012a9e
    r0 = r1
L02012a9e:
    call ram_callbacks_empty_hook  ; @call.xl
    call state_queries_tenfold_word
    r5 = r0
    r0 = r6
    call mode_and_settings_mode_service
    r3 = [r14+280]
    r6 = r0
    call state_queries_tenfold_word
    r0 = r0 - r5
    r0 = 8728  #
    [sp+4] = r0
    r5 = r14 + r0  #
    [sp] = r6
    r2 = r15 + 3768
    r1 = 512
    goto L0201173c
L02012ad4:
    r0 = 0
    [sp+312] = r0
    r0 = -1
    [sp+308] = r0
    r0 = 99
    [sp+304] = r0
    r0 = sp + 304
    r1 = r15 + 1353  #
    [sp] = r0
    r2 = sp + 308
    r3 = sp + 312
    r0 = r5
    call L0200b7c2
    call audio_pause_pause_audio
    r3 = [sp+308]
    r0 = b[sp+312] (u)
    call dispatch_helpers_path_letter
    r2 = [sp+304]
    r1 = r0
    r0 = r3
    call slot_queries_slot_move  ; @call.xl
    r1 = r15 + 1363
    r5 = r15 + 1724
    r6 = r0
    if (r6 != 0) goto L02012b2a
    r5 = r1
L02012b2a:
    call audio_pause_resume_audio
    if (r6 == 0) goto L02012b38
    r0 = r6
    call dispatch_helpers_error_text
    r15 = r0
L02012b38:
    r0 = 8728
    r6 = r14 + r0
    r1 = 512
    r0 = r6
    r2 = r5
    r3 = r15
    goto L02011a48
L02012b4e:
    r1_r0 = 0
    r3_r2 = 0
    call audio_pause_breadcrumb
    if (r5 == -4) goto L02012c5c
    if (r5 != -1) goto L02012c6a
    r0 = sp + 320
    call dispatch_helpers_effect_number
    if (r0 != 7) goto L02012c6a
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 6448
    goto L0201215a
L02012b7a:
    r0 = -1
    [sp+300] = r0
    r0 = 1
    [sp+296] = r0
    r1 = r15 + 815
    r2 = sp + 300
    r3 = sp + 296
    r0 = r5
    call L0200b7c2
    r1 = [sp+296]
    r0 = [sp+300]
    call slot_commands_enable_command
    r5 = r0
    if (r5 == 0) goto L02012cbc
    if (r5 != -4) goto L02012bbe
    r0 = [sp+300]
    call preset_application_effect_type  ; @call.xl
    r1 = 1
    call dispatch_helpers_cpu_notify
L02012bbe:
    r0 = r5
    call dispatch_helpers_error_text
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1736
    goto L02011ba4
L02012bd6:
    r0 = r5
    call dispatch_helpers_bank_bit_clear
    call audio_pause_resume_audio
    r0 = r15 + 858
    call dispatch_helpers_cpu_line
    goto L02011a58
L02012bec:
    r0 = -1
    [sp+292] = r0
    [sp+288] = r0
    r0 = 0
    [sp+284] = r0
    r0 = sp + 284
    r1 = r15 + 1325  #
    [sp] = r0
    r2 = sp + 292
    r3 = sp + 288
    r0 = r5
    call L0200b7c2
    r3 = b[r9+0] (u)
    r2 = [sp+284]
    r1 = [sp+288]
    r0 = [sp+292]
    call dispatch_helpers_parameter_apply
    r5 = r0
    if (r5 == -4) goto L0201304c
    if (r5 == -3) goto L02013024
    if (r5 != 0) goto L0201305c
    r1 = [sp+288]
    r0 = [sp+292]
    call preset_application_parameter  ; @call.xl
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1505
    goto L02011ba4
L02012c5c:
    r0 = sp + 320
    call dispatch_helpers_effect_number
    r1 = 0
    call dispatch_helpers_cpu_notify
L02012c6a:
    r0 = r5
    call dispatch_helpers_error_text
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1700
    goto L02011ba4
L02012c82:
    r6 = -1
    [sp+280] = r6
    [sp+276] = r6
    r1 = r15 + 815
    r2 = sp + 280
    r3 = sp + 276
    r0 = r5
    call L0200b7c2
    if (r0 == 2) goto L0201307c
    if (r0 != 1) goto L020130ac
    r0 = [sp+280]
    call slot_queries_slot_mode  ; @call.xl
    ifs (r0 >= 0) goto L020130c4
    goto L020130ac
L02012cbc:
    r0 = r15 + 865
    call dispatch_helpers_cpu_line
    goto L02011a58
L02012cc8:
    r0 = 0
    goto L02012e7c
L02012ccc:
    r0 = 81
    [sp+104] = r0
    r0 = [sp+100]
    if (r0 != 0) goto L02012cd8
    r0 = 80
    [sp+104] = r0
L02012cd8:
    r1 = sp + 266
    r0 = [sp+100]
    call preset_application_chain_read  ; @call.xl
    [sp+108] = r0
    r0 = 0
    [sp+128] = r0
    goto L02012e70
L02012cec:
    r0 = sp + 266
    r1 = [sp+128]
    r5 = b[r0+r1] (u)
    r0 = r5
    call preset_application_effect_type  ; @call.xl
    r6 = r0
    r0 = sp + 242
    r1 = 0
    rep 24 {
    b[r0++=1] = r1
    }
    if (r6 != 7) goto L02012d4c
    r0 = r5
    call ir_block_load_ir_word  ; @call.xl
    if (r0 == 0) goto L02012d4c
    r0 = r5
    call slot_queries_slot_ir_blocks  ; @call.xl
    r7 = r0
    r0 = r5
    call ir_block_load_ir_word  ; @call.xl
    r3 = r0
    if (r7 != 0) goto L02012d3c
    r0 = L01c1f7d0
    r0 = [r0+0]
    r7 = 48
    if (r0 != 0) goto L02012d3c
    r7 = 24
L02012d3c:
    r2 = r15 + 1981  #
    [sp] = r7
    r0 = sp + 242
    r1 = 24
    call L0200691e
L02012d4c:
    r0 = r5
    call slot_queries_slot_parts  ; @call.xl
    r3 = r0
    r0 = 0
    [sp+236] = r0
    r1 = 0
    d[sp+228] = r1_r0
    if (r3 >= 2) {  ; @if.ge.ri.s12
    r2 = r15 + 1046
    r0 = sp + 228
    r1 = 12
    call L0200691e
    }
    r0 = r6
    call console_reports_type_name  ; @call.xl
    r0 = r5  #
    [sp+124] = r0
    call preset_application_effect_enabled  ; @call.xl
    r0 = r5  #
    [sp+120] = r0
    r1 = 0
    call preset_application_parameter  ; @call.xl
    r0 = r5  #
    [sp+116] = r0
    r1 = 1
    call preset_application_parameter  ; @call.xl
    r0 = r5  #
    [sp+112] = r0
    r1 = 2
    call preset_application_parameter  ; @call.xl
    r6 = r0
    r1 = 3
    r0 = r5
    call preset_application_parameter  ; @call.xl
    r7 = r0
    r1 = 4
    r0 = r5
    call preset_application_parameter  ; @call.xl
    r8 = r0
    r1 = 5
    r0 = r5
    call preset_application_parameter  ; @call.xl
    r9 = r0
    r1 = 6
    r0 = r5
    call preset_application_parameter  ; @call.xl
    r1 = L01c343d8
    r4 = [r1+r5<<2]
    r10 = r0
    r0 = r5
    call preset_application_placement  ; @call.xl
    r11 = r0
    r0 = r5
    call slot_queries_slot_position  ; @call.xl
    r12 = r0
    r0 = r5
    call slot_queries_slot_route  ; @call.xl
    r13 = r0
    r0 = r5
    call slot_queries_slot_memory  ; @call.xl
    r1 = sp + 228
    d[sp+64] = r1_r0
    r0 = sp + 242
    r1 = 512  #
    [sp+60] = r0
    d[sp+52] = r13_r12
    [sp+48] = r11  ; @st.w.sp.l
    [sp+44] = r4
    [sp+40] = r10  ; @st.w.sp.l
    d[sp+32] = r9_r8
    d[sp+24] = r7_r6
    r0 = [sp+112]
    [sp+20] = r0
    r0 = [sp+116]
    [sp+16] = r0
    r0 = [sp+120]
    [sp+12] = r0
    r0 = [sp+124]
    r0 = 8728  #
    [sp+8] = r0
    r5 = r14 + r0  #
    [sp+4] = r5
    r0 = 9195  #
    r4 = [sp+128]
    r2 = r15 + r0  #
    [sp] = r4
    r0 = r5  #
    r3 = [sp+104]
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r4 += 1  ; @add.ri.u5
    [sp+128] = r4
L02012e70:
    r0 = [sp+108]
    r1 = [sp+128]
    ifs (r1 < r0) goto L02012cec
    r0 = [sp+100]
    r0 += 1  ; @add.ri.u5
L02012e7c:
    [sp+100] = r0
    r0 = [sp+100]
    if (r0 != 2) goto L02012ccc
    call dispatch_helpers_mix_list
    call dispatch_helpers_crossover_list
    call preset_application_mode
    r3 = r0
    call slot_commands_requested
    r1 = 8728  #
    [sp] = r0
    r5 = r14 + r1
    r2 = r15 + 3125
    r1 = 512
    r0 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = [sp+96]
    call dispatch_helpers_cpu_line
    r0 = L01c34430
    r8 = [r0+0]
    r0 = L01c34420
    r9 = [r0+0]
    r0 = L01c34438
    r10 = [r0+0]
    r0 = L01c34450
    r11 = [r0+0]
    r0 = L01c34428
    r12 = [r0+0]
    r0 = L01c341a4
    r7 = [r0+0]
    r0 = L01c341bc
    r6 = [r0+0]
    r0 = L01c34424
    r4 = [r0+0]
    call ram_callbacks_zero_leaf  ; @call.xl
    r0 = 8613  #
    [sp+28] = r0
    r2 = r15 + r0  #
    [sp+24] = r4
    r1 = 512  #
    [sp+20] = r6
    r0 = r5  #
    [sp+16] = r7
    [sp+12] = r12  ; @st.w.sp.l
    d[sp+4] = r11_r10
    [sp] = r9  ; @st.w.sp.l
    r3 = r8
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = L01c34448
    r3 = [r0+0]
    r0 = L01c340c4
    r0 = [r0+0]
    r1 = L01c34184
    r1 = [r1+0]
    r2 = L01c34190
    r2 = [r2+0]
    r4 = L01c34188
    r4 = [r4+0]
    r6 = L01c34174
    r6 = [r6+0]
    r7 = L01c340c8
    r7 = [r7+0]
    d[sp+16] = r7_r6
    [sp+12] = r4
    r2 = r15 + 7376  #
    [sp+8] = r2
    d[sp] = r1_r0
    r1 = 512
    r0 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = r14 + 472
    r3 = [r0+12]
    r8 = [r0+0]
    r9 = [r0+4]
    r10 = [r0+8]
    call preset_application_rate
    r1 = r14 + 336
    r4 = [r1+0]
    r6 = [r1+4]
    r2 = r0  #
    r7 = [r1+8]
    call preset_application_rate
    r1 = [r14+668]
    r1 = 1000  #
    [sp+24] = r1
    r0 = r0 / r1 (u)
    r0 = r7 / r0 (u)
    r0 = r2 / r1 (u)  #
    [sp+20] = r0
    r0 = r10 / r0 (u)  #
    [sp+16] = r6
    r1 = 512  #
    [sp+12] = r4
    r0 = 10400  #
    [sp+8] = r0
    d[sp] = r9_r8
    r2 = r15 + r0
    r0 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = L01c343c8
    r2 = r15 + 4901  #
    r3 = [r0+0]
    r0 = L01c3445c
    r0 = [r0+0]
    goto L02011736
L02013024:
    r0 = -3
    call dispatch_helpers_error_text
    r1 = [sp+288]
    r2 = [sp+292]
    r5 = r0
    r0 = r2
    call preset_application_parameter  ; @call.xl
    r1 = 8728
    r6 = r14 + r1
    r2 = r15 + 3684
    goto L020120f4
L0201304c:
    r0 = [sp+292]
    call preset_application_effect_type  ; @call.xl
    r1 = 2
    call dispatch_helpers_cpu_notify
L0201305c:
    r0 = r5
    call dispatch_helpers_error_text
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1748
    goto L02011ba4
L02013074:
    call console_reports_effect_table
    goto L02011a58
L0201307c:
    call audio_pause_pause_audio
    r1 = [sp+276]
    r0 = [sp+280]
    call slot_queries_slot_set_mode  ; @call.xl
    r6 = r0
    call audio_pause_resume_audio
    if (r6 == 0) goto L020130c4
    if (r6 != -4) goto L020130ac
    r0 = [sp+280]
    call preset_application_effect_type  ; @call.xl
    r1 = 2
    call dispatch_helpers_cpu_notify
    r6 = -4
L020130ac:
    r0 = r6
    call dispatch_helpers_error_text
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1968
    goto L02011ba4
L020130c4:
    r5 = [sp+280]
    r0 = r5
    call preset_application_effect_type  ; @call.xl
    call console_reports_type_name  ; @call.xl
    r1 = [sp+280]
    r8 = r0
    r0 = r1
    call slot_queries_slot_mode  ; @call.xl
    r1 = [sp+280]
    r9 = r0
    r0 = r1
    call slot_queries_slot_mode_value  ; @call.xl
    r1 = [sp+280]
    r6 = r0
    r0 = r1
    call preset_application_effect_type  ; @call.xl
    r1 = [sp+280]
    r7 = r0
    r0 = r1
    call slot_queries_slot_mode  ; @call.xl
    r1 = r0
    r0 = r7
    call slot_queries_mode_cost  ; @call.xl
    r1 = [sp+280]
    r2 = L01c343d8
    r1 = [r2+r1<<2]
    d[sp+12] = r1_r0
    r0 = 8728  #
    [sp+8] = r6
    [sp+4] = r9  ; @st.w.sp.l
    r6 = r14 + r0
    r2 = r15 + 6769
    goto L02011fde
L02013140:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02013174
    r1 = r15 + 815
    r2 = sp + 224
    r3 = sp + 220
    r0 = r5
    call L0200b7c2
    if (r0 != 2) goto L02012418
    r1 = [sp+220]
    r0 = [sp+224]
    call preset_application_services_set_levels
    call control_actions_clock
    r1 = r0 + 4000
    [r14+808] = r1
    [r14+812] = r0
L02013174:
    r0 = 1038
    r3 = [r14+r0<<2]
    r0 += 1  ; @add.ri.u5
    r0 = [r14+r0<<2]
    r1 = 8728
    r5 = r14 + r1
    r2 = r15 + 3790
    goto L02011736
L02013192:
    call console_reports_level_record
    r0 = 8728
    r4 = r14 + r0
    call console_reports_level_line
    r1 = r0
    r0 = r4
    call command_services_console_send
    r0 = b[r14+50] (u)
    if (r0 != 0) goto L02011a58
    r0 = 952
    r0 = b[r14+r0] (u)
    if ((r0 & 0x1) != 0) goto L02011a58
    r0 = [r9+0]
    [r14+948] = r0
    r0 = 872
    r1 = 0
    b[r14+r0] = r1
    goto L02011a58
L020131d8:
    r0 = 0
    [sp+216] = r0
    [sp+212] = r0
    [sp+208] = r0
    [sp+204] = r0
    r0 = sp + 216
    r1 = sp + 212
    r2 = sp + 208
    r3 = sp + 204
    call status_helpers_status_fields
    r8 = r0
    r0 = sp + 192
    call status_helpers_counter_words
    r3 = [sp+216]
    r4 = [sp+212]
    r1 = [sp+208]
    r2 = [sp+204]
    r7_r6 = d[sp+192]
    r5 = [sp+200]
    [sp+24] = r5
    d[sp+16] = r7_r6
    [sp+12] = r2
    [sp+8] = r0
    [sp+4] = r1
    if (r8 == 0) {  ; @if.eq.ri.s12
    r4 = -1
    }
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 7063
    goto L02011af2
L02013230:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201353a
    r7 = 0
    r0 = r5  #
    [sp+188] = r7
    r1 = sp + 188
    r2 = 10
    call capture_command_decimal  ; @call.xl
    if (r0 == 0) goto L0201325c
    r1 = r0 + -50
    r2 = 4950
    r7 = -1
    if (r1 <= r2) {
    r7 = r0
    }
L0201325c:
    r3 = [sp+188]
    goto L0201326c
L02013260:
    r1 = b[r3+0] (u)
    if (r1 != 32) goto L02013540
    r3 += 1  ; @add.ri.u5
    [sp+188] = r3
L0201326c:
    r0 = 1
    if (r3 != 0) goto L02013260
    goto L02013558
L02013272:
    r1 = b[r14+136] (u)
    r0 = r5
    call auth_memory_report_auth_command
L0201327c:
    r3 = r0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 162
    goto L02011ba4
L0201328e:
    r1 = r15 + 375
    r2 = 4
    r0 = r5
    call capture_command_prefix  ; @call.xl
    if (r0 != 0) goto L020132ba
    r0 = r5 + 4
    call phase3_p12_atoi  ; @call.xl
    r1 = 1
    if (r0 != 0) goto L020132ac
    r1 = r0
L020132ac:
    b[r8+17] = r1
    r0 = h[r14+82] (u)
    if (r0 != 0) goto L020132ba
    call console_helpers_ble_advertise
L020132ba:
    r1 = r15 + 166
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020136ea
    r1 = r15 + 380
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02013318
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r14 + 58
L020132e6:
    testset b[r0]
    ifeq goto L020132e6
    csync
    call console_helpers_now_ms
    call console_helpers_key_open
    csync
    r0 = 0
    b[r14+58] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 32
    r1 = -7
    r2 = 1
    call storage_coordination_notify
    r0 = h[r14+82] (u)
    if (r0 != 0) goto L02013318
    call console_helpers_ble_advertise
L02013318:
    r1 = r15 + 879
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020136fc
    call console_helpers_ble_address
    r0 = r14 + 56
    r1 = b[r0+4] (u)
    [sp+128] = r1
    r1 = b[r8+17] (u)
    [sp+124] = r1
    r12 = h[r0+26] (u)
    r1 = b[r0+6] (u)
    [sp+120] = r1
    r1 = h[r0+28] (u)
    r1 = r14 + 1584  #
    [sp+116] = r1
    r2 = b[r1+5] (u)
    [sp+112] = r2
    r2 = b[r1+4] (u)
    [sp+108] = r2
    r2 = b[r1+3] (u)
    [sp+104] = r2
    r2 = b[r1+2] (u)
    [sp+100] = r2
    r2 = b[r1+1] (u)
    [sp+96] = r2
    r1 = b[r1+0] (u)
    r1 = r14 + 1212  #
    [sp+92] = r1
    r11 = [r1+0]
    r0 = b[r0+1] (u)
    [sp+88] = r0
    r9 = [r9+48]
    r0 = r14 + 1288
    r2 = 338  #
    r6 = [r0+8]
    r5 = [r14+r2<<2]
    r4 = [r0+12]
    r2 += 1  ; @add.ri.u5
    r7 = [r14+r2<<2]
    r13 = [r0+0]
    r10 = [r1+8]
    r8 = [r1+12]
    r0 = 0
    call storage_fault_read_register  ; @call.xl
    r0 = r11 & 0x7FFFFFFF  #
    [sp+84] = r0
    [sp+80] = r8  ; @st.w.sp.l
    [sp+76] = r10  ; @st.w.sp.l
    [sp+72] = r13  ; @st.w.sp.l
    r1 = r12  #
    [sp+68] = r7
    [sp+64] = r4
    [sp+60] = r5
    [sp+56] = r6
    [sp+52] = r9  ; @st.w.sp.l
    [sp+48] = r0
    r0 = [sp+88]
    [sp+44] = r0
    r0 = [sp+92]
    [sp+40] = r0
    r0 = [sp+96]
    [sp+36] = r0
    r0 = [sp+100]
    [sp+32] = r0
    r0 = [sp+104]
    [sp+28] = r0
    r0 = [sp+108]
    [sp+24] = r0
    r0 = [sp+112]
    r0 = r14 + 2072  #
    [sp+20] = r0
    [sp+16] = r0
    r0 = [sp+116]
    [sp+12] = r0
    r0 = [sp+120]
    [sp+8] = r0
    r0 = 1
    if (r1 != 0) goto L020133f0
    r0 = r1
L020133f0:
    r0 = 11651  #
    [sp+4] = r0
    r2 = r15 + r0  #
    r0 = [sp+124]
    r5 = r14 + 6972  #
    [sp] = r0
    r1 = 400  #
    r3 = [sp+128]
    r0 = r5
    call L0200691e
    r6 = r0
    ifs (r6 < 0) goto L0201352a
    if (r6 > 399) goto L0201352a
    call console_helpers_key_ready
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r11 = r14 + 58
L0201342a:
    testset b[r11]
    ifeq goto L0201342a
    r0 = 1
    [sp+128] = r0
    if (r2 != 0) goto L02013438
    [sp+128] = r2
L02013438:
    csync
    r0 = 1228
    r0 = b[r14+r0] (u)
    r7 = 0
    r1 = 0
    [sp+124] = r1
    if (r0 == 0) goto L02013454
    r0 = r14 + 6592
    call bond_records_and_prints_bond_count
    [sp+124] = r0
L02013454:
    r4 = r6 + r14
    csync
    b[r14+58] = r7
    call storage_coordination_irq_leave  ; @call.xl
    call console_helpers_key_left_locked
    r1 = 1536
    r3 = b[r14+r1] (u)
    r1 = r14 + 1308
    r2 = [r1+4]
    [sp+120] = r2
    r2 = [r1+0]
    [sp+116] = r2
    r2 = [r1+16]
    [sp+112] = r2
    r8 = [r1+12]
    r9 = [r1+36]
    r13 = 1
    r12 = r0 + 999
    call console_helpers_key_window
    if (r0 == 0) goto L020134a0
    call console_helpers_key_ready
    r7 = 1
    if (r0 == 0) goto L020134a0
    r7 = 0
L020134a0:
    r10 = r4 + 6972
    r6 = 0x190 - r6
    r13 = r13 & ~r3
    r0 = 1000
    r12 = r12 / r0 (u)
    call storage_coordination_irq_enter  ; @call.xl
    csync
L020134bc:
    testset b[r11]
    ifeq goto L020134bc
    csync
    r0 = 1228
    r0 = b[r14+r0] (u)
    r4 = 0
    r3 = 0
    if (r0 == 0) goto L020134dc
    r0 = r14 + 6592
    call bond_records_and_prints_bit_count
    r3 = r0
L020134dc:
    csync
    b[r14+58] = r4
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 329
    r0 = [r14+r0<<2]
    r1 = 334
    r1 = [r14+r1<<2]
    d[sp+40] = r1_r0
    r1 = r6  #
    [sp+36] = r3
    [sp+32] = r7
    d[sp+24] = r9_r8
    r0 = [sp+112]
    [sp+20] = r0
    r0 = [sp+116]
    [sp+16] = r0
    r0 = [sp+120]
    r0 = 10738  #
    [sp+12] = r0
    d[sp+4] = r13_r12
    r2 = r15 + r0  #
    r0 = [sp+124]
    r0 = r10  #
    [sp] = r0
    r3 = [sp+128]
    call L0200691e
L0201352a:
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 162
    goto L02011c3e
L0201353a:
    r7 = [r14+188]
    goto L02013596
L02013540:
    if (r1 == 0) goto L02013558
    r1 = 0
    r2 = 10
    r0 = r3
    call capture_command_decimal  ; @call.xl
    r1 = r0 + -1
    if (r1 >= 2) {  ; @if.ge.ri.s12
    r0 = -1
    }
L02013558:
    r1 = r0 | r7
    ifs (r1 <= -1) goto L02012418
    [r14+188] = r7
    r1 = 0
    b[r14+50] = r1
    r2 = 952
    r3 = [r9+0]
    b[r14+r2] = r1
    r2 += -80
    b[r14+r2] = r1
    [r14+948] = r3
    r2 = r14 + 6588
    b[r2+0] = r1
    b[r2+1] = r1
    b[r2+2] = r0
    call state_queries_tenfold_word
    r0 = r0 - r7
    [r14+228] = r0
L02013596:
    r0 = 6590
    r0 = b[r14+r0] (u)
    if (r0 != 0) goto L020135a2
    r0 = 1
L020135a2:
    r1 = [r14+236]
    r2 = [r14+232]
    r0 = 2000  #
    [sp+12] = r0
    r3 = r7  #
    [sp+8] = r2
    r1 = 8728  #
    [sp+4] = r1
    r5 = r14 + r1  #
    [sp] = r0
    r2 = r15 + 6583
    r1 = 512
    r0 = r5
    goto L0201173e
L020135ce:
    r8 = [r9+0]
    [r9+0] |= 0x4000
    r0 = 15
    call phase3_p13_adc_sample_average
    [r9+0] &= 0xFFFFBFFF
    r6 = r0
    call phase3_p13_get_vbg_trim
    r2 = r0.b0 (s)
    r0 = uextra(r0, p:2, l:5)
    r1 = r0 * 0x3
    r0 = 0x0 - r1
    ifs (r2 >= 0) {  ; @ifs.ge.ri.s12
    r0 = r1
    }
    r7 = r0 + 800
    r4 = 0
    goto L02013628
L02013602:
    r0 = r6
    if (r4 == 0) goto L02013608
    r0 = 0
L02013608:
    if (r4 == 0) goto L0201361e
    if (r6 == 0) goto L0201361e
    r0 = r15 + 4084
    r0 = [r0+r4<<2]
    call phase3_p13_adc_sample_average
    r0 *= r7
    r0 = r0 / r6 (u)
L0201361e:
    r1 = sp + 164
    [r1+r4<<2] = r0
    r4 += 1  ; @add.ri.u5
L02013628:
    if (r4 != 6) goto L02013602
    r0 = [r9+0]
    r1 = r8 >> 14
    r0 <= insert(r1, p:14, l:1)
    [r9+0] = r0
    r0 = 0
    r10 = 0
    call L0200ff48
    if (r6 == 0) goto L02013650
    r0 = 1023
    r0 *= r7
    r10 = r0 / r6 (u)
L02013650:
    r0 = 17
    call storage_fault_read_register  ; @call.xl
    r9_r8 = d[sp+168]
    r11 = [sp+180]  ; @ld.w.sp.l
    r12 = [sp+184]  ; @ld.w.sp.l
    r7 = r0  #
    r6 = [sp+176]
    r4 = [sp+164]
    r0 = 21
    call storage_fault_read_register  ; @call.xl
    r1 = r7 >> 7
    r0 = uextra(r0, p:2, l:1)
    d[sp+28] = r1_r0
    r0 = r7 & 0xFFFFFF01
    r0 = r12 << 2  #
    [sp+24] = r0
    r1 = 512  #
    [sp+20] = r4
    r3 = r8  #
    [sp+16] = r6
    r0 = r11 << 2  #
    [sp+12] = r0
    r0 = 8728  #
    [sp+8] = r0
    [sp+4] = r10  ; @st.w.sp.l
    r7 = r14 + r0
    r0 = 10505
    r2 = r15 + r0
    [sp] = r9  ; @st.w.sp.l
    r0 = r7
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r7
    call command_services_console_send
    r1 = r15 + 170
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02011a58
    r0 = 17
    r1 = 64
    call L01c00f72  ; @call.xl
    goto L02011a58
L020136e2:
    call audio_stats_audio_stats
    goto L02011a58
L020136ea:
    r0 = b[r14+136] (u)
    call console_helpers_key_issue
    goto L0201327c
L020136f4:
    call fault_record_life_report
    goto L02011a58
L020136fc:
    r0 = b[r14+136] (u)
    if (r0 == 0) goto L020139a0
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 2479
    r1 = 512
    r0 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = 30
    call L0203feb8  ; @call.xl
    call bond_records_and_prints_bond_reset
    goto L02011a58
L02013738:
    r0 = r5
    r1 = r7
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02014092
    r1 = r15 + 182
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020139f4
    r1 = r15 + 647
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020139f4
    r1 = r15 + 653
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02013e02
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02013e6a
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 7165
    goto L0201215a
L02013796:
    r0 = 29883864
    r3 = r0
    r4 = [r3+0]
    r0 = [r3+0]
    r1 = [r3+12]
    r2 = [r3+16]
    r3 = [r3+20]
    r6 = [r14+128]
    [sp] = r6
    call fault_record_crash_cause
    r7 = r0
    r0 = 4293918720
    r0 &= r4
    [sp+128] = r0
    if (r7 > 399) goto L0201397e
    r0 = 3495952384
    r1 = [sp+128]
    if (r1 != r0) goto L0201397e
    ifs (r7 < 1) goto L0201397e
    r0 = 29883864
    r2 = r0
    r0 = [r2+4]
    r1 = [r2+16]
    r2 = [r2+20]
    call fault_record_check_word
    r11 = 0x190 - r7
    if (r11 == 0) goto L020139dc
    r1 = r7 + r14
    r2 = r1 + 7372
    r1 = 0
    [sp+124] = r2
    b[r2+0] = r1
    r1 = 29883520
    r1 = [r1+0]
    r1 = r1 >> 16
    r2 = 53341
    if (r1 != r2) goto L020139dc
    r1 = 29883520
    r1 = [r1+36]
    if (r1 != r0) goto L020139dc
    r0 = 29883520
    r7 = r0
    r3 = [r7+4]
    r0 = [r7+8]
    r1 = [r7+12]
    r2 = [r7+16]
    r4 = [r7+20]
    r6 = [r7+24]
    r7 = [r7+28]
    d[sp+16] = r7_r6
    [sp+12] = r4
    r2 = r15 + 7487  #
    [sp+8] = r2
    d[sp] = r1_r0
    r1 = r11  #
    r0 = [sp+124]
    call L0200691e
    r8 = r0
    ifs (r0 < 0) goto L020139dc
    if (r11 <= r0) goto L020139dc
    r0 = 29883520
    r1 = 32767  #
    r0 = [r0+0]
    r0 &= r1
    [sp+120] = r0
    if (r0 >= 8) {  ; @if.ge.ri.s12
    r0 = 8
    [sp+120] = r0
    }
    r0 = [sp+120]
    if (r0 != 0) goto L02013880
    r0 = [sp+124]
    r0 += r8
    r1 = r11 - r8
    r2 = r15 + 15
    call L0200691e
    r8 += r0
L02013880:
    r0 = sp + 587
    [sp+116] = r0
    r6 = 0
L02013888:
    r0 = [sp+120]
    if (r6 >= r0) goto L02013946
    if (r11 <= r8) goto L02013946
    r0 = r6 * 0x3
    r1 = 29883560
    r13 = [r1+r0<<2]
    r1 = r0 + 11
    r3_r2 = 0
L020138a4:
    if (r3 > 7) goto L020138f6
    r0 = r3 >> 2
    r0 += r1  ; @add.rr
    r4 = 29883520
    r0 = [r4+r0<<2]
    r4 = r2 & 0x18
    r4 = r0 >> r4
    r0 = 63
    if ((r4 & 0xFF) == 0) {
    r0 = 0
    }
    r12 = uextra(r4, p:0, l:8)
    r7 = r12 + -33
    r10 = r0
    if (r7 <= 93) {  ; @if.le.ri.s12
    r10 = r4
    }
    r9 = r0
    if (r12 != 44) {  ; @if.ne.ri.s12
    r9 = r10
    }
    if (r12 != 47) {  ; @if.ne.ri.s12
    r0 = r9
    }
    r7 = sp + 587
    b[r7+r3] = r0
    r2 += 8  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
    if ((r4 & 0xFF) != 0) goto L020138a4
L020138f6:
    r4 = 0
    r1 = r15 + 17  #
    r0 = [sp+116]
    b[r0+8] = r4
    r2 = b[sp+587] (u)
    r0 = sp + 587
    if (r2 != 0) goto L0201390c
    r0 = r1
L0201390c:
    r1 = r15 + 26  #
    [sp+8] = r0
    if ((r13 & 0x1) == 0) {
    r1 = r15
    }
    r0 = r13 & 0xFFFFFFFE
    r3 = r15 + 9
    d[sp] = r1_r0
    if (r6 != 0) goto L02013928
    r3 = r15
L02013928:
    r0 = [sp+124]
    r0 += r8
    r1 = r11 - r8
    r2 = r15 + 1373
    call L0200691e
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r4 = r0
    }
    r8 += r4
    r6 += 1  ; @add.ri.u5
    ifs (r0 > -1) goto L02013888
L02013946:
    r0 = 29883520
    r0 = [r0+0]
    if (r11 <= r8) goto L0201397e
    r0 = r0.l (s)
    ifs (r0 > -1) goto L0201397e
    r0 = 29883652
    r1 = r0
    r3 = [r1+4]
    r4 = [r1+8]
    r0 = [r1+12]
    r1 = [r1+16]
    d[sp+4] = r1_r0
    r0 = [sp+124]
    r0 += r8  #
    [sp] = r4
    r1 = r11 - r8
    r2 = r15 + 5985
    call L0200691e
L0201397e:
    r0 = 2782920704
    r1 = [sp+128]
    if (r1 == r0) goto L02013a80
    r0 = 3888119808
    r1 = [sp+128]
    if (r1 != r0) goto L020139dc
    r3 = r15 + 174
    r9 = 1
    goto L02013a86
L020139a0:
    r0 = 9362
    r4 = r15 + r0
    r5 = r15 + 2479
    call bond_records_and_prints_bond_reset
    if (r0 != 0) goto L020139b4
    r4 = r5
L020139b4:
    r2 = r15 + 4843
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r2 = r4
    }
    r0 = 8728
    r4 = r14 + r0
    r1 = 512
    r0 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    goto L02011a54
L020139dc:
    r0 = r15 + 530  #
    r2 = [sp+128]
    r3 = r15 + 400
    r1 = 3495952384
    if (r2 != r1) {
    r3 = r0
    }
    goto L02013a84
L020139f4:
    call fault_record_radio_wait
    if (r0 == 0) goto L02013a3c
    r7 = sp + 136
    r0 = r7
    call record_helpers_half_fields
    r0 = 396
    call boundary_hooks_rate_level
    r6 = r0
    r0 = r7
    r1 = r6
    call record_helpers_leading_ones
    r1 = b[r5+0] (u)
    if (r1 != 82) goto L02013a4c
    r0 = 1
    r1 = 0
    goto L02013a2c
L02013a22:
    r2 = sp + 136
    b[r2+r0] = r1
    r0 += 1  ; @add.ri.u5
L02013a2c:
    if (r0 != 4) goto L02013a22
    goto L02013a58
L02013a32:
    r0 = r5
    call clock_test_clock_test
    goto L02011a58
L02013a3c:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 7013
    goto L0201215a
L02013a4c:
    if (r0 == 0) goto L02013a58
    r1 = sp + 136
    r2 = 5
    b[r1+r0] = r2
L02013a58:
    r2 = b[sp+139] (u)
    r1 = b[sp+138] (u)
    r0 = b[sp+137] (u)
    call settings_store_select_save
    r3 = r0
    if (r3 == 0) goto L02013e4e
L02013a70:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 3812
    goto L02011ba4
L02013a80:
    r3 = r15 + 886
L02013a84:
    r9 = 0
L02013a86:
    r0 = 29883864
    r4 = r0
    r0 = [r4+0]
    r1 = [r4+4]
    r2 = [r4+8]
    r6 = [r4+12]
    r7 = [r4+16]
    r11 = r14 + 7372  #
    r4 = [r4+20]
    [sp+24] = r11  ; @st.w.sp.l
    r0 = r0 & 0xF  #
    [sp+20] = r4
    d[sp+12] = r7_r6
    [sp+8] = r2
    r1 = 8728  #
    [sp+4] = r1
    r8 = r14 + r1  #
    [sp] = r0
    r1 += 24  ; @add.ri.u5
    r2 = r15 + r1
    r1 = 512
    r0 = r8
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r8
    call command_services_console_send
    r0 = 1
    [sp+124] = r0
    if (r9 != 0) goto L02013af4
    r1 = r15 + 178
    r0 = r5
    call L02028308  ; @call.xl
    r1 = 1
    [sp+124] = r1
    if (r0 == 0) goto L02013af4
    r0 = 0
    [sp+124] = r0
L02013af4:
    r12 = sp + 140
    r13 = 0
    r4 = 29883300
    goto L02013bb0
L02013b02:
    r0 = 0
    r1 = r4
    goto L02013b14
L02013b08:
    r2 = [r1++=4]
    r3 = sp + 140
    [r3+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
L02013b14:
    if (r0 != 6) goto L02013b08
    r10 = [r12+20]
    r9 = [r12+16]
    r6 = [r12+12]
    r0 = [r14+128]
    r1 = r6  #
    r7 = [sp+140]
    r0 = r7  #
    [sp] = r0
    r2 = r9
    r3 = r10
    call fault_record_crash_cause
    r0 = 4293918720
    r0 &= r7
    r1 = 2782920704
    if (r0 == r1) goto L02013b5a
    r1 = 3888119808
    if (r0 != r1) goto L02013b60
    r3 = r15 + 174
    goto L02013b74
L02013b5a:
    r3 = r15 + 886
    goto L02013b74
L02013b60:
    r1 = r15 + 530
    r3 = r15 + 400
    r2 = 3495952384
    if (r0 != r2) {
    r3 = r1
    }
L02013b74:
    r1_r0 = d[r12+4]
    d[sp+20] = r11_r10
    [sp+16] = r9  ; @st.w.sp.l
    [sp+12] = r6
    d[sp+4] = r1_r0
    r0 = r7 & 0xF
    r1 = 9043  #
    [sp] = r0
    r2 = r15 + r1
    r1 = 512
    r0 = r8
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r8
    call command_services_console_send
    r4 += 24  ; @add.ri.u5
    r13 = r13 + 1
L02013bb0:
    call storage_fault_record_count
    if (r0 > r13) goto L02013b02
    r0 = [sp+124]
    if (r0 == 0) goto L02013daa
    r0 = 29883520
    r1 = 3708  #
    r0 = [r0+0]
    r0 = r0 >> 20
    r9 = 29883588
    if (r0 != r1) goto L02013d52
    r6 = 0
    r11 = r9 + -64
    r12 = 8728
    goto L02013c32
L02013be2:
    r0 = r6 << 2
    r13 = [++r0=r11]
    r2 = [r0+4]
    r3 = [r0+8]
    r7 = [r0+12]
    r4 = [r0+16]
    r1 = [r0+20]
    r8 = [r0+24]
    r0 = [r0+28]
    [sp+32] = r0
    [sp+28] = r8  ; @st.w.sp.l
    r1 = 512  #
    [sp+24] = r1
    [sp+20] = r4
    [sp+16] = r7
    d[sp+8] = r3_r2
    [sp+4] = r13  ; @st.w.sp.l
    r0 = r6 + 7
    r7 = r14 + r12  #
    [sp] = r0
    r2 = r15 + 6817
    r0 = r7
    r3 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r7
    call command_services_console_send
    r6 += 8  ; @add.ri.u5
L02013c32:
    ifs (r6 <= 15) goto L02013be2
    r3 = [r9+0]
    r8 = [r9+4]
    r11 = [r9+8]
    r2 = [r9+12]
    r4 = [r9+16]
    r6 = [r9+20]
    r7 = [r9+24]
    r0 = [r9+28]
    r1 = [r9+32]
    d[sp+24] = r1_r0
    d[sp+16] = r7_r6
    r0 = r12  #
    [sp+12] = r4
    r6 = r14 + r0  #
    [sp+8] = r2
    [sp+4] = r11  ; @st.w.sp.l
    r0 = 9448
    r2 = r15 + r0
    r1 = 512
    [sp] = r8  ; @st.w.sp.l
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    r3 = [r9+36]
    r8 = [r9+40]
    r11 = [r9+44]
    r12 = [r9+48]
    r13 = [r9+52]
    r7 = [r9+56]
    r0 = [r9+60]
    r10 = r9 + 64
    r1 = [r10+0]
    r2 = [r10+0]
    r4 = [r10+0]
    r4 = r4 >> 16
    r2 = uextra(r2, p:8, l:8)  #
    [sp+32] = r4
    r1 = r1.b0 (u)  #
    [sp+28] = r2
    d[sp+20] = r1_r0
    r0 = 10198  #
    [sp+16] = r7
    d[sp+8] = r13_r12
    [sp+4] = r11  ; @st.w.sp.l
    r2 = r15 + r0
    r1 = 512
    [sp] = r8  ; @st.w.sp.l
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    r3 = [r10+20]
    r8 = [r10+24]
    r11 = [r10+12]
    r12 = [r10+16]
    r4 = [r10+4]
    r7 = [r10+8]
    r0 = [r10+44]
    r1 = [r10+48]
    r2 = [r10+52]
    [sp+28] = r2
    d[sp+20] = r1_r0
    r0 = 10299  #
    [sp+16] = r7
    r2 = r15 + r0  #
    [sp+12] = r4
    [sp+8] = r12  ; @st.w.sp.l
    [sp+4] = r11  ; @st.w.sp.l
    r1 = 512
    [sp] = r8  ; @st.w.sp.l
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
L02013d52:
    r0 = r9 + -68
    r1 = 3708  #
    r0 = [r0+0]
    r0 = r0 >> 20
    if (r0 != r1) goto L02013f5e
    r0 = r9 + 64
    r1 = r9 + 128  #
    r0 = [r0+56]
    r10 = [r1+0]
    r1 = r0 & 0xFF000000  #
    r7 = [r1+4]
    if (r1 != 4194304000) goto L02013e72
    r1 = r9 + 64
    r1 = [r1+60]
    r1 = uextra(r0, p:8, l:8)  #
    [sp+8] = r1
    r4 = r0.b0 (u)  #
    [sp+4] = r1
    r1 = 8728  #
    [sp] = r4
    r6 = r14 + r1
    r2 = r15 + 4510
    r3 = uextra(r0, p:16, l:8)
    r1 = 512
    r0 = r6
    call L0200691e
    goto L02013e88
L02013daa:
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 1516
    goto L02014034
L02013db8:
    call bond_records_and_prints_boot_clear
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1527
    r1 = 512
    r0 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = [r14+280]
    if (r0 == 0) goto L02013dea
    r0 = 1
    call storage_coordination_gate
L02013dea:
    r0 = 5
    call L0203feb8  ; @call.xl
    r0 = 160
    r1 = 4
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
L02013e00:
    goto L02013e00
L02013e02:
    r5 = sp + 132
    r0 = r5
    call record_helpers_half_fields
    r0 = 396
    call boundary_hooks_rate_level
    r1 = r0
    r0 = r5
    call record_helpers_leading_ones
    if (r0 >= r1) goto L02013e6a
    r0 += 1  ; @add.ri.u5
    r1 = sp + 132
    r2 = b[r1+r0] (u)
    if (r2 != 4) goto L02013e6a
    r2 = 0
    b[r1+r0] = r2
    r2 = b[sp+135] (u)
    r1 = b[sp+134] (u)
    r0 = b[sp+133] (u)
    call settings_store_select_save
    r3 = r0
    if (r3 != 0) goto L02013a70
    goto L02013e6a
L02013e4e:
    call link_and_print_link_pause
    r4 = r0
    r0 = sp + 136
    r1 = r6
    call flash_helpers_level_rate
    r1 = 0
    call cpu_clock_set_clock_rate
    r0 = r4
    call link_and_print_link_resume
L02013e6a:
    call fault_record_clock_state
    goto L02011a58
L02013e72:
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 893
    r1 = 512
    r0 = r6
    call L0200691e
L02013e88:
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    r0 = r10 & 0xFF000000
    if (r0 != 4211081216) goto L02013f0a
    r0 = r7 >> 24
    r0 = uextra(r7, p:16, l:8)  #
    [sp+44] = r0
    r0 = uextra(r7, p:8, l:8)  #
    [sp+40] = r0
    r0 = uextra(r7, p:6, l:2)  #
    [sp+36] = r0
    r0 = uextra(r7, p:5, l:1)  #
    [sp+32] = r0
    r0 = uextra(r7, p:4, l:1)  #
    [sp+28] = r0
    r0 = uextra(r7, p:3, l:1)  #
    [sp+24] = r0
    r0 = uextra(r7, p:2, l:1)  #
    [sp+20] = r0
    r0 = uextra(r7, p:1, l:1)  #
    [sp+16] = r0
    r0 = r7 & 0x1  #
    [sp+12] = r0
    r0 = uextra(r10, p:0, l:8)  #
    [sp+8] = r0
    r0 = uextra(r10, p:8, l:8)  #
    [sp+4] = r0
    r1 = 8728  #
    [sp] = r0
    r6 = r14 + r1
    r2 = r15 + 7543
    r3 = uextra(r10, p:16, l:8)
    r1 = 512
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
L02013f0a:
    r0 = [r9+36]
    r0 = r0 & 0xFF000000
    if (r0 == 2902458368) goto L02013f26
    r0 = [r9+44]
    r0 = r0 & 0xFF000000
    if (r0 != 2885681152) goto L02013f5e
L02013f26:
    r3 = [r9+36]
    r0 = [r9+40]
    r1 = [r9+44]
    r2 = [r9+48]
    [sp+8] = r2
    d[sp] = r1_r0
    r1 = 8728
    r6 = r14 + r1
    r2 = r15 + 4253
    r1 = 512
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
L02013f5e:
    r0 = r9 + -68
    r1 = 3708  #
    r0 = [r0+0]
    r0 = r0 >> 20
    if (r0 != r1) goto L02013fb8
L02013f6e:
    r0 = r9 + -164
    r3 = [r0+0]
    r8 = [r0+4]
    r1 = [r0+8]
    r2 = [r0+12]
    r6 = [r0+16]
    r7 = [r0+20]
    r4 = [r0+24]
    r0 = [r0+28]
    r0 = 8728  #
    [sp+24] = r0
    [sp+20] = r4
    d[sp+12] = r7_r6
    r6 = r14 + r0  #
    [sp+8] = r2
    r2 = r15 + 7114  #
    [sp+4] = r1
    r1 = 512
    [sp] = r8  ; @st.w.sp.l
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    goto L02013fd6
L02013fb8:
    r0 = [sp+128]
    r1 = 3495952384
    if (r0 != r1) goto L02013fd6
    r0 = r9 + -68
    r0 = [r0+0]
    r0 = r0 >> 16
    r1 = 53341
    if (r0 == r1) goto L02013f6e
L02013fd6:
    r0 = r9 + -68
    r1 = 3708  #
    r0 = [r0+0]
    r0 = r0 >> 20
    if (r0 != r1) goto L02014028
    r0 = r9 + 64
    r3 = [r0+4]
    r8 = [r0+8]
    r1 = [r0+12]
    r2 = [r0+16]
    r4 = [r0+20]
    r6 = [r0+24]
    r7 = [r0+28]
    r0 = [r0+32]
    r0 = 8728  #
    [sp+24] = r0
    d[sp+16] = r7_r6
    r6 = r14 + r0  #
    [sp+12] = r4
    r0 = 9901  #
    [sp+8] = r2
    r2 = r15 + r0  #
    [sp+4] = r1
    r1 = 512
    [sp] = r8  ; @st.w.sp.l
    r0 = r6
    call L0200691e
    goto L0201403e
L02014028:
    r0 = 8728
    r6 = r14 + r0
    r2 = r15 + 4012
L02014034:
    r1 = 512
    r0 = r6
    call L0200691e
L0201403e:
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    r1 = r15 + 170
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02011a58
    r0 = 0
    r1 = 29883864
    r1 = r1 + -344  #
    [r1+0] = r0
    r1 = r1 + -224  #
    [r1+0] = r0
    r2 = 3349479424
    r1 = r1 + 420  #
    [r1+0] = r2
    [r1+4] = r0
    [r1+0] = r0
    r1 += -64
    [r1+60] = r0
    [r1+56] = r0
    [r1+52] = r0
    [r1+48] = r0
    [r1+44] = r0
    [r1+40] = r0
    goto L02011a58
L02014092:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 3345
    r1 = 512
    r0 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = 5
    call L0203feb8  ; @call.xl
    r0 = 1
    r1 = 0
    r2 = 0
    call fault_record_fatal_record
L020140c6:
    goto L020140c6
L020140c8:
    r0 = 8728
    r5 = r14 + r0
    r2 = r15 + 1383
    r1 = 512
    r0 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r0 = 5
    call L0203feb8  ; @call.xl
    r0 = 29883864
    [r0+36] = 0x0
    call phase3_p7_go_mask_usb_updata  ; @call.xl
L02014102:
    goto L02014102
