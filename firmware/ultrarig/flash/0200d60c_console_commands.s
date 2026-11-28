; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_commands: 1 function, 0x0200d60c..0x0200e03a

; console_commands_console_command: 0x0200d60c..0x0200e03a, module console-commands (console_command)
.type console_commands_console_command,@function
console_commands_console_command:
    [--sp] = {rets, r15-r4}
    sp += -208
    r4 = r1
    r5 = r0
    r9 = L02035810
    r1 = r9 + 206
    call L02028308  ; @call.xl
    r12 = L01c1f180
    r15 = L01c26890
    if (r0 == 0) goto L0200d6e0
    r1 = r9 + 791
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d77a
    r1 = r9 + 935
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d7e4
    r1 = r9 + 1142
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200db4c
    r1 = r9 + 1150
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200dc02
    r1 = r9 + 949
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200dcd6
    r1 = r9 + 505
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200dd84
    r1 = r9 + 510
    r0 = r5
    call L02028308  ; @call.xl
    r5 = 0
    if (r0 != 0) goto L0200dcd0
    r1 = r9 + 214
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200defc
    r1 = r9 + 59
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200df1e
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0200df24
    r0 = r9 + 2772
    goto L0200dcca
L0200d6e0:
    r0 = -1
    r10 = 0  #
    [sp+168] = r0
    [sp+164] = r0
    [sp+160] = r10  ; @st.w.sp.l
    [sp+156] = r10  ; @st.w.sp.l
    r0 = 255
    [sp+152] = r0
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0200daac
    r0 = sp + 152
    r1 = r9 + 2629  #
    [sp+8] = r0
    r0 = sp + 156
    [sp+4] = r0
    r0 = sp + 160
    r2 = sp + 168
    r3 = sp + 164
    r0 = r4  #
    [sp] = r0
    call L0200b7c2
    r3 = [sp+160]
; HyperRig MINI, product option: action 11 is a ramp while the switch is held, for the hold, and 12 the same ramp on and off, for
; the tap (mini/product/ramp.c).
.if MINI_PRODUCT
    if (r3 > 12) goto L0200db46
.else
    if (r3 > 10) goto L0200db46
.endif
    r2 = [sp+164]
    if (r2 > 2) goto L0200db46
    ifs (r0 < 3) goto L0200db46
    r1 = [sp+168]
    if (r1 > 3) goto L0200db46
    r0 = [sp+152]
    if (r3 != 8) goto L0200dbca
    if (r0 != 255) goto L0200dbca
    r4 = sp + 132
    r1 = sp + 116
    r0 = r4
    call selection_effect_flatten
    r0 = r4  #
    r1 = [sp+156]
    r2 = sp + 115
    r3 = sp + 114
    call preset_loader_binding
    r4 = b[sp+115] (u)
    r0 = b[sp+114] (u)
    r2 = [sp+164]
    r1 = [sp+168]
    r3 = b[sp+160] (u)
    [sp+156] = r4
    [sp+152] = r0
    goto L0200dbce
L0200d77a:
    call mode_and_settings_block_ensure
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0200dbb4
    r0 = -1
    r1 = r9 + 2059  #
    [sp+80] = r0
    r0 = 0
    [sp+76] = r0
    r2 = 0
    r3 = 0
    d[sp+68] = r3_r2
    [sp+64] = r0
    d[sp+56] = r3_r2
    r0 = sp + 56
    r2 = sp + 80
    r3 = sp + 68
    r0 = r4  #
    [sp] = r0
    call L0200b7c2
    r5 = r0  #
    r4 = [sp+80]
    ifs (r5 < 2) goto L0200dca8
    if (r4 > 3) goto L0200dca8
    r1 = r9 + 485
    r0 = sp + 68
    call L02028308  ; @call.xl
    if (r5 != 2) goto L0200dc92
    if (r0 != 0) goto L0200dc92
    r0 = 2423
    r0 = b[r15+r0] (u)
    r0 = r0 & ~(1 << r4)
    goto L0200deec
