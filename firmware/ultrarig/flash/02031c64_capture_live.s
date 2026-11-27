; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_live: 1 function, 0x02031c64..0x0203291c

; capture_live_parse: 0x02031c64..0x0203291c, module capture-live (parse), capture-native (parse), capture-parser (parse)
.type capture_live_parse,@function
capture_live_parse:
    [--sp] = {rets, r15-r4}
    sp += -380
; HyperRig MINI, product option: what is behind the plain capture is not read here (mini/product/parametric.c).
.if MINI_PRODUCT
    r12 = r2
    r15_r14 = r1_r0
    r0 = r2
    r1 = r3
    call hyperrig_capture_length  ; @call.xl
    r3 = r0
    r2 = r12
.else
    r12 = r2
    r15_r14 = r1_r0
.endif
    r11 = -1
    if (r3 < 44) goto L02032916
    [sp+364] = r2
    r8 = r3 + -4
    [sp+368] = r8
    r1 = 0
    [sp+372] = r1
    [sp+376] = r1
    r0 = r2 + r3
    r7 = r0 + -4
    r13 = sp + 364
; HyperRig MINI, product option: it was checked a moment ago (mini/product/swap.c).
.if MINI_PRODUCT
    r0 = hyperrig_capture_unstopped
    r0 = b[r0+0] (u)
    if (r0 != 0) goto hyperrig_parse_checked
.endif
    if (r8 == 0) goto L02031d2e
    r1 = -1
    r6 = 3988292384
    r4 = r12
    r3 = r8
L02031ca6:
    r0 = b[r4++=1] (u)
    r1 ^= r0
    r0 = r1 & 0x1
    r0 = 0x0 - r0
    r0 &= r6
    r1 = r1 >> 1
    r0 ^= r1
    r2 = r0 >> 1
    r0 = r2 & 0x1
    r0 = 0x0 - r0
    r5 = r0 & r6
    r0 = r1 & 0x1
    r0 = 0x0 - r0
    r0 &= r6
    r0 ^= r2
    r1 = r0 >> 1
    r0 = r5 ^ r1
    r2 = r0 >> 1
    r0 = r2 & 0x1
    r0 = 0x0 - r0
    r5 = r0 & r6
    r0 = r1 & 0x1
    r0 = 0x0 - r0
    r0 &= r6
    r0 ^= r2
    r1 = r0 >> 1
    r0 = r5 ^ r1
    r2 = r0 >> 1
    r0 = r2 & 0x1
    r0 = 0x0 - r0
    r5 = r0 & r6
    r0 = r1 & 0x1
    r0 = 0x0 - r0
    r0 &= r6
    r0 ^= r2
    r1 = r0 >> 1
    r0 = r5 ^ r1
    r2 = r0 >> 1
    r0 = r1 & 0x1
    r0 = 0x0 - r0
    r0 &= r6
    r1 = r0 ^ r2
    if (--r3 != 0) goto L02031ca6
    r1 = ~r1
L02031d2e:
    r11 = -3  #
    r4 = b[r7+1] (u)
    r0 = b[r7+0] (u)
    r0 <= insert(r4, p:8, l:8)  #
    r3 = b[r7+2] (u)
    r0 <= insert(r3, p:16, l:8)  #
    r2 = b[r7+3] (u)
    r0 <= insert(r2, p:24, l:8)
    if (r1 != r0) goto L02032916
.if MINI_PRODUCT
hyperrig_parse_checked:
.endif
    if (r8 >= 4) goto L02031d5c
    [r13+12] = 0x1
    r11 = -2
    goto L02032916
L02031d5c:
    r1 = b[r12+1] (u)
    r0 = b[r12+0] (u)
    r2 = b[r12+2] (u)
    r3 = b[r12+3] (u)
    [r13+8] = 0x4
    r0 <= insert(r1, p:8, l:8)
    r0 <= insert(r2, p:16, l:8)
    r0 <= insert(r3, p:24, l:8)
    r1 = 827077185
    r11 = -2
    if (r0 != r1) goto L02032916
    if (r8 >= 6) goto L02031d98
    [r13+12] = 0x1
    goto L02032916
L02031d98:
    r1 = b[r12+5] (u)
    r0 = b[r12+4] (u)
    [r13+8] = 0x6
    r0 <= insert(r1, p:8, l:8)
    if (r0 != 1) goto L02032916
    if (r8 >= 7) goto L02031dbe
    r5 = 1
    [r13+12] = r5
    r2 = 0
    r0 = 6
    goto L02031dca
L02031dbe:
    r2 = b[r12+6] (u)
    r0 = 7
    [r13+8] = r0
    r5 = 0
