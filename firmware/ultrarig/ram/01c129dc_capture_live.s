; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_live: 6 functions, 0x01c129dc..0x01c13072

; capture_live_rechannel: 0x01c129dc..0x01c12a54, module capture-live (rechannel), capture-processing (rechannel)
.type capture_live_rechannel,@function
capture_live_rechannel:
    [--sp] = {rets, r6-r4}
    r6 = r2
    r5 = r0
    r4 = [r5+92]
    r2 = L01c33d00
    [r2+0] = r1
    [r2+4] = r6
    r0 = r1 + 256
    [r2+12] = r0
    r1 = [r4+68]
    [r2+52] = r1
    r4 = [r4+76]
    r0 = r3 / r4 (u)
    r0 *= r4
    r0 = r3 - r0
    r0 = r0 * 0xC
    r0 = r0 + r1
    r3 = r4 * 0xC  #
    [r2+8] = r0
    r0 = r1 + r3
    r0 = r1 + 768  #
    [r2+48] = r0
    [r2+40] = r0
    [r2+44] = r3
    r1 = [r5+60]
    r0 = h[r1+0] (s)
    [r2+16] = r0
    r0 = h[r1+2] (s)
    [r2+20] = r0
    r0 = h[r1+4] (s)
    [r2+24] = r0
    r0 = b[r5+56] (s)
    r3 = r0 + -1  #
    [r2+28] = r0
    r0 = 1
    r1 = 0
    r1_r0 <<= r3
    [r2+32] = r0
    [r2+36] = r1
    r0 = r2
    call capture_live_rechannel3  ; @call.xl
    {pc, r6-r4} = [sp++]

; capture_live_layer: 0x01c12a54..0x01c12c32, module capture-live (layer), capture-processing (layer)
.type capture_live_layer,@function
capture_live_layer:
    [--sp] = {rets, r15-r4}
    sp += -12
    r10 = [r0+92]
    r15 = r1  #
    r0 = [sp+80]
    r8 = r1 * 0x50
    r1 = r8
    r12 = b[++r1=r10] (u)
    r11 = r3  #
    [sp] = r2
    r0 = r0 & 0x1
    r2 = r0 * 0xC8
    r3 = [r1+76]
    r0 = L01c33d38
    r9 = r2 + r0  #
    r2 = [sp+68]
    r4 = r12 + -1
    r0 = r11 / r3 (u)
    r0 *= r3
    r0 = r11 - r0
    r5 = [r1+68]
    r0 = r0 * 0xC  #
    r1 = h[r1+2] (u)
    r13 = [sp+76]
    r14 = [sp+72]
    [sp+4] = r2
    r2 = [sp+64]
    r2 = r5 + r0  #
    [sp+8] = r2
    r7 = r4 << 2
    [++r7=r9] = r2
    if (r4 == 0) goto L01c12ae2
    r0 = r3 - r1
    r6 = r0 * 0x3
    r1 = r1 * 0x3
    r0 = r1 << 2
    r5 = r5 + r0
    r4 = r9 + -8
    r3 = 0x0 - r1
    r1 = r12
L01c12aca:
    r0 = r3
    if (r2 < r5) {
    r0 = r6
    }
    r0 = r0 << 2
    r2 = r2 + r0
    [r4+r1<<2] = r2
    r1 += -1
    if (r1 != 1) goto L01c12aca
    r2 = [r7+0]
