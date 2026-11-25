; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 16 functions, 0x02026ba4..0x02027264

; phase3_p12_lmp_hci_private_free_acl_packet: 0x02026ba4..0x02026bf8, module phase3-p12 (lmp_hci_private_free_acl_packet)
.type phase3_p12_lmp_hci_private_free_acl_packet,@function
phase3_p12_lmp_hci_private_free_acl_packet:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r3 = [r1+r0<<2]
    r4 = r3 + 1
    [r1+r0<<2] = r4
    r0 = L01c1fa20
    if (r3 != 0) goto L02026bd4
    csync
L02026bcc:
    testset b[r0]
    ifeq goto L02026bcc
    csync
L02026bd4:
    r3 = h[r2+-22] (u)
    r3 |= 8
    h[r2+-22] = r3
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L02026bf0
    csync
    r1 = 0
    b[r0+0] = r1
L02026bf0:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]

; phase3_p12_bt_stub_26bf8: 0x02026bf8..0x02026bfc, module phase3-p12 (bt_stub_26bf8)
.type phase3_p12_bt_stub_26bf8,@function
phase3_p12_bt_stub_26bf8:
    r0 = 0
    rts

; phase3_p12_bt_stub_26bfc: 0x02026bfc..0x02026c00, module phase3-p12 (bt_stub_26bfc)
.type phase3_p12_bt_stub_26bfc,@function
phase3_p12_bt_stub_26bfc:
    r0 = -1
    rts

; phase3_p12_bt_stub_26c00: 0x02026c00..0x02026c04, module phase3-p12 (bt_stub_26c00)
.type phase3_p12_bt_stub_26c00,@function
phase3_p12_bt_stub_26c00:
    r0 = -1
    rts

; phase3_p12_bt_stub_26c04: 0x02026c04..0x02026c08, module phase3-p12 (bt_stub_26c04)
.type phase3_p12_bt_stub_26c04,@function
phase3_p12_bt_stub_26c04:
    r0 = 0
    rts

; phase3_p12_bt_stub_26c08: 0x02026c08..0x02026c0c, module phase3-p12 (bt_stub_26c08)
.type phase3_p12_bt_stub_26c08,@function
phase3_p12_bt_stub_26c08:
    r0 = 0
    rts

; phase3_p12_bt_stub_26c0c: 0x02026c0c..0x02026c10, module phase3-p12 (bt_stub_26c0c)
.type phase3_p12_bt_stub_26c0c,@function
phase3_p12_bt_stub_26c0c:
    r0 = 0
    rts

; phase3_p12_bt_stub_26c10: 0x02026c10..0x02026c12, module phase3-p12 (bt_stub_26c10)
.type phase3_p12_bt_stub_26c10,@function
phase3_p12_bt_stub_26c10:
    rts

; phase3_p12_bt_stub_26c12: 0x02026c12..0x02026c14, module phase3-p12 (bt_stub_26c12)
.type phase3_p12_bt_stub_26c12,@function
phase3_p12_bt_stub_26c12:
    rts

; phase3_p12_bt_stub_26c14: 0x02026c14..0x02026c16, module phase3-p12 (bt_stub_26c14)
.type phase3_p12_bt_stub_26c14,@function
phase3_p12_bt_stub_26c14:
    rts

; phase3_p12_bt_stub_26c16: 0x02026c16..0x02026c18, module phase3-p12 (bt_stub_26c16)
.type phase3_p12_bt_stub_26c16,@function
phase3_p12_bt_stub_26c16:
    rts

; phase3_p12_bt_stub_26c18: 0x02026c18..0x02026c1a, module phase3-p12 (bt_stub_26c18)
.type phase3_p12_bt_stub_26c18,@function
phase3_p12_bt_stub_26c18:
    rts

; phase3_p12_bip_get_image: 0x02026c1a..0x02026d44, module phase3-p12 (bip_get_image)
.type phase3_p12_bip_get_image,@function
phase3_p12_bip_get_image:
    [--sp] = {rets, r8-r4}
    sp += -260
    r8 = L01c26830
    r6 = [r8+0]
    r4 = r0
    if (r6 == 0) goto L02026d40
    r5 = sp + 5
    r0 = r5 + 4
    r1 = 0
    r2 = 251
    r7 = 0
    call effect_enable_memset  ; @call.xl
    r0 = 131
    b[sp+5] = r0
    b[sp+6] = r7
    b[sp+7] = r7
    r0 = 203
    b[sp+8] = r0
    r0 = r5  #
    r2 = [r6+16]
    r1 = 4
    call L020513d6  ; @call.xl
    r0 = 66
    b[sp+13] = r0
    r1 = 9
    r2 = 16
    r0 = r5
    call L020513fc  ; @call.xl
    r1 = r5 + 11
    r0 = L02035810
    r2 = 2111
    goto L02026c8a