L02031dca:
    r1 = r0 + 1
    b[r14+0] = r2
    if (r1 > r8) {
    r5 = 1
    [r13+12] = r5
    r3 = 0
    r1 = r0
    } else {
    r3 = b[r12+r0] (u)
    [r13+8] = r1
    }
    r2 = r1 + 4
    b[r14+1] = r3
    if (r2 <= r8) goto L02031dfc
    r5 = 1
    [r13+12] = r5
    r0 = 0
    r2 = r1
    goto L02031e16
L02031dfc:
    r1 += r12
    r3 = b[r1+1] (u)
    r0 = b[r1+0] (u)
    r0 <= insert(r3, p:8, l:8)  #
    r4 = b[r1+2] (u)
    r0 <= insert(r4, p:16, l:8)  #
    r1 = b[r1+3] (u)
    [r13+8] = r2
    r0 <= insert(r1, p:24, l:8)
L02031e16:
    r1 = r2 + 2
    [r14+4] = r0
    if (r1 <= r8) goto L02031e2c
    r5 = 1
    [r13+12] = r5
    r3 = 0
    r1 = r2
    goto L02031e3c
L02031e2c:
    r0 = r12 + r2
    r2 = b[r0+1] (u)
    r3 = b[r0+0] (u)
    [r13+8] = r1
    r3 <= insert(r2, p:8, l:24)
L02031e3c:
    r0 = r1 + 1
    h[r14+8] = r3
    if (r0 > r8) {
    r5 = 1
    [r13+12] = r5
    r2 = 0
    r0 = r1
    } else {
    r2 = b[r12+r1] (u)
    [r13+8] = r0
    }
    r1 = r0 + 1
    b[r14+2] = r2
    if (r1 > r8) {
    r5 = 1
    [r13+12] = r5
    r2 = 0
    r1 = r0
    } else {
    r2 = b[r12+r0] (u)
    [r13+8] = r1
    }
    r0 = r1 + 1
    b[r14+3] = r2
    if (r0 > r8) {
    r5 = 1
    [r13+12] = r5
    r2 = 0
    r0 = r1
    } else {
    r2 = b[r12+r1] (u)
    [r13+8] = r0
    }
    r1 = r0 + 1
    b[r14+10] = r2
    if (r1 > r8) {
    r5 = 1
    [r13+12] = r5
    r2 = 0
    r1 = r0
    } else {
    r2 = b[r12+r0] (u)
    [r13+8] = r1
    }
    r0 = r1 + 1
    b[r14+11] = r2
    if (r0 > r8) {
    r5 = 1
    [r13+12] = r5
    r2 = 0
    r0 = r1
    } else {
    r2 = b[r12+r1] (u)
    [r13+8] = r0
    }
    r4 = r0 + 1
    b[r14+12] = r2
    if (r4 > r8) {
    r5 = 1
    [r13+12] = r5
    r1 = 0
    r4 = r0
    } else {
    r1 = b[r12+r0] (u)
    [r13+8] = r4
    }
    b[r14+13] = r1
    r3 = r14 + 14
    r0 = 0
L02031eee:
    r1 = r4 + 1
    if (r1 <= r8) {
    r2 = b[r12+r4] (u)
    [r13+8] = r1
    r4 = r1
    } else {
    r5 = 1
    [r13+12] = r5
    r2 = 0
    }
    b[r3+r0] = r2
    r0 = r0 + 1
    if (r0 != 16) goto L02031eee
    r0 = 0
    r1 = r14 + 28
    r11 = -4  #
    [sp+88] = r1
    r1 = [sp+88]
    b[r1+2] = r0
    r0 = b[r14+0] (u)
    if (r0 != 16) goto L02032916
    r0 = b[r14+3] (u)
    [sp+92] = r0
    r1 = b[r14+1] (u)
    r0 = b[r14+2] (u)
    [sp+104] = r0
    if (r1 != 16) goto L02031f58
    r0 = [sp+104]
    r0 += -1
    r0 = r0.b0 (u)
    if (r0 > 15) goto L02032916
    r0 = [sp+92]
    r0 += -1
    r0 = r0.b0 (u)
    if (r0 <= 63) goto L02031f76
    goto L02032916
L02031f58:
    r0 = [sp+92]
    r0 += -1
    r0 = r0.b0 (u)
    if (r0 > 63) goto L02032916
    r0 = [sp+104]
    r0 += -1
    r0 = r0.b0 (u)
    if (r0 > 15) goto L02032916
    if (r1 != 32) goto L02032916
L02031f76:
    r6 = h[r14+8] (u)
    if (r6 == 0) goto L02032916
    r2 = 1
    r3 = 0
    [sp+72] = r2
    [sp+76] = r3
    r7 = r1 + -1
    r2 = [sp+72]
    r3 = [sp+76]
    r3_r2 <<= r7
    r9 = -1
    r0 = r2 + -1
    r1 = r3 + r9 + c
    [r14+48] = r0
    [r14+52] = r1
    r0 = r9 + 0
    r1 = r0
    r1_r0 <<= r7
    [r14+40] = r0
    [r14+44] = r1
    r0 = L01c1fa18
    r1 = r6 * 0x50  #
    r0 = [r0+0]
    [r14+36] = r0
    r0 = [r15+4]
    r0 = r0 + 7
    r0 = r0 & 0xFFFFFFF8
    r1 = r1 + r0
    [r15+4] = r1
    r2 = [r15+0]
    r9 = 0  #
    [sp+100] = r2
    r3 = 0
    r2 = [sp+100]
    if (r2 == 0) goto L02031ff6
    r2 = [r15+8]
    r6 = [sp+100]
    r0 = r0 + r6
    if (r1 <= r2) {
    r9 = r0
    }
