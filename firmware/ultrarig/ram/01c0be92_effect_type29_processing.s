; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_type29_processing: 7 functions, 0x01c0be92..0x01c0deb6

; effect_type29_processing_phase29: 0x01c0be92..0x01c0c09e, module effect-type29-processing (phase29)
.type effect_type29_processing_phase29,@function
effect_type29_processing_phase29:
    [--sp] = {rets, r15-r4}
    sp += -48
    r1 = r1 >>> 1
    r0 = r0 >>> 1
    ifs (r0 <= 4294967295) {
    r1 = 0x0 - r1
    r0 = 0x0 - r0
    r2 = 0x80000000
    } else {
    r2 = 0
    }
    r4 = r1  #
    [sp+44] = r2
    r5 = r1 >>> 31
    r1 = r0 ^ r5  #
    [sp+32] = r5
    r1 = r5 - r1  #
    [sp+40] = r4
    r3 = r1 + r4
    [sp+28] = r3
    r2 = r3 >>> 31
    r1 = r5 ^ r4  #
    [sp+36] = r2
    r1 = r1 - r5
    r0 = r0 + r1
    r1 = r0 >>> 1
    r1 ^= r2
    r1 = r2 - r1
    r4 = r1 + r3
    r15 = r4 >>> 31  #
    [sp+24] = r4
    r1 = r3 >>> 1
    r1 ^= r2
    r1 = r1 - r2
    r0 = r0 + r1
    r1 = r0 >>> 2
    r1 = r1 ^ r15
    r1 = r15 - r1
    r2 = r1 + r4
    r12 = r2 >>> 31  #
    [sp+20] = r2
    r1 = r4 >>> 2
    r1 = r1 ^ r15
    r1 = r1 - r15
    r0 = r0 + r1
    r1 = r0 >>> 3
    r1 = r1 ^ r12
    r1 = r12 - r1
    r3 = r1 + r2
    r11 = r3 >>> 31
    r1 = r2 >>> 3
    r1 = r1 ^ r12
    r1 = r1 - r12
    r0 = r0 + r1
    r1 = r0 >>> 4
    r1 = r1 ^ r11
    r1 = r11 - r1
    r2 = r1 + r3
    r6 = r2 >>> 31
    r1 = r3 >>> 4
    r1 = r1 ^ r11
    r1 = r1 - r11
    r0 = r0 + r1
    r1 = r0 >>> 5
    r1 ^= r6
    r1 = r6 - r1
    [sp+12] = r2
    [sp+16] = r3
    r4 = r1 + r2
    r1 = r2 >>> 5
    r1 ^= r6  #
    [sp+8] = r4
    r1 = r1 - r6
    r1 = r1 + r0
    r0 = r4 >>> 31
    r2 = r4 >>> 6
    r2 ^= r0
    r2 = r2 - r0
    r3 = r2 + r1
    r1 = r1 >>> 6
    r1 ^= r0
    r1 = r0 - r1
    r8 = r1 + r4
    r2 = r8 >>> 31
    r1 = r8 >>> 7
    r1 ^= r2
    r1 = r1 - r2
    r1 = r1 + r3
    r3 = r3 >>> 7
    r3 ^= r2
    r3 = r2 - r3
    r3 += r8
    r9 = r3 >>> 31
    r5 = r3 >>> 8
    r5 = r5 ^ r9
    r5 = r5 - r9
    r10 = r5 + r1
    r1 = r1 >>> 8
    r1 = r1 ^ r9
    r1 = r9 - r1
    r5 = r1 + r3
    r1 = r5 >>> 31
    r14 = r5 >>> 9
    r14 = r14 ^ r1
    r4 = r5 >> 31
    r13 = r4 + r10  #
    [sp+4] = r4
    r13 += r14
    r7 = r10 >>> 9
    r7 ^= r1
    r7 = r1 - r7
    r10 = r7 + r5
    r7 = r13 >>> 10
    r13 = r10 >>> 31
    r7 = r7 ^ r13
    r5 = r13 + r10
    r14 = r5 - r7
    r5 = r14 >>> 31
    r7 = 333772
    r4 = r5 ^ r7
    [sp] = r4
    r5 = [sp+40]
    r5 = r5 >> 31
    r7 = [sp+44]
    r5 |= r7  #
    r4 = [sp+32]
    r7 = r4 ^ 0x20000000  #
    r4 = [sp+28]
    r5 = r5 + r7
    r7 = r4 >> 31
    r5 = r5 + r7  #
    r4 = [sp+36]
    r7 = 316933406
    r7 ^= r4  #
    r4 = [sp+24]
    r5 = r5 + r7
    r7 = r4 >> 31
    r5 = r5 + r7  #
    r4 = [sp+20]
    r7 = 167458907
    r7 = r7 ^ r15
    r5 = r5 + r7
    r7 = r4 >> 31
    r5 = r5 + r7  #
    r4 = [sp+16]
    r7 = 85004756
    r7 = r7 ^ r12
    r5 = r5 + r7
    r7 = r4 >> 31
    r5 = r5 + r7
    r7 = 42667331
    r4 = r11 ^ r7
    r4 = r4 + r5  #
    r5 = [sp+12]
    r5 = r5 >> 31
    r4 = r4 + r5
    r5 = 21354465
    r5 ^= r6
    r4 = r4 + r5  #
    r5 = [sp+8]
    r5 = r5 >> 31
    r4 = r4 + r5
    r5 = 10679838
    r0 ^= r5
    r0 = r0 + r4
    r4 = r8 >> 31
    r0 = r0 + r4
    r4 = 5340245
    r2 ^= r4
    r0 = r0 + r2
    r2 = r3 >> 31
    r0 = r0 + r2
    r2 = 2670163
    r2 = r2 ^ r9
    r0 = r0 + r2  #
    r2 = [sp+4]
    r0 = r0 + r2
    r2 = 1335087
    r1 ^= r2
    r0 = r0 + r1
    r1 = r10 >> 31
    r0 = r0 + r1
    r1 = 667544
    r1 = r1 ^ r13
    r0 = r0 + r1
    r1 = r14 >> 31
    r0 = r0 + r1  #
    r1 = [sp]
    r0 = r0 + r1
    sp += 48
    {pc, r15-r4} = [sp++]

; effect_type29_processing_spectral29: 0x01c0c09e..0x01c0c6ea, module effect-type29-processing (spectral29)
.type effect_type29_processing_spectral29,@function
effect_type29_processing_spectral29:
    [--sp] = {rets, r15-r4}
    sp += -116
    r9 = L01c34198
    r2 = [r9+0]
    r11 = r1
    r14 = r0
    if (r2 == 0) goto L01c0c0b8
    call r2
    r12 = r0
    goto L01c0c0ba
L01c0c0b8:
    r12 = 0
L01c0c0ba:
    r5 = L01c34460
    r8 = r14 + 64
    r0 = r14 + 924
    r0 = 12284  #
    [sp+76] = r0
    r15 = r14 + r0
    if (r11 == 1) goto L01c0c192
    if (r11 != 0) goto L01c0c1ac
    r1 = [r15+0]
    r0 = [r15+4]
    r3 = r1 | r0
    r0 = 0
    r2 = 0
    if (r3 == 0) goto L01c0c0f2
L01c0c0ec:
    r3 = r3 >> 1
    r2 = r2 + 1
    if (r3 != 0) goto L01c0c0ec
L01c0c0f2:
    [r15+0] = r0
    [r15+4] = r1
    r1 = r2 + -17
    if (r2 <= 17) {
    r1 = 0
    }
    r2 = r1 + -5
    r3 = 2048
    r2 = r3 >> r2
    r4 = 0x5 - r1
    r3 <<= r4
    [r15+8] = r1
    ifs (r1 >= 6) {
    r3 = r2
    }
    [r15+16] = r3
    [r15+24] = r0
    r0 = r1 << 16
    r6 = [r14+44]
    r1 = 3090
    r4 = [r14+r1<<2]
    r1 = [r14+8]
    r2 = [r15+28]
    r5 = [r15+36]
    r7 = r6 | r0
    r0 = r1 << 2
    r1 = r2 + r0
    r0 = r5
    r2 = r4
    r3 = r7
    call effect_type29_processing_window29  ; @call.xl
    r0 = [r14+8]
    r1 = [r15+28]
    r0 ^= r6
    r0 = r0 << 2
    r1 = r1 + r0
    r3 = r7 | 0x80000000
    r2 = r6 << 2
    r0 = r5 + r2
    r2 = r2 + r4
    call effect_type29_processing_window29  ; @call.xl
    r0 = [r14+28]
    r2 = [r15+36]
    r1 = r15 + 40
    r3 = [r1+r0<<2]
    r0 = [r14+40]
    r1 = 0
    call ir_processing_start  ; @call.xl
    goto L01c0c6b8
L01c0c192:
    call ir_processing_wait  ; @call.xl
    if (r0 == 0) goto L01c0c2d0
    [r15+24] = 0x1
    r0 = [r5+0]
    r0 = r0 + 1
    [r5+0] = r0
    [r14+32] = 0x0
    goto L01c0c6b8
L01c0c1ac:
    r0 = [r15+24]
    if (r11 != 2) goto L01c0c23e
    if (r0 != 0) goto L01c0c6b8
    r0 = [r14+48]
    r9 = [r14+32]
    r0 += -2
    if (r0 < 161) goto L01c0c228
    if (r9 > 39) goto L01c0c228
    r1 = [r15+48]
    r2 = [r8+4]
    r3 = 160
    r4 = 0
L01c0c1d8:
    r6 = r1 + 632
    r5 = r6 + 8
    r5 = [r5+r4<<2]
    ifs (r5 <= r2) goto L01c0c21c
    r7 = r6 + 4
    r7 = [r7+r4<<2]
    ifs (r5 <= r7) goto L01c0c21c
    r7 = r6 + 12
    r7 = [r7+r4<<2]
    ifs (r5 < r7) goto L01c0c21c
    r7 = [r6+r4<<2]
    ifs (r5 <= r7) goto L01c0c21c
    r6 = r6 + 16
    r6 = [r6+r4<<2]
    ifs (r5 < r6) goto L01c0c21c
    r5 = [sp+76]
    h[r5+r9<<1] = r3
    r9 = r9 + 1
    if (r9 == 40) goto L01c0c6e4
L01c0c21c:
    r5 = r4 + 161
    r4 = r4 + 1
    r3 = r3 + 1
    if (r5 < r0) goto L01c0c1d8
L01c0c228:
    [r14+32] = r9
    r1 = [r15+20]
    if (r1 == 0) goto L01c0c38a
    r0 = 0
L01c0c236:
    r1 = r1 >> 1
    r0 = r0 + 1
    if (r1 != 0) goto L01c0c236
    goto L01c0c38c
L01c0c23e:
    if (r0 != 0) goto L01c0c252
    call ir_processing_wait  ; @call.xl
    if (r0 == 0) goto L01c0c252
    [r15+24] = 0x1
    r0 = [r5+0]
    r0 = r0 + 1
    [r5+0] = r0
L01c0c252:
    r6 = [r8+0]
    r0 = [r15+24]
    r5 = [r14+16]
    if (r0 != 0) goto L01c0c2aa
    r0 = [r15+8]
    r1 = [r15+12]
    r0 = r0 + r1
    r10 = r0 + 2
    r13 = r9
    r8 = [r15+32]
    r9 = [r15+36]
    r7 = [r14+40]
    r0 = r5 << 2
    r0 += r8
    r1 = 0x1 - r5
    r1 = r1 + r6
    r4 = umin(r1, r7)
    r1 = r9
    r2 = r4
    r3 = r10
    call effect_type29_processing_accumulate29  ; @call.xl
    r2 = r7 - r4
    r0 = r4 << 2
    r1 = r9 + r0
    r9 = r13
    r0 = r8
    r3 = r10
    call effect_type29_processing_accumulate29  ; @call.xl