L02026c7e:
    r3 = r7 + r0
    r3 = b[r3+r2] (u)
    b[r1+r7] = r3
    r7 += 1  ; @add.ri.u5
L02026c8a:
    if (r7 != 12) goto L02026c7e
    r1 = 0
    b[sp+28] = r1
    r2 = 48
    b[sp+29] = r2
    b[sp+30] = r1
    r2 = 19
    b[sp+31] = r2
    r2 = sp + 5
    r2 += 27  ; @add.ri.u5
    r3 = 0
    goto L02026cb6
L02026cac:
    r5 = b[r4+r3] (u)
    b[r2+1] = r5
    r2 += 2  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L02026cb6:
    b[r2+0] = r1
    if (r3 != 7) goto L02026cac
    b[sp+47] = r1
    r2 = 113
    b[sp+48] = r2
    b[sp+49] = r1
    r2 = 167
    b[sp+50] = r2
    r2 = sp + 5
    r2 += 46
    r3 = 11303
    goto L02026ce6
L02026cda:
    r4 = r1 + r0
    r4 = b[r4+r3] (u)
    b[r2+r1] = r4
    r1 += 1  ; @add.ri.u5
L02026ce6:
    if (r1 != 164) goto L02026cda
    r0 = 0
    b[sp+215] = r0
    b[sp+216] = r0
    r0 = sp + 5
    r1 = 1
    r2 = 210
    call L020513fc  ; @call.xl
    r1 = [r8+0]
    r0 = [r1+8]
    if (r0 == 0) goto L02026d40
    r1 += 64
    r2 = b[r1+2] (u)
    r3 = r2 & 0xFFFFFFC0
    r4 = r2 + 1
    r4 = r4 & 0x3F
    r3 |= r4
    b[r1+2] = r3
    r1 = b[r1+3] (u)
    r4 = r1 & 0xFFFFFF3F
    r3 = r2 & 0xFFFFFF3F  #
    [sp] = r4
    r1 = sp + 5
    r2 = 210
    call L0205017c  ; @call.xl
    r0 = [r8+0]
    r1 = r0 + 40
    r0 += 30  ; @add.ri.u5
    rep 7 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
L02026d40:
    sp += 260
    {pc, r8-r4} = [sp++]

; phase3_p12_avrcp_image_handle: 0x02026d44..0x02026dba, module phase3-p12 (avrcp_image_handle)
.type phase3_p12_avrcp_image_handle,@function
phase3_p12_avrcp_image_handle:
    [--sp] = {rets, r4}
    r4 = L01c26830
    r3 = [r4+0]
    if (r3 == 0) goto L02026db8
    if (r2 == 0) goto L02026d60
    r0 = r3 + 30
    rep 8 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = b[r3+4] (u)
    if (r0 != 0) goto L02026d94
    {pc, r4} = [sp++]
L02026d60:
    r0 = b[r3+4] (u)
    if (r0 == 0) goto L02026d7a
    r0 = [r3+20]
    if (r0 != 3) goto L02026d88
    r0 = h[r3+0] (u)
    if (r0 == 0) goto L02026db8
    call phase3_p6_sys_timer_del
    r0 = [r4+0]
    r1 = 0
    h[r0+0] = r1
    {pc, r4} = [sp++]
L02026d7a:
    r0 = r3 + 40
    r1 = r3 + 30
    rep 7 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    {pc, r4} = [sp++]
L02026d88:
    r0 = r3 + 40
    r1 = r3 + 30
    rep 7 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
L02026d94:
    r0 = [r3+20]
    if (r0 != 3) goto L02026db8
    r0 = h[r3+0] (u)
    if (r0 == 0) goto L02026da8
    call phase3_p6_sys_timer_del
    r3 = [r4+0]
    r0 = 0
    h[r3+0] = r0
L02026da8:
    [r3+20] = 0x4
    r0 = r3 + 30
    call phase3_p12_bip_get_image
    r0 = [r4+0]
    r1 = 0
    b[r0+4] = r1
L02026db8:
    {pc, r4} = [sp++]

