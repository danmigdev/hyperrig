; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage_preparation: 1 function, 0x020031d4..0x020034ce

; preset_storage_preparation_prepare: 0x020031d4..0x020034ce, module preset-storage-preparation (prepare)
.type preset_storage_preparation_prepare,@function
preset_storage_preparation_prepare:
    [--sp] = {rets, r14-r4}
    sp += -172
    r0 = 712
    r13 = L01c26890
    r0 = b[r13+r0] (u)
    if (r0 != 0) goto L020034ca
    call storage_platform_clock  ; @call.xl
    r1 = 716
    r1 = b[r13+r1] (u)
    r10 = r0
    if (r1 != 0) goto L02003388
    r1 = r13 + 3440
    r0 = 0
    rep 17 {
    [r1++=4] = r0
    }
    r1 = 3476
    r2 = 255
    r3 = 0
    goto L02003224
L02003214:
    r4 = r3 + r13
    b[r4+r1] = r2
    r4 = sp + 84
    [r4+r3<<2] = r0
    r3 += 1  ; @add.ri.u5
L02003224:
    if (r3 != 16) goto L02003214
    r8 = 873
    r0 = 1
    [r13+r8<<2] = r0
    r14 = sp + 68
    r6 = 0
    r9 = 1129335636
    r11 = 3440
    r12 = 2
    r5 = 0
    goto L020032d4
L0200324a:
    r0 = r5
    call preset_storage_block
    r0 = r0 + 4080
    r1 = sp + 68
    r2 = 16
    call preset_storage_preparation_read_forward
    r2 = 5
    if (r0 == 0) goto L0200326e
L02003260:
    r0 = r5 + r13
    b[r0+r11] = r2
L02003268:
    r6 += 1  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
    goto L020032d4
L0200326e:
    r0 = [r14+12]
    if (r0 != r9) goto L02003268
    r0 = [r14+8]
    if (r0 != -1) goto L02003268
    r2 = [sp+68]
    r0 = 0
    if (r2 != -1) {  ; @if.ne.ri.s12
    r0 = [r14+4]
    }
    r1 = r5
    if (r2 != -1) {  ; @if.ne.ri.s12
    r1 = r2
    }
    r2 = [r13+r8<<2]
    if (r0 >= r2) {
    r2 = r0 + 1
    [r13+r8<<2] = r2
    }
    r2 = 2
    if (r1 > 15) goto L02003260
    r3 = r1 + r13
    r3 = r3 + 3476
    r4 = b[r3+0] (s)
    ifs (r4 < 0) goto L020032c8
    r7 = sp + 84
    r7 = [r7+r1<<2]
    if (r0 <= r7) goto L02003260
    r2 = r4 + r13
    b[r2+r11] = r12
L020032c8:
    b[r3+0] = r6
    r2 = sp + 84
    [r2+r1<<2] = r0
    r2 = 3
    goto L02003260
L020032d4:
    if (r5 != 18) goto L0200324a
    r9 = sp + 8
    r8 = 0
    r7 = r11
    r11 = 1246776148
    r12 = 5
    r5 = 0
    goto L0200337a
L020032ee:
    r4 = r5 + r13
    r0 = b[r4+r7] (u)
    if (r0 != 0) goto L02003342
    r0 = r5
    call preset_storage_block
    r6 = r0
    r1 = sp + 28
    r2 = 40
    call preset_storage_preparation_read_forward
    if (r0 == 0) goto L02003310
    b[r4+r7] = r12
    goto L02003342
L02003310:
    if (r5 != 17) goto L02003332
    r0 = [sp+28]
    if (r0 != r11) goto L02003332
    [sp+4] = r8  ; @st.w.sp.l
    r1 = sp + 8
    r2 = 20
    r0 = r6
    call preset_storage_preparation_read_forward
    if (r0 == 0) goto L02003346
L0200332a:
    r6 = 2
L0200332c:
    b[r4+r7] = r6
    goto L02003342
L02003332:
    r0 = r6
    call preset_storage_preparation_erased
    r1 = 1
    if (r0 != 0) goto L0200333e
    r1 = 2
L0200333e:
    b[r4+r7] = r1
L02003342:
    r5 += 1  ; @add.ri.u5
    goto L0200337a
