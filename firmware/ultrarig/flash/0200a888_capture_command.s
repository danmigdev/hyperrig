; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_command: 1 function, 0x0200a888..0x0200ad06

; capture_command_command: 0x0200a888..0x0200ad06, module capture-command (command)
.type capture_command_command,@function
capture_command_command:
    [--sp] = {rets, r15-r4}
    sp += -236
    r4 = r0
    r14 = L02035836  ; "ok"
    r7 = r14 + 482  #
    [sp+124] = r4
    r2 = 4
    r1 = r7
    call capture_command_prefix  ; @call.xl
    r11 = L01c26890
    r10 = L01c1f180
    if (r0 == 0) goto L0200a8c8
L0200a8b2:
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0200a964
    r0 = sp + 124
    r1 = 15
    call capture_command_slot_parse
    r5 = r0
    ifs (r5 <= -1) goto L0200a9d0
    r15 = 0
    goto L0200a8e4
L0200a8c8:
    r0 = r4
    r1 = b[++r0=4] (u)
    r1 |= 32
    if (r1 != 32) goto L0200a8b2
L0200a8d4:
    [sp+124] = r0
    r1 = b[r0+0] (u)
    r0 += 1  ; @add.ri.u5
    if (r1 == 32) goto L0200a8d4
    r5 = -1
    r15 = 1
L0200a8e4:
    r0 = r11 + 696
    r13 = [r0+8]
    r1 = r14 + 2702
    r3_r2 = d[r1+8]
    {r6, r4} = [r0+]
    r9_r8 = d[r1+0]
    d[sp+72] = r3_r2
    [sp+80] = r6
    d[sp+64] = r9_r8
    if (r15 == 0) goto L0200a98e
L0200a90a:
    r6 = [sp+124]
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L0200a9e4
    r0 = 0
    r0 = r6  #
    [sp+56] = r0
    r1 = sp + 56
    call capture_command_tenths
    if (r0 == 0) goto L0200a9da
    r0 = [sp+56]
    r1 = r0 + 120
    if (r1 > 240) goto L0200a9da
    r1 = 5
    r1 = r0 / r1 (s)
    r1 = r1 * 0x5
    r1 = r0 - r1
    if (r1 != 0) goto L0200a9da
    r1 = 5
    r9 = r0 / r1 (s)
    goto L0200a940
L0200a93e:
    r6 += 1  ; @add.ri.u5
L0200a940:
    r0 = b[r6+0] (u)
    r0 |= 32
    if (r0 != 32) goto L0200a93e
    [sp+124] = r6
    goto L0200a94e
L0200a94c:
    r6 += 1  ; @add.ri.u5
L0200a94e:
    r0 = b[r6+0] (u)
    if (r0 == 32) goto L0200a94c
    if (r0 == 0) goto L0200aa4a
    if (r0 != 45) goto L0200aa4e
    [sp+124] = r6
    r0 = b[r6+1] (u)
    if (r0 != 0) goto L0200aa50
    r13 = 0
    goto L0200aa74
L0200a964:
    r1 = r11 + 696
    r3 = [r1+8]
    r2 = [r1+0]
    r0 = b[r10+9] (u)
    r1 = [r1+4]
    r4 = 0
    [sp+20] = r4
    [sp+16] = r4
    [sp+12] = r4
    [sp+8] = r4
    [sp+4] = r4
    [sp] = r1
    r1 = -1
    if (r0 != 255) {  ; @if.ne.ri.s12
    r1 = r0
    }
    r0 = r14 + 1072
    goto L0200aa1e