; phase3_p12_notify_client_simple: 0x02026dba..0x02026e00, module phase3-p12 (notify_client_simple)
.type phase3_p12_notify_client_simple,@function
phase3_p12_notify_client_simple:
    [--sp] = {rets, r5, r4}
    sp += -8
    r3 = L01c26838
    r1 = [r3+0]
    r2 = [r1+128]
    if (r2 == 0) goto L02026dfc
    r2 = 234
    b[sp+3] = r2
    r2 = 3
    b[sp+4] = r2
    b[sp+5] = r0
    r2 = h[r1+142] (u)
    r4 = sp + 3
    r1 = 3
    r0 = r4
    call L0204cc4a  ; @call.xl
    r2 = r4  #
    r0 = [r3+0]
    r5 = [r0+128]
    r0 = 4
    r1 = 0
    r3 = 5
    call r5
L02026dfc:
    sp += 8
    {pc, r5, r4} = [sp++]

; phase3_p12_ancs_handle_hci_event: 0x02026e00..0x02027264, module phase3-p12 (ancs_handle_hci_event)
.type phase3_p12_ancs_handle_hci_event,@function
phase3_p12_ancs_handle_hci_event:
    [--sp] = {rets, r15-r4}
    sp += -68
    r7 = r2
    r12 = r3  #
    r0 = b[r7+0] (u)
    r10 = L01c26838
    if (r0 == 5) goto L02026e54
    if (r0 == 8) goto L02026e7e
    if (r0 != 62) goto L02026eb6
    r0 = b[r7+2] (u)
    if (r0 != 1) goto L02027246
    r0 = b[r7+6] (u)
    if (r0 == 0) goto L02027246
    r1 = 4
    r0 = r7
    call L0204cb74  ; @call.xl
    r4 = [r10+0]
    r2 = r0
    r0 = r4 + 140
    h[r0+2] = r2
    r1 = b[r0+1] (u)
    r1 = r1 & 0xFFFFFFFC
    b[r0+1] = r1
    r1 = 0
    b[r0+0] = r1
    [r0+24] = 0x20
    goto L02026e86
L02026e54:
    r1 = 3
    r0 = r7
    call L0204cb74  ; @call.xl
    r4 = [r10+0]
    r1 = h[r4+142] (u)
    if (r0 != r1) goto L02026eba
    r0 = 242
    call phase3_p12_notify_client_simple
    r0 = [r10+0]
    r1 = 0
    [r0+164] = r1
    h[r0+142] = r1
    goto L02027246
L02026e7e:
    r4 = [r10+0]
    r2 = h[r4+142] (u)
L02026e86:
    r1 = 3
    r0 = r7
    call L0204cb74  ; @call.xl
    r1 = r2.l (u)
    if (r1 != r0) goto L02027246
    r0 = b[r7+5] (u)
    if (r0 == 0) goto L02027246
    r0 = r4 + 140
    r1 = b[r0+1] (u)
    r1 |= 2
    b[r0+1] = r1
    r1 = [r0+24]
    if (r1 == 1) {  ; @if.eq.ri.s12
    [r0+24] = 0x21
    }
    goto L02026eba
L02026eb6:
    r4 = [r10+0]
L02026eba:
    r5 = r4 + 104
    r0 = [r5+60]
    r1 = r0 + -2
    r8 = L02036304
    r9 = phase3_p12_ancs_handle_hci_event
    r11 = r4 + 140
    if (r1 > 4) goto L02026f0a
    r0 = r1 << 1
    tbh [r0]
phase3_p12_case_table_02026edc:
    .short (L02026ee6 - phase3_p12_case_table_02026edc) / 2, (L0202705c - phase3_p12_case_table_02026edc) / 2, (L020270b4 - phase3_p12_case_table_02026edc) / 2, (L020270a8 - phase3_p12_case_table_02026edc) / 2, (L02026f10 - phase3_p12_case_table_02026edc) / 2
L02026ee6:
    r0 = b[r7+0] (u)
    if (r0 == 160) goto L020270fa  ; @beq.ri.l
    if (r0 != 161) goto L02027194
    r1 = r4 + 28
    r0 = r7
    call L02055394  ; @call.xl
    r0 = b[r11+1] (u)
    r0 |= 1
    b[r11+1] = r0
    goto L02027194
L02026f0a:
    if (r0 != 36) goto L02027194
L02026f10:
    r0 = b[r7+0] (u)
    r0 += 89
    r0 = r0.b0 (u)
    if (r0 > 1) goto L02027194
    r1 = 4
    r0 = r7
    call L0204cb74  ; @call.xl
    r1 = h[r5+0] (u)
    r6 = r7 + 8
    if (r0 != r1) goto L020270c6
    r1 = 6
    r0 = r7
    call L0204cb74  ; @call.xl
    r7 = r0
    r5 = sp + 55
    r11 = r5 + 9
    r0 = r5 + 7
    r13 = 0  #
    [sp+4] = r0
    r14 = 1
    r15 = 2
    goto L02027056
