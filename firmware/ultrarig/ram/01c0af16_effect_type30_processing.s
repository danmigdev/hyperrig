; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_type30_processing: 3 functions, 0x01c0af16..0x01c0b4b8

; effect_type30_processing_spectral30: 0x01c0af16..0x01c0b00e, module effect-type30-processing (spectral30)
.type effect_type30_processing_spectral30,@function
effect_type30_processing_spectral30:
    [--sp] = {rets, r7-r4}
    sp += -44
    r5_r4 = r1_r0
    if (r5 == 0) goto L01c0af2a
L01c0af1e:
    r0 = [r4+28]
    if (r0 != 0) goto L01c0aff8
    r0 = [r4+52]
    if (r5 == 0) goto L01c0af3a
    r1 = [r4+56]
    goto L01c0af5c
L01c0af2a:
    call ir_processing_wait  ; @call.xl
    if (r0 == 0) goto L01c0af1e
    [r4+28] = 0x1
    sp += 44
    {pc, r7-r4} = [sp++]
L01c0af3a:
    r2 = [r4+36]
    if (r2 == 0) goto L01c0af58
    r3 = 0
    r1 = r2
L01c0af42:
    r1 = r1 >> 1
    r3 = r3 + 1
    if (r1 != 0) goto L01c0af42
    r1 = 0
    ifs (r3 < 26) goto L01c0af5a
    r1 = -25
L01c0af50:
    r2 = r2 >> 1
    r1 = r1 + 1
    if (r2 != 0) goto L01c0af50
    goto L01c0af5a
L01c0af58:
    r1 = 0
L01c0af5a:
    [r4+56] = r1
L01c0af5c:
    if (r5 == 0) {
    r3 = 129
    r2 = 0
    } else {
    r3 = 128
    r2 = 129
    }
    r6 = r2 << 3
    r6 = r6 + r4
    r7 = 11168
    r7 = r7 + r6
    r7 = 13224  #
    [sp] = r7
    r7 = r7 + r6
    r7 = 9112  #
    [sp+4] = r7
    r6 = r6 + r7
    r6 = 18356  #
    [sp+8] = r6
    r6 = r6 + r4
    r6 = 17328  #
    [sp+12] = r6
    r6 = r6 + r4
    r7 = r2 << 2
    r6 = r6 + r7
    [sp+16] = r6
    [sp+20] = r3
    r3 = [r4+20]
    r6 = 1664525
    r3 *= r6
    r6 = 1013904223
    r3 = r3 + r6
    r3 = r3 >> 24
    r3 = r3 << 3
    r2 = r2 * 0x538
    r2 = r2 + r3
    r0 = 0x23 - r0  #
    [sp+24] = r2
    r2 = [r4+60]
    [sp+28] = r2
    [sp+32] = r0
    [sp+36] = r1
    r0 = sp + 0
    call effect_type30_processing_complex30  ; @call.xl
    r1 = 13220  #
    r0 = [sp+40]
    r2 = r4 + r1
    if (r5 == 0) goto L01c0affc
    r1 = 0
    r3 = 3819  #
    [r2++=4] = r1
    [r4+r3<<2] = r1
    r1 = [r4+48]
    r0 |= r1
    r3 = r4 + 7064  #
    [r4+36] = r0
    r0 = 512
    r1 = 1
    call ir_processing_start  ; @call.xl
L01c0aff8:
    sp += 44
    {pc, r7-r4} = [sp++]
L01c0affc:
    r1 = 2793
    r3 = 0
    [r4+r1<<2] = r3
    [r2+8] = r3
    [r4+48] = r0
    sp += 44
    {pc, r7-r4} = [sp++]

; effect_type30_processing_engine30: 0x01c0b00e..0x01c0b3b0, module effect-type30-processing (engine30)
.type effect_type30_processing_engine30,@function
effect_type30_processing_engine30:
    [--sp] = {rets, r15-r4}
    sp += -516
    r4 = r2
    r14 = r0
    r6 = r0 + 68
    r12 = r0 + 636
    r7 = r4 >> 1
    if (r3 == 0) goto L01c0b030
    r0 = r6 + 56
    call dsp_stage_copy  ; @call.xl
    goto L01c0b03e
