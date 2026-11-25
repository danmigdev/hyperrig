; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201ade8..0x0201b1b6: vendor code (JieLi SDK or library, not reversed), as instructions
L0201ade8:
    sp += -24
    r11 = cnum
    r9 = 29883864
    r5 = [r9+0]
    r4 = r0
    r0 = 4293918736
    r1 = r5 & r0
    r0 = 3888119824
    r13 = 32432708
    r14 = r13 + 284
    r8 = r13 + 3640
    r7 = r8 + 88
    if (r1 == r0) goto L0201af5e
    r10 = L01c26890
    r1 = [r10+104]
    r1 = r1 | r11
    r0 |= r1
    [r9+0] = r0
    r0 = 1
    call storage_fault_once
    [sp] = r5
    r0 = [r9+4]
    [sp+4] = r0
    r0 = [r9+8]
    [sp+8] = r0
    r0 = [r9+12]
    [sp+12] = r0
    r0 = [r9+16]
    [sp+16] = r0
    r0 = [r9+20]
    [sp+20] = r0
    r0 = sp + 0
    call storage_fault_append
    r0 = 3888119808
    r0 = r0 | r11
    r1 = r9 + -344
    [r1+0] = r0
    r0 = 0
    r1 += 4  ; @add.ri.u5
    goto L0201ae80