L02031ff6:
    r0 = r14 + 56
    [sp+52] = r0
    r0 = [sp+52]
    [r0+36] = r9
    r0 = r14 + 104
    [sp+40] = r0
    r0 = [sp+40]
    [r0+36] = r3
    r7 = r4 + 1
    r0 = [sp+40]
    [r0+40] = r3
    if (r7 > r8) {
    r5 = 1
    [r13+12] = r5
    r11 = 0
    r7 = r4
    } else {
    r11 = b[r12+r4] (u)
    [r13+8] = r7
    }
    r0 = [sp+104]
    r0 = r0 << 1
    [sp+120] = r0
    r0 = [sp+120]
    r10 = r1 + r0
    [r15+4] = r10
    r0 = [sp+100]
    if (r0 == 0) goto L0203204e
    r0 = [r15+8]
    r2 = [sp+100]
    r1 = r1 + r2
    r6 = 0
    if (r10 <= r0) {
    r6 = r1
    }
    goto L02032050
L0203204e:
    r6 = 0
L02032050:
    r0 = [sp+104]
    if (r0 == 0) goto L02032084
    r1 = r6  #
    r0 = [sp+104]
L02032058:
    r2 = r7 + 2
    if (r2 <= r8) goto L02032068
    r5 = 1
    [r13+12] = r5
    r3 = 0
    goto L0203207a
L02032068:
    r3 = r12 + r7
    r7 = r2  #
    r4 = b[r3+1] (u)
    r3 = b[r3+0] (u)
    [r13+8] = r2
    r3 <= insert(r4, p:8, l:24)
L0203207a:
    if (r6 == 0) goto L0203207e
    h[r1+0] = r3
L0203207e:
    r1 = r1 + 2
    if (--r0 != 0) goto L02032058
L02032084:
    [r14+60] = r6
    r0 = b[r14+10] (u)
    r1 = b[r14+11] (s)
    r0 += r11  #
    [sp+64] = r1
    r11 = -4  #
    r1 = [sp+64]
    r1 = r0 - r1  #
    r0 = [sp+52]
    r0 = r1.b0 (s)  #
    b[r0+0] = r1
    r0 += 62
    if (r0 > 124) goto L02032916
    r0 = r1 + -1
    r1 = 1
    r0 = r0.b0 (u)  #
    [sp+32] = r1
    [sp+36] = r1
    if (r0 >= 31) {
    r0 = 0
    [sp+36] = r0
    }
    r1 = h[r14+8] (u)
    r0 = [sp+104]
    r2 = [sp+92]
    r0 *= r2
    [sp+28] = r0
    if (r1 == 0) goto L02032716
    r0 = [sp+120]
    r1 = [sp+104]
    r0 *= r1
    [sp+12] = r0
    r0 = [sp+104]
    r1 = r0 + -1  #
    r0 = [sp+104]
    r0 = r0 << 2
    [sp+4] = r0
    r0 = [sp+104]
    r0 = r0 << 3
    [sp+16] = r0
    r0 = [sp+104]
    r0 *= r0
    [sp+24] = r0
    r0 = [sp+24]
    r0 = r0 << 1
    r0 = r1.b0 (u)  #
    [sp] = r0
    [sp+8] = r0
    r0 = 1
    [sp+32] = r0
    r0 = 0
    [sp+68] = r0
    goto L0203211c
L02032104:
    r8 = [r13+4]
    r7 = [r13+8]
    r0 = [sp+52]
    r9 = [r0+36]
    r5 = 0
    r0 = [sp+56]
    [sp+64] = r0
    r0 = [sp+112]
    [sp+36] = r0
L0203211c:
    r0 = [sp+68]
    r0 = r0 * 0x50
    r1 = r9 + r0
    r0 = sp + 284
    [sp+108] = r0
    if (r9 != 0) {
    [sp+108] = r1
    }
    r1 = r7 + 1
    if (r1 <= r8) goto L02032146
    r5 = 1
    [r13+12] = r5
    r0 = 0
    r1 = r7  #
    [sp+84] = r0
    goto L02032154
L02032146:
    r0 = [sp+364]
    r0 = b[r0+r7] (u)
    [sp+84] = r0
    [r13+8] = r1