L01c0b030:
    if (r4 == 0) goto L01c0b03e
    r0 = r6 + 56
    r1 = 0
L01c0b038:
    [r0++=4] = r1
    if (--r2 != 0) goto L01c0b038
L01c0b03e:
    r0 = r6 + 56
    r1 = sp + 260
    r2 = r7
    call effect_resampling_down4  ; @call.xl
    r0 = r4 << 2
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
    [r6+20] = r1
    r1 = [r0+24]
    [r6+24] = r1
    r1 = [r0+28]
    [r6+28] = r1
    r1 = [r0+32]
    [r6+32] = r1
    r1 = [r0+36]
    [r6+36] = r1
    r1 = [r0+40]
    [r6+40] = r1
    r1 = [r0+44]
    [r6+44] = r1
    r1 = [r0+48]
    [r6+48] = r1
    r0 = [r0+52]
    [r6+52] = r0
    r11 = L01c34198
    r1 = [r11+0]
    if (r1 == 0) goto L01c0b09c
    call r1
    r5 = r0
    goto L01c0b09e
L01c0b09c:
    r5 = 0
L01c0b09e:
    r0 = [r14+24]
    r6 = L01c34474
    if (r0 == 3) goto L01c0b0c8
    if (r0 == 2) goto L01c0b0dc
    if (r0 != 1) goto L01c0b19a
    r1 = 0
    r0 = r14
    call effect_type30_processing_spectral30
    [r14+24] = 0x2
    r1 = [r11+0]
    if (r1 != 0) goto L01c0b0ee
    goto L01c0b19a
L01c0b0c8:
    r0 = [r14+28]
    if (r0 != 0) goto L01c0b164
    call ir_processing_wait  ; @call.xl
    if (r0 == 0) goto L01c0b0fe
    [r14+28] = 0x1
    goto L01c0b164
L01c0b0dc:
    r1 = 1
    r0 = r14
    call effect_type30_processing_spectral30
    [r14+24] = 0x3
    r1 = [r11+0]
    if (r1 == 0) goto L01c0b19a
L01c0b0ee:
    call r1
    r1 = r0 - r5  #
    r2 = [r6+4]
    r5 = r0
    if (r1 > r2) {
    [r6+4] = r1
    }
    goto L01c0b19a
L01c0b0fe:
    r0 = [r14+28]
    if (r0 != 0) goto L01c0b164
    r0 = [r14+16]
    r1 = 15280
    r2 = r14 + r1
    r9 = 0x400 - r0
    r10 = r9
    if (r9 >= 512) {
    r10 = 512
    }
    r1 = [r14+56]
    r1 = r1 << 16
    r8 = r1 + 0x80000
    r3 = r10 | r8
    r0 = r0 << 2
    r0 += r14
    r0 = r0 + 2968
    r1 = r14 + 7064
    call effect_type30_processing_window_add30  ; @call.xl
    if (r9 > 511) goto L01c0b164
    r0 = 0x200 - r10
    r3 = r0 | r8
    r0 = r10 << 2
    r0 += r14
    r1 = 15280
    r2 = r0 + r1
    r1 = r0 + 7064
    r0 = r14 + 2968
    call effect_type30_processing_window_add30  ; @call.xl
L01c0b164:
    r0 = [r14+16]
    r0 = r0 + 256
    r1 = 1023
    r0 &= r1
    [r14+16] = r0
    r0 = [r14+20]
    r0 = r0 + 1
    [r14+20] = r0
    [r14+24] = 0x0
    r1 = [r11+0]
    if (r1 == 0) goto L01c0b19a
    call r1
    r3 = r6
    r1 = r0 - r5  #
    r2 = [r3+8]
    r5 = r0
    if (r1 > r2) {
    [r3+8] = r1
    }
L01c0b19a:
    [sp] = r5
    r0 = [r14+32]
    r2 = [r14+8]
    r13 = [r14+4]
    if (r7 == 0) goto L01c0b1ec
    r3 = r14 + 920
    r5 = sp + 260
    r15 = 4261412865
    r11 = 33554431
    r8 = 511
    r9 = r7
    r6 = r7