L02026f50:
    r2 = r4 + 128  #
    r0 = b[r6++=1] (u)
    r1 = h[r2+24] (u)
    if (r1 == 0) goto L02026f76
    r3 = h[r2+16] (u)
    if (r1 <= r3) goto L02026f76
    r12 = r3 + 1  #
    r1 = [r2+28]
    h[r2+16] = r12
    b[r1+r3] = r0
    r1 = h[r2+16] (u)
    r0 = h[r2+18] (u)
    if (r1 >= r0) goto L02026f7a
L02026f76:
    r7 += -1
    goto L02027056
L02026f7a:
    r0 = [r2+32]
    if (r0 == 2) goto L02026f9c
    if (r0 == 1) goto L02027026
    if (r0 != 0) goto L02026f76
    r0 = [r2+28]
    r0 += r1  ; @add.rr
    r0 = b[r0+-1] (u)
    h[r2+22] = r0
    h[r2+16] = r13
    h[r2+18] = r15
    [r2+32] = r14
    goto L02026f76
L02026f9c:
    r0 = h[r2+24] (u)
    if (r0 <= r1) goto L02026f76
    r0 = [r2+28]
    b[r0+r1] = r13
    r0 = [r2+0]
    if (r0 == 0) goto L02027016
    r0 = h[r2+24] (u)
    if (r0 == 0) goto L02027016
    r0 = 234
    b[sp+55] = r0
    r0 = 11
    b[r5+1] = r0
    r0 = 241
    b[r5+2] = r0
    r4 = sp + 55
    r1 = 3
    r0 = r4  #
    r2 = h[r2+14] (u)
    call L0204cc4a  ; @call.xl
    r0 = [r10+0]
    r2 = h[r0+150] (u)
    r1 = 5
    r0 = r4
    call L0204cc4a  ; @call.xl
    r0 = [r10+0]
    r1 = b[r0+149] (u)
    r2 = b[r0+148] (u)
    r2 <= insert(r1, p:8, l:24)
    b[r5+7] = r2
    r1 = r2 >> 8
    r2 = [sp+4]
    r1 = r0 + 156  #
    b[r2+1] = r1
    r2 = r11
    rep 4 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r12 = [r0+128]
    r2 = r4  #
    r0 = b[r5+1] (u)
    r3 = r0 + 2
    r0 = 4
    r1 = 0
    call r12
    r4 = [r10+0]
L02027016:
    r0 = r4
    h[++r0=144] = r13
    h[r0+2] = r14
    [r0+16] = r13
    goto L02026f76
L02027026:
    r0 = [r2+28]
    r1 += -2
    call L0204cb74  ; @call.xl
    h[r2+20] = r0
    h[r2+16] = r13
    h[r2+18] = r0
    if (r0 == 0) goto L0202704c
    r1 = h[r2+24] (u)
    if (r0 >= r1) {
    r0 = r1 + -1
    h[r2+20] = r0
    }
    [r2+32] = r15
    goto L02026f76
L0202704c:
    h[r2+18] = r14
    [r2+32] = r13
    goto L02026f76
L02027056:
    if (r7 != 0) goto L02026f50
    goto L02027194
L0202705c:
    r0 = b[r7+0] (u)
    if (r0 == 160) goto L02027122
    if (r0 != 162) goto L02027194
    r5 = sp + 28
    r0 = r7
    r1 = r5
    call L020553d4  ; @call.xl
    r5 += 10  ; @add.ri.u5
    r2 = 16
    r0 = r5
    r1 = r8
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02027178
    r1 = r8 + 16
    r2 = 16
    r0 = r5
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0202717e
    r1 = r8 + 32
    r2 = 16
    r0 = r5
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L02027194
    r0 = r4 + 102
    goto L02027182
L020270a8:
    r0 = b[r7+0] (u)
    if (r0 == 160) {  ; @if.eq.ri.s12
    [r5+60] = 0x23
    }
    goto L02027194
L020270b4:
    r0 = b[r7+0] (u)
    if (r0 != 160) goto L02027194
    [r5+60] = 0x6
    r0 = 240
    call phase3_p12_notify_client_simple
    goto L02027194
L020270c6:
    r1 = h[r4+52] (u)
    if (r0 != r1) goto L02027194
    r1 = 4
    r0 = r6
    call L02051472  ; @call.xl
    [r4+0] = r0
    r0 = 0
    [r5+56] = r0
    h[r11+4] = r0
    r0 = 6
    h[r11+6] = r0
    [r5+60] = 0x24
    r2 = [r11+28]
    if (r2 == 0) goto L02027194
    r0 = r7
    r1 = r12
    call r2
    goto L02027194