L02032154:
    r2 = r1 + 2
    r0 = [sp+108]
    r3 = [sp+84]
    b[r0+0] = r3
    if (r2 <= r8) goto L0203216c
    r5 = 1
    [r13+12] = r5
    r7 = 0
    r2 = r1
    goto L0203217e
L0203216c:
    r0 = [sp+364]
    r0 = r0 + r1
    r1 = b[r0+1] (u)
    r7 = b[r0+0] (u)
    [r13+8] = r2
    r7 <= insert(r1, p:8, l:24)
L0203217e:
    r1 = r2 + 1
    r0 = [sp+108]
    h[r0+2] = r7
    if (r1 <= r8) goto L02032196
    r5 = 1
    [r13+12] = r5
    r0 = 0
    r1 = r2  #
    [sp+60] = r0
    goto L020321a4
L02032196:
    r0 = [sp+364]
    r0 = b[r0+r2] (u)
    [sp+60] = r0
    [r13+8] = r1
L020321a4:
    r3 = r1 + 1
    if (r3 <= r8) goto L020321b8
    r5 = 1
    [r13+12] = r5
    r0 = 0
    r3 = r1  #
    [sp+56] = r0
    goto L020321c6
L020321b8:
    r0 = [sp+364]
    r0 = b[r0+r1] (u)
    [sp+56] = r0
    [r13+8] = r3
L020321c6:
    r2 = r3 + 4
    if (r2 > r8) goto L02032902
    r0 = [sp+364]
    r1 = r0 + r3
    r4 = b[r1+1] (u)
    r0 = b[r1+0] (u)
    r0 <= insert(r4, p:8, l:8)  #
    r6 = b[r1+2] (u)
    r0 <= insert(r6, p:16, l:8)  #
    r1 = b[r1+3] (u)
    [r13+8] = r2
    r0 <= insert(r1, p:24, l:8)  #
    r1 = [sp+108]
    [r1+12] = r0
    if (r5 != 0) goto L0203290c
    r0 = [sp+84]
    if (r0 == 0) goto L02032916
    r0 = r7.l (u)
    if (r0 == 0) goto L02032916
    r0 = [sp+104]
    r1 = [sp+84]
    r0 *= r1
    [sp+116] = r0
    r0 = r3 + 5
    [sp+112] = r0
    r0 = [sp+116]
    r1 = [sp+108]
    h[r1+4] = r0
    r0 = [sp+112]
    if (r0 <= r8) goto L0203222c
    r0 = 1
    [r13+12] = r0
    r0 = 0
    [sp+44] = r0
    [sp+112] = r2
    goto L0203223c
L0203222c:
    r0 = [sp+364]
    r0 = b[r0+r2] (u)
    [sp+44] = r0
    r0 = [sp+112]
    [r13+8] = r0
L0203223c:
    r0 = [sp+116]
    r1 = [sp+104]
    r0 *= r1  #
    r2 = [sp+112]
    if (r0 == 0) goto L02032260
    r1 = [sp+112]
L02032248:
    r2 = r1 + 2
    if (r2 > r8) {
    r2 = 1
    [r13+12] = r2
    r2 = r1
    } else {
    [r13+8] = r2
    }
    r1 = r2
    if (--r0 != 0) goto L02032248
L02032260:
    r0 = [sp+104]
    if (r0 == 0) goto L02032288
    r10 = sp + 156
    r9 = [sp+104]
L0203226a:
    r0 = sp + 364
    call capture_live_read64  ; @call.xl
    [r10++=4] = r0
    [r10++=4] = r1
    if (--r9 != 0) goto L0203226a
    r8 = [r13+4]
    r2 = [r13+8]
L02032288:
    r3 = r2 + 1
    if (r3 <= r8) goto L0203229c
    r0 = 1
    [r13+12] = r0
    r0 = 0
    r3 = r2  #
    [sp+48] = r0
    goto L020322aa
L0203229c:
    r0 = [sp+364]
    r0 = b[r0+r2] (u)
    [sp+48] = r0
    [r13+8] = r3
L020322aa:
    r0 = [sp+104]
    if (r0 == 0) goto L020322e0
    r2 = sp + 124
    r1 = [sp+104]
L020322b2:
    r4 = r3 + 2
    if (r4 <= r8) goto L020322c4
    r0 = 1
    [r13+12] = r0
    r0 = 0
    r4 = r3
    goto L020322d6
L020322c4:
    r0 = [sp+364]
    r0 = r0 + r3
    r3 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    [r13+8] = r4
    r0 <= insert(r3, p:8, l:24)
L020322d6:
    r3 = r4  #
    h[r2++=2] = r0
    if (--r1 != 0) goto L020322b2
    goto L020322e2
L020322e0:
    r4 = r3
L020322e2:
    r5 = r4 + 1
    if (r5 <= r8) goto L020322f6
    r0 = 1
    [r13+12] = r0
    r0 = 0
    r5 = r4  #
    [sp+20] = r0
    goto L02032304