L01c12ae2:
    r4 = r9 + 60
    r5 = r10 + r8  #
    [r4+0] = r2
    r8 = [r5+36]
    r10 = b[r5+8] (s)
    r6 = [r8+0]
    r7 = [r8+4]
    r0 = r10 + -1
    r2 = 1
    r3 = 0
    r3_r2 <<= r0
    r0 = r2 + r6
    r1 = r3 + r7 + c
    [r4+4] = r0
    [r4+8] = r1
    r0 = [r5+52]
    [r4+56] = r0
    r6 = [r8+8]
    r7 = [r8+12]
    r0 = r2 + r6
    r1 = r3 + r7 + c
    [r4+12] = r0
    [r4+16] = r1
    r0 = [r5+56]
    [r4+60] = r0
    r6 = [r8+16]
    r7 = [r8+20]
    r0 = r2 + r6
    r1 = r3 + r7 + c
    [r4+20] = r0
    [r4+24] = r1
    r1 = r9 + 124  #
    r0 = [r5+60]
    [r1+0] = r0
    r0 = [r5+44]
    [r4+28] = r0
    r0 = [sp]
    [r4+32] = r0
    r0 = [sp+4]
    [r4+36] = r0
    [r4+40] = r14
    r0 = [r5+32]
    [r4+44] = r0
    r3 = 1
    [r9+196] = r3
    r2 = b[r5+6] (s)
    r0 = r2 + -1
    r0 = r3 << r0
    [r4+48] = r0
    [r4+52] = r2
    r0 = [r5+12]
    [r1+4] = r0
    r0 = b[r5+10] (s)
    [r1+8] = r0
    r0 += -1
    [r1+12] = r0
    [r1+16] = r10
    r2 = b[r5+9] (s)
    [r1+20] = r2
    r0 = b[r5+64] (s)
    r0 = r11 / r13 (u)  #
    [r1+24] = r0
    r0 *= r13
    r0 = r11 - r0
    r0 = r0 * 0xC
    r0 = r13 * 0xC  #
    [r1+28] = r0
    [r1+32] = r0
    r0 = [sp+8]
    r0 = r0 * 0xC
    r0 = r12 << 2  #
    [r1+36] = r0
    [r1+40] = r12
    r0 += r9
    r0 = r2 + -1  #
    [r1+44] = r0
    r0 = 0x0 - r2  #
    [r1+48] = r0
    r0 = r2 + 32  #
    [r1+52] = r0
    [r1+56] = r0
    [r1+60] = 0x300
    if (r15 != 0) goto L01c12be6
    r0 = [sp+8]
    r1 = r0 * 0x3  #
    r0 = [sp+4]
    call capture_live_zero  ; @call.xl
    r0 = [r4+136]
    if (r0 == 0) goto L01c12c02
L01c12be6:
    r0 = b[r5+11] (u)
    r1 = r0 + -1
    if (r1 > 3) goto L01c12c02
    tbb [r1]
capture_processing_jump_table:
    .byte (L01c12bf6 - capture_processing_jump_table) / 2, (L01c12c26 - capture_processing_jump_table) / 2, (L01c12c0e - capture_processing_jump_table) / 2, (L01c12c1a - capture_processing_jump_table) / 2
L01c12bf6:
    r0 = r9
    call capture_live_layer6  ; @call.xl
    sp += 12
    {pc, r15-r4} = [sp++]
L01c12c02:
    r0 = r9
    call capture_live_layer_generic  ; @call.xl
    sp += 12
    {pc, r15-r4} = [sp++]
L01c12c0e:
    r0 = r9
    call capture_live_layer15  ; @call.xl
    sp += 12
    {pc, r15-r4} = [sp++]
L01c12c1a:
    r0 = r9
    call capture_live_layer15_shift  ; @call.xl
    sp += 12
    {pc, r15-r4} = [sp++]
L01c12c26:
    r0 = r9
    call capture_live_layer6_shift  ; @call.xl
    sp += 12
    {pc, r15-r4} = [sp++]

; capture_live_iterate: 0x01c12c32..0x01c12cc2, module capture-live (iterate), capture-processing (iterate)
.type capture_live_iterate,@function
capture_live_iterate:
    [--sp] = {rets, r13-r4}
    sp += -20
    r12 = r3
    r8 = r2
    r2 = r1
    r7 = r0
    if (r2 >= r8) goto L01c12c90
    r6 = h[r7+8] (u)
    if (r6 <= r2) goto L01c12c90
    r10 = [sp+72]
    r9 = [sp+68]
    r11 = [sp+64]
    r1 = r2 + 1
    r0 = r2 * 0x50
    r5 = r0 + 156
    r13 = 64