L01c0c2aa:
    r0 = [r14+20]
    r1 = [r14+28]
    r2 = [r14+52]
    r2 = r2 + r5
    r2 &= r6
    [r14+16] = r2
    r1 ^= 1
    [r14+28] = r1
    r0 = r0 + 1
    [r14+20] = r0
    [r15+12] = 0x0
    goto L01c0c6b8
L01c0c2d0:
    r13 = r9
    r3 = [r14+48]
    r0 = [r15+48]
    r1 = 0
    r2 = 0
    if (r3 == 0) goto L01c0c31e
    r2 = [r14+28]
    r3 = r15 + 40
    r3 = [r3+r2<<2]
    r2 = 0
    r5 = 0
L01c0c2f0:
    r4 = [r3+4]
    r7 = [r3++=8]
    r6 = abs(r4)
    r7 = abs(r7)
    ifs (r7 <= r6) {
    r4 = r7
    } else {
    r4 = r6
    r6 = r7
    }
    r4 = r4 >>> 1
    r4 = r4 + r6
    [r0+r5<<2] = r4
    r6 = [r14+48]
    r5 = r5 + 1
    r2 = smax(r4, r2)
    if (r5 < r6) goto L01c0c2f0
L01c0c31e:
    r3 = [r15+16]
    [r15+20] = r2
    r2 = r2 >>> 10
    r2 = smax(r2, r3)
    [r8+4] = r2
    r3 = 2
    r4 = r0 + 8
    r6 = r0 + 4
    r9 = r0 + 12
    r8 = r0 + 16
    r10 = 0
L01c0c340:
    r7 = [r4+r1<<2]
    ifs (r7 <= r2) goto L01c0c378
    r5 = [r6+r1<<2]
    ifs (r7 <= r5) goto L01c0c378
    r5 = [r9+r1<<2]
    ifs (r7 < r5) goto L01c0c378
    r5 = [r0+r1<<2]
    ifs (r7 <= r5) goto L01c0c378
    r5 = [r8+r1<<2]
    ifs (r7 < r5) goto L01c0c378
    r5 = [sp+76]
    h[r5+r10<<1] = r3
    r10 = r10 + 1
    if (r10 == 40) goto L01c0c6de
L01c0c378:
    r5 = r1 + 3
    r1 = r1 + 1
    r3 = r3 + 1
    if (r5 < 160) goto L01c0c340
L01c0c382:
    [r14+32] = r10
    r9 = r13
    goto L01c0c6b8
L01c0c38a:
    r0 = 0
L01c0c38c:
    [sp+8] = r12
    [sp+12] = r11
    r1 = r0 + -21
    [r15+12] = r1
    r1 = [r14+28]
    r2 = [r14+20]
    r2 = r15 + 40  #
    [sp+72] = r2
    r3 = [r2+r1<<2]
    [sp+52] = r3
    r1 ^= 1
    r1 = [r2+r1<<2]
    [sp+36] = r1
    r1 = [r14+48]
    r2 = [r14+0]
    [sp+56] = r2
    [sp+60] = r3
    r2 = [r15+48]
    [sp+112] = r2
    r5 = r1 << 1
    if (r5 == 0) goto L01c0c3d6
    r2 = 0
    r4 = r5  #
    r3 = [sp+112]
L01c0c3d0:
    [r3++=4] = r2
    if (--r4 != 0) goto L01c0c3d0
L01c0c3d6:
    [sp+4] = r5
    if (r9 == 0) goto L01c0c684
    r2 = 65535
    r3 = [sp+72]
    r2 = r2 + r3
    [sp+44] = r2
    r4 = r0 + 9
    r5 = 0
    r2 = [sp+56]
    r3 = [sp+60]
    r3 = r2 >>> 31
    [sp+56] = r2
    [sp+60] = r3
    r0 = r14 + 7120
    r0 = r1 + -5  #
    [sp+20] = r0
    r0 = 11764  #
    [sp+40] = r0
    r0 += r14
    [sp+16] = r0
    [sp+24] = r4
    [sp+28] = r5
    r1 = 0
    [sp+68] = r14
    [sp+64] = r15
    [sp+48] = r9
    goto L01c0c420
L01c0c41a:
    r2 = r4  #
    r3 = [r5+56]
    goto L01c0c4f4
L01c0c420:
    r0 = [sp+76]
    [sp+80] = r1
    r7 = h[r0+r1<<1] (u)
    r6 = 1
    r6 <= insert(r7, p:1, l:16)  #
    r1 = [sp+52]
    r8 = [r1+r6<<2]
    r0 = r7 << 3
    r9 = [r1+r0]
    r0 = r9
    r1 = r8
    call effect_type29_processing_phase29
    r5 = [r15+60]
    r1 = h[r5+r7<<1] (u)
    r4 = r0  #
    r2 = [sp+44]
    r12 = uextra(r2, p:0, l:16)
    if (r1 != r12) goto L01c0c460
    r1 = [r15+52]
    r0 = [r1+r7<<2]
    goto L01c0c474
L01c0c460:
    r0 = r7 << 1
    r2 = [sp+36]
    r1 = [r2+r6<<2]
    r0 = [r2+r0<<2]
    call effect_type29_processing_phase29
    r1 = [r15+52]
L01c0c474:
    [r1+r7<<2] = r4
    r1 = [sp+72]
    h[r5+r7<<1] = r1
    r1 = r7 << 31
    r1 = r1 + r4
    r0 = r1 - r0
    r1 = r0 >>> 15
    r0 = 0x8000
    ifs (r1 <= 32768) {
    r0 = -32768
    r0 = smax(r1, r0)
    }
    r1 = r7 << 16
    r1 = r1 + r0
    r2 = [sp+56]
    r3 = [sp+60]
    r11_r10 = r1 * r2 (s)
    r11_r10 >>= 16
    r2 = r10 + 0x8000
    r13 = r2 >>> 16
    ifs (r13 < 1) goto L01c0c674
    r1 = [sp+40]
    ifs (r13 > r1) goto L01c0c674
    r5 = [sp+64]
    r1 = [r5+64]
    r3 = h[r1+r13<<1] (u)
    r6 = 4294901760
    r7 = r2 & r6
    r2 = r13
    if (r3 == r12) goto L01c0c4e8
    r2 += -1
    r3 = h[r1+r2<<1] (u)
    if (r3 == r12) goto L01c0c4e8
    r2 = r13 + 1
    r3 = h[r1+r2<<1] (u)
    if (r3 != r12) goto L01c0c41a
L01c0c4e8:
    r5 = r10 << 15  #
    r3 = [r5+56]
    r2 = [r3+r2<<2]
    r2 = r2 + r5
L01c0c4f4:
    r6 = 1023  #
    r5 = [sp+68]
    [r3+r13<<2] = r2
    r3 = [sp+72]
    h[r1+r13<<1] = r3
    r1 = r2 - r4
    r2 = r1 >> 22
    r3 = r2 << 2
    r4 = r5 + 3020
    r5 = [++r3=r4]
    r2 = r2 + 256  #
    r3 = [r3+4]
    r2 &= r6
    r2 = r2 << 2
    r2 = [++r4=r2]
    r3 = r3 - r5  #
    r4 = [r4+4]
    r6 = uextra(r1, p:6, l:16)
    r15_r14 = r3 * r6 (s)
    r15_r14 >>= 16
    r1 = r14 + r5
    r3 = r4 - r2
    r5_r4 = r3 * r6 (s)
    r5_r4 >>= 16
    r4 = r4 + r2  #
    r5 = [sp+16]
    r3_r2 = r4 * r8 (s)
    r3_r2 += r1 * r9 (s)
    r0 = r0 + 0x8100
    r0 = r0 >>> 9
    r0 = [r5+r0<<2]
    r5_r4 = r4 * r9 (s)
    r5_r4 -= r1 * r8 (s)
    r3_r2 <<= 2
    r3_r2 >>>= 32
    r3_r2 = r2 * r0 (s)
    r5_r4 <<= 2
    r5_r4 >>>= 32
    r9_r8 = r4 * r0 (s)
    r0 = r10 + 0x8100
    r11_r10 = r3_r2
    r0 = r0 - r7
    r2 = [sp+24]
    r3 = [sp+28]
    r11_r10 >>>= r2
    r9_r8 >>>= r2
    r0 = r0 >> 9
    r0 = r0 << 2
    ifs (r13 <= 3) goto L01c0c5d0
    r4 = -72  #
    r1 = [sp+20]
    r0 = r0 + r1  #
    r2 = [sp+112]
    r1 = r13 << 3
    r1 = r1 + r2
    r11 = r10 >>> 31
    r9 = r8 >>> 31
L01c0c5a8:
    r2 = [r0++=516]
    r3 = r1 + r4
    r7_r6 = r2 * r8 (s)  #
    r5 = [r3+40]
    r7_r6 >>= 30
    r5 = r5 + r6
    r7_r6 = r2 * r10 (s)  #
    [r3+40] = r5
    r7_r6 >>= 30  #
    r5 = [r3+44]
    r2 = r5 + r6
    r4 = r4 + 8
    [r3+44] = r2
    if (r4 != 0) goto L01c0c5a8
    goto L01c0c674
L01c0c5d0:
    r1 = [sp+20]
    r4 = r1 + r0  #
    r1 = [sp+112]
    r11 = r10 >>> 31
    r9 = r8 >>> 31
    r0 = r13 << 3
    r2 = r0 + -28
    r1 = r1 + r2  #
    [sp+92] = r2
    r1 = r13 + -4  #
    [sp+88] = r1
    r6 = 0x0 - r0  #
    [sp+84] = r1
    r15 = r0 + -32
    r5 = 0
    r0 = r1
    r1 = 0
    [sp+104] = r10
    [sp+108] = r11
    [sp+96] = r8
    [sp+100] = r9
L01c0c608:
    r2 = [r4++=516]
    r13_r12 = r2 * r10 (s)
    r13_r12 >>= 30
    r11_r10 = r2 * r8 (s)
    r11_r10 >>= 30
    ifs (r0 < 0) goto L01c0c63e
    r2 = [sp+112]
    r2 = r2 + r5
    r3 = [r2+r15]
    r3 += r10
    [r2+r15] = r3
    r3 = [sp+92]
    r3 = [r2+r3]
    r2 = [sp+88]
    r2 = r2 + r5
    r7 = r3 + r12
    goto L01c0c65e
L01c0c63e:
    r14 = [sp+112]
    r2 = r14 + r6
    r3 = [r2+32]
    r3 += r10
    [r2+32] = r3
    r3 = [sp+84]
    r3 = r3 + r1  #
    r2 = [r2+36]
    r3 = r3 << 1
    r7 = r2 - r12
    r2 = r3 << 2
    r2 = r14 - r2
    r2 = r2 + 4
L01c0c65e:
    r10 = [sp+104]
    r11 = [sp+108]
    r8 = [sp+96]
    r9 = [sp+100]
    [r2+0] = r7
    r0 = r0 + 1
    r6 += -8
    r5 = r5 + 8
    r1 = r1 + 1
    if (r5 != 72) goto L01c0c608
L01c0c674:
    r1 = [sp+80]
    r1 = r1 + 1
    r14 = [sp+68]
    r15 = [sp+64]
    r9 = [sp+48]
    if (r1 != r9) goto L01c0c420
L01c0c684:
    r0 = [r14+32]
    if (r0 != r9) goto L01c0c69a
    r0 = 0
    r1 = [sp+112]
    [r1+4] = r0
    r1 += -4
    r2 = [sp+4]
    [r1+r2<<2] = r0
L01c0c69a:
    r3 = [r15+36]
    r2 = [r15+48]
    r0 = [r14+40]
    r1 = 1
    call ir_processing_start  ; @call.xl
    r11 = [sp+12]
    r12 = [sp+8]
    r9 = L01c34198
L01c0c6b8:
    r0 = [r9+0]
    if (r0 == 0) goto L01c0c6da
    call r0
    r1 = r11 & 0x3
    r2 = L01c341ac
    r3 = [r2+r1<<2]
    r0 = r0 - r12
    if (r0 > r3) {
    [r2+r1<<2] = r0
    }
