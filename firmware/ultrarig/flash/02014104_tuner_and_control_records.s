; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tuner_and_control_records: 3 functions, 0x02014104..0x02014366

; tuner_and_control_records_console_line: 0x02014104..0x020142ca, module tuner-and-control-records (console_line)
.type tuner_and_control_records_console_line,@function
tuner_and_control_records_console_line:
    [--sp] = {rets, r8-r4}
    sp += -44
    r5 = r0
    call record_helpers_pack_tag
    r6 = L01c26890
    [r6+124] = r0
    r4 = r5
L0201411a:
    r0 = b[r4++=1] (u)
    r1 = 1
    if (r0 != 0) goto L02014122
    r1 = r0
L02014122:
    if (r0 == 32) goto L02014128
    if (r1 != 0) goto L0201411a
L02014128:
    r1 = r4 + -1
    if (r0 != 0) {  ; @if.ne.ri.s12
    r0 = 0
    b[r1+0] = r0
    } else {
    r4 = r1
    }
    r0 = r5
    r1 = r4
    call text_commands_text_command
    if (r0 != 0) goto L0201414a
    r0 = r5
    r1 = r4
    call console_commands_console_command
    if (r0 == 0) goto L02014152
L0201414a:
    [r6+124] = 0x0
    sp += 44
    {pc, r8-r4} = [sp++]
L02014152:
    r8 = L02035810
    r1 = r8 + 827
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02014186
    r1 = r8 + 525
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02014206
    r0 = r5
    call calibration_commands_global_save
    if (r0 != 0) goto L0201414a
; HyperRig MINI, product option: its own console words first (mini/product).
.if MINI_PRODUCT
    r0 = r5
    r1 = r4
    call hyperrig_console
    if (r0 != 0) goto L0201414a
.endif
    r0 = r5
    r1 = r4
    call console_dispatch_console_dispatch
    goto L0201414a
L02014186:
    r0 = b[r6+52] (u)
    [sp+40] = r0
    r5 = L01c1f180
    r0 = b[r5+16] (u)
    r7 = [r5+144]
    r0 = ftoi(r7) (trunc)  #
    [sp+36] = r0
    r1 = r8 + 1325  #
    [sp+32] = r0
    r0 = sp + 32
    r2 = sp + 40
    r3 = sp + 36
    r0 = r4  #
    [sp] = r0
    call L0200b7c2
    r0 = [sp+32]
    r1 = r0 + -415
    if (r1 <= 51) {  ; @if.le.ri.s12
    r7 = itof(r0)
    [r5+144] = r7
    }
    r1 = [sp+36]
    r0 = 1
    if (r1 != 0) goto L020141ce
    r0 = r1
L020141ce:
    b[r5+16] = r0
    r0 = [sp+40]
    if (r0 == 0) goto L020141e6
    r1 = b[r6+52] (u)
    if (r1 != 0) goto L020141e6
    r1 = 1012
    r2 = 0
    b[r6+r1] = r2
L020141e6:
    r1 = 1
    if (r0 != 0) goto L020141ec
    r1 = r0
L020141ec:
    b[r6+52] = r1
    r1 = b[r6+52] (u)
    r2 = b[r5+16] (u)
    r0 = r8 + 4328
    r3 = ftoi(r7) (trunc)
    call bond_records_and_prints_print_b
    goto L0201414a
L02014206:
    r0 = b[r6+52] (u)
    if (r0 == 0) goto L02014288
    r0 = 1068
    r0 = b[r6+r0] (u)
    if (r0 == 0) goto L02014292
    r0 = 291
    r0 = [r6+r0<<2]
    r1 = r6 + 1168
    r3_r2 = d[r1+0]
    r7 = 276  #
    r4 = [r1+8]
    r5 = [r1+20]
    r1 = [r1+12]
    r7 = [r6+r7<<2]
    [sp+28] = r7
    r1 = abs(r3)  #
    [sp+24] = r1
    d[sp+16] = r5_r4
    r4 = 10
    r4 = r1 / r4 (s)
    [sp+8] = r4
    r3 = r3 >> 31
    r3 = r3 << 1
    r3 += 43
    [sp+4] = r3
    r3 = 100
    r3 = r2 / r3 (s)
    r5 = r3 * 0x64
    r2 = r2 - r5
    r2 = r4 * 0xA  #
    [sp] = r2
    r4 = r1 - r2
    r1 = 12
    r2 = r0 / r1 (s)
    r1 = r2 * 0xC
    r0 = r0 - r1
    r1 = r8 + 6916
    r1 = [r1+r0<<2]
    r0 = 8408  #
    [sp+12] = r4
    r0 += r8
    r2 += -1
    call bond_records_and_prints_print_b
    goto L0201414a