L01c12c5c:
    r4 = r1
    r1 = r4 + -1
    if (r6 == r4) goto L01c12c94
    r0 = [r7+92]
    r0 = r0 + r5
    r3 = r11  #
    r2 = [r0+-8]
    r0 = [r0+0]
    [sp+16] = r10
    r0 = r7  #
    [sp+12] = r0
    r2 = r12  #
    [sp+8] = r2
    [sp+4] = r9
    [sp] = r13
    call capture_live_layer
    if (r4 >= r8) goto L01c12c90
    r5 += 80
    r1 = r4 + 1
    if (r4 < r6) goto L01c12c5c
L01c12c90:
    sp += 20
    {pc, r13-r4} = [sp++]
L01c12c94:
    [sp+16] = r10
    r0 = 1
    r3 = r11  #
    [sp+12] = r0
    [sp+4] = r9
    r0 = 64
    r0 = r10 & 0x1  #
    [sp] = r0
    r2 = r0 * 0x18
    r0 = L01c33ed0
    r0 = r0 + r2
    r0 += 64
    r0 = r7  #
    [sp+8] = r0
    r2 = r12
    call capture_live_layer
    sp += 20
    {pc, r13-r4} = [sp++]

; capture_live_head: 0x01c12cc2..0x01c12d34, module capture-live (head), capture-processing (head)
.type capture_live_head,@function
capture_live_head:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r6 = r0
    r1 = L01c33ed0
    [++r1=112] = r4
    r5 = r6 + 68
    r0 = [r5+12]
    [r1+4] = r0
    r4 = [r5+16]
    r0 = r4 & r2
    r0 = r0 * 0xC
    r0 = r4 * 0xC  #
    [r1+8] = r0
    r0 = r0 + 12
    [r1+12] = r0
    [r1+16] = 0x300
    r2 = b[r6+3] (u)
    r0 = r2 * 0xC
    r0 += -12
    [r1+20] = r0
    r0 = [r5+0]
    r0 = r2 * 0x3  #
    [r1+24] = r0
    [r1+28] = r3
    [r1+32] = 0x40
    [r1+36] = r0
    r2 = b[r6+57] (s)
    r3 = r2 + -1
    r0 = 1
    r0 <<= r3
    r0 += -1
    r0 = r1  #
    [r1+40] = r0
    [r1+44] = r2
    r2 = [r6+72]
    r3 = [r6+76]
    [r1+48] = r2
    [r1+52] = r3
    call capture_live_head3  ; @call.xl
    {pc, r6-r4} = [sp++]

; capture_live_process: 0x01c12d34..0x01c12f20, module capture-live (process), capture-processing (process)
.type capture_live_process,@function
capture_live_process:
    [--sp] = {rets, r15-r4}
    sp += -36
    r13 = r0  #
    r0 = h[r0+8] (u)
    r6 = r3
    r9 = r2
    r7 = r1
    if (r0 == 0) goto L01c12d72
    r14 = r13 + 68
    r1 = [r14+24]
    if (r1 == 0) goto L01c12d72
    r2 = [r1+76]
    if (r2 == 0) goto L01c12d72
    r0 = [r1+68]
    if (r0 == 0) goto L01c12d72
    if (r6 < 64) goto L01c12d88
    r12 = [r14+20]
    r15 = L01c33d00
    r4 = 1
    r5 = 0
    [sp+24] = r4
    [sp+28] = r5
    goto L01c12e4c
L01c12d72:
    if (r6 == 0) goto L01c12d7e
L01c12d74:
    r0 = [r7++=4]
    [r9++=4] = r0
    if (--r6 != 0) goto L01c12d74
L01c12d7e:
    r0 = L01c344b0
    [r0+0] += 0x1
L01c12d88:
    sp += 36
    {pc, r15-r4} = [sp++]