L0201ae76:
    r2 = [r4+r0<<2]
    [r1+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
L0201ae80:
    if (r0 != 25) goto L0201ae76
    r0 = r1 + 100
    call ram_callbacks_link_status  ; @call.xl
    r0 = 0
    r1 = r7 + -212
    r2 = r9 + -440
    goto L0201aeb4
L0201ae9a:
    r3 = [++r1=452]
    r5 = r2
    [++r5=r0] = r3
    r3 = [r1+4]
    [r5+4] = r3
    r3 = [r1+8]
    [r5+8] = r3
    r3 = [r1+12]
    [r5+12] = r3
    r1 += 60
    r0 += 16  ; @add.ri.u5
L0201aeb4:
    if (r0 != 32) goto L0201ae9a
    r0 = r11 << 9
    r12 = r0 + r7
    r1 = [r12+16]
    r0 = r2 + 232
    [r0+0] = r1
    r1 = [r12+12]
    [r0+4] = r1
    r1 = [r7+0]
    [r0+8] = r1
    r1 = [r8+600]
    [r0+12] = r1
    r1 = [r14+16]
    [r0+16] = r1
    r1 = [r14+20]
    [r0+20] = r1
    r1 = 1
    if (r11 != 0) {  ; @if.ne.ri.s12
    r1 = 0
    }
    r2 = r7 + -100
    r2 <= insert(r1, p:9, l:1)
    r2 = [r2+0]
    r5 = r8  #
    [r0+24] = r2
    r5 <= insert(r1, p:9, l:1)
    r1 = [r5+0]
    [r0+28] = r1
    r1 = [r14+12]
    [r0+40] = r1
    r1 = [r14+28]
    [r0+44] = r1
    r1 = [r14+24]
    [r0+48] = r1
    r1 = [r10+528]
    r2 = L01c34454
    r2 = [r2+0]
    r2 = r2.l (u)
    r2 <= insert(r1, p:16, l:16)
    r1 = r2 | 0xFB000000
    [r0+60] = r1
    call fault_record_status_bits
    r1 = r9 + -144
    [r1+0] = r0
    r0 = [r13+0]
    [r9+4] = r0
    r0 = [r12+0]
    [r9+8] = r0
    r0 = [r4+64]
    [r9+12] = r0
    r0 = [r4+76]
    [r9+16] = r0
    r0 = [r5+0]
    [r9+20] = r0
L0201af5e:
    r0 = cnum
    r1 = r7 + -4308
    if (r0 == 0) goto L0201af84
    [r8+28] = 0xFFFFFFFF
    [r1+0] &= 0xFFFFFFF7
    [r1+0] |= 0x2
    r2 = [r8+0]
    r2 = [r13+0]
    r2 = [r8+600]
    r1 = [r1+4]
    goto L0201af9e
L0201af84:
    r2 = r1 + 4732
    [r2+28] = 0xFFFFFFFF
    [r1+4] &= 0xFFFFFFF7
    [r1+4] |= 0x2
    r2 = [r2+0]
    r2 = [r13+0]
    r2 = [r7+0]
    r1 = [r1+0]
L0201af9e:
    r1 = 0
    r2 = r7 + 240
    goto L0201afb4
L0201afa6:
    r3 = r1 + r2
    r4 = [r3+12]
    r4 = [r3+8]
    r4 = [r3+4]
    r1 = r1 + 512  #
    r3 = [r3+0]
L0201afb4:
    if (r1 != 1024) goto L0201afa6
    r6 = r0 << 9
    r5 = 0
    goto L0201afe8
L0201afc0:
    r4 = r6
    r0 = [++r4=r7]
    r0 = r0 & (1 << r5)
    if (r0 == 0) goto L0201afe6
    if (r5 != 3) goto L0201afe6
    call L0203e742  ; @call.xl
    if (r0 == 0) goto L0201afde
    call L0203e742  ; @call.xl
L0201afde:
    r0 = [r4+16]
    r0 = [r4+12]
    r0 = [r4+8]
    r0 = [r4+4]
L0201afe6:
    r5 += 1  ; @add.ri.u5
L0201afe8:
    if (r5 != 32) goto L0201afc0
    call L0203e742  ; @call.xl
    if (r0 == 0) goto L0201affa
    call L0203e742  ; @call.xl
L0201affa:
    r0 = [r14+16]
    r0 = [r14+20]
    r0 = [r14+16]
    r0 = [r14+12]
    r0 = [r14+28]
    r0 = [r14+24]
    r0 = 0
    r1 = r7 + -3668
    r2 = r1 + 64
    r3 = 263224
    r4 = r3 + 6092
    goto L0201b0bc
L0201b028:
    r5 = [r1+-60]
    r5 = r5 & (1 << r0)
    if (r5 == 0) goto L0201b0ba
    r5 = r0 + -2
    if (r5 > 13) goto L0201b0ba
    tbb [r5]
L0201b03a:
    .byte (L0201b05a - L0201b03a) / 2, (L0201b0ba - L0201b03a) / 2, (L0201b0ba - L0201b03a) / 2, (L0201b0ba - L0201b03a) / 2, (L0201b0ba - L0201b03a) / 2, (L0201b0ba - L0201b03a) / 2, (L0201b0ba - L0201b03a) / 2, (L0201b0ba - L0201b03a) / 2
    .byte (L0201b048 - L0201b03a) / 2, (L0201b076 - L0201b03a) / 2, (L0201b048 - L0201b03a) / 2, (L0201b08a - L0201b03a) / 2, (L0201b0a6 - L0201b03a) / 2, (L0201b0b0 - L0201b03a) / 2
L0201b048:
    r5 = [r14+32]
    r5 = [r14+36]
    r5 = [r14+40]
    r5 = [r14+44]
    goto L0201b0ba
L0201b05a:
    r5 = [r14+24]
    r5 = [r14+8]
    r6 = [r14+8]
    r5 = 0
L0201b068:
    r7 = r6 & (1 << r5)
    if (r7 != 0) goto L0201b09c
    r5 += 1  ; @add.ri.u5
    ifs (r5 < 8) goto L0201b068
    goto L0201b09c
L0201b076:
    r6 = [r14+4]
    r5 = 0
L0201b07c:
    r7 = r6 & (1 << r5)
    if (r7 != 0) goto L0201b09c
    r5 += 1  ; @add.ri.u5
    ifs (r5 < 8) goto L0201b07c
    goto L0201b09c
L0201b08a:
    r6 = [r14+0]
    r5 = 0
L0201b090:
    r7 = r6 & (1 << r5)
    if (r7 != 0) goto L0201b09c
    r5 += 1  ; @add.ri.u5
    ifs (r5 < 8) goto L0201b090
L0201b09c:
    r6 = [r1+r5<<2]
    r5 = [r2+r5<<2]
    goto L0201b0ba
L0201b0a6:
    r5 = [r3+0]
    r5 = [r3+12]
    r5 = [r3+4]
    r5 = [r3+8]
    goto L0201b0ba
L0201b0b0:
    r5 = [r4+8]
    r5 = [r4+12]
    r5 = [r4+0]
    r5 = [r4+4]
    r5 = [r4+16]
L0201b0ba:
    r0 += 1  ; @add.ri.u5
L0201b0bc:
    if (r0 != 32) goto L0201b028
    r3 = 81416
    [r3+0] &= 0xFFFFFEFF
    [r3+0] |= 0x1
    r0 = 32
    call storage_fault_exchange  ; @call.xl
    r0 = 128
    call storage_fault_exchange  ; @call.xl
    r0 = 64
    call storage_fault_exchange  ; @call.xl
    r4 = -258
    [r3+0] &= r4
    [r3+0] &= 0xFFFFFEFF
    [r3+0] |= 0x1
    r0 = 128
    call storage_fault_exchange  ; @call.xl
    r0 = 160
    call storage_fault_exchange  ; @call.xl
    r0 = 94
    call storage_fault_exchange  ; @call.xl
    [r3+0] &= r4
    [r3+0] &= 0xFFFFFEFF
    [r3+0] |= 0x1
    r2 = r0
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r0 = 160
    call storage_fault_exchange  ; @call.xl
    r0 = r2 | 0x10
    call storage_fault_exchange  ; @call.xl
    [r3+0] &= r4
L0201b13a:
    goto L0201b13a
L0201b13c:
    r0 = cnum
    r0 = r0 << 9
    r1 = 32436432
    r0 += r1  ; @add.rr
    [r0+0] &= 0xFFFFFFF7
    rts
L0201b150:
    r0 = cnum
    r0 = r0 << 9
    r1 = 32436432
    r0 += r1  ; @add.rr
    [r0+0] |= 0x8
    rts
L0201b164:
    [--sp] = {reti}
    [--sp] = {r0}
    r0 = 0x13400
    [r0+0] |= 0x40
    {r0} = [sp++]
    {reti} = [sp++]
    rti
L0201b17a:
    r0 = L01c25434
    r0 = b[r0+0] (u)
    r1 = 1
    r0 = r1 & ~r0
    rts
L0201b18a:
    [--sp] = {rets, r6-r4}
    r1 = r0
    r2 = r1 + 24
    r0 = 0
    r3 = 0
    goto L0201b1ac
L0201b196:
    r4 = r1  #
    r5 = b[r2+0] (u)
    r6 = b[r4++=1] (u)
    if (r6 != r5) goto L0201b1a8
    r5 = b[r2+1] (u)
    r4 = b[r4+0] (u)
    if (r4 == r5) goto L0201b1b2
L0201b1a8:
    r2 += 8  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L0201b1ac:
    ifs (r3 <= 3) goto L0201b196
    {pc, r6-r4} = [sp++]
L0201b1b2:
    r0 = r2
    {pc, r6-r4} = [sp++]