L02003346:
    r0 = r6 + 4088
    r1 = sp + 4
    r2 = 4
    r6 = 4
    call preset_storage_preparation_read_forward
    if (r0 != 0) goto L0200332a
    r0 = [sp+4]
    if (r0 != -1) goto L0200332a
    r0 = [r9+4]
    if (r0 > 15) goto L0200332a
    r0 = [r9+8]
    if (r0 > 1920) goto L0200332a
    r0 = [r9+12]
    if (r0 < 1921) goto L0200332c
    goto L0200332a
L0200337a:
    if (r5 != 18) goto L020032ee
    r0 = 716
    r1 = 1
    b[r13+r0] = r1
L02003388:
    r0 = 3840
    call L0203c15c  ; @call.xl
    r12 = r0
    if (r0 == 0) goto L020034ca
    r0 = 3457
    r0 = b[r13+r0] (u)
    r11 = 0
    r6 = 0
    if (r0 != 4) goto L02003464
    r1 = sp + 152
    r0 = 0xDE000
    r2 = 20
    call preset_storage_preparation_read_forward
    if (r0 == 0) goto L020033be
L020033b8:
    r6 = -2
    r4 = -2
    goto L02003496
L020033be:
    r6 = [sp+160]
    if (r6 == 0) goto L020033d2
    r0 = 909344
    r1 = r12
    r2 = r6
    call preset_storage_preparation_read_forward
    if (r0 != 0) goto L020033b8
L020033d2:
    r8 = r12 + 1920  #
    r7 = [sp+164]
    if (r7 == 0) goto L020033ec
    r0 = 911264
    r1 = r8
    r2 = r7
    call preset_storage_preparation_read_forward
    if (r0 != 0) goto L020033b8
    goto L020033ee
L020033ec:
    r7 = 0
L020033ee:
    r0 = sp + 152
    r9 = r0 + 4
    r0 = -1
    r2 = 12
    r1 = r9
    call preset_storage_crc_update
    r1 = r12
    r2 = r6
    call preset_storage_crc_update
    r1 = r8
    r2 = r7
    call preset_storage_crc_update
    r0 = ~r0  #
    r1 = [sp+168]
    if (r1 != r0) goto L02003458
    r0 = [r9+0]
    r1 = r12  #
    [sp] = r7
    r2 = r6
    r3 = r8
    call preset_storage_preparation_replace_pair
    r6 = r0
    if (r6 != 0) goto L02003450
    r0 = 0
    [sp+148] = r0
    r0 = 913400
    r1 = sp + 148
    r2 = 4
    call preset_storage_preparation_write_forward
    r6 = -3
    if (r0 != 0) goto L02003450
    r0 = 3457
    r1 = 2
    b[r13+r0] = r1
    r6 = 1
L02003450:
    r4 = r6
    ifs (r6 >= 0) goto L02003464
    goto L02003496
L02003458:
    r0 = 3457
    r1 = 2
    b[r13+r0] = r1
    r6 = 0
L02003464:
    r5 = 3476
    r4 = 0
    r7 = 0
    goto L0200348e
L0200346e:
    r0 = r7 + r13
    r0 = b[r0+r5] (s)
    ifs (r0 > -1) goto L0200348c
    r1 = 0
    r3_r2 = 0
    [sp] = r11  ; @st.w.sp.l
    r0 = r7
    call preset_storage_preparation_replace_pair
    if (r0 != 0) goto L02003494
    r4 += 1  ; @add.ri.u5
L0200348c:
    r7 += 1  ; @add.ri.u5
L0200348e:
    if (r7 <= 15) goto L0200346e
    goto L02003496
L02003494:
    r4 = r0
L02003496:
    r0 = r12
    call L0203d218  ; @call.xl
    r0 = r4 & 0xF
    r1 = r6 << 4
    r1 = r1.b0 (u)
    r5 = r0 | r1
    r0 = r10
    call preset_loader_elapsed
    r5 <= insert(r0, p:8, l:24)
    r0 = 18
    r1 = 0xDE000
    r2 = r5
    call storage_coordination_notify
    r0 = 712
    r1 = 1
    b[r13+r0] = r1
L020034ca:
    sp += 172
    {pc, r14-r4} = [sp++]