L01c0c6da:
    sp += 116
    {pc, r15-r4} = [sp++]
L01c0c6de:
    r10 = 40
    goto L01c0c382
L01c0c6e4:
    r9 = 40
    goto L01c0c228

; effect_type29_processing_filter29: 0x01c0c6ea..0x01c0c8d4, module effect-type29-processing (filter29)
.type effect_type29_processing_filter29,@function
effect_type29_processing_filter29:
    [--sp] = {rets, r15-r4}
    sp += -8
    r13 = r0 + 360
    r3 = b[r13+13] (u)
    r5 = r2
    r6 = r1
    r8 = r0 + 288
    if (r3 == 0) goto L01c0c71c
    r1 = [r6+0]
    [r13+52] = r1
    [r13+48] = r1
    [r13+44] = r1
    [r13+40] = r1
    r1 = 0
    [r13+56] = r1
    b[r13+13] = r1
L01c0c71c:
    r9 = r8 + 92
    r1 = b[++r8=83] (u)
    r2 = b[r13+12] (u)
    r3 = 1
    if (r2 != r1) {
    r3 = 0
    }
    r7 = h[r13+0] (u)
    r1 = r3 << 8
    if (r1 <= r7) goto L01c0c744
    r12 = r7 + 64
    if (r12 <= r1) goto L01c0c74e
    goto L01c0c756
L01c0c744:
    r12 = r7 + -64
    if (r1 >= r7) {
    r12 = r7
    }
L01c0c74e:
    if (r1 >= r7) goto L01c0c758
    ifs (r12 >= r1) goto L01c0c758
L01c0c756:
    r12 = r1
L01c0c758:
    r10 = r9 + 41  #
    [sp+4] = r0
    [sp] = r10
    if (r7 != 256) goto L01c0c77e
    if (r12 != r7) goto L01c0c77e
    r1 = b[r10+0] (u)
    if (r1 == 0) goto L01c0c7a6
    if (r5 == 0) goto L01c0c7f8
    r0 = r6
    r1 = r5
    r2 = r9
    call biquad_residual  ; @call.xl
    goto L01c0c7f8
L01c0c77e:
    r4 = L01c30c3c
    r0 = r4
    r1 = r6
    r2 = r5
    call dsp_stage_copy  ; @call.xl
    r0 = b[r10+0] (u)
    if (r0 == 0) goto L01c0c7b6
    if (r5 == 0) goto L01c0c7f8
    r0 = r6
    r1 = r5
    r2 = r9
    call biquad_residual  ; @call.xl
    goto L01c0c7c4
L01c0c7a6:
    if (r5 == 0) goto L01c0c7f8
    r0 = r6
    r1 = r5
    r2 = r9
    call biquad_rounded  ; @call.xl
    goto L01c0c7f8
L01c0c7b6:
    if (r5 == 0) goto L01c0c7f8
    r0 = r6
    r1 = r5
    r2 = r9
    call biquad_rounded  ; @call.xl
L01c0c7c4:
    r0 = r12 - r7
    r0 = r0 << 8
    r9 = r0 / r5 (s)
    r1 = r7 << 8
    r1 += r9
    r3 = 0
L01c0c7d4:
    r7 = [r6+0]
    r0 = r1 >>> 8
    r15_r14 = r7 * r0 (s)  #
    r2 = [r4++=4]
    r15_r14 -= r2 * r0 (s)
    r15_r14 >>= 8
    r10 = r14 + r2
    r11 = r15 + r3 + c
    [r6++=4] = r10
    r1 += r9
    if (--r5 != 0) goto L01c0c7d4
L01c0c7f8:
    h[r13+0] = r12
    r1 = b[r13+12] (u)
    r2 = b[r8+0] (u)
    r0 = [sp+4]
    r0 = r0 + 420
    if (r1 != r2) goto L01c0c88a
    r2 = [r13+20]
    r1 = [r0+4]
    r3 = r1 - r2
    r4 = r3 >>> 2
    r2 = r2 + r4
    r3 = r3 + 3
    if (r3 >= 7) {
    r1 = r2
    }
    [r13+20] = r1
    r2 = [r13+24]
    r1 = [r0+8]
    r3 = r1 - r2
    r4 = r3 >>> 2
    r2 = r2 + r4
    r3 = r3 + 3
    if (r3 >= 7) {
    r1 = r2
    }
    [r13+24] = r1
    r2 = [r13+28]
    r1 = [r0+12]
    r3 = r1 - r2
    r4 = r3 >>> 2
    r2 = r2 + r4
    r3 = r3 + 3
    if (r3 >= 7) {
    r1 = r2
    }
    [r13+28] = r1
    r2 = [r13+32]
    r1 = [r0+16]
    r3 = r1 - r2
    r4 = r3 >>> 2
    r2 = r2 + r4
    r3 = r3 + 3
    if (r3 >= 7) {
    r1 = r2
    }
    [r13+32] = r1
    r1 = [r13+36]
    r0 = [r0+20]
    r2 = r0 - r1
    r3 = r2 >>> 2
    r1 = r1 + r3
    r2 = r2 + 3
    if (r2 >= 7) {
    r0 = r1
    }
    [r13+36] = r0
    sp += 8
    {pc, r15-r4} = [sp++]
L01c0c88a:
    if (r12 != 0) goto L01c0c8c4
    if (r1 == 0) goto L01c0c8c8
    r2 = [r0+4]
    [r13+20] = r2
    r2 = [r0+8]
    [r13+24] = r2
    r2 = [r0+12]
    [r13+28] = r2
    r2 = [r0+16]
    [r13+32] = r2
    r0 = [r0+20]
    [r13+36] = r0
    r0 = 1
    r2 = 1
    if (r1 != 2) {
    r2 = 0
    }
    r3 = [sp]
    b[r3+0] = r2
    b[r8+0] = r1
    b[r13+13] = r0
L01c0c8c4:
    sp += 8
    {pc, r15-r4} = [sp++]
L01c0c8c8:
    r1 = 0
    b[r0+0] = r1
    b[r8+0] = r1
    sp += 8
    {pc, r15-r4} = [sp++]

; effect_type29_processing_correlate29: 0x01c0c8d4..0x01c0cd80, module effect-type29-processing (correlate29)
.type effect_type29_processing_correlate29,@function
effect_type29_processing_correlate29:
    [--sp] = {rets, r15-r4}
    sp += -100
    [sp+36] = r2
    [sp+40] = r3
    r7 = r1
    r1 = r7 + -12
    r6 = 0
    if (r1 > 1168) goto L01c0cd7a
    r1 = [r0+288]
    r5 = [r0+84]
    r0 = r1 + 1983  #
    [sp+16] = r1
    r9 = 0  #
    r1 = [sp+152]
    r2 = 2047  #
    [sp+12] = r1
    r1 = 40
    r3 = r0
L01c0c906:
    r3 &= r2
    r4 = [r5+r3<<2]
    r4 = abs(r4)
    r9 = umax(r4, r9)
    r3 += -20
    if (--r1 != 0) goto L01c0c906
    r1 = 8188  #
    [sp+44] = r5
    r0 = r0 << 2
    r0 &= r1
    r1 = sample_correlation_weights
    r8 = 1  #
    [sp+48] = r1
    [sp+52] = r0
    [sp+56] = r7
    r0 = 20
    [sp+60] = r0
    if (r9 <= 33554432) {
    r8 = 0
    }
    [sp+64] = r8
    r4 = sp + 44
    r0 = r4
    call effect_sample_processing_correlation  ; @call.xl
    r0 = [sp+68]
    r1 = [sp+72]
    [sp+24] = r0
    [sp+28] = r1
    r12 = [sp+76]
    r13 = [sp+80]
    r14 = [sp+84]
    r15 = [sp+88]
    r10 = [sp+92]
    r11 = [sp+96]
    r1 = 8188  #
    [sp+44] = r5
    r0 = sample_correlation_weights
    r0 += 80
    [sp+48] = r0
    r0 = [sp+16]
    r0 = r0 << 2
    r0 = r0 + 6332
    r0 &= r1
    [sp+52] = r0
    [sp+56] = r7
    r0 = 20
    r0 = r4  #
    [sp+60] = r0
    [sp+64] = r8
    call effect_sample_processing_correlation  ; @call.xl
    r2 = [sp+92]
    r3 = [sp+96]
    r0 = r2 + r10
    r1 = r3 + r11 + c
    if (r9 <= 33554432) {
    r2 = r6 + 0x40000000
    } else {
    r2 = r6 + 0x400000
    }
    r3 = 0
    r4 = r0 - r2
    r2 = r1 - r3 - !c
    r2 = psr
    r4 = [sp+84]
    r5 = [sp+88]
    r3 = r2 >> 3
    r7 = r2 ^ r3
    [sp+16] = r0
    [sp+20] = r1
    r0 = r4 + r14
    r10 = [sp+76]
    r11 = [sp+80]
    r2 = [sp+68]
    r3 = [sp+72]
    r1 = r5 + r15 + c
    r14 = r10 + r12
    r15 = r11 + r13 + c
    r4 = [sp+24]
    r5 = [sp+28]
    r12 = r2 + r4
    r13 = r3 + r5 + c
    if ((r7 & 0x1) != 0) goto L01c0cd7a
    r11_r10 = r1_r0
    r3 = 2147483647
    r2 = 0
    r0 = [sp+16]
    r1 = [sp+20]
    r4 = r0 + r3
    r5 = r1 + r2 + c
    r7 = -2
    r3 = r4 - r7
    r2 = r5 - r2 - !c
    r5 = psr
    r4 = r3 | r2
    r5 = sextra(r5, p:1, l:1)
    if (r9 <= 33554432) {
    r8 = r6 + 0x44000000
    } else {
    r8 = r6 + 0x46000000
    }
    [sp+24] = r8
    [sp] = r14
    [sp+4] = r15
    if ((r5 & r4) != 0) goto L01c0ca30
    r6 = itof(r0)
    r5 = 2147483647
    goto L01c0cab4
L01c0ca30:
    r9 = r7
    r3_r2 = r1_r0
    r3_r2 >>>= 63
    r4 = r0 + r2
    r5 = r1 + r3 + c
    r7 = r5 ^ r3
    r6 = r4 ^ r2
    r4 = 0
    r2 = r6 - 0x80000000
    r2 = r7 - r4 - !c
    r2 = psr
    if ((r2 & 2) == 0) goto L01c0caa2
    r5 = 0
L01c0ca5a:
    r3_r2 = r7_r6
    r7_r6 >>= 1
    r2 = r2 & 0x1
    r5 |= r2
    r4 = r4 + 1
    if (r3 != 0) goto L01c0ca5a
    r2 = r6 | r5
    r6 = itof(r2)
    if (r4 < 16) goto L01c0ca90
    r5 = 0x47800000
    r7 = r4
L01c0ca7c:
    r7 += -16
    r6 = r6 * r5 (f)
    if (r7 > 15) goto L01c0ca7c
    if ((r4 & 0xF) == 0) goto L01c0caa6
    r4 = r4 & 0xF
L01c0ca90:
    r5 = 2147483647
    r7 = r9
L01c0ca98:
    r6 = r6 + r6 (f)
    if (--r4 != 0) goto L01c0ca98
    goto L01c0caae
L01c0caa2:
    r6 = itof(r6)
L01c0caa6:
    r5 = 2147483647
    r7 = r9
L01c0caae:
    ifs (r1 < 0) {
    r6 ^= 2147483648
    }
L01c0cab4:
    r13_r12 >>>= 2
    r11_r10 >>>= 2
    r14 = r10 - r12
    r9_r8 = r11_r10
    r15 = r9 - r13 - !c
    r0 = 0
    r2 = r14 + r5
    r3 = r15 + r0 + c
    r1 = r2 - r7
    r2 = r3 - r0 - !c
    r3 = psr
    r1 |= r2
    r2 = sextra(r3, p:1, l:1)
    if ((r2 & r1) != 0) goto L01c0caea
    r7 = itof(r14)
    goto L01c0cb6e