L0200d7e4:
    call mode_and_settings_block_ensure
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0200da38
    r10 = r15 + 2420
    r1 = sp + 176
    r11 = r1 + 28
    r2 = r1
    r3 = r10
    rep 32 {
    r5 = b[r3++=1] (u)
    b[r2++=1] = r5
    }
    r12 = r1 | 0x2
    r13 = r1 | 0x1
    r8 = 0
    goto L0200da0e
L0200d812:
    r0 = b[r5++=1] (u)
    r6 += 1  ; @add.ri.u5
L0200d816:
    if (r0 == 0) goto L0200d8fe
    if (r0 == 32) goto L0200d8fe
    if (r0 != 61) goto L0200d812
    b[r5+-1] = r8
L0200d824:
    r0 = b[++r6=1] (u)
    r1 = 1
    if (r0 != 0) goto L0200d82e
    r1 = r0
L0200d82e:
    if (r0 == 32) goto L0200d834
    if (r1 != 0) goto L0200d824
L0200d834:
    if (r0 == 0) goto L0200d83a
    b[r6++=1] = r8
L0200d83a:
    r1 = sp + 172
    r2 = 10
    r0 = r5
    call capture_command_decimal  ; @call.xl
    r8 = r0  #
    r1 = [sp+172]
    if (r1 == r5) goto L0200d858
    r14 = 1  #
    r0 = b[r1+0] (u)
    if (r0 == 0) goto L0200d85a
L0200d858:
    r14 = 0
L0200d85a:
    r1 = r9 + 942
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d932
    r1 = r9 + 797
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d94c
    r1 = r9 + 210
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d982
    r1 = r9 + 803
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d9ec
    r1 = r9 + 490
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d9b8
    r1 = r9 + 495
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200d9b8
    r1 = r9 + 500
    r0 = r4
    call L02028308  ; @call.xl
    r1 = r9 + 5441
    r7 = r9 + 1832
    if (r0 != 0) goto L0200d8cc
    r7 = r1
L0200d8cc:
    if (r0 != 0) goto L0200e032
    r0 = r14 ^ 0x1
    if (r0 != 0) goto L0200e032
    if (r8 == 0) goto L0200d8ea
    r0 = r8 + -10
    if (r0 > 240) goto L0200e02e
L0200d8ea:
    r0 = b[r12+0] (u)
    if (r8 == 0) goto L0200da0a
    r0 |= 64
    b[r12+0] = r0
    b[r11+1] = r8
    goto L0200da02
L0200d8fe:
    r6 = r5 + -1
    r0 = r6 - r4
    r7 = r9 + 3421
    if (r0 != 7) goto L0200e032
    r1 = r9 + 1134
    r2 = 7
    r0 = r4
    call capture_command_prefix  ; @call.xl
    if (r0 != 0) goto L0200e032
    r0 = sp + 176
    call mode_and_settings_block_defaults
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L0200da04
    r6 = r5
    goto L0200da04
L0200d932:
    r7 = r9 + 3944
    if (r8 > 100) goto L0200e032
    r0 = r14 ^ 0x1
    if (r0 != 0) goto L0200e032
    b[r13+0] = r8
    goto L0200da02
L0200d94c:
    r1 = r9 + 1808
    r2 = 3
    r0 = r5
    call footswitch_events_name_index
    ifs (r0 < 0) goto L0200e022
    r1 = 1
    r2 = 1
    if (r0 != 2) {  ; @if.ne.ri.s12
    r2 = 0
    }
    r8 = 0
    if (r0 != 0) goto L0200d96e
    r1 = r0
L0200d96e:
    r0 = b[r12+0] (u)
    r1 <= insert(r2, p:1, l:1)
    r0 = r0 & 0xFFFFFFFC
    r0 |= r1
    b[r12+0] = r0
    goto L0200da04