L020270fa:
    r0 = b[r11+1] (u)
    if ((r0 & 1) != 0) goto L02027130
    [r5+60] = 0x0
    r0 = h[r11+2] (u)
    r1 = 1
    call L020544c6  ; @call.xl
    r0 = [r10+0]
    r0 = h[r0+142] (u)
    call L020537d6  ; @call.xl
    goto L02027194
L02027122:
    r0 = b[r11+0] (u)
    if (r0 > 2) goto L0202715e
    [r5+60] = 0x0
    goto L02027194
L02027130:
    r0 = h[r11+2] (u)
    r1 = 2
    call L020544c6  ; @call.xl
    r0 = [r10+0]
    r0 = h[r0+142] (u)
    call L020537d6  ; @call.xl
    r0 = [r10+0]
    r1 = b[r0+175] (u)
    r0 = r0 + 140
    if (r1 == 0) goto L0202724a
    [r0+24] = 0x0
    goto L02027194
L0202715e:
    r2 = h[r11+2] (u)
    r0 = r4 + 4
    r1 = r9
    call L0205542c  ; @call.xl
    r0 = [r10+0]
    r1 = 34
    [r0+164] = r1
    goto L02027194
L02027178:
    r0 = r4 + 50
    goto L02027182
L0202717e:
    r0 = r4 + 76
L02027182:
    r1 = sp + 28
    rep 13 {
    r2 = h[r1++=2] (u)
    h[r0++=2] = r2
    }
    r0 = b[r11+0] (u)
    r0 += 1  ; @add.ri.u5
    b[r11+0] = r0
L02027194:
    r2 = [r10+0]
    r0 = r2 + 140
    r1 = [r0+24]
    if (r1 < 32) goto L02027246
    r1 += -32
    if (r1 > 4) goto L02027246
    tbb [r1]
phase3_p12_case_table_020271aa:
    .byte (L020271b0 - phase3_p12_case_table_020271aa) / 2, (L020271c8 - phase3_p12_case_table_020271aa) / 2, (L020271de - phase3_p12_case_table_020271aa) / 2, (L020271f4 - phase3_p12_case_table_020271aa) / 2, (L0202720a - phase3_p12_case_table_020271aa) / 2
    .byte 0x00  ; alignment
L020271b0:
    r2 = r8 + 48  #
    r1 = h[r0+2] (u)
    r0 = r9
    call L0205547c  ; @call.xl
    if (r0 != 0) goto L02027246
    r0 = [r10+0]
    r1 = 2
    goto L02027242
L020271c8:
    r0 = r9  #
    r1 = h[r0+2] (u)
    r2 += 28  ; @add.ri.u5
    call L020554bc  ; @call.xl
    if (r0 != 0) goto L02027246
    r0 = [r10+0]
    r1 = 3
    goto L02027242
L020271de:
    r0 = r9  #
    r1 = h[r0+2] (u)
    r2 += 50
    call L020554f4  ; @call.xl
    if (r0 != 0) goto L02027246
    r0 = [r10+0]
    r1 = 5
    goto L02027242
L020271f4:
    r0 = r9  #
    r1 = h[r0+2] (u)
    r2 += 102
    call L020554f4  ; @call.xl
    if (r0 != 0) goto L02027246
    r0 = [r10+0]
    r1 = 4
    goto L02027242
L0202720a:
    r0 = sp + 11
    r1 = r8 + 268
    r3 = r0
    rep 17 {
    r4 = b[r1++=1] (u)
    b[r3++=1] = r4
    }
    r2 = [r2+0]
    r1 = 1
    call L0204cc6c  ; @call.xl
    r1 = [r10+0]
    r2 = h[r1+78] (u)
    r1 = h[r1+142] (u)
    r3 = 17
    r0 = r9  #
    [sp] = r0
    call L0205553e  ; @call.xl
    if (r0 != 0) goto L02027246
    r0 = [r10+0]
    r1 = 6
L02027242:
    [r0+164] = r1
L02027246:
    sp += 68
    {pc, r15-r4} = [sp++]
L0202724a:
    r1 = b[r0+1] (u)
    if ((r1 & 2) != 0) goto L0202725e
    [r0+24] = 0x1
    r0 = h[r0+2] (u)
    call L020537f6  ; @call.xl
    goto L02027194
L0202725e:
    [r0+24] = 0x21
    goto L02027194