L01c0caea:
    r3_r2 = r15_r14
    r3_r2 >>>= 63
    r10 = r14 + r2
    r11 = r15 + r3 + c
    r5 = r11 ^ r3
    r4 = r10 ^ r2
    r1 = r4 - 0x80000000
    r0 = r5 - r0 - !c
    r0 = psr
    if ((r0 & 2) == 0) goto L01c0cb4e
    r1_r0 = 0
L01c0cb12:
    r3_r2 = r5_r4
    r5_r4 >>= 1
    r2 = r2 & 0x1
    r1 |= r2
    r0 = r0 + 1
    if (r3 != 0) goto L01c0cb12
    r1 |= r4
    r7 = itof(r1)
    if (r0 < 16) goto L01c0cb5a
    r1 = 0x47800000
    r4 = r0
    r5 = 2147483647
L01c0cb38:
    r4 += -16
    r7 = r7 * r1 (f)
    if (r4 > 15) goto L01c0cb38
    if ((r0 & 0xF) == 0) goto L01c0cb68
    r0 = r0 & 0xF
    goto L01c0cb60
L01c0cb4e:
    r7 = itof(r4)
    r5 = 2147483647
    goto L01c0cb68
L01c0cb5a:
    r5 = 2147483647
L01c0cb60:
    r7 = r7 + r7 (f)
    if (--r0 != 0) goto L01c0cb60
L01c0cb68:
    ifs (r15 < 0) {
    r7 ^= 2147483648
    }
L01c0cb6e:
    r14 = [sp]
    r15 = [sp+4]
    r1_r0 = r15_r14
    r1_r0 >>>= 2
    r1_r0 <<= 1
    r2 = r8 - r0
    r3 = r9 - r1 - !c
    r10 = r2 + r12
    r11 = r3 + r13 + c
    r0 = 0
    r2 = r10 + r5
    r3 = r11 + r0 + c
    r1 = -2
    r1 = r2 - r1
    r2 = r3 - r0 - !c
    r3 = psr
    r1 |= r2
    r2 = sextra(r3, p:1, l:1)
    if ((r2 & r1) != 0) goto L01c0cbb6
    r4 = itof(r10)  #
    r3 = [sp+24]
    r1 = -2
    goto L01c0cc40
L01c0cbb6:
    r5_r4 = r11_r10
    r5_r4 >>>= 63
    r12 = r10 + r4
    r13 = r11 + r5 + c
    r3 = r13 ^ r5
    r2 = r12 ^ r4
    r1 = r2 - 0x80000000
    r0 = r3 - r0 - !c
    r0 = psr
    if ((r0 & 2) == 0) goto L01c0cc1c
    r1_r0 = 0
L01c0cbde:
    r5_r4 = r3_r2
    r3_r2 >>= 1
    r4 = r4 & 0x1
    r1 |= r4
    r0 = r0 + 1
    if (r5 != 0) goto L01c0cbde
    r1 |= r2  #
    r3 = [sp+24]
    r4 = itof(r1)
    if (r0 < 16) goto L01c0cc2a
    r1 = 0x47800000
    r2 = r0
    r5 = 2147483647
L01c0cc06:
    r2 += -16
    r4 = r4 * r1 (f)
    if (r2 > 15) goto L01c0cc06
    if ((r0 & 0xF) == 0) goto L01c0cc38
    r0 = r0 & 0xF
    goto L01c0cc30
L01c0cc1c:
    r4 = itof(r2)  #
    r3 = [sp+24]
    r5 = 2147483647
    goto L01c0cc38
L01c0cc2a:
    r5 = 2147483647
L01c0cc30:
    r4 = r4 + r4 (f)
    if (--r0 != 0) goto L01c0cc30
L01c0cc38:
    ifs (r11 < 0) {
    r4 ^= 2147483648
    }
    r1 = -2
L01c0cc40:
    r2 = r3 * r6 (f)
    r0 = 0
    r8 = r14 + r5
    r9 = r15 + r0 + c
    r1 = r8 - r1
    r3 = r9 - r0 - !c
    r5 = psr
    r1 |= r3
    r3 = sextra(r5, p:1, l:1)
    if ((r3 & r1) != 0) goto L01c0cc6c
    r1 = itof(r14)  #
    r3 = [sp+12]
    goto L01c0cce4
L01c0cc6c:
    r11_r10 = r15_r14
    r11_r10 >>>= 63
    r12 = r14 + r10
    r13 = r15 + r11 + c
    r9 = r13 ^ r11
    r8 = r12 ^ r10
    r1 = r8 - 0x80000000
    r0 = r9 - r0 - !c
    r0 = psr
    if ((r0 & 2) == 0) goto L01c0ccd8
    r1_r0 = 0
L01c0cc94:
    r3 = r8
    r5 = r9
    r9_r8 >>= 1
    r3 = r3 & 0x1
    r1 |= r3
    r0 = r0 + 1
    if (r5 != 0) goto L01c0cc94
    r1 = r1 | r8
    r1 = itof(r1)
    if (r0 < 16) goto L01c0cccc
    r3 = 0x47800000
    r5 = r0
L01c0ccb8:
    r5 += -16
    r1 = r1 * r3 (f)
    if (r5 > 15) goto L01c0ccb8
    if ((r0 & 0xF) == 0) goto L01c0ccdc
    r0 = r0 & 0xF
L01c0cccc:
    r3 = [sp+12]
L01c0ccce:
    r1 = r1 + r1 (f)
    if (--r0 != 0) goto L01c0ccce
    goto L01c0ccde
L01c0ccd8:
    r1 = itof(r8)
L01c0ccdc:
    r3 = [sp+12]
L01c0ccde:
    ifs (r15 < 0) {
    r1 ^= 2147483648
    }
L01c0cce4:
    r0 = r1 / r2 (f)
    [r3+0] = r0
    r1 = 1051931443
    r6 = 0
    iff (r0 < r1) goto L01c0cd7a
    r1 = r6 + 0x40800000
    r0 = r4 * r1 (f)
    r3 = 3114780076
    r2 = r2 * r3 (f)
    r1 = r7 * r1 (f)
    iff (r0 u>= r2) goto L01c0cd1e
    r2 = r6 + 0xC0000000
    r1 = r1 * r2 (f)
    r0 = r1 / r0 (f)
    goto L01c0cd30
L01c0cd1e:
    r0 = 0
    iff (r1 u<= r0) {
    r0 = 3251109888
    } else {
    r0 = 1103626240
    }
L01c0cd30:
    r4 = [sp+40]
    r3 = [sp+36]
    r2 = 3251109888
    iff (r0 u>= r2) {
    r2 = r0
    }
    r1 = 1103626240
    iff (r0 u<= r1) {
    r1 = r2
    }
    r0 = r6 + 0x47800000
    r0 = r1 * r0 (f)
    r0 = ftoi(r0) (trunc)
    [r3+0] = r0
    r6 = 1
    r2 = 1077936128
    r0 = 1
    iff (r1 u>= r2) {
    r0 = 0
    }
    r3 = r2 + 0x80000000
    r2 = 1
    iff (r1 u<= r3) {
    r2 = 0
    }
    r0 &= r2
    [r4+0] = r0
L01c0cd7a:
    r0 = r6
    sp += 100
    {pc, r15-r4} = [sp++]

; effect_type29_processing_update29: 0x01c0cd80..0x01c0d312, module effect-type29-processing (update29)
.type effect_type29_processing_update29,@function
effect_type29_processing_update29:
    [--sp] = {rets, r15-r4}
    sp += -140
    r12 = r0 + 288
    r6 = [r12+12]
    r2 = r0 + 84  #
    [sp+64] = r0
    r5 = r2 + 204
    r7 = r5 + 70
    if (r6 == 0) goto L01c0ce2c
    r3 = [r12+52]
    r3 = r3 + 0x8000
    r1 = r3 >>> 16
    ifs (r1 < 72) goto L01c0ce2c
    r10 = [r2+0]
    if (r10 == 0) goto L01c0ce2c
    r2 = 0
    r8 = r5  #
    [sp+136] = r2
    [sp+132] = r2
    r2 = b[++r8=86] (u)
    if ((r2 & 4) != 0) goto L01c0ce34
    r2 = r6 >> 31
    r3 = 16
    r3 <= insert(r2, p:2, l:1)
    r2 = [r5+r3]
    r0 = r6 >>> 31
    r3 = r5 + 20
    r0 = [r3+r0<<2]
    r0 = r0 - r2  #
    r2 = [sp+64]
    r5 = r2 + 376
    r0 = r0 >>> 16
    r2 = 2
    r6 = r0 / r2 (s)  #
    r3 = b[r5+0] (u)
    r9 = r0 + 64
    if (r3 == 0) goto L01c0ce0e
    r0 = r9 - r6
    ifs (r0 < 1) goto L01c0ce0e
    r2 += -98
    r2 *= r3
    r1 = r1 + r2
    r1 = r1 - r6
    r2 = r1 / r0 (s)
    r2 *= r0
    r1 = r1 - r2
    r2 = r1 + r6
    r1 = r1 >>> 31
    r0 &= r1
    r1 = r2 + r0
L01c0ce0e:
    r0 = 0
    b[r7+5] = r0
    r3 = b[r7+4] (u)
    if (r3 == 0) goto L01c0ce6a
    [sp+8] = r9
    [sp+12] = r6
    [sp+16] = r5
    if (r3 > 10) goto L01c0d144
    [sp+4] = r7
    [sp+28] = r8
    r0 = [r12+0]
    goto L01c0cee2
L01c0ce2c:
    r0 = 0
    b[r7+4] = r0
    sp += 140
    {pc, r15-r4} = [sp++]
L01c0ce34:
    r0 = [sp+64]
    r2 = h[r0+352] (u)
    if (r2 != 0) goto L01c0d2a6
    r2 = 364  #
    r0 = [sp+64]
    r2 = b[r0+r2] (u)
    if (r2 != 0) goto L01c0d2a6
    r2 = b[r7+5] (u)
    if (r2 == 0) goto L01c0d2aa
    r0 = h[r7+0] (u)
    r1 = r0 + 1
    h[r7+0] = r1
    if (r0 < 13) goto L01c0d2a6
    r0 = 0
    b[r7+5] = r0
    goto L01c0d30c
L01c0ce6a:
    r0 = b[r8+1] (u)
    if (r0 == 0) goto L01c0ce7c
    r0 = r0 + 255
    b[r8+1] = r0
    sp += 140
    {pc, r15-r4} = [sp++]
L01c0ce7c:
    [sp+4] = r7
    [sp+8] = r9
    r6 = r3  #
    [sp+12] = r6
    [sp+16] = r5
    [sp+28] = r8
    r0 = [r12+0]
    r3 = 128
    r5 = [sp+64]
    r2 = r5 + 444
    b[r2+0] = r3
    b[r2+1] = r3
    b[r2+2] = r3
    b[r2+3] = r3
    b[r2+4] = r3
    b[r2+5] = r3
    b[r2+6] = r3
    b[r2+7] = r3
    b[r2+8] = r3
    b[r2+9] = r3
    b[r2+10] = r3
    b[r2+11] = r3
    b[r2+12] = r3
    b[r2+13] = r3
    b[r2+14] = r3
    r2 = r5 + 460  #
    b[r2+15] = r3
    b[r2+0] = r3
    b[r2+1] = r3
    b[r2+2] = r3
    b[r2+3] = r3
    b[r2+4] = r3
    b[r2+5] = r3
    b[r2+6] = r3
    b[r2+7] = r3
    b[r2+8] = r3
    b[r2+9] = r3
    b[r2+10] = r3
    b[r2+11] = r3
    b[r2+12] = r3
    b[r2+13] = r3
    b[r2+14] = r3
    r2 = 476  #
    b[r2+15] = r3
    b[r5+r2] = r3
    r3 = r6