L0200d982:
    r7 = r9 + 3233
    if (r8 > 2) goto L0200e032
    r0 = r14 ^ 0x1
    if (r0 != 0) goto L0200e032
    r0 = 1
    r1 = 1
    if (r8 != 2) {  ; @if.ne.ri.s12
    r1 = 0
    }
    if (r8 == 0) {  ; @if.eq.ri.s12
    r0 = r8
    }
    r2 = b[r12+0] (u)
    r0 = r0 << 2
    r0 <= insert(r1, p:3, l:1)
    r1 = r2 & 0xFFFFFFF3
    r0 |= r1
    goto L0200d9e6
L0200d9b8:
    r7 = r9 + 4430
    if (r8 > 1) goto L0200e032
    r0 = r14 ^ 0x1
    if (r0 != 0) goto L0200e032
    r1 = b[r4+0] (u)
    r0 = 16
    if (r1 != 104) {  ; @if.ne.ri.s12
    r0 = 32
    }
    r2 = b[r12+0] (u)
    r1 = r2 & ~r0
    r0 |= r2
    if (r8 == 0) {  ; @if.eq.ri.s12
    r0 = r1
    }
L0200d9e6:
    b[r12+0] = r0
    goto L0200da02
L0200d9ec:
    r1 = r9 + 1820
    r2 = 3
    r0 = r5
    call footswitch_events_name_index
    ifs (r0 < 0) goto L0200e028
    b[r11+0] = r0
L0200da02:
    r8 = 0
L0200da04:
    r4 = r6  #
    r0 = b[r6+0] (u)
    goto L0200da0e
L0200da0a:
    r0 &= 4294967231
    goto L0200d9e6
L0200da0e:
    if (r0 == 0) goto L0200da26
    r5 = r4 + 1
    goto L0200da1a
L0200da14:
    r0 = b[++r4=1] (u)
    r5 += 1  ; @add.ri.u5
L0200da1a:
    if (r0 == 32) goto L0200da14
    r6 = r4
    if (r0 != 0) goto L0200d816  ; @bne.ri.l
L0200da26:
    r3 = sp + 176
    r0 = r3
    call mode_and_settings_block_clamp
    rep 32 {
    r0 = b[r3++=1] (u)
    b[r10++=1] = r0
    }
L0200da38:
    r0 = 2422
    r2 = b[r15+r0] (u)
    r3 = 0
    r0 = 0
    if ((r2 & 0x1) != 0) {
    r0 = uextra(r2, p:1, l:1)
    r0 += 1  ; @add.ri.u5
    }
    if ((r2 & 0x4) != 0) {
    r1 = uextra(r2, p:3, l:1)
    r3 = r1 + 1
    }
    r1 = 2421
    r1 = b[r15+r1] (u)
    r4 = 2448
    r4 = b[r15+r4] (u)
    if ((r2 & 0x40) == 0) {
    r5 = 0
    } else {
    r5 = 2449
    r5 = b[r15+r5] (u)
    }
    r5 = uextra(r2, p:5, l:1)  #
    [sp+12] = r5
    r2 = uextra(r2, p:4, l:1)  #
    [sp+8] = r5
    [sp+4] = r2
    r5 = 1
    r2 = 1
    if (r4 <= 2) {  ; @if.le.ri.s12
    r2 = r4
    }
    r4 = r9 + 1820
    r4 = [r4+r2<<2]
    r2 = r9 + 1808
    r2 = [r2+r0<<2]
    r0 = 8341  #
    [sp] = r4
    r0 += r9
    call bond_records_and_prints_print_a
    goto L0200dcd0
L0200daac:
    r11 = r12 + 236
    r8 = 0
    goto L0200db3c
L0200dab4:
    r5 = 0
    r6 = r11
    goto L0200db30
L0200daba:
    r3 = b[r6+0] (u)
    if (r3 != 8) goto L0200db08
    r1 = sp + 98
    r0 = r6
    call selection_effect_match
    r4 = r0  #
    r7 = b[r6+2] (u)
    r3 = b[r6+1] (u)
    b[sp+86] = r10
    r0 = 255
    ifs (r4 >= 0) {  ; @ifs.ge.ri.s12
    r0 = r4
    }
    r12 = r3
    if (r7 != 255) {  ; @if.ne.ri.s12
    r12 = r0
    }
    if (r7 == 255) goto L0200daf4
    r2 = r9 + 1453  #
    [sp] = r7
    r0 = sp + 86
    r1 = 12
    call L0200691e