L020322f6:
    r0 = [sp+364]
    r0 = b[r0+r4] (u)
    [sp+20] = r0
    [r13+8] = r5
L02032304:
    r0 = [r15+4]
    r0 = r0 + 7
    r0 = r0 & 0xFFFFFFF8  #
    r1 = [sp+12]
    r7 = r0 + r1
    [r15+4] = r7
    r6 = [r15+0]
    if (r6 == 0) goto L0203232e
    r1 = [r15+8]
    r2 = r6 + r0
    r0 = 0
    [sp+96] = r0
    if (r7 <= r1) {
    [sp+96] = r2
    }
    goto L02032332
L0203232e:
    r0 = 0
    [sp+96] = r0
L02032332:
    r0 = [sp+24]
    if (r0 == 0) goto L0203236a
    r2 = [sp+96]
    r1 = [sp+24]
L0203233a:
    r3 = r5 + 2
    if (r3 <= r8) goto L0203234a
    r0 = 1
    [r13+12] = r0
    r0 = 0
    goto L0203235e
L0203234a:
    r0 = [sp+364]
    r0 = r0 + r5
    r5 = r3  #
    r4 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    [r13+8] = r3
    r0 <= insert(r4, p:8, l:24)
L0203235e:
    r3 = [sp+96]
    if (r3 == 0) goto L02032364
    h[r2+0] = r0
L02032364:
    r2 = r2 + 2
    if (--r1 != 0) goto L0203233a
L0203236a:
    r0 = r7 + 7
    r0 = r0 & 0xFFFFFFF8  #
    r1 = [sp+16]
    r1 = r1 + r0
    [r15+4] = r1
    if (r6 == 0) goto L0203238c
    r2 = [r15+8]
    r3 = r6 + r0
    r0 = 0
    [sp+100] = r0
    if (r1 <= r2) {
    [sp+100] = r3
    }
    goto L02032390
L0203238c:
    r0 = 0
    [sp+100] = r0
L02032390:
    r0 = [sp+104]
    if (r0 == 0) goto L020323b6
    r10 = [sp+100]
    r9 = [sp+104]
L02032398:
    r0 = sp + 364
    call capture_live_read64  ; @call.xl
    r2 = [sp+100]
    if (r2 == 0) goto L020323ae
    [r10+0] = r0
    [r10+4] = r1
L020323ae:
    r10 = r10 + 8
    if (--r9 != 0) goto L02032398
L020323b6:
    r0 = [r13+12]
    if (r0 != 0) goto L02032912
    r2 = 0
    r0 = [sp+108]
    [r0+48] = r2
    r0 = [sp+60]
    r4 = r0.b0 (s)  #
    r0 = [sp+64]
    r1 = r0 - r4  #
    r0 = [sp+44]
    r0 = r0.b0 (s)
    r9 = r1 + r0  #
    r0 = [sp+108]
    b[r0+6] = r9
    r7 = b[r14+10] (s)
    r0 = [sp+60]
    r1 = [sp+48]
    r0 = r1 - r0
    r0 = r0 + r7
    [sp+44] = r0
    r0 = [sp+108]
    r1 = [sp+44]
    b[r0+7] = r1
    r0 = [sp+56]
    r0 = r0.b0 (s)
    [sp+56] = r0
    r0 = [sp+56]
    r1 = r4 - r0  #
    r0 = [sp+20]
    r0 = r0.b0 (s)
    r5 = r1 + r0  #
    r0 = [sp+108]
    b[r0+8] = r5
    r0 = [sp+64]
    r1 = [sp+56]
    r3 = r0 - r1  #
    r0 = [sp+108]
    b[r0+9] = r3
    r6 = b[r14+12] (s)
    r0 = [sp+60]
    r0 = r0 - r6  #
    r1 = [sp+108]
    b[r1+10] = r0
    r0 = [sp+108]
    r0 = b[r0+0] (u)
    if (r0 == 15) goto L02032430
    if (r0 != 6) goto L02032438
    r2 = 2
    if ((r3 & 0xFF) == 0) {
    r2 = 1
    }
    goto L02032438
L02032430:
    r2 = 4
    if ((r3 & 0xFF) == 0) {
    r2 = 3
    }