L01c12d8c:
    r0 = 0
    r1 = r10  #
    [sp+16] = r0
    r0 = 1
    r2 = r11  #
    [sp+12] = r0
    r0 = L01c33ed0
    r0 += 64
    r3 = r12  #
    [sp+8] = r0
    r0 = L01c33a00
    [sp+4] = r0
    r0 = 64
    r0 = r13  #
    [sp] = r0
    call capture_live_layer
L01c12db6:
    r1 = L01c33ed0
    r0 = L01c33a00
    [++r1=112] = r0
    r0 = [r14+12]
    [r1+4] = r0
    r2 = [r14+16]
    r0 = r2 & r12
    r0 = r0 * 0xC
    r0 = r2 * 0xC  #
    [r1+8] = r0
    r0 = r0 + 12
    [r1+12] = r0
    [r1+16] = 0x300
    r2 = b[r13+3] (u)
    r0 = r2 * 0xC
    r0 += -12
    [r1+20] = r0
    r0 = [r14+0]
    [r1+24] = r0
    [r1+28] = r9
    r0 = 64
    r0 = r2 * 0x3  #
    [r1+32] = r0
    [r1+36] = r0
    r2 = b[r13+57] (s)
    r0 = r2 + -1
    r3 = 1
    r0 = r3 << r0
    r0 += -1
    r0 = r1  #
    [r1+40] = r0
    [r1+44] = r2
    r2 = [r13+72]
    r3 = [r13+76]
    [r1+48] = r2
    [r1+52] = r3
    call capture_live_head3  ; @call.xl
    r0 = [r14+20]
    r12 = r0 + 64
    r6 += -64
    [r14+20] = r12
    if (r6 < 64) goto L01c12d88
    r1 = [r14+24]
    r2 = [r1+76]
    r9 = r9 + 256
L01c12e4c:
    r0 = L01c33ed0
    r11 = r0 + 168
    [r15+0] = r7
    [r15+4] = r11
    r7 = r7 + 256
    [r15+12] = r7
    r1 = [r1+68]
    [r15+52] = r1
    r0 = r12 / r2 (u)
    r0 *= r2
    r0 = r12 - r0
    r0 = r0 * 0xC
    r0 = r0 + r1
    [r15+8] = r0
    r2 = r2 * 0xC
    r0 = r1 + r2
    [r15+48] = r0
    r0 = r1 + 768
    [r15+40] = r0
    [r15+44] = r2
    r1 = [r13+60]
    r0 = h[r1+0] (s)
    [r15+16] = r0
    r0 = h[r1+2] (s)
    [r15+20] = r0
    r0 = h[r1+4] (s)
    [r15+24] = r0
    r0 = b[r13+56] (s)
    [r15+28] = r0
    r2 = r0 + -1
    r0 = [sp+24]
    r1 = [sp+28]
    r1_r0 <<= r2
    [r15+32] = r0
    [r15+36] = r1
    r0 = r15
    call capture_live_rechannel3  ; @call.xl
    r8 = h[r13+8] (u)
    if (r8 == 0) goto L01c12db6
    r10 = r8 + -1
    r1 = 0
    r4 = 156
L01c12ee8:
    if (r10 == r1) goto L01c12d8c
    r0 = [r14+24]
    r0 = r0 + r4
    r2 = [r0+-8]
    r0 = [r0+0]
    r5 = r1 + 1
    r3 = 0
    r3 = r12  #
    [sp+16] = r3
    [sp+12] = r0
    r2 = r11  #
    [sp+8] = r2
    r0 = L01c33a00
    [sp+4] = r0
    r0 = 64
    r0 = r13  #
    [sp] = r0
    call capture_live_layer
    r4 += 80
    r1 = r5
    if (r5 < r8) goto L01c12ee8
    goto L01c12db6