L01c0cee2:
    r0 = r0 + 1983
    r5 = 2047
    r0 &= r5
    r13 = -2  #
    [sp+44] = r0
    r0 = r0 << 2
    r0 = r12 + 156  #
    [sp+40] = r0
    [sp+24] = r12
    r12 = 0  #
    [sp+56] = r0
    r0 = sp + 72
    r0 = r1 + -60  #
    [sp+36] = r0
    r11 = r12 + 0x47800000  #
    [sp+20] = r1
    [sp+32] = r0
    r4 = 2147483647
    r0 = 0
L01c0cf18:
    [sp+48] = r0
    r0 = 20
    r6 = 0
    r1 = [sp+44]
L01c0cf20:
    r2 = [r10+r1<<2]
    r1 = r1 + 2028
    r1 &= r5
    r2 = abs(r2)
    r6 = umax(r2, r6)
    if (--r0 != 0) goto L01c0cf20
    [sp+72] = r10
    r5 = [sp+36]
    r0 = L0203b830
    [r5+4] = r0
    r0 = [sp+40]
    r0 = r3 * 0xC  #
    [r5+8] = r0
    [sp+52] = r3
    r1 = [sp+32]
    r0 = r0 + r1
    [r5+12] = r0
    r0 = 20
    [r5+16] = r0
    r0 = 1
    if (r6 <= 33554432) {
    r0 = 0
    }
    [r5+20] = r0
    r0 = sp + 72
    call effect_sample_processing_correlation  ; @call.xl
    if (r6 <= 33554432) {
    r2 = r12 + 0x20000000
    } else {
    r2 = r12 + 0x200000
    }
    r3 = 0
    r0 = [r5+48]
    r1 = [r5+52]
    r5 = r0 - r2
    r2 = r1 - r3 - !c
    r2 = psr
    r3 = r2 >> 3
    r2 ^= r3
    if ((r2 & 1) != 0) goto L01c0d120
    r2 = r0 + r4
    r3 = r1 + r12 + c
    r5 = r2 - r13
    r2 = r3 - r12 - !c
    r3 = psr
    r2 |= r5
    r3 = sextra(r3, p:1, l:1)
    r14 = r12 + 0x46000000
    if (r6 <= 33554432) {
    r14 = r12 + 0x44000000
    }
    if ((r3 & r2) != 0) goto L01c0cfba
    r6 = itof(r0)
    goto L01c0d02a
L01c0cfba:
    r3_r2 = r1_r0
    r3_r2 >>>= 63
    r6 = r0 + r2
    r7 = r1 + r3 + c
    r9 = r7 ^ r3
    r8 = r6 ^ r2
    r2 = r8 - 0x80000000
    r2 = r9 - r12 - !c
    r2 = psr
    if ((r2 & 2) == 0) goto L01c0d020
    r3 = 0
    r6 = 0
L01c0cfe2:
    r2 = r8
    r5 = r9
    r9_r8 >>= 1
    r2 = r2 & 0x1
    r6 |= r2
    r3 = r3 + 1
    if (r5 != 0) goto L01c0cfe2
    r2 = r8 | r6
    r6 = itof(r2)
    if (r3 < 16) goto L01c0d016
    r2 = r3
L01c0d002:
    r2 += -16
    r6 = r6 * r11 (f)
    if (r2 > 15) goto L01c0d002
    if ((r3 & 0xF) == 0) goto L01c0d024
    r3 = r3 & 0xF
L01c0d016:
    r6 = r6 + r6 (f)
    if (--r3 != 0) goto L01c0d016
    goto L01c0d024
L01c0d020:
    r6 = itof(r8)
L01c0d024:
    ifs (r1 < 0) {
    r6 ^= 2147483648
    }
L01c0d02a:
    r0 = r14 * r6 (f)  #
    r1 = [sp+52]
    r1 = r1 * 0x3  #
    [sp+60] = r0
    r2 = 0
L01c0d038:
    r3 = 4
    r3 <= insert(r2, p:3, l:29)
    r5 = sp + 72
    r5 = r5 + 24
    r9 = [r5+r3]
    r3 = r2 << 3
    r8 = [r5+r3]
    r6 = r8 + r4
    r7 = r9 + r12 + c
    r3 = r6 - r13
    r5 = r7 - r12 - !c
    r6 = psr
    r3 |= r5
    r5 = sextra(r6, p:1, l:1)
    if ((r5 & r3) != 0) goto L01c0d070
    r6 = itof(r8)
    goto L01c0d0ea
L01c0d070:
    r0 = r13
    r7_r6 = r9_r8
    r7_r6 >>>= 63
    r12 = r8 + r6
    r13 = r9 + r7 + c
    r15 = r13 ^ r7
    r14 = r12 ^ r6
    r12 = 0
    r3 = r14 - 0x80000000
    r3 = r15 - r12 - !c
    r3 = psr
    if ((r3 & 2) == 0) goto L01c0d0de
    r3 = 0
    r6 = 0
L01c0d09e:
    r5 = r14
    r7 = r15
    r15_r14 >>= 1
    r5 = r5 & 0x1
    r6 |= r5
    r3 = r3 + 1
    if (r7 != 0) goto L01c0d09e
    r5 = r14 | r6
    r6 = itof(r5)
    r13 = r0
    if (r3 < 16) goto L01c0d0d4
    r5 = r3
L01c0d0c0:
    r5 += -16
    r6 = r6 * r11 (f)
    if (r5 > 15) goto L01c0d0c0
    if ((r3 & 0xF) == 0) goto L01c0d0e4
    r3 = r3 & 0xF
L01c0d0d4:
    r6 = r6 + r6 (f)
    if (--r3 != 0) goto L01c0d0d4
    goto L01c0d0e4
L01c0d0de:
    r6 = itof(r14)
    r13 = r0
L01c0d0e4:
    ifs (r9 < 0) {
    r6 ^= 2147483648
    }
L01c0d0ea:
    r3 = r2 + r1
    ifs (r3 > 32) goto L01c0d11a
    r0 = [sp+60]
    r5 = r6 / r0 (f)
    r0 = r11 + 0xFB000000
    r5 = r5 * r0 (f)
    r5 = ftoi(r5) (trunc)
    r7 = r5
    ifs (r5 <= -127) {
    r7 = -127
    }
    r6 = 127
    ifs (r5 <= 127) {
    r6 = r7
    }
    r5 = [sp+56]
    b[r5+r3] = r6
L01c0d11a:
    r2 = r2 + 1
    if (r2 != 3) goto L01c0d038
L01c0d120:
    r5 = 2047  #
    r0 = [sp+48]
    r0 = r0 + 1
    r3 = [sp+52]
    r3 = r3 + 1
    ifs (r0 > 2) goto L01c0d136
    if (r3 < 11) goto L01c0cf18
L01c0d136:
    r7 = [sp+4]
    b[r7+4] = r3
    r8 = [sp+28]
    r12 = [sp+24]
    r1 = [sp+20]
    if (r3 < 11) goto L01c0d2a6
L01c0d144:
    r0 = 0
    r11 = r12 + 156  #
    b[r7+4] = r0
    r6 = -1
    r2 = 4292967296
    r0 = 444
    r5 = 16
L01c0d15a:
    r3 = [sp+64]
    r4 = b[r3+r0] (s)
    r3 = r6
    if (r4 == -128) goto L01c0d17c
    r6 = r0 + -444
    r7 = r0 + -460
    ifs (r6 <= 16) {
    r7 = r5
    }
    r4 = r4 << 4
    r4 = r4 - r7
    ifs (r4 > r2) goto L01c0d180
L01c0d17c:
    r6 = r3
    r4 = r2
L01c0d180:
    r0 = r0 + 1
    r5 += -1
    r2 = r4
    if (r0 != 477) goto L01c0d15a
    r4 = [sp+64]
    ifs (r6 < 0) goto L01c0d25c
    [sp+24] = r12
    [sp+28] = r8
    r12 = r1 + -64  #
    [sp+20] = r1
    r9 = 0
    r14 = 0
    r10 = 4292967296
    r15 = 444
    r7 = 128
    r5 = 0
    r13 = 0
L01c0d1ae:
    r0 = b[r11+r6] (s)
    ifs (r0 <= 15) goto L01c0d252
    r0 = sp + 128
    r1 = r6 << 2
    r1 += r12  #
    [sp] = r0
    r2 = sp + 68
    r3 = sp + 132
    r0 = r4
    call effect_type29_processing_correlate29
    if (r0 == 0) goto L01c0d1ec
    r0 = [sp+128]
    iff (r0 u<= r14) goto L01c0d1ec
    r2 = [sp+132]
    r1 = 1
    if (r2 != 0) goto L01c0d1dc
    r1 = r2
L01c0d1dc:
    r13 = r1 | 0x6  #
    r2 = [sp+68]
    r1 = r6 << 18
    r1 = r1 + r2
    r9 = r1 - 0x400000
    r14 = r0
L01c0d1ec:
    r0 = r6 + 3
    ifs (r6 >= 29) {
    r0 = 32
    }
    r1 = r6 + -3
    ifs (r6 <= 3) {
    r1 = 0
    }
    ifs (r1 > r0) goto L01c0d20e
L01c0d202:
    r2 = r4 + r1
    r1 = r1 + 1
    b[r2+r15] = r7
    ifs (r1 <= r0) goto L01c0d202
L01c0d20e:
    r6 = -1
    r0 = r15
    r1 = 16
    r2 = r10
L01c0d216:
    r4 = b[r4+r0] (s)
    r3 = r6
    if (r4 == -128) goto L01c0d238
    r6 = r0 + -444
    r8 = r0 + -460
    ifs (r6 <= 16) {
    r8 = r1
    }
    r4 = r4 << 4
    r4 = r4 - r8
    ifs (r4 > r2) goto L01c0d23c
L01c0d238:
    r6 = r3
    r4 = r2
L01c0d23c:
    r0 = r0 + 1
    r1 += -1
    r2 = r4  #
    r4 = [sp+64]
    if (r0 != 477) goto L01c0d216
    ifs (r6 < 0) goto L01c0d252
    r5 = r5 + 1
    ifs (r5 < 3) goto L01c0d1ae
L01c0d252:
    [sp+136] = r9
    r8 = [sp+28]
    r12 = [sp+24]
    r1 = [sp+20]
    goto L01c0d260
L01c0d25c:
    r9 = 0
    r13 = 0
L01c0d260:
    r2 = [sp+12]
    r3 = [sp+16]
    r0 = r1 << 16
    r0 += r9  #
    r4 = [sp+8]
    r1 = r4 << 16
    ifs (r0 > r1) goto L01c0d28c
    if ((r13 & 0xFF) == 0) goto L01c0d28c
    r1 = r2 << 16
    ifs (r0 < r1) goto L01c0d28c
    [r12+52] = r0
    b[r8+0] = r13
    r0 = 0
    b[r3+0] = r0
    sp += 140
    {pc, r15-r4} = [sp++]
L01c0d28c:
    r0 = 0
    b[r8+0] = r0
    r1 = b[r3+0] (u)
    r2 = r1 + 1
    r1 = 40
    if (r2 <= 5) {
    r1 = 2
    r0 = r2
    }
    b[r3+0] = r0
    b[r8+1] = r1
L01c0d2a6:
    sp += 140
    {pc, r15-r4} = [sp++]
L01c0d2aa:
    r2 = r6 >>> 31
    r3 = r2 & 0x4
    r3 |= 1
    r3 = [r5+r3<<2]
    r2 = r2 << 2
    r2 = r2 & 0xFFFFFFF0
    r2 = r2 + r5
    r2 = [r2+20]
    r2 = r2 - r3
    ifs (r2 < 1) goto L01c0d2d4
    r0 = abs(r6)
    r0 = r2 / r0 (s)
    ifs (r0 > 768) goto L01c0d2a6