L02032438:
    r0 = [sp+108]
    r0 = r9 + 62  #
    b[r0+11] = r2
    r2 = -4
    if (r0 > 124) goto L02032914
    r0 = r3 + 62
    if (r0 > 124) goto L02032914
    r0 = r5 + 62
    if (r0 > 124) goto L02032914
    r0 = [sp+48]
    r1 = r0.b0 (s)
    r0 = 0x3E - r4
    r0 = r0 + r1
    r0 = r0 + r7
    if (r0 > 124) goto L02032914
    if (r9 > 31) goto L02032914
    r0 = r4 + 62
    r0 = r0 - r6
    if (r0 > 124) goto L02032914
    r0 = [sp+108]
    r1 = 0
    [r0+16] = r1
    r0 = [sp+108]
    [r0+20] = r1
    r0 = [sp+108]
    [r0+24] = r1
    r0 = [sp+108]
    [r0+28] = r1
    r0 = [sp+96]
    r1 = [sp+108]
    [r1+32] = r0
    r0 = [sp+100]
    r1 = [sp+108]
    [r1+36] = r0
    r1 = [r15+4]
    r0 = [sp+116]
    r0 = r0 + 1
    [sp+64] = r0
    r0 = [sp+120]
    r2 = [sp+64]
    r2 *= r0
    r0 = r1 + 7
    r10 = r0 & 0xFFFFFFF8
    r0 = r2 + r10
    r0 = r0 + 4
    [sp+96] = r0
    r0 = [sp+96]
    [r15+4] = r0
    r0 = [r15+0]
    [sp+100] = r0
    r0 = [sp+100]
    if (r0 == 0) goto L020324d6
    r0 = [r15+8]
    r1 = [sp+96]
    if (r1 <= r0) goto L020324de
L020324d6:
    r0 = 0
    r1 = [sp+108]
    [r1+40] = r0
    goto L0203255c
L020324de:
    r0 = [sp+100]
    r0 += r10
    [sp+60] = r0
    r0 = 0
    r1 = [sp+108]
    [r1+40] = r0
    r1 = [sp+60]
    if (r1 == 0) goto L0203255c
    r0 = [sp+116]
    if (r0 == 0) goto L0203253e
    r7 = 0
    r8 = [sp+60]
L020324f6:
    r0 = [sp+104]
    if (r0 == 0) goto L02032532
    r3 = r8  #
    r0 = [sp+104]
    r6 = r7 / r0 (u)  #
    r0 = [sp+104]
    r0 *= r6  #
    r1 = [sp+84]
    r0 = r7 - r0
    r5 = r0 * r1  #
    r1 = [sp+104]
    r2 = 0
L02032512:
    r0 = [sp+116]
    r0 *= r2  #
    r4 = [sp+112]
    r0 = r0 + r5
    r0 = r0 + r6
    r0 = r0 << 1
    r0 = r0 + r4
    r0 += r12
    r4 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r4, p:8, l:24)
    h[r3++=2] = r0
    r2 = r2 + 1
    if (--r1 != 0) goto L02032512
L02032532:
    r7 = r7 + 1
    r0 = [sp+120]
    r8 += r0  #
    r0 = [sp+116]
    if (r7 != r0) goto L020324f6
L0203253e:
    r0 = [sp+104]
    if (r0 == 0) goto L0203255a
    r0 = [sp+84]
    r1 = [sp]
    r0 *= r1  #
    r1 = [sp+100]
    r0 += r10
    r2 = r1 + r0  #
    r0 = [sp+104]
    r1 = sp + 124
L02032552:
    r3 = h[r1++=2] (u)
    h[r2++=2] = r3
    if (--r0 != 0) goto L02032552
L0203255a:
    r0 = [sp+60]
L0203255c:
    r1 = [sp+108]
    [r1+44] = r0
    r0 = [sp+44]
    r0 = r0 - r9  #
    r1 = [sp+108]
    r1 += 64
    [sp+116] = r1
    r1 = [sp+116]
    b[r1+0] = r0
    r0 = [sp+8]
    if (r0 > 2) goto L02032628
    r8 = sp + 156
    r6 = 13
    goto L02032586
L0203257e:
    r0 = [sp+108]
    r9 = b[r0+6] (u)
    r6 = r6 + 1
L02032586:
    r2 = [r8++=4]
    r3 = [r8++=4]
    r1 = sextra(r9, p:0, l:8)
    ifs (r1 < 1) goto L020325c6
    ifs (r1 > 31) goto L020325e8
    r0 = r1 + -1
    r4 = 1
    r0 = r4 << r0
    r5 = r0 + r2
    if (r5 >= r0) {
    r4 = 0
    }
    r4 = r4 + r3
    r3 = r4 >>> r1
    r0 = 0x20 - r1
    r7 = r4 << r0
    r0 = r5 >> r1
    r2 = r7 | r0
    r0 = r4 >> 31
    goto L02032608
L020325c6:
    if ((r9 & 128) == 0) goto L02032606
    r4 = 0x0 - r1
    ifs (r4 > 31) goto L02032602
    r5 = r3 << r4
    r0 = r1 + 32
    r0 = r2 >> r0
    r3 = r0 | r5
    r0 = r3 >> 31
    r2 <<= r4
    goto L02032608
L020325e8:
    r0 = r1 + -1
    r4 = [sp+72]
    r5 = [sp+76]
    r5_r4 <<= r0
    r2 = r2 + r4
    r3 = r3 + r5 + c
    r0 = r3 >> 31
    r3_r2 >>>= r1
    goto L02032608