L02014288:
    r0 = r8 + 1463
    call bond_records_and_prints_print_b
    goto L0201414a
L02014292:
    r0 = 275
    r3 = [r6+r0<<2]
    r0 += -6
    r2 = [r6+r0<<2]
    r0 += 28  ; @add.ri.u5
    r4 = b[r6+54] (u)
    r1 = [r6+r0<<2]
    if (r4 == 0) goto L020142bc
    r5 = [r6+1016]
    r0 = r8 + 963
    r4 = r8
    if (r5 != 0) goto L020142be
    r4 = r0
    goto L020142be
L020142bc:
    r4 = r8
L020142be:
    r0 = r8 + 5374  #
    [sp] = r4
    call bond_records_and_prints_print_b
    goto L0201414a

; tuner_and_control_records_word_listed: 0x020142ca..0x02014336, module tuner-and-control-records (word_listed)
.type tuner_and_control_records_word_listed,@function
tuner_and_control_records_word_listed:
    [--sp] = {rets, r5, r4}
    r2 = b[r0+0] (u)
    r1 = L01c27cd5
    goto L0201431a
L020142d6:
    r3 = r1
    goto L020142e0
L020142da:
    r2 = b[++r0=1] (u)
    r3 += 1  ; @add.ri.u5
L020142e0:
    r5 = r2 + -32
    if (r5 < 2) goto L020142f8
    if (r2 == 0) goto L020142f8
    r4 = b[r3+-1] (u)
    if (r2 == r4) goto L020142da
    if (r5 < 2) goto L020142fa
    if (r2 != 0) goto L0201430a
    goto L020142fa
L020142f8:
    r4 = b[r3+-1] (u)
L020142fa:
    r5 = r4 | 0x20
    r5 = r5.b0 (u)
    if (r5 != 32) goto L0201430a
    goto L02014320
L02014306:
    r2 = b[++r0=1] (u)
L0201430a:
    r2 |= 32
    r2 = r2.b0 (u)
    if (r2 != 32) goto L02014306
L02014312:
    r2 = b[r0++=1] (u)
    if (r2 == 32) goto L02014312
    r0 += -1
L0201431a:
    if (r2 != 0) goto L020142d6
L0201431c:
    r0 = 0
    {pc, r5, r4} = [sp++]
L02014320:
    r0 = 1
    if (r2 == 33) goto L0201432a
    {pc, r5, r4} = [sp++]
L02014328:
    r4 = b[r3++=1] (u)
L0201432a:
    if (r4 == 32) goto L02014328
    if ((r4 & 0xFF) != 0) goto L0201431c
    {pc, r5, r4} = [sp++]

; tuner_and_control_records_name_listed: 0x02014336..0x02014366, module tuner-and-control-records (name_listed)
.type tuner_and_control_records_name_listed,@function
tuner_and_control_records_name_listed:
    [--sp] = {rets, r5, r4}
    r1 = L01c27cd4
L0201433e:
    r3 = [r0++=4]
    if (r3 == 0) goto L02014362
    r2 = r1
L02014344:
    r4 = b[r3++=1] (u)
    if (r4 == 0) goto L02014350
    r5 = b[r2++=1] (u)
    if (r4 == r5) goto L02014344
    goto L0201433e
L02014350:
    r3 = 0
L02014352:
    r4 = b[r2+r3] (u)
    r3 += 1  ; @add.ri.u5
    if (r4 == 32) goto L02014352
    if (r4 != 0) goto L0201433e
    r0 = 1
    {pc, r5, r4} = [sp++]
L02014362:
    r0 = 0
    {pc, r5, r4} = [sp++]