L01c0d2d4:
    r0 = sp + 128
    r2 = sp + 136
    r3 = sp + 132
    [sp] = r0
    r0 = [sp+64]
    call effect_type29_processing_correlate29
    if (r0 == 0) goto L01c0d2fa
    r0 = [sp+132]
    r1 = 1
    if (r0 != 0) goto L01c0d2f2
    r1 = r0
L01c0d2f2:
    r1 = r1 | 0x6  #
    r0 = [sp+136]
    goto L01c0d2fe
L01c0d2fa:
    r1_r0 = 0
    [sp+136] = r0
L01c0d2fe:
    b[r8+0] = r1
    [r12+48] = r0
    r0 = 1
    b[r7+5] = r0
    r0 = 0
L01c0d30c:
    h[r7+0] = r0
    sp += 140
    {pc, r15-r4} = [sp++]

; effect_type29_processing_engine29: 0x01c0d312..0x01c0ddae, module effect-type29-processing (engine29)
.type effect_type29_processing_engine29,@function
effect_type29_processing_engine29:
    [--sp] = {rets, r15-r4}
    sp += -516
    r14 = r1  #
    [sp+92] = r2
    r15 = L01c30a3c
    r5 = r0 + 84
    r7 = r0 + 288
    r10 = r0  #
    [sp+88] = r7
    if (r3 == 0) goto L01c0d5ac
    call effect_processing_capture_probe
    if (r0 == 0) goto L01c0d5ac
    r0 = [r7+36]
    r1 = [r7+28]
    r2 = [r7+24]
    [sp+68] = r2
    r2 = [r7+32]
    [sp+72] = r2
    r0 |= r1  #
    [sp+100] = r0
    [sp+76] = r1
    r4 = [sp+92]
    [sp+108] = r0
    if (r0 == 0) goto L01c0d362
    r0 = r15
    r1 = r14
    r2 = r4
    call dsp_stage_copy  ; @call.xl
L01c0d362:
    r0 = [r7+0]
    r1 = [r5++=204]
    [sp+80] = r5
    if (r4 == 0) goto L01c0d382
    r2 = 2047
    r3 = r14
L01c0d372:
    r5 = [r3++=4]
    r5 = r5 >>> 2
    [r1+r0<<2] = r5
    r0 = r0 + 1
    r0 &= r2
    if (--r4 != 0) goto L01c0d372
L01c0d382:
    r0 = r10  #
    [r7+0] = r0
    [sp+84] = r10
    call effect_processing_capture_probe
    r7 = r0  #
    r1 = [r7+56]
    r5 = r7 + 64  #
    [r7+0] = r1
    r15 = [r5+0]
    r10 = r7 + 128  #
    r0 = [r7+52]
    r0 = r10  #
    [sp+128] = r0
    r1 = r14  #
    r4 = [r7+40]
    r6 = [sp+92]
    r2 = r6
    call dsp_stage_copy  ; @call.xl
    r11 = r6 >> 1
    r1 = sp + 164
    r0 = r10
    r2 = r11
    call effect_resampling_down4  ; @call.xl
    r0 = r6 << 2
    r1 = r7 + 72
    r0 = [++r1=r0]
    [r5+8] = r0
    r0 = [r1+4]
    [r5+12] = r0
    r0 = [r1+8]
    [r5+16] = r0
    r0 = [r1+12]
    [r5+20] = r0
    r0 = [r1+16]
    [r5+24] = r0
    r0 = [r1+20]
    [r5+28] = r0
    r0 = [r1+24]
    [r5+32] = r0
    r0 = [r1+28]
    [r5+36] = r0
    r0 = [r1+32]
    [r5+40] = r0
    r0 = [r1+36]
    [r5+44] = r0
    r0 = [r1+40]
    [r5+48] = r0
    r0 = [r1+44]
    [r5+52] = r0
    r0 = [r1+48]
    [r5+56] = r0
    r0 = [r1+52]
    [r5+60] = r0
    r10 = [r7+24]
    if (r10 == 0) goto L01c0d422
    r0 = r7
    r1 = r10
    call effect_type29_processing_spectral29
    r0 = r10 + 1  #
    r1 = [r7+56]
    if (r0 >= r1) {
    r0 = 0
    }
    [r7+24] = r0
L01c0d422:
    r8 = [r7+12]
    r12 = [r7+8]
    r6 = r7 + 640  #
    r0 = [r7+4]
    [sp+132] = r0
    if (r11 == 0) goto L01c0d51a
    [sp+96] = r14
    r4 += -1
    r13 = 12284  #
    [sp+64] = r6
    r0 = r6 + 28
    r10 = 0  #
    [sp+112] = r0
    [sp+104] = r7
    r0 = [++r13=r7]
    r7 = 33554431
    r1 = 0
    [sp+124] = r11
L01c0d456:
    r9 = r1  #
    r1 = [sp+128]
    r2 = [sp+132]
    r1 = r1 - r2
    r2 = r11 - r9
    r14 = umin(r2, r1)
    if (r14 == 0) goto L01c0d4aa
    r2 = r9 << 2
    r1 = [r13+28]
    r3 = sp + 164
    r2 = r2 + r3
    r3 = 0
L01c0d47a:
    r6 = [r2+r3<<2]
    r11 = r6 >>> 2
    r6 = r7
    ifs (r11 < 33554432) {
    r5 = 4261412865
    r6 = smax(r11, r5)
    }
    [r1+r12<<2] = r6
    r5 = r6 >>> 31
    r5 ^= r6
    r0 |= r5
    r5 = r12 + 1
    r3 = r3 + 1
    r12 = r5 & r4
    if (r3 < r14) goto L01c0d47a
L01c0d4aa:
    r2 = [sp+132]
    [r13+0] = r0
    r2 += r14  #
    r1 = [sp+128]
    [sp+132] = r2
    if (r2 != r1) goto L01c0d4da
    r1_r0 = 0  #
    r5 = [sp+104]
    [r5+8] = r12
    r0 = r5  #
    [sp+132] = r0
    call effect_type29_processing_spectral29
    r1 = [r5+56]
    r0 = 1
    if (r1 <= 1) {
    r0 = 0
    }
    [r5+24] = r0
    r0 = [r13+0]
L01c0d4da:
    r1 = r14 + r9
    r11 = [sp+124]
    if (r14 == 0) goto L01c0d510
    r6 = [r13+32]
    r2 = r9 << 2  #
    r3 = [sp+112]
    r2 = r2 + r3
    r3 = 0
L01c0d4f2:
    r5 = [r6+r8<<2]
    [r2+r3<<2] = r5
    r6 = [r13+32]
    [r6+r8<<2] = r10
    r5 = r8 + 1
    r3 = r3 + 1
    r8 = r5 & r15
    if (r3 < r14) goto L01c0d4f2
L01c0d510:
    if (r11 > r1) goto L01c0d456
    r14 = [sp+96]
    r7 = [sp+104]
    r6 = [sp+64]
L01c0d51a:
    r1 = r14  #
    r0 = [sp+132]
    r2 = r11  #
    [r7+4] = r0
    [r7+8] = r12
    [r7+12] = r8
    r0 = r6 + 28
    call effect_resampling_up4  ; @call.xl
    r0 = r11 << 2
    r1 = [++r0=r6]
    [r6+0] = r1
    r1 = [r0+4]
    [r6+4] = r1
    r1 = [r0+8]
    [r6+8] = r1
    r1 = [r0+12]
    [r6+12] = r1
    r1 = [r0+16]
    [r6+16] = r1
    r1 = [r0+20]
    r1 = 420  #
    [r6+20] = r1
    r0 = [r0+24]
    [r6+24] = r0
    r0 = [sp+84]
    r1 = b[r0+r1] (u)
    r13 = L01c30a3c
    r4 = [sp+92]
    if (r1 == 0) goto L01c0d570
    r1 = r14
    r2 = r4
    call effect_type29_processing_filter29
L01c0d570:
    r0 = [sp+68]
    r5 = r0 >>> 2
    r2 = [sp+72]
    r3 = [sp+76]
    r0 = r2 >>> 2
    r1 = [sp+100]
    if (r1 != r3) goto L01c0d5e0
    if (r0 != r5) goto L01c0d5e0
    [sp+136] = r14
    [sp+140] = r13
    [sp+144] = r4
    [sp+148] = r13
    r0 = 0
    [sp+152] = r0
    r1 = r2 >>> 3
    r0 = [sp+100]
    r0 = r0 >>> 1
    [sp+156] = r1
    r1 = [sp+108]
    if (r1 != 0) goto L01c0d59e
    r0 = r1
L01c0d59e:
    [sp+160] = r0
    r0 = sp + 136
    call dsp_stage_mix  ; @call.xl
    goto L01c0dd2a
L01c0d5ac:
    r1 = [sp+92]
    if (r1 == 0) goto L01c0dda8
    r0 = [r5+0]
    if (r0 == 0) goto L01c0dda8
    if (r1 < 129) goto L01c0d602
L01c0d5c0:
    r5 = r1
    r4 = r1
    if (r4 >= 128) {
    r5 = 128
    }
    r0 = r10
    r1 = r14
    r2 = r5
    call effect_type29_processing_process29
    r4 = r4 - r5
    r0 = r5 << 2
    r14 += r0
    r1 = r4
    if (r1 != 0) goto L01c0d5c0
    goto L01c0dda8
L01c0d5e0:
    if (r4 == 0) goto L01c0dd2a
    r1 = r0 - r5
    r15 = r1 / r4 (s)  #
    r1 = [sp+100]
    r2 = r1 - r3
    r2 = r2 / r4 (s)
    r3 = r3 + r2
    r1 = r5 + r15
    r12 = 2147483647
    goto L01c0dcde
L01c0d602:
    r0 = 420  #
    r4 = [r7+12]
    r2 = b[r10+r0] (u)
    r0 = r1 + 15
    r11 = r0 >> 4
    r1_r0 = 0
    [sp+128] = r0
    [sp+36] = r2
    if (r2 == 0) goto L01c0d632
    r0 = [r7+36]
    if (r0 != 0) goto L01c0d622
    r0 = [r7+28]
    if (r0 == 0) goto L01c0d632
L01c0d622:
    r2 = r11 << 4
    r0 = r15
    r1 = r14
    call dsp_stage_copy  ; @call.xl
    r1 = 1
L01c0d632:
    r0 = r5 + 204  #
    [sp+20] = r1
    r2 = r10 + 348
    r1 = r10 + 364
    [sp+40] = r1
    [sp+124] = r4
    [sp+132] = r11
    [sp+52] = r2
    [sp+84] = r10
    [sp+100] = r0
    if (r4 == 0) goto L01c0d76a
    r0 = b[r0+79] (u)
    if (r0 == 0) goto L01c0d76a
    r4 = r14  #
    [sp+80] = r5
    r0 = [sp+40]
    r8 = b[r0+4] (u)
    r9 = 0  #
    r0 = h[r2+0] (u)
    r12 = [r7+40]
    r2 = r0 >> 8
    r13 = r0 & 0xFFFF00FF  #
    r5 = [r7+44]
    r1_r0 = 0
    [sp+112] = r8
    [sp+116] = r9
    [sp+128] = r1
L01c0d67a:
    r1 = [r4+0]
    r7 = r1 >>> 31
    r1 ^= r7
    r1 = r1 >>> 1
    ifs (r1 <= 0) {
    r1 = 0
    }
    r7 = [r4+8]
    r6 = r7 >>> 31
    r6 ^= r7  #
    r3 = [r4+16]
    r6 = r6 >>> 1
    r1 = smax(r6, r1)  #
    r7 = [r4+24]
    r6 = r3 >>> 31
    r3 ^= r6  #
    r6 = [r4+32]
    r3 = r3 >>> 1
    r1 = smax(r3, r1)
    r3 = r7 >>> 31
    r3 ^= r7  #
    r7 = [r4+40]
    r3 = r3 >>> 1
    r1 = smax(r3, r1)
    r3 = r6 >>> 31
    r3 ^= r6  #
    r6 = [r4+48]
    r3 = r3 >>> 1
    r1 = smax(r3, r1)
    r3 = r7 >>> 31
    r3 ^= r7
    r3 = r3 >>> 1
    r1 = smax(r3, r1)
    r3 = r6 >>> 31
    r7 = [++r4=56]
    r3 ^= r6
    r3 = r3 >>> 1
    r1 = smax(r3, r1)
    r3 = r7 >>> 31
    r3 ^= r7
    r3 = r3 >>> 1
    r8 = smax(r3, r1)
    if (r13 == 0) goto L01c0d6e8
    r13 = r13 + -1
    goto L01c0d738