L01c0b1c6:
    r1 = [r5++=4]
    r10 = r1 >>> 2
    r1 = r11
    ifs (r10 < 33554432) {
    r1 = smax(r10, r15)
    }
    [r3+r2<<2] = r1
    r7 = r1 >>> 31
    r1 ^= r7
    r0 |= r1
    r1 = r2 + 1
    r2 = r1 & r8
    if (--r6 != 0) goto L01c0b1c6
    goto L01c0b1ee
L01c0b1ec:
    r9 = r7
L01c0b1ee:
    [r14+32] = r0
    r11 = r9
    r5 = r13 + r9
    [r14+8] = r2
    if (r5 <= 255) goto L01c0b23e
    r1 = [r14+20]
    r2 = r14 + 40
    r1 = r1 & 0x1
    [r2+r1<<2] = r0
    r6 = 0
    [r14+32] = r6
    r8 = L01c34198
    r1 = [r8+0]
    if (r1 == 0) goto L01c0b248
    call r1
    r9 = L01c34474
    r2 = [r9+12]
    r10 = r0  #
    r1 = [sp]
    r1 = r0 - r1
    if (r1 > r2) {
    [r9+12] = r1
    }
    goto L01c0b250
L01c0b23e:
    r10 = [sp]
    r9 = L01c34474
    goto L01c0b2f4
L01c0b248:
    r10 = [sp]
    r9 = L01c34474
L01c0b250:
    r0 = [r14+40]
    r1 = [r14+44]
    r0 |= r1
    if (r0 == 0) goto L01c0b262
L01c0b25c:
    r0 = r0 >> 1
    r6 = r6 + 1
    if (r0 != 0) goto L01c0b25c
L01c0b262:
    r0 = r6 + -17
    r1 = 0
    if (r6 <= 17) {
    r0 = 0
    }
    [r14+52] = r0
    [r14+28] = r1
    r5 = [r14+8]
    r6 = r0 << 16
    r7 = 0x200 - r5
    r3 = r7 | r6
    r13 = 15280
    r2 = r14 + r13
    r0 = r5 << 2
    r0 += r14
    r1 = r0 + 920
    r15 = r14 + 7064
    r0 = r15
    call effect_type29_processing_window29  ; @call.xl
    if (r7 > 511) goto L01c0b2be
    r3 = r5 | r6
    r0 = r7 << 2
    r0 += r14
    r2 = r0 + r13
    r0 = r0 + 7064
    r1 = r14 + 920
    call effect_type29_processing_window29  ; @call.xl
L01c0b2be:
    r0 = 9112
    r3 = r14 + r0
    r0 = 512
    r1 = 0
    r5 = 0
    r2 = r15
    call ir_processing_start  ; @call.xl
    [r14+24] = 0x1
    r1 = [r8+0]
    if (r1 == 0) goto L01c0b2f4
    call r1
    r2 = [r9+0]
    r1 = r0 - r10
    r10 = r0
    if (r1 > r2) {
    [r9+0] = r1
    }
L01c0b2f4:
    [r14+4] = r5
    if (r11 == 0) goto L01c0b338
    r1 = [r14+12]
    r0 = r14 + 2968
    r2 = sp + 4
    r3 = 0
    r5 = 1023
    r6 = r11
L01c0b30e:
    r7 = [r0+r1<<2]
    [r2++=4] = r7
    [r0+r1<<2] = r3
    r1 = r1 + 1
    r1 &= r5
    if (--r6 != 0) goto L01c0b30e
    [r14+12] = r1
    if (r11 == 0) goto L01c0b338
    r0 = r12 + 28
    r1 = sp + 4
    r2 = r11
L01c0b330:
    r3 = [r1++=4]
    [r0++=4] = r3
    if (--r2 != 0) goto L01c0b330