L02032602:
    r3_r2 <<= r4
L02032606:
    r0 = r3 >> 31
L02032608:
    r1 = 2147483647
    r1 = r1 + r0
    r0 = r2 >>> 31
    if (r3 != r0) {
    r2 = r1
    }
    r0 = r6 + -12  #
    r1 = [sp+108]
    [r1+r6<<2] = r2
    r1 = [sp+104]
    if (r0 < r1) goto L0203257e
L02032628:
    r4 = 0
    r0 = 0
    [sp+112] = r0
    r0 = [sp+36]
    if (r0 == 0) goto L0203268e
    r0 = [sp+108]
    r0 = b[r0+6] (u)
    r0 += -1
    r1 = 0
    r0 = r0.b0 (u)  #
    [sp+112] = r1
    if (r0 > 30) goto L0203268e
    r0 = [sp+108]
    r0 = b[r0+7] (u)
    r0 += -1
    r0 = r0.b0 (u)  #
    [sp+112] = r1
    if (r0 > 30) goto L0203268e
    r0 = [sp+108]
    r0 = b[r0+8] (u)
    r0 += -1
    r0 = r0.b0 (u)  #
    [sp+112] = r1
    if (r0 > 30) goto L0203268e
    r0 = [sp+108]
    r0 = b[r0+9] (u)
    r0 = r0 + 31
    r1 = r0.b0 (u)
    r0 = 0
    [sp+112] = r0
    if (r1 > 62) goto L0203268e
    r0 = [sp+108]
    r0 = b[r0+10] (u)
    r0 += -1
    r1 = r0.b0 (u)
    r0 = 0
    [sp+112] = r0
    if (r1 > 30) goto L0203268e
    r0 = [sp+116]
    r1 = b[r0+0] (u)
    r0 = 1
    [sp+112] = r0
    if (r1 >= 32) {
    r0 = 0
    [sp+112] = r0
    }
L0203268e:
    r1 = [r14+36]
    r0 = 1
    r2 = [sp+68]
    if (r2 != r1) {
    r0 = 0
    }
    r1 = [sp+108]
    r1 = h[r1+2] (u)
    r2 = r0 << 6
    r0 = [sp+84]
    r0 += -1
    r3 = r1 * r0
    r1 = r3 + r2  #
    r2 = [sp+4]
    r0 = r1 + 128
    r2 *= r0  #
    r0 = [sp+96]
    r0 = r0 + 7
    r0 = r0 & 0xFFFFFFF8
    r10 = r2 + r0
    [r15+4] = r10
    r1 += 64
    r2 = [sp+100]
    if (r2 == 0) goto L020326da
    r2 = [r15+8]
    r4 = [sp+100]
    r0 = r0 + r4
    r4 = 0
    if (r10 <= r2) {
    r4 = r0
    }
L020326da:
    r0 = [sp+116]
    r0 = r1 + -1  #
    [r0+4] = r4
    r2 = [sp+116]
    [r2+8] = r0
    r0 = [sp+116]
    [r0+12] = r1
    r0 = h[r14+8] (u)
    r1 = [sp+64]
    r2 = [sp+28]
    r2 = umax(r1, r2)
    [sp+28] = r2
    r1 = [sp+68]
    r1 = r1 + 1
    [sp+68] = r1
    r1 = [sp+32]
    r1 = r1 + r3
    [sp+32] = r1
    r1 = [sp+68]
    if (r1 < r0) goto L02032104
    r8 = [r13+4]
    r7 = [r13+8]
    goto L0203271a
L02032716:
    r0 = [sp+36]
    [sp+112] = r0
L0203271a:
    r4 = r7 + 1
    if (r4 <= r8) {
    r0 = [sp+364]
    r9 = b[r0+r7] (u)
    [r13+8] = r4
    } else {
    [r13+12] = 0x1
    r9 = 0
    r4 = r7
    }
    r5 = 0
    r0 = [sp+88]
    [r0+36] = r5
    r0 = [sp+120]
    r1 = [sp+92]
    r1 *= r0
    r0 = r10 + 7
    r0 = r0 & 0xFFFFFFF8
    r1 = r1 + r0
    [r15+4] = r1
    r2 = [sp+100]
    if (r2 == 0) goto L02032760
    r3 = [r15+8]
    r2 = [sp+100]
    r0 = r0 + r2
    if (r1 <= r3) {
    r5 = r0
    }
L02032760:
    r0 = [sp+104]
    if (r0 == 0) goto L020327a8
    r7 = 0
    r6 = r5
L02032768:
    r2 = r6  #
    r1 = [sp+92]
    r0 = [sp+92]
    if (r0 == 0) goto L0203279e
L02032770:
    r3 = r4 + 2
    if (r3 <= r8) goto L0203277e
    [r13+12] = 0x1
    r0 = 0
    goto L02032792