L0200daf4:
    ifs (r4 <= -1) goto L0200db1a
    r0 = sp + 98
    r0 = b[r0+r4] (u)
    r0 = r9 + 4872  #
    [sp+4] = r0
    r1 = sp + 86
    goto L0200db20
L0200db08:
    r2 = r5  #
    r1 = b[r6+1] (u)
    r0 = b[r6+2] (u)
    r0 = r9 + 3540  #
    [sp+4] = r0
    r1 = r8  #
    [sp] = r1
    goto L0200db28
L0200db1a:
    r1 = sp + 86
    r0 = r9 + 4758
L0200db20:
    r1 = r8  #
    [sp] = r1
    r2 = r5
    r3 = r12
L0200db28:
    call bond_records_and_prints_print_a
    r6 += 3  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L0200db30:
    if (r5 != 3) goto L0200daba
    r11 = r11 + 9
    r8 = r8 + 1
L0200db3c:
    if (r8 != 4) goto L0200dab4
    r0 = r9 + 1316
    goto L0200dcca
L0200db46:
    r0 = r9 + 3922
    goto L0200dcca
L0200db4c:
    call mode_and_settings_block_ensure
    call control_actions_clock
    r5 = r0
    r1 = r9 + 535
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200dce4
    r1 = r9 + 809
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200de64
    r1 = r9 + 797
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200de96
    r1 = r9 + 803
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200de9a
    r1 = r9 + 214
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200df00
    r0 = r9 + 3440
    goto L0200dcca
L0200dbb4:
    r4 = 0
    goto L0200dbc0
L0200dbb8:
    r0 = r4
    call footswitch_events_colour_line
    r4 += 1  ; @add.ri.u5
L0200dbc0:
    if (r4 != 4) goto L0200dbb8
    r0 = r9 + 1615
    goto L0200dcca
L0200dbca:
    r4 = b[sp+156] (u)
L0200dbce:
    r5 = r2 * 0x3
    r6 = r1 * 0x9
    r5 += r6  ; @add.rr
    r5 += r12
    b[++r5=236] = r3
    r6 = 964  #
    b[r5+1] = r4
    r5 = r1 + r15  #
    b[r5+2] = r0
    r7 = 0
    b[r5+r6] = r7
    r0 = r0.b0 (u)
    r0 = r9 + 4591  #
    [sp+4] = r0
    r3 = r3.b0 (u)
L0200dbfa:
    [sp] = r4
    call bond_records_and_prints_print_a
    goto L0200dcce
L0200dc02:
    r0 = -1
    [sp+44] = r0
    [sp+40] = r0
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0200dc48
    r1 = r9 + 815
    r2 = sp + 44
    r3 = sp + 40
    r0 = r4
    call L0200b7c2
    r1 = [sp+40]
    if (r1 > 1) goto L0200de90
    if (r0 != 2) goto L0200de90
    r0 = [sp+44]
    if (r0 >= 4) goto L0200de90
    r2 = b[r4+0] (u)
    if (r2 == 0) goto L0200dc48
    r3 = b[r12+11] (u)
    r2 = r3 & ~(1 << r0)
    r0 = r3 | (1 << r0)
    if (r1 != 0) goto L0200dc44
    r0 = r2
L0200dc44:
    b[r12+11] = r0