L01c0d6e8:
    r13 = 0
    ifs (r8 <= 131072) goto L01c0d738
    r1 = r12
    r11_r10 = r15_r14
    r9 = r8 >>> 31
    r7_r6 = r9_r8
    r7_r6 <<= 4
    r1 = smax(r1, r5)
    r14 = [sp+112]
    r15 = [sp+116]
    r15_r14 = r1 * r14 (s)
    r1 = r6 - r14
    r3 = r7 - r15 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r1 |= r3
    if ((r1 & r6) != 0) {
    r1 = [sp+128]
    r1 = r1 | (1 << r0)
    [sp+128] = r1
    r13 = 120
    }
    r15_r14 = r11_r10
    r11 = [sp+132]
L01c0d738:
    r1 = smax(r8, r5)
    r2 = r2 + 1
    r5 = 0
    if (r2 <= 31) {
    r5 = r1
    } else {
    r2 = 0
    r12 = r1
    }
    r0 = r0 + 1
    r4 = r4 + 8
    if (r11 != r0) goto L01c0d67a
    r0 = [sp+88]
    [r0+40] = r12
    r7 = r0
    r0 = r2 << 8
    r0 = r0 | r13  #
    [r7+44] = r5
    r1 = [sp+52]
    h[r1+0] = r0
    r4 = [sp+124]
    r5 = [sp+80]
L01c0d76a:
    r0 = [r5+0]
    [sp+452] = r0
    r0 = 0x10000 - r4
    [sp+476] = r0
    r3 = 0
    [sp+504] = r3
    r0 = 0x40000000
    [sp+508] = r0
    r0 = 0x20000
    [sp+512] = r0
    r0 = [r7+24]
    r13 = [r7+32]
    r6 = r13 - r0
    r1 = r11 << 2
    r2 = 0x0 - r1
    r4 = sp + 448
    ifs (r6 < r2) goto L01c0d7ac
    ifs (r6 <= r1) goto L01c0d7b2
L01c0d7ac:
    r3 = r6 / r1 (s)
    r13 = r0
L01c0d7b2:
    [r4+44] = r3
    [sp+484] = r13
    r6 = [r7+28]
    r5 = sp + 448
    r0 = [sp+36]
    [sp+12] = r6
    if (r0 == 0) goto L01c0d7d0
    r0 = 0
    [sp+480] = r0
    [sp+488] = r0
    goto L01c0d7ee
L01c0d7d0:
    r3 = [r7+36]
    r4 = r3 - r6
    r0 = sp + 448
    ifs (r4 < r2) goto L01c0d7e2
    r2 = 0
    ifs (r4 <= r1) goto L01c0d7e8
L01c0d7e2:
    r2 = r4 / r1 (s)
    r3 = r6
L01c0d7e8:
    [r0+40] = r2
    [sp+480] = r3
L01c0d7ee:
    r11 = [r7+0]
    r1 = [sp+124]
    r2 = 0x0 - r1
    r0 = r5 + 36
    [sp+456] = r11
    r0 = 0
    [sp+460] = r0
    ifs (r1 >= 0) {
    r2 = r1
    }
    r0 = r2 * 0x60  #
    r6 = [r7+20]
    r3 = r0 + 0x200000
    ifs (r1 >= 0) {
    r3 = r6
    }
    r0 = r2 * 0xD8  #
    [sp+16] = r5
    [sp+96] = r14
    r5 = r3 + r0  #
    r1 = [r7+16]
    r0 = r6 - r1  #
    [sp+60] = r3
    r3 = r1 - r6  #
    [sp+44] = r1
    r1 = [sp+124]
    ifs (r1 >= 0) {
    r3 = r0
    }
    r0 = [r7+52]
    [sp+48] = r0
    r0 = [sp+40]
    r9 = b[r0+0] (u)
    r0 = [sp+100]
    r14 = h[++r0=62] (u)
    [sp+100] = r0
    r0 = h[r0+4] (u)
    [sp+104] = r0
    r4 = [sp+52]
    r8 = h[r4+4] (u)
    r12 = [r7+8]
    r10 = [r7+4]
    r7 = sp + 448
    r0 = [sp+44]
    r1 = [sp+124]
    ifs (r1 >= 0) {
    r0 = h[r4+8] (u)
    r0 *= r2
    r0 = r0 << 4
    r0 = r0 + r6
    }
    r4 = [sp+104]
    if (r4 != 0) {
    r1 = 0x40000000
    r1 = r1 / r4 (u)
    } else {
    r1 = 0
    }
    [sp+80] = r1
    [sp+24] = r7
    [sp+68] = r6
    r4 = r0 >>> 20
    if (r8 == 0) goto L01c0d8ce
    r6 = 0
    r0 = [sp+104]
    if (r0 == r8) goto L01c0d8d2
    r0 = [sp+104]
    r0 = r0 - r8  #
    r1 = [sp+80]
    r0 *= r1
    r1 = r0 >>> 31
    r0 ^= r1
    r0 = r0 >>> 1
    ifs (r0 <= 0) {
    r0 = 0
    }
    r6 = r0 << 1
    ifs (r6 >= 1073741824) {
    r6 = 0x40000000
    }
    r1_r0 = r6 * r6 (u)
    r1_r0 <<= 2
    r1_r0 >>>= 32
    r6 = 0x60000000 - r6
    r7_r6 = r0 * r6 (s)
    r7_r6 >>= 29
    goto L01c0d8d2
L01c0d8ce:
    r6 = 0x40000000
L01c0d8d2:
    r3 = r3 >>> 16
    r0 = r4 + 3
    [sp+108] = r0
    [sp+496] = r6
    r0 = [sp+124]
    if (r0 != 0) goto L01c0d8e2
    r9 = [sp+124]
L01c0d8e2:
    r0 = sp + 448
    [sp+112] = r0
    r0 = [sp+132]
    r7 = [sp+24]
    if (r0 == 0) goto L01c0dc2a
    [sp] = r5
    [sp+56] = r5
    r5 = [sp+124]
    ifs (r5 >= 0) {
    r0 = 0x200000
    [sp+56] = r0
    }
    r0 = 2
    r0 = r3 / r0 (s)
    r0 = r0 << 16
    r15 = r5 << 4  #
    [sp+8] = r0
    r11 = sp + 448
    r0 = 0xF4000000 - r5
    [sp+76] = r0
    r0 = r5 << 3
    [sp+72] = r0
    r0 = r2 << 4
    [sp+64] = r0
    r0 += -1
    [sp+32] = r0
    r0 = r3 << 16
    r1 = r0 + 0x4C0000
    r0 = r0 + 0x400000  #
    [sp+4] = r1
    [sp+28] = r0
    r6 = 0
    goto L01c0d9d6
L01c0d938:
    r7 = r8
    goto L01c0da88
L01c0d93c:
    r2 = [sp+60]
    if (r0 != 0) goto L01c0d942
    r2 = [sp+68]
L01c0d942:
    ifs (r10 <= r2) goto L01c0d94c
    r0 = r1
    r7 = r8
    goto L01c0da88
L01c0d94c:
    r1 = [sp+100]
    r1 = b[r1+13] (u)
    r4 = [sp+48]
    if (r1 == 0) goto L01c0d996
    r1 = [sp+88]
    r2 = [sp+48]
    r2 = r2 + 0x8000  #
    r1 = [r1+48]
    r4 = 4294901760
    r2 &= r4
    r2 = r2 + r1
    ifs (r2 <= r7) goto L01c0d980
    r1 = r7  #
    r4 = [sp+4]
    ifs (r2 > r4) {
    r1 = [sp+100]
    r2 = 0
    b[r1+24] = r2
    r1 = [sp+48]
    }
    goto L01c0d982
L01c0d980:
    r1 = r2
L01c0d982:
    r2 = [sp+48]
    r1 = r1 - r2
    r1 = r1 >>> 1
    r1 = r1 + r2  #
    r2 = [sp+8]
    r4 = r2
    ifs (r1 >= r2) {
    r4 = smin(r1, r7)
    }
L01c0d996:
    ifs (r5 <= -1) goto L01c0d9a6
    r2 = r10 - r4  #
    r1 = [sp+52]
    r7 = r8  #
    r1 = h[r1+8] (u)
    goto L01c0d9c8
L01c0d9a6:
    r2 = r4 + r10  #
    r1 = [sp+52]
    r7 = r8  #
    r1 = h[r1+8] (u)
    if (r0 == 0) goto L01c0d9c8
    r3 = r3 - 0x780000  #
    r7 = [sp]
    r3 = smax(r3, r7)  #
    r7 = [sp+24]
    ifs (r3 >= r2) goto L01c0d9c8
    r1 = 6
    r2 = r3
    goto L01c0da28
L01c0d9c8:
    if (r1 != 6) {
    [sp+48] = r4
    }
    if (r0 != 0) goto L01c0d9d2
    [sp+48] = r4
L01c0d9d2:
    if (r1 != 0) goto L01c0da28
    goto L01c0da88
L01c0d9d6:
    r0 = [sp+128]
    r0 = r0 & (1 << r6)
    if (r0 == 0) goto L01c0d9f2
    r1 = -1
    r14 = 3
    r9 = 1
    if (r8 <= 1) goto L01c0d9f2
    r8 = 1
    goto L01c0db30
L01c0d9f2:
    r1 = 1
    r0 = [sp+108]
    if (r14 >= r0) {
    r1 = 0
    }
    r0 = r5 >> 31
    r0 &= r1
    r2 = r14
    if (r2 >= 125) {
    r2 = 125
    }
    if (r8 != 0) goto L01c0da7e
    r3 = r2 << 20
    if (r9 == 0) goto L01c0dafe
    r1 = r3 - 0x80000  #
    r2 = [sp+56]
    r2 = smax(r1, r2)
    ifs (r5 < 0) {
    r1 = [sp+44]
    r2 = smin(r2, r1)
    }
    r1 = 6
L01c0da28:
    r4 = 0x7D00000 - r10
    r3 = r10 - 0x200000
    ifs (r5 >= 0) {
    r3 = r4
    }
    ifs (r3 >= 1) {
    r4 = [sp+64]
    r3 = r3 / r4 (s)
    } else {
    r3 = 1
    }
    r9 = 0  #
    r4 = [sp+112]
    [r4+48] = r9
    r4 = [sp+100]
    b[r4+13] = r9
    b[r4+12] = r9
    r4 = r2
    ifs (r2 >= 131072000) {
    r4 = 0x7D00000
    }
    r12 = 0x180000
    ifs (r2 >= 1572864) {
    r12 = r4
    }
    ifs (r3 <= 1) {
    r3 = 1
    }
    r8 = smin(r1, r3)
    r1 = 0x40000000
    r1 = r1 / r8 (s)
    [sp+80] = r1
    [sp+104] = r8
L01c0da7e:
    r1 = -1
    if (r8 == 1) goto L01c0dae0
    if (r8 != 0) goto L01c0dae6
L01c0da88:
    r1 = r6 + 1
    r2 = [sp+132]
    r13 = r2 - r6
    ifs (r1 > 31) goto L01c0daae
    r2 = [sp+128]
    r1 = r2 >> r1
    if (r1 == 0) goto L01c0daae
    r2 = 1
    if ((r1 & 1) != 0) goto L01c0daaa
L01c0daa2:
    r1 = r1 >> 1
    r2 = r2 + 1
    if ((r1 & 1) == 0) goto L01c0daa2