L0203277e:
    r0 = [sp+364]
    r0 = r0 + r4
    r4 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    [r13+8] = r3
    r0 <= insert(r4, p:8, l:24)
    r4 = r3
L02032792:
    if (r5 == 0) goto L02032796
    h[r2+0] = r0
L02032796:
    r0 = [sp+120]
    r2 = r2 + r0
    if (--r1 != 0) goto L02032770
L0203279e:
    r7 = r7 + 1
    r6 = r6 + 2
    r0 = [sp+104]
    if (r7 != r0) goto L02032768
L020327a8:
    r0 = [sp+88]
    [r0+40] = r5
    r0 = sp + 364
    call capture_live_read64  ; @call.xl
    r2 = b[r14+12] (s)
    r3 = b[r14+13] (s)
    r5_r4 = r1_r0
    r0 = r2 + r9
    r1 = r0 - r3
    r0 = sextra(r9, p:0, l:8)
    r0 = r0 + r2  #
    r2 = [sp+52]
    r0 += 62
    r0 = r0 - r3  #
    b[r2+1] = r1
    if (r0 >= 125) goto L02032916
    r0 = r1.b0 (u)
    if (r0 > 31) goto L02032916
    if ((r1 & 0xFF) == 0) goto L0203280c
    r2 = r1.b0 (s)
    r0 = r2 + -1
    r3 = 1
    r0 = r3 << r0
    r6 = r0 + r4
    if (r6 >= r0) {
    r3 = 0
    }
    r3 = r3 + r5
    r5 = r3 >>> r2
    r0 = 0x20 - r2
    r3 <<= r0
    r0 = r6 >> r2
    r4 = r3 | r0
L0203280c:
    [r14+72] = r4
    [r14+76] = r5
    r0 = r1 + -1
    r1 = r0.b0 (u)
    r0 = 1
    r3 = 1
    if (r1 >= 31) {
    r3 = 0
    }
    r2 = 1
    r1 = [sp+112]
    if (r1 != 0) goto L0203282c
    r2 = [sp+112]
L0203282c:
    r1 = r3 & r2
    r3 = r14 + 164
    b[r3+0] = r1
L02032836:
    r1 = r0  #
    r2 = [sp+92]
    r0 = r1 << 1
    if (r1 < r2) goto L02032836
    r0 = r1
    if (r1 >= 64) {
    r0 = 64
    }
    r4 = [r15+4]
    r0 = r0 + r1  #
    r2 = [sp+104]
    r0 *= r2
    r2 = r0 << 2
    r0 = r4 + 7
    r5 = r0 & 0xFFFFFFF8
    r6 = r5 + r2
    [r15+4] = r6
    r0 = [r15+0]
    r2 = 0
    r4 = 0
    if (r0 == 0) goto L02032876
    r7 = [r15+8]
    r0 = r0 + r5
    if (r6 <= r7) {
    r4 = r0
    }
L02032876:
    r11 = -1  #
    r0 = [sp+88]
    r0 = r1 + -1  #
    [r0+52] = r4
    r1 = [sp+88]
    [r1+56] = r0
    r0 = [sp+92]
    r1 = [sp+32]
    r0 = r0 + r1
    r0 += -1
    [r14+32] = r0
    r0 = [sp+28]
    r1 = [sp+40]
    h[r1+0] = r0
    r0 = [sp+40]
    [r0+24] = r2
    r0 = [sp+40]
    [r0+20] = r2
    r0 = [sp+52]
    [r0+44] = r2
    r0 = [sp+52]
    [r0+40] = r2
    r0 = [sp+92]
    r0 += 95
    r0 = r0 & 0x1E0  #
    r1 = [sp+40]
    [r1+48] = r0
    r0 = [sp+40]
    [r0+44] = r2
    r0 = [sp+40]
    [r0+52] = r2
    r0 = [sp+40]
    [r0+56] = r2
    r0 = [sp+40]
    [r0+28] = r2
    b[r14+204] = r2
    b[r14+205] = r2
    [r3+44] = r2
    [r3+36] = r2
    [r3+48] = r2
    [r3+52] = r2
    [r3+56] = r2
    [r3+60] = r2
    r0 = [sp+40]
    [r0+16] = r2
    [r3+4] = r2
    [r3+8] = r2
    [r3+32] = r2
    [r3+12] = r2
    [r3+16] = r2
    [r3+20] = r2
    [r3+24] = r2
    [r3+28] = r2
    r0 = [r13+12]
    if (r0 != 0) goto L02032916
    r1 = [r13+4]
    r0 = [r13+8]
    if (r0 == r1) {
    r11 = 0
    }
    goto L02032916
L02032902:
    [r13+12] = 0x1
    r0 = [sp+108]
    [r0+12] = 0x0
L0203290c:
    r11 = -1
    goto L02032916
L02032912:
    r2 = -1
L02032914:
    r11 = r2
L02032916:
    r0 = r11
    sp += 380
    {pc, r15-r4} = [sp++]