L0200dc48:
    r4 = b[r12+11] (u)
    r0 = 0
    call controls_immediate
    r8 = r0
    r0 = 1
    r5 = 1
    call controls_immediate
    r6 = r0
    r0 = 2
    call controls_immediate
    r7 = r0
    r0 = 3
    call controls_immediate
    [sp+16] = r0
    d[sp+8] = r7_r6
    [sp+4] = r8  ; @st.w.sp.l
    r6 = uextra(r4, p:3, l:1)
    r0 = r9 + 5615  #
    [sp] = r6
    r1 = r4 & 0xFFFFFF01
    r2 = uextra(r4, p:1, l:1)
    r3 = uextra(r4, p:2, l:1)
    call bond_records_and_prints_print_a
    goto L0200dcd0
L0200dc92:
    r1 = r9 + 928
    r0 = sp + 68
    call L02028308  ; @call.xl
    if (r5 != 2) goto L0200dca8
    if (r0 == 0) goto L0200dedc
L0200dca8:
    if (r5 != 3) goto L0200dcc6
    if (r4 > 3) goto L0200dcc6
    r0 = sp + 68
    r1 = sp + 53
    call footswitch_events_hex_colour
    if (r0 != 0) goto L0200dcc6
    r0 = sp + 56
    r1 = sp + 50
    call footswitch_events_hex_colour
    if (r0 == 0) goto L0200debc
L0200dcc6:
    r0 = r9 + 3004
L0200dcca:
    call bond_records_and_prints_print_a
L0200dcce:
    r5 = 1
L0200dcd0:
    r0 = r5
    sp += 208
    {pc, r15-r4} = [sp++]
L0200dcd6:
    r8 = -1
    r11 = 0
    r10 = -1
    r5 = -1
    goto L0200dcfe
L0200dce4:
    r1 = 0
    r0 = r15 + 904
    b[r0+8] = r1
    r1 = 1
    if (r5 != 0) goto L0200dcf2
    r5 = 1
L0200dcf2:
    [r0+0] = r5
    b[r0+4] = r1
    goto L0200dea4
L0200dcf8:
    r0 = r6.b0 (s)
    r8 = r0 + -49
L0200dcfe:
    r0 = r5
L0200dd00:
    r5 = r0  #
    r1 = b[r4+0] (u)
    if (r1 != 0) goto L0200dd0c
    goto L0200dd6a
L0200dd08:
    r4 += 1  ; @add.ri.u5
    r1 = b[r4+0] (u)
L0200dd0c:
    if (r1 == 32) goto L0200dd08
    r0 = r4
    goto L0200dd24
L0200dd14:
    r2 = r4 + 1
    r3 = r2
    if (r1 != 61) {  ; @if.ne.ri.s12
    r3 = r0
    }
    r4 = r2  #
    r1 = b[r4+1] (u)
    r0 = r3
L0200dd24:
    r2 = 1
    if ((r1 & 0xFF) == 0) {
    r2 = 0
    }
    if (r1 == 32) goto L0200dd32
    if (r2 != 0) goto L0200dd14
L0200dd32:
    if (r1 == 0) goto L0200dd38
    b[r4++=1] = r11
L0200dd38:
    r6 = b[r0+0] (u)
    if (r6 == 0) goto L0200dd6a
    r1 = r6 + -49
; HyperRig MINI, product option: banks 1 to 9 in one digit.
.if MINI_PRODUCT
    r1 = r1.b0 (u)
    if (r1 > 8) goto L0200dd4a
.else
    r1 = r1.b0 (u)
    if (r1 > 7) goto L0200dd4a
.endif
    r1 = b[r0+1] (u)
    if (r1 == 0) goto L0200dcf8
L0200dd4a:
    r1 = r9 + 3560
    r2 = 5
    call footswitch_events_name_index
    if (r0 == 9) goto L0200dcf8
    if (r0 < 3) goto L0200dd00
    r10 = r0 + -3
    ifs (r0 > 2) goto L0200dcfe
    r0 = r9 + 3251
    goto L0200dcca
L0200dd6a:
    r0 = r10 & r8
    ifs (r0 < 0) goto L0200ddc6
    r0 = r5
    ifs (r5 <= -1) {  ; @ifs.le.ri.s12
    r0 = b[r15+74] (u)
    }
    if (r0 == 0) goto L0200ddc6
    r0 = r9 + 6629
    goto L0200dcca