L0200a98e:
    r0 = 0xDF000
    r1 = r5
    ifs (r5 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 = r5 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r0 += r1  ; @add.rr
    r1 = 1128745812
    r3 = sp + 84
    r2 = 8152
    call preset_application_header
    if (r0 == 0) goto L0200a9c6
    r1 = sp + 84
    r2 = sp + 60
    r0 = r5
    call preset_application_asset_resolve
    if (r0 == 0) goto L0200aa26
L0200a9c6:
    r0 = r14 + 5303
    call link_and_print_print
    goto L0200aa22
L0200a9d0:
    r0 = r14 + 2915
    call link_and_print_print
    goto L0200aa22
L0200a9da:
    r0 = r14 + 7978
    call link_and_print_print
    goto L0200aa22
L0200a9e4:
    r0 = r14 + 432
    if (r15 == 0) {  ; @if.eq.ri.s12
    r7 = r0
    }
    if (r15 == 0) goto L0200a9fe
    r0 = b[r10+9] (u)
    r5 = -1
    if (r0 != 255) {  ; @if.ne.ri.s12
    r5 = r0
    }
L0200a9fe:
    r0 = [sp+80]
    r1 = [sp+72]
    r2 = [sp+76]
    r3 = 0
    d[sp+16] = r3_r2
    r1 = r15 ^ 0x1  #
    [sp+12] = r1
    r2 = r4  #
    [sp+8] = r1
    d[sp] = r1_r0
    r0 = r7
    r1 = r5
L0200aa1c:
    r3 = r13
L0200aa1e:
    call calibration_commands_trim_report
L0200aa22:
    sp += 236
    {pc, r15-r4} = [sp++]
L0200aa26:
    r0 = r5  #
    r2 = [sp+60]
    r1 = sp + 84
    r3 = sp + 64
    call capture_metadata_lookup
    r6 = r0
    call capture_loader_gain_value
    r4 = r0
    r0 = 0
    r0 = r6  #
    [sp+80] = r0
    r1 = sp + 80
    call capture_loader_aux
    r13 = r0
    goto L0200a90a
L0200aa4a:
    [sp+124] = r6
    goto L0200aa74
L0200aa4e:
    [sp+124] = r6
L0200aa50:
    r1 = sp + 52
    r2 = 10
    r0 = r6
    call capture_command_decimal  ; @call.xl
    r1 = [sp+52]
    if (r1 == r6) goto L0200aad2
    r2 = r0 + 200
    if (r2 > 600) goto L0200aad2
    r1 = b[r1+0] (u)
    if (r1 != 0) goto L0200aad2
    r13 = 1  #
    [sp+80] = r0
L0200aa74:
    r7_r6 = 0
    r8 = [sp+80]  ; @ld.w.sp.l
    r12 = 0
    r4 = 0
    if (r15 == 0) goto L0200aae4
L0200aa82:
    [++r11=696] = r9
    [r11+8] = r13
    r0 = r8
    if (r13 == 0) {  ; @if.eq.ri.s12
    r0 = r13
    }
    [r11+4] = r0
    r1 = 0
    r0 = r9
    call capture_loader_set_gain
    if (r15 == 0) goto L0200aaae
    r0 = b[r10+9] (u)
    r5 = -1
    if (r0 != 255) {  ; @if.ne.ri.s12
    r5 = r0
    }
L0200aaae:
    r0 = 1
    if (r7 != 2) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r0 = r15 ^ 0x1  #
    [sp+20] = r0
    [sp+16] = r12  ; @st.w.sp.l
    r1 = r5  #
    [sp+12] = r4
    r0 = r14  #
    [sp+8] = r0
    r2 = r9  #
    [sp+4] = r6
    [sp] = r8  ; @st.w.sp.l
    goto L0200aa1c
L0200aad2:
    r0 = r14 + 7178
    r1 = -200
    r2 = 400
    call link_and_print_print
    goto L0200aa22
L0200aae4:
    r0 = r9
    r1 = r13
    r2 = r8
    call capture_command_pack
    r6 = r0
    r0 = 0xDF000
    r1 = r5
    ifs (r5 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 = r5 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r4 = r1 + r0
    r1 = 1128745812
    r3 = sp + 164
    r2 = 8152
    r0 = r4
    call preset_application_header
    if (r0 == 0) goto L0200ab72
    r1 = sp + 164
    r2 = sp + 160
    r0 = r5
    call preset_application_asset_resolve
    r7 = -2
    if (r0 != 0) goto L0200ab74
    [sp+156] = r4
    r0 = capture_metadata_read_adapter
    [sp+144] = r0
    r0 = capture_journal_write_offset
    [sp+148] = r0
    r0 = sp + 156
    [sp+152] = r0
    call storage_platform_clock  ; @call.xl
    r12 = r0  #
    r7 = [sp+160]
    r0 = sp + 144
    r1 = sp + 164
    r3 = sp + 128
    r2 = r7
    call capture_metadata_scan
    if (r0 == 0) goto L0200ab86
    r12 = [sp+140]  ; @ld.w.sp.l
    r4 = [sp+136]
    r7 = -2
    goto L0200acf4
L0200ab72:
    r7 = -1
L0200ab74:
    r0 = r7
    call capture_command_status_text
    r1 = r0
    r0 = r14 + 2282
    call link_and_print_print
    goto L0200aa22
L0200ab86:
    r0 = [sp+128]
    if (r0 != r6) goto L0200ab96
    r12 = [sp+140]  ; @ld.w.sp.l
    r4 = [sp+136]
    r7 = 0
    goto L0200acf4
L0200ab96:
    [sp+24] = r12  ; @st.w.sp.l
    [sp+36] = r4
    [sp+48] = r8  ; @st.w.sp.l
    r0 = 1413958484
    [sp+220] = r0
    [sp+224] = r7
    [sp+32] = r6
    [sp+228] = r6
    r0 = sp + 220
    r1 = 12
    call capture_metadata_crc
    r8 = 0  #
    r7 = [sp+136]
    r1 = [sp+168]
    [sp+232] = r0
    r0 = r7 << 4
    [sp+40] = r1
    r1 += 55
    r1 = r1 & 0xFFFFFFF0
    r6 = r0 + r1
    r12 = [sp+140]  ; @ld.w.sp.l
    r0 = sp + 164
    [sp+28] = r0
    r0 = sp + 128
    [sp+44] = r0
    goto L0200ac1e
L0200abde:
    ifs (r8 > 1) goto L0200ac26
    r0 = sp + 156
    r2 = sp + 220
    r3 = 16
    r1 = r6
    call capture_journal_write_offset
    if (r0 != 0) goto L0200ac18
    r0 = sp + 156
    r2 = sp + 204
    r3 = 16
    r1 = r6
    call capture_metadata_read_adapter
    if (r0 != 0) goto L0200ac18
    r0 = sp + 204
    r1 = sp + 220
    r2 = 16
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0200acb4
L0200ac18:
    r6 += 16  ; @add.ri.u5
    r8 = r8 + 1
L0200ac1e:
    r4 = r7 + r8
    if (r4 < r12) goto L0200abde
L0200ac26:
    r1 = [sp+40]
    r0 = r1 + 3
    r0 = r0 & 0xFFFFFFFC  #
    r2 = [sp+44]
    [r2+8] = r4
    if (r1 != 0) goto L0200ac36
    r0 = 4
L0200ac36:
    call L0203c15c  ; @call.xl
    r7 = r0
    r8 = [sp+48]  ; @ld.w.sp.l
    if (r7 == 0) goto L0200ac70
    r1 = 1128745812
    r3 = sp + 164
    r2 = 8152  #
    [sp] = r7
    r0 = [sp+36]
    call preset_storage_record
    r6 = r0
    if (r6 == 0) goto L0200ac76
    r0 = r7
    call L0203d218  ; @call.xl
L0200ac66:
    r7 = -1
    if (r6 != -2) {
    r7 = r6
    }
    goto L0200acf4
L0200ac70:
    r7 = -100
    goto L0200acf4
L0200ac76:
    r1 = 8192  #
    r0 = [sp+32]
    r3 = r7  #
    [sp+176] = r0
    r0 = [sp+28]
    r6 = [r0+4]
    r2 = sp + 164
    [sp] = r6
    r0 = [sp+36]
    call capture_journal_rewrite
    [sp+44] = r6
    if (r0 == 0) goto L0200ace0
    r2 = sp + 164
    r1 = 8192  #
    [sp] = r6
    r3 = r7  #
    r0 = [sp+36]
    call capture_journal_rewrite
    r6 = r0
    r0 = r7
    call L0203d218  ; @call.xl
    if (r6 != 0) goto L0200ac66
    goto L0200ace8
L0200acb4:
    r0 = r7 + r8  #
    r1 = [sp+156]
    r4 = r0 + 1
    r6 += r1  #  ; @add.rr.p
    r2 = [sp+44]
    [r2+8] = r4
    r2 = [sp+32]
    [sp+128] = r2
    [sp+132] = r0
    r0 = [sp+24]
    call preset_loader_elapsed
    r2 = r0 << 8
    r0 = 18
    r1 = r6
    call storage_coordination_notify
    r7 = 1
    r8 = [sp+48]  ; @ld.w.sp.l
    goto L0200acf4
L0200ace0:
    r0 = r7
    call L0203d218  ; @call.xl
L0200ace8:
    r0 = [sp+44]
    call capture_metadata_capacity
    r12 = r0
    r7 = 2
    r4 = 0
L0200acf4:
    ifs (r7 <= -1) goto L0200ab74
    r0 = b[r10+9] (u)
    r6 = 1
    if (r5 == r0) goto L0200aa82
    goto L0200aaae