L01c0b338:
    r0 = r12 + 28
    r7 = L01c30e84
    r1 = r7
    r2 = r11
    call effect_resampling_up4  ; @call.xl
    r0 = r11 << 2
    r1 = [++r0=r12]
    [r12+0] = r1
    r1 = [r0+4]
    [r12+4] = r1
    r1 = [r0+8]
    [r12+8] = r1
    r1 = [r0+12]
    [r12+12] = r1
    r1 = [r0+16]
    [r12+16] = r1
    r1 = [r0+20]
    [r12+20] = r1
    r0 = [r0+24]
    [r12+24] = r0
    r2 = L01c34198
    r5 = 0
    if (r4 == 0) goto L01c0b392
L01c0b386:
    r0 = [r7++=4]
    r1 = r0 >>> 31
    r0 ^= r1
    r5 |= r0
    if (--r4 != 0) goto L01c0b386
L01c0b392:
    r1 = [r2+0]
    if (r1 == 0) goto L01c0b3a8
    call r1
    r1 = [r9+12]
    r0 = r0 - r10
    if (r0 > r1) {
    [r9+12] = r0
    }
L01c0b3a8:
    r0 = r5
    sp += 516
    {pc, r15-r4} = [sp++]

; effect_type30_processing_process30: 0x01c0b3b0..0x01c0b4b8, module effect-type30-processing (process30)
.type effect_type30_processing_process30,@function
effect_type30_processing_process30:
    [--sp] = {rets, r15-r4}
    sp += -4
    r6 = r3
    r4 = r1
    r5 = r0
    r0 = 0
    if (r2 != 128) goto L01c0b4b4
    r1 = [r5+84]
    if (r1 == 0) goto L01c0b4b4
    r3 = [r1+0]
    r2 = 1397904945
    if (r3 != r2) goto L01c0b4b4
    r2 = 128
    r0 = r1
    r1 = r4
    r3 = r6
    call effect_type30_processing_engine30
    r12 = [++r5=288]
    if (r6 != 0) {
    r1 = [r5+4]
    } else {
    r1 = 0x8000
    }
    r13 = r1 - r12
    r1 = 4
    r3 = r13 / r1 (s)
    r2 = r13 + 3
    if (r2 >= 7) {
    r13 = r3
    }
    r2 = r13 + r12  #
    [sp] = r0
    r0 = [r5+12]
    r8 = [r5+8]
    r11 = r0 - r8  #
    [r5+0] = r2
    r0 = r11 / r1 (s)
    r1 = r11 + 3
    if (r1 >= 7) {
    r11 = r0
    }
    r0 = r11 + r8
    [r5+8] = r0
    r9 = 2147483647
    r7 = 0
    r1 = 0
    r2 = 0
L01c0b432:
    r0 = L01c30e84
    r5 = [r0+r2<<2]
    r0 = r7 >>> 7
    r0 += r8
    r10 = [r4+r2<<2]
    r15_r14 = r5 * r0 (s)
    r0 = r1 >>> 7
    r0 += r12
    r15_r14 += r10 * r0 (s)
    r15_r14 >>>= 15
    r0 = r14 - r9
    r3 = 0
    r5 = r15 - r3 - !c
    r3 = psr
    r6 = sextra(r3, p:0, l:1)
    r3 = sextra(r3, p:3, l:1)
    r3 ^= r6
    r3 = ~r3
    r0 |= r5
    r5 = r9
    if ((r0 & r3) != 0) goto L01c0b4a4
    r0 = r9 + 2
    r0 = r14 - r0
    r3 = -1
    r3 = r15 - r3 - !c
    r5 = psr
    r6 = sextra(r5, p:0, l:1)
    r5 = sextra(r5, p:3, l:1)
    r5 ^= r6
    r5 = ~r5
    r0 |= r3
    if ((r0 & r5) == 0) {
    r14 = r9 + 2
    r15 = r9 + 0x80000000
    }
    r5 = r14
L01c0b4a4:
    [r4+r2<<2] = r5
    r7 += r11
    r2 = r2 + 1
    r1 += r13
    if (r2 != 128) goto L01c0b432
    r0 = [sp]
L01c0b4b4:
    sp += 4
    {pc, r15-r4} = [sp++]