L0200dd84:
    r0 = b[r4+0] (s)
    r5 = r0 + -97
    r7 = r5.b0 (u)
    r6 = 0
    if (r7 > 2) goto L0200dda2
    r1 = b[r4+1] (s)
    r0 += 1  ; @add.ri.u5
    r6 = 1
    if (r1 != r0) {
    r6 = 0
    }
L0200dda2:
    r0 = 2
    if (r6 != 0) goto L0200dda8
    r0 = 1
L0200dda8:
    r4 += r0  ; @add.rr
    r1 = r9 + 821
    r0 = r4
    call L02028308  ; @call.xl
    if (r7 > 3) goto L0200ddc0
    if (r0 == 0) goto L0200deb0
    r1 = b[r4+0] (u)
    if (r1 == 0) goto L0200deb0
L0200ddc0:
    r0 = r9 + 2756
    goto L0200dcca
L0200ddc6:
    ifs (r5 < 0) goto L0200de38
    r0 = b[r15+74] (u)
    if (r5 == r0) goto L0200de38
    r0 = b[r15+77] (u)
    if (r0 == 0) goto L0200dde2
    r0 = 0
    b[r15+77] = r0
    call footswitch_events_reload_preset
L0200dde2:
    b[r15+74] = r5
    r4 = 0
    b[r15+75] = r4
    call panel_inputs_switches_reset
    r0 = 1567
    r1 = 964
    r2 = 960
    r3 = 932
    r9 = L01c26888
    r11 = 3
    r7 = 0
    goto L0200de34
L0200de0e:
    r5 = r7 + r12
    r5 = b[r5+116] (u)
    r5 += r15
    r5 = b[r5+r0] (u)
    r6 = r7 + r15
    b[r6+r1] = r4
    b[r6+r2] = r5
    b[r6+r3] = r5
    if (r5 == 0) goto L0200de32
    b[r7+r9] = r11
L0200de32:
    r7 += 1  ; @add.ri.u5
L0200de34:
    if (r7 != 4) goto L0200de0e
L0200de38:
    ifs (r10 < 0) goto L0200de56
    r0 = b[r15+75] (u)
    if (r10 == r0) goto L0200de56
    r1 = [r12+92]
    r0 = sp + 36
    call panel_inputs_switch_status
    r0 = b[sp+37] (s)
    call panel_inputs_analog_command
L0200de56:
    ifs (r8 >= 0) {  ; @ifs.ge.ri.s12
    b[r15+76] = r8
    }
L0200de5e:
    call footswitch_events_switch_line
    goto L0200dcce
L0200de64:
    r0 = 892
    r1 = 1
    b[r15+r0] = r1
    [r15+896] = r5
    r0 += 16  ; @add.ri.u5
    b[r15+r0] = r1
    r5 = r15 + 92
    r0 = r5
    call footswitch_events_colour_word
    if (r0 != 0) goto L0200dea4
    r0 = r15 + 2424
    rep 3 {
    r1 = b[r0++=1] (u)
    b[r5++=1] = r1
    }
    goto L0200dea4
L0200de90:
    r0 = r9 + 3459
    goto L0200dcca
L0200de96:
    r0 = 1
    goto L0200de9c
L0200de9a:
    r0 = 2
L0200de9c:
    b[r15+48] = r0
    [r15+916] = r5
L0200dea4:
    r0 = r9 + 1844
    r1 = r4
L0200deaa:
    call bond_records_and_prints_print_a
    goto L0200dcce
L0200deb0:
    r1 = b[r15+74] (u)
    if (r1 == 0) goto L0200df88
    r0 = r9 + 5115
    goto L0200dcca
L0200debc:
    r4 = [sp+80]
    r0 = r4 * 0x3
    r0 += r15
    r1 = r0 + 2424
    r2 = sp + 53
    rep 3 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r0 = r0 + 2436
    r1 = sp + 50
    rep 3 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