L01c0daaa:
    r13 = smin(r2, r13)
L01c0daae:
    if (r5 == 0) goto L01c0dbc4
    r1 = [sp+60]
    if (r0 != 0) goto L01c0dab8
    r1 = [sp+68]
L01c0dab8:
    ifs (r5 >= 0) {
    r1 = [sp+68]
    }
    r2 = r1 - r10
    r0 = r10 - r1
    ifs (r5 >= 0) {
    r0 = r2
    }
    ifs (r0 < 1) goto L01c0dbc0
    r1 = [sp+32]
    r0 = r0 + r1  #
    r1 = [sp+64]
    r0 = r0 / r1 (s)
    r13 = smin(r0, r13)
    goto L01c0dbc4
L01c0dae0:
    r8 = 1
    goto L01c0db30
L01c0dae6:
    r0 = r10 + r15
    ifs (r5 <= -1) goto L01c0db18
    r2 = 131727360
    ifs (r0 <= r2) goto L01c0db24
    r8 = 1
    goto L01c0db30
L01c0dafe:
    r8 = r7  #
    r7 = [sp+28]
    r9 = 0
    if (r5 == 0) goto L01c0d938
    ifs (r5 <= -1) goto L01c0d93c
    r1 = [sp+68]
    ifs (r10 >= r1) goto L01c0d94c
    r0 = 0
    r7 = r8
    goto L01c0da88
L01c0db18:
    ifs (r0 >= 1048576) goto L01c0db24
    r8 = 1
    goto L01c0db30
L01c0db24:
    r0 = [sp+104]
    r0 = r0 + 1
    r0 = r0 - r8  #
    r1 = [sp+80]
    r1 *= r0
L01c0db30:
    r3 = r10 - r12  #
    r2 = [sp+96]
    r0 = r6 << 6
    r0 = r0 + r2
    ifs (r3 < 0) goto L01c0db4e
    r4 = r1 >> 1
    r2 = 0x30000000
    ifs (r1 >= 0) {
    r2 = r4
    }
    r4 = r3 << 2
    goto L01c0db68
L01c0db4e:
    r2 = r1 >> 1
    r4 = 2147483647
    r4 ^= r2
    r2 = 0x50000000
    ifs (r1 >= 0) {
    r2 = r4
    }
    r1 = r3 << 2
    r4 = 0x0 - r1
L01c0db68:
    [sp+448] = r0
    r0 = 0
    [r11+16] = r0
    [r11+20] = r4
    r0 = r2 << 1
    r5 = r4 >>> 31
    r0 = r5 * r2  #
    [r7+12] = r0
    r3_r2 = r4 * r2 (u)
    r0 = r0 + r3
    r0 = r12 - r0
    [r11+24] = r0
    r13 = 1
    [r11+52] = r13
    r0 = sp + 448
    call effect_sample_processing_ring  ; @call.xl
    r12 += r15
    r8 = r8 + -1
    r6 = r6 + 1
    if (r8 == 0) goto L01c0dbb0
    r10 += r15
    goto L01c0dbbc
L01c0dbb0:
    r1 = 0x40000000  #
    r0 = [sp+112]
    r8 = 0  #
    [r0+48] = r1
    r10 = r12
L01c0dbbc:
    r5 = [sp+124]
    goto L01c0dc04
L01c0dbc0:
    r13 = 1
L01c0dbc4:
    r0 = r6 << 6
    r1 = [sp+96]
    r0 = r0 + r1
    [sp+448] = r0
    r1 = 0x40000000  #
    r0 = [sp+72]
    [r11+16] = r0
    [r11+20] = r1
    [r7+12] = 0x60000000
    r0 = [sp+76]
    r0 += r10
    [r11+24] = r0
    r0 = [sp+112]
    [r0+48] = r1
    [r11+52] = r13
    r0 = sp + 448
    call effect_sample_processing_ring  ; @call.xl
    r6 += r13
    r0 = r15 * r13
    r10 += r0
    r8 = 0
L01c0dc04:
    r0 = r13 + r14
    r1 = 65535
    r14 = umin(r0, r1)  #
    r0 = [sp+132]
    ifs (r0 > r6) goto L01c0d9d6
    r0 = [sp+16]
    r13 = [r0+36]
    r11 = [r7+8]
    r15 = L01c30a3c
L01c0dc2a:
    r0 = [sp+88]
    [r0+0] = r11
    [r0+24] = r13
    [r0+4] = r10
    [r0+8] = r12
    r5 = r0  #
    r0 = [sp+52]
    h[r0+4] = r8
    r1 = [sp+100]
    r0 = [sp+104]
    h[r1+4] = r0
    h[r1+0] = r14
    r0 = [sp+40]
    b[r0+0] = r9
    r0 = [sp+48]
    [r5+52] = r0
    r0 = 1
    b[r1+15] = r0
    r0 = [sp+36]
    if (r0 == 0) goto L01c0dcae
    r6 = [sp+84]
    r0 = r6  #
    r4 = [sp+96]
    r1 = r4  #
    r2 = [sp+92]
    call effect_type29_processing_filter29
    r0 = [r5+36]
    r1 = [sp+20]
    if (r1 == 0) goto L01c0dcb4
    r7 = [sp+12]
    if (r0 != r7) goto L01c0dcb8
    [sp+420] = r4
    [sp+424] = r15
    r0 = [sp+132]
    r0 = r0 << 4
    [sp+428] = r0
    [sp+432] = r15
    r0 = 0
    [sp+436] = r0
    r0 = 0x8000
    [sp+440] = r0
    r0 = r7 >>> 1
    [sp+444] = r0
    r0 = sp + 420
    call dsp_stage_mix  ; @call.xl
    goto L01c0dd9c
L01c0dcae:
    r7 = [sp+480]
    goto L01c0dd9a
L01c0dcb4:
    r7 = r0
    goto L01c0dd9c
L01c0dcb8:
    r1 = [sp+132]
    if (r1 == 0) goto L01c0dcd0
    r2 = r0 - r7
    r1 = r1 << 4
    r11 = r2 / r1 (s)
    r3 = r7 + r11
    r2 = r1 + -1
    r6 = 0
    goto L01c0dd58
L01c0dcd0:
    r7 = r0
    goto L01c0dd9c
L01c0dcd4:
    r5 = r7 >> 31
    r5 = r5 << 1
    r6 = r5 + r12
    goto L01c0dd1a
L01c0dcde:
    r6 = r0
    if (r4 != 1) {
    r6 = r1
    }
    r7 = [r14+0]
    r9_r8 = r7 * r6 (s)  #
    r5 = [sp+108]
    if (r5 == 0) goto L01c0dd04
    r6 = [sp+100]
    if (r4 != 1) {
    r6 = r3
    }
    r7 = [r13+0]
    r11_r10 = r7 * r6 (s)
    goto L01c0dd08
L01c0dd04:
    r10 = 0
    r11 = 0
L01c0dd08:
    r6 = r10 + r8
    r7 = r11 + r9 + c
    r7_r6 >>>= 16
    r5 = r6 >>> 31
    if (r7 != r5) goto L01c0dcd4
L01c0dd1a:
    [r14++=4] = r6
    r3 = r3 + r2
    r1 += r15
    r13 = r13 + 4
    if (--r4 != 0) goto L01c0dcde
L01c0dd2a:
    r1 = [sp+88]
    r0 = [sp+100]
    [r1+28] = r0
    r0 = [r1+32]
    [r1+24] = r0
    r0 = 1
    r1 = [sp+80]
    b[r1+77] = r0
    sp += 516
    {pc, r15-r4} = [sp++]
L01c0dd42:
    r5 = r9 >> 31
    r5 = r5 << 1
    r12 = r2
    r2 = 2147483647
    r8 = r5 + r2
    r2 = r12
    goto L01c0dd88
L01c0dd58:
    r7 = r0
    if (r2 != r6) {
    r7 = r3
    }
    r10 = r15
    r5 = [r10+r6<<2]
    r12 = [r4+r6<<2]
    r15_r14 = r5 * r7 (s)
    r15_r14 >>>= 16
    r13 = r12 >>> 31
    r8 = r14 + r12
    r9 = r15 + r13 + c
    r5 = r8 >>> 31
    r7 = r6 + 1
    if (r9 != r5) goto L01c0dd42
L01c0dd88:
    [r4+r6<<2] = r8
    r3 += r11  #
    r5 = [sp+88]
    r6 = r7
    r15 = r10
    ifs (r7 < r1) goto L01c0dd58
    r7 = r0
L01c0dd9a:
    r6 = [sp+84]
L01c0dd9c:
    [r5+28] = r7
    r0 = [sp+124]
    if (r0 == 0) goto L01c0dda8
    r0 = r6
    call effect_type29_processing_update29
L01c0dda8:
    sp += 516
    {pc, r15-r4} = [sp++]

; effect_type29_processing_process29: 0x01c0ddae..0x01c0deb6, module effect-type29-processing (process29)
.type effect_type29_processing_process29,@function
effect_type29_processing_process29:
    [--sp] = {rets, r15-r4}
    sp += -4
    r4 = r2
    r5 = r1
    r6 = r0
    r0 = r6 + 80
    if (r4 == 0) goto L01c0ddde
    r1 = [r0+4]
    if (r1 == 0) goto L01c0ddde
    if (r4 < 129) goto L01c0dde2
L01c0ddc6:
    r7 = r4
    if (r4 >= 128) {
    r7 = 128
    }
    r0 = r6
    r1 = r5
    r2 = r7
    call effect_type29_processing_process29
    r4 = r4 - r7
    r0 = r7 << 2
    r5 = r5 + r0
    if (r4 != 0) goto L01c0ddc6
L01c0ddde:
    sp += 4
    {pc, r15-r4} = [sp++]
L01c0dde2:
    r10 = r6 + 368
    r12 = b[r10+2] (u)
    r15 = h[r0+2] (s)
    r0 = r0 + 208
    r8 = r0 + 81
    if (r12 != 0) goto L01c0de0e
    r0 = b[r8+0] (u)
    if (r0 != r15) goto L01c0de0e
    r0 = r6
    r1 = r5
    r3 = r15
    call effect_type29_processing_engine29
    goto L01c0ddde
L01c0de0e:
    r7 = L01c31fac
    r0 = r7
    r1 = r5
    call dsp_stage_copy  ; @call.xl
    r11 = 1
    if (r12 != 0) {
    r11 = r12
    }
    [sp] = r8
    if (r11 > 4) goto L01c0de4a
    r3 = b[r8+0] (u)
    r0 = r6
    r1 = r5
    r2 = r4
    call effect_type29_processing_engine29
    r0 = 0x4 - r11
    r0 = r0 << 6
    r1 = 0x5 - r11
    r1 = r1 << 6
    goto L01c0de66
L01c0de4a:
    r0 = r6
    r1 = r5
    r2 = r4
    r3 = r15
    call effect_type29_processing_engine29
    r1 = r11 << 8
    r0 = r1 + -1024
    r0 = r0 >> 2
    r1 = r1 + -1280
    r1 = r1 >> 2
L01c0de66:
    r0 = r0 - r1
    r0 = r0 << 8
    r14 = r0 / r4 (s)
    r1 = r1 << 8
    r1 += r14
    r3 = 0
L01c0de74:
    r6 = [r5+0]
    r0 = r1 >>> 8
    r13_r12 = r6 * r0 (s)  #
    r2 = [r7++=4]
    r13_r12 -= r2 * r0 (s)
    r13_r12 >>= 8
    r8 = r12 + r2
    r9 = r13 + r3 + c
    [r5++=4] = r8
    r1 += r14
    if (--r4 != 0) goto L01c0de74
    if (r11 > 3) {
    r0 = [sp]
    b[r0+0] = r15
    }
    r1 = r11 + 1
    r0 = 0
    if (r11 != 8) {
    r0 = r1
    }
    b[r10+2] = r0
    sp += 4
    {pc, r15-r4} = [sp++]