; capture_live_warmup: 0x01c12f20..0x01c13072, module capture-live (warmup), capture-warmup (warmup)
.type capture_live_warmup,@function
capture_live_warmup:
    [--sp] = {rets, r14-r4}
    sp += -20
    r7 = r0
    r8 = h[r7+8] (u)
    r10 = r1
    if (r8 == 0) goto L01c12ff2
    r9 = r7 + 80
    r0 = [r9+12]
    if (r0 == 0) goto L01c12ff2
    r2 = r0 + 68
    r1 = [r2+8]
    if (r1 == 0) goto L01c12ff2
    r3 = [r2+0]
    if (r3 == 0) goto L01c12ff2
    r0 = b[r7+2] (u)
    if (r0 != 3) goto L01c12ff2
    r0 = b[r7+164] (u)
    if (r0 == 0) goto L01c12ff2
    r0 = b[r7+1] (u)
    if (r0 != 32) goto L01c12ff2
    r0 = r1 * 0x3
    if (r0 == -192) goto L01c12f78
    r4 = 0
    r1 = 0
L01c12f64:
    [r3+r1<<2] = r4
    r0 = [r2+8]
    r1 = r1 + 1
    r0 = r0 * 0x3
    r0 = r0 + 192
    if (r1 < r0) goto L01c12f64
L01c12f78:
    r11 = L01c33ed0
    r12 = 0
    [r11+0] = r12
    [r11+4] = r12
    [r11+8] = r12
    [r11+12] = r12
    [r9+8] = r12
    r14 = r8 + -1
    r13 = 4
    r1 = 0
L01c12f9e:
    r6 = r1 + 1
    if (r6 == r8) goto L01c13000
    r2 = [r9+12]
    r0 = r6 * 0x50
    r5 = r2 + r0
    r2 = [++r5=68]
    r0 = [r5+8]
    [sp+16] = r12
    r0 = r11 + 16  #
    [sp+12] = r0
    r2 = r11  #
    [sp+8] = r2
    r0 = r7  #
    [sp+4] = r0
    r3 = 0
    [sp] = r13
    call capture_live_layer
    r2 = [r5+0]
    r1 = r2  #
    r0 = [r5+8]
    r4 = [r1++=20]
    r0 += 63
    if (r0 == 0) goto L01c12fea
    r3 = [r2+8]
    r2 = [r2+4]
L01c12fde:
    [r1+-8] = r4
    [r1+-4] = r2
    [r1++=12] = r3
    if (--r0 != 0) goto L01c12fde
L01c12fea:
    r1 = r6
    if (r6 < r8) goto L01c12f9e
    goto L01c13024
L01c12ff2:
    r0 = r7
    call capture_live_reset
    r1 = 0
L01c12ffa:
    r0 = r1
    sp += 20
    {pc, r14-r4} = [sp++]
L01c13000:
    r0 = 0
    r1 = r14  #
    [sp+16] = r0
    r0 = 1
    r0 = r11 + 64  #
    [sp+12] = r0
    r0 = r11 + 16  #
    [sp+8] = r0
    r2 = r11  #
    [sp+4] = r0
    r0 = 4
    r3 = 0
    r0 = r7  #
    [sp] = r0
    call capture_live_layer
L01c13024:
    r0 = [r9+4]
    r0 = r0 + 1
    r1 = r0
    if (r0 >= 64) {
    r1 = 64
    }
    r1 = r1 + r0
    if (r1 == 0) goto L01c13052
    r4 = [r11+24]
    r2 = [r11+16]
    r3 = [r11+20]
    r0 = [r9+0]
L01c13046:
    [r0+0] = r2
    [r0+4] = r3
    [r0+8] = r4
    r0 = r0 + 12
    if (--r1 != 0) goto L01c13046
L01c13052:
    r1 = 1
    if (r10 == 0) goto L01c12ffa
    r0 = [r11+16]
    [r10+0] = r0
    r0 = [r11+20]
    [r10+4] = r0
    r0 = [r11+24]
    [r10+8] = r0
    goto L01c12ffa