L0200dedc:
    r0 = 2423
    r0 = b[r15+r0] (u)
    r1 = 255
    r1 = r1 & (1 << r4)
    r0 |= r1
L0200deec:
    r1 = 2423
    b[r15+r1] = r0
    r0 = r4
    call footswitch_events_colour_line
    goto L0200dcce
L0200defc:
    r0 = 0
    goto L0200df20
L0200df00:
    r0 = 0
    b[r15+48] = r0
    r1 = 912
    r2 = 1
    b[r15+r1] = r2
    r1 += -20
    b[r15+r1] = r0
    r1 += 16  ; @add.ri.u5
    b[r15+r1] = r0
    goto L0200dea4
L0200df1e:
    r0 = 1
L0200df20:
    b[r12+14] = r0
L0200df24:
    call panel_inputs_pedal_volume
    r0 = b[r12+15] (u)
    r1 = 0
    if (r0 > 126) goto L0200dfae
    if (r0 == 0) goto L0200dfaa
    r1 = 4294901760
    r2 = r0
    goto L0200df44
L0200df3e:
    r1 = r1 - 0x10000
    r2 = r2 << 1
L0200df44:
    if (r2 <= 63) goto L0200df3e
    r2 = r2 << 10
    r2 = r2 - 0x10000
    r3 = r2 >> 12
    r3 = r3 << 2
    r3 += r9
    r4 = 2119
    r4 = [r3+r4<<2]
    r5 = 2120
    r3 = [r3+r5<<2]
    r3 = r3 - r4
    r2 = r2 << 4
    r2 = r2.l (u)
    r2 *= r3
    r2 = r2 >> 16
    r2 += r4  ; @add.rr
    r1 += r2  ; @add.rr
    r1 = r1 >>> 4
    r2 = 6021
    r1 *= r2
    r1 = r1 - 0x32000
    r2 = 0x64000
    r1 = r1 / r2 (s)
    goto L0200dfae
L0200df88:
    if (r0 != 0) {  ; @if.ne.ri.s12
    r0 = 1
    r4 = 3
    } else {
    r0 = 2
    r4 = 4
    }
    if (r6 != 0) goto L0200df98
    r4 = r0
L0200df98:
    call panel_inputs_switch_targets
    call control_actions_clock
    r2 = r0
    r1_r0 = r5_r4
    call footswitch_events_switch_event
    goto L0200de5e
L0200dfaa:
    r1 = -1440
L0200dfae:
    if (r0 == 0) goto L0200dfe0
    r0 = abs(r1)
    r2 = 10
    r2 = r0 / r2 (s)
    r2 = r2 * 0xA  #
    [sp] = r2
    r0 = r0 - r2
    r3 = r9 + 15  #
    [sp+4] = r0
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r3 = r9
    }
    r2 = r9 + 1158
    r0 = sp + 24
    r1 = 12
    call L0200691e
    r3 = b[r12+15] (u)
    goto L0200dffa
L0200dfe0:
    r0 = r9 + 515
    r1 = 519
    r1 = b[r9+r1] (u)
    r2 = sp + 24
    rep 4 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    b[sp+28] = r1
    r3 = 0
L0200dffa:
    r0 = r15 + 2048
    r2 = h[r0+2] (u)
    r1 = h[r0+0] (u)
    r4 = b[r0+12] (u)
    r5 = h[r0+4] (u)
    r6 = h[r0+6] (u)
    r0 = [r0+16]
    r7 = b[r12+14] (u)
    r0 = 8823  #
    [sp+20] = r0
    r0 += r9  #
    [sp+16] = r6
    d[sp+8] = r5_r4
    [sp+4] = r7
    r4 = sp + 24
    goto L0200dbfa
L0200e022:
    r7 = r9 + 5242
    goto L0200e032
L0200e028:
    r7 = r9 + 4961
    goto L0200e032
L0200e02e:
    r7 = r9 + 5441
L0200e032:
    r0 = r9 + 2644
    r1 = r7
    goto L0200deaa
