; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; looper_engine: 1 function, 0x01c08f80..0x01c097b8

; looper_engine_looper_engine: 0x01c08f80..0x01c097b8, module looper-engine (looper_engine)
.type looper_engine_looper_engine,@function
looper_engine_looper_engine:
    [--sp] = {rets, r15-r4}
    sp += -148
    r6 = r0
    r11 = r6 + 84
    r12 = [r11+0]
    r8 = r2  #
    [sp+88] = r3
    r0 = 0
    if (r12 == 0) goto L01c095e8
    r5 = r6 + 288  #
    [sp+12] = r1
    r1 = [r5+4]
    [sp+76] = r1
    if (r1 == 0) goto L01c095e8
    r9 = [r5+36]
    if (r9 == 0) goto L01c095e8
    r0 = L01c32db0
    r0 = b[r0+10] (u)
    if (r0 == 0) goto L01c08fd2
    r0 = r6
    r1 = r8
    call delay_reader_reader
    r0 = [r5+4]
    [sp+76] = r0
    r9 = [r5+36]
    r12 = [r11+0]
L01c08fd2:
    r4 = r6 + 392  #
    r2 = [r5+0]
    r13 = r9  #
    r1 = [r4+20]
    r0 = [r5+20]
    [sp+84] = r0
    [sp+80] = r1
    [sp+144] = r1
    r0 = [sp+76]
    [sp+20] = r2
    if (r2 >= r0) {
    r13 = 0
    }
    r6 = [r4+16]
    r2 = [r5+16]
    [sp+56] = r2
    [sp+60] = r3
    r2 = [r5+12]
    [sp+48] = r2
    [sp+52] = r3
    r1 = [sp+88]
    if (r1 == 0) goto L01c0901e
    r2 = [r5+24]
    if (r2 == 0) goto L01c0901e
    r0 = [r5+8]
    if (r2 == 65536) goto L01c09020
    [sp+32] = r2
    [sp+36] = r3
    r1_r0 = r0 * r2 (s)
    r1_r0 >>= 16
    [sp+40] = r0
    [sp+44] = r1
    goto L01c0902c
L01c0901e:
    r0 = [r5+8]
L01c09020:
    [sp+40] = r0
    [sp+44] = r1
    r2 = 0x10000
    [sp+32] = r2
    [sp+36] = r3
L01c0902c:
    r3 = [r5+32]
    r0 = [sp+76]
    r0 = r0 << 12
    if (r3 == 0) goto L01c09040
    r1 = r9 << 12
    r1 = r1 + -8192
    if (r3 <= r1) goto L01c09042
L01c09040:
    r3 = r0
L01c09042:
    r2 = [r4+0]
    r14 = r2
    if (r2 != -1) goto L01c09062
    r1 = r9 + -1
    r2 = r3 + 2048
    r2 = r2 >> 12
    if (r2 >= r9) {
    r2 = r1
    }
    if (r2 != 0) goto L01c0905e
    r2 = 1
L01c0905e:
    r14 = r2  #
    [r4+0] = r2
L01c09062:
    [sp+24] = r3
    [sp+4] = r0
    [sp] = r5
    r2 = [r4+8]
    [sp+8] = r4
    r0 = [r4+4]
    r15 = r0  #
    [sp+96] = r2
    r2 |= r0  #
    r0 = [sp+76]
    r4 = [sp+20]
    r0 = r4 - r0
    if (r2 == 0) goto L01c090a0
    r10 = [sp+12]
    if (r14 >= r9) goto L01c09092
    r1 = [sp+96]
    if (r1 > 1024) goto L01c09092
    if (r15 == 0) goto L01c09092
    if (r15 < r9) goto L01c090a2
L01c09092:
    r1 = 0
    r15 = 0  #
    r2 = [sp+8]
    [r2+8] = r1
    [r2+4] = r1
    [sp+96] = r1
    goto L01c090a2
L01c090a0:
    r10 = [sp+12]
L01c090a2:
    r0 += r13
    r0 = r11 + 244  #
    [sp+16] = r0
    [sp+28] = r0
    r0 = 1
    r1 = [sp+96]
    if (r1 == 0) goto L01c090b4
    r0 = 0
L01c090b4:
    r11 = r10  #
    r1 = [sp+76]
    if (r15 != r1) goto L01c090ca
    if (r0 == 0) goto L01c090ca
    r15 = 0  #
    r0 = [sp+8]
    [r0+4] = r15
    r0 = [sp+4]
    [sp+24] = r0
L01c090ca:
    [sp+92] = r12
    r0 = [sp+96]
    if (r0 != 0) goto L01c090da
    if (r15 == 0) goto L01c09136
    r0 = [sp+76]
    if (r15 == r0) goto L01c09136
L01c090da:
    r0 = 0
    [sp+72] = r0
    r0 = 1
    r1 = [sp+96]
    if (r1 == 0) goto L01c090e6
    r0 = 0
L01c090e6:
    if (r8 == 0) goto L01c0912e
    r7 = r6 >>> 31
    r2 = [sp+48]
    r3 = [sp+52]
    r3 = r2 >>> 31
    [sp+48] = r2
    [sp+52] = r3
    r2 = [sp+40]
    r3 = [sp+44]
    r3 = r2 >>> 31
    [sp+40] = r2
    [sp+44] = r3
    r2 = [sp+32]
    r3 = [sp+36]
    r3 = r2 >>> 31
    [sp+32] = r2
    [sp+36] = r3
    r2 = [sp+56]
    r3 = [sp+60]
    r3 = r2 >>> 31
    [sp+56] = r2
    [sp+60] = r3
    r4 = r9
    r1 = r4 << 1
    r3_r2 = r7_r6
    r5 = r12
    r6 = r5 + r1
    r1 = 0
    r13_r12 = r3_r2  #
    [sp+72] = r1
    [sp+64] = r2
    [sp+68] = r3
    [sp+24] = r6
    r10 = [sp+20]
    goto L01c0939a
L01c0912e:
    r13_r12 = r7_r6  #
    r1 = [sp+20]
    r8 = [sp+80]
    goto L01c09544
L01c09136:
    r11 = [sp+4]
    r0 = [sp+24]
    if (r0 != r11) goto L01c09326
    if (r8 == 0) goto L01c09372
    r0 = r9 << 1
    r11 = r12 + r0
    r0 = r9 ^ 0xFFFFFFFF
    r0 = r8 ^ 0xFFFFFFFF  #
    [sp+96] = r0
    r10 = 0  #
    [sp+80] = r0
    r15 = sp + 104
    r2 = 0
    r0 = [sp+20]
    [sp+64] = r6
    [sp+68] = r7
L01c09166:
    r0 = r9 - r0  #
    [sp+20] = r0
    r14 = r2
    r1 = r8 - r2
    if (r1 >= 128) {
    r1 = 128
    }
    r13 = umin(r1, r0)
    if (r13 == 0) goto L01c091cc
    r0 = 0
    r1 = [sp+16]
L01c09184:
    r2 = r13 - r0
    r3 = r1 & 0xF
    r3 = 0x10 - r3
    r2 = umin(r3, r2)
    if (r2 == 0) goto L01c091bc
    r3 = r1 << 1
    r3 += r12
    r4 = r1 >> 4
    r7 = b[r11+r4] (u)
    r4 = r0 << 2
    r5 = L01c31c94
    r4 = r4 + r5
    r5 = 0
L01c091ac:
    r6 = h[r3+r5<<1] (s)
    r6 <<= r7
    [r4+r5<<2] = r6
    r5 = r5 + 1
    if (r5 < r2) goto L01c091ac
L01c091bc:
    r3 = r2 + r1
    r1 = 0
    if (r3 != r9) {
    r1 = r3
    }
    r0 = r0 + r2
    if (r0 < r13) goto L01c09184
L01c091cc:
    r4 = [sp+64]
    r5 = [sp+68]
    if (r4 == 0) goto L01c091ee
    r3 = sp + 144
    r0 = L01c31c94
    r1 = r13
    r2 = r4
    call sample_leaves_high_pass
    r4 = [sp+84]
    r5 = [sp+12]
    r6 = [sp+40]
    r7 = [sp+44]
    goto L01c0922c
L01c091ee:
    r0 = [sp+144]
    r4 = [sp+84]
    r5 = [sp+12]
    r6 = [sp+40]
    r7 = [sp+44]
    if (r0 == 0) goto L01c0922c
    if (r13 == 0) goto L01c0922a
    r1 = [sp+96]
    r2 = [sp+20]
    r1 = r1 + r2  #
    r2 = [sp+80]
    r2 += r14
    r1 = umax(r2, r1)
    r2 = -129
    r1 = umax(r1, r2)
    r1 = r1 + 1
    r2 = L01c31c94
L01c0921c:
    r3 = [r2+0]
    r3 = r3 - r0
    [r2++=4] = r3
    r3 = r0 >>> 9
    r1 = r1 + 1
    r0 = r0 - r3
    if (r1 != 0) goto L01c0921c
L01c0922a:
    [sp+144] = r0
L01c0922c:
    r0 = r14 << 2
    r0 = r0 + r5
    [sp+104] = r0
    r0 = L01c31c94
    [r15+4] = r0
    r0 = L01c31a84
    [r15+8] = r0
    [r15+12] = r13
    [r15+16] = r4
    [r15+20] = r10
    [r15+24] = r6
    r0 = [sp+48]
    r1 = [sp+52]
    [r15+28] = r0
    r0 = [sp+56]
    r1 = [sp+60]
    [r15+32] = r0
    r0 = [sp+32]
    r1 = [sp+36]
    [r15+36] = r0
    r0 = [sp+88]
    if (r0 == 0) goto L01c0927e
    r0 = sp + 104
    call blend_leaves_peak_blend  ; @call.xl
    goto L01c09286
L01c0927e:
    r0 = sp + 104
    call blend_leaves_level_blend  ; @call.xl
L01c09286:
    r5 = [sp+28]
    r0 = [r15+20]
    [sp+72] = r0
    r4 = [r15+16]
    r6 = L01c31a84
    if (r13 == 0) goto L01c092f0
    r7 = 0
    r12 = [sp+20]
L01c092a0:
    if ((r12 & 0xF) != 0) goto L01c092c6
    r0 = r13 - r7
    if (r0 < 16) goto L01c092c6
    r0 = r7 << 2
    r3 = r0 + r6  #
    r0 = [sp+92]
    r2 = r12 >> 4
    r1 = r9
    call effect_parameter_lifecycle_resource_encode_group
    r10 = r12 + 16
    r7 = r7 + 16
    goto L01c092ea
L01c092c6:
    r0 = [r6+r7<<2]
    r1 = r12 & 0xF
    [r5+r1<<2] = r0
    r10 = r12 + 1
    r7 = r7 + 1
    if (r1 != 15) goto L01c092ea
    r2 = r12 >> 4  #
    r0 = [sp+92]
    r1 = r9
    r3 = r5
    call effect_parameter_lifecycle_resource_encode_group
L01c092ea:
    r12 = r10
    if (r7 < r13) goto L01c092a0
L01c092f0:
    [sp+84] = r4
    r0 = [sp+16]
    r0 += r13
    r1 = 0
    r2 = 0
    if (r0 >= r9) {
    r2 = r9
    }
    r0 = r0 - r2
    [sp+16] = r0
    r0 = [sp+20]
    r0 += r13  #
    r3 = [sp+8]
    r6 = [sp+64]
    r7 = [sp+68]
    r12 = [sp+92]
    r10 = [sp+72]
    if (r0 != r9) {
    r1 = r0
    }
    r2 = r14
    r2 += r13
    r0 = r1
    if (r2 < r8) goto L01c09166
    r8 = [sp+144]
    goto L01c09564
L01c09326:
    if (r8 == 0) goto L01c09384
    r7 = r6 >>> 31
    r0 = [sp+48]
    r1 = [sp+52]
    r1 = r0 >>> 31
    [sp+48] = r0
    [sp+52] = r1
    r0 = [sp+32]
    r1 = [sp+36]
    r5 = r0 >>> 31
    r2 = [sp+40]
    r3 = [sp+44]
    r3 = r2 >>> 31
    [sp+40] = r2
    [sp+44] = r3
    r4 = r0
    [sp+96] = r4
    [sp+100] = r5
    r0 = [sp+56]
    r1 = [sp+60]
    r1 = r0 >>> 31
    [sp+56] = r0
    [sp+60] = r1
    r0 = r9 << 1
    r14 = r12 + r0
    r15 = 1073741823
    r0 = 0
    r13 = r9 << 12  #
    [sp+72] = r0
    [sp+64] = r6
    [sp+68] = r7
    goto L01c095f8
L01c09372:
    [sp+24] = r11
    r10 = 0  #
    r1 = [sp+20]
    r5 = [sp]
    r12 = [sp+32]
    r13 = [sp+36]
    r3 = [sp+8]
    r8 = [sp+80]
    goto L01c0956e
L01c09384:
    r10 = 0  #
    r5 = [sp]
    r8 = [sp+80]
    goto L01c097aa
L01c0938c:
    r0 = r7 >> 31
    r0 = r0 << 1
    r2 = 2147483647
    r6 = r0 + r2
    goto L01c09500
L01c0939a:
    r1 = [sp+76]
    if (r15 == r1) goto L01c093b0
    r0 ^= 1
    if ((r0 & 0x1) == 0) {
    r0 = 1024
    [sp+96] = r0
    r14 = r15
    r15 = [sp+76]
    }
L01c093b0:
    r1 = r10 + r4
    r0 = r1
    if (r10 >= r14) {
    r0 = r10
    }
    r9 = r8
    r0 = r0 - r14
    r2 = h[r5+r0<<1] (s)
    r0 = r0 >> 4
    r0 = b[r6+r0] (u)
    r0 = r2 << r0
    if (r10 >= r15) {
    r1 = r10
    }
    r1 = r1 - r15
    r2 = h[r5+r1<<1] (s)
    r1 = r1 >> 4
    r1 = b[r6+r1] (u)
    r1 = r2 << r1
    r1 = r1 - r0
    r8 = r4  #
    r2 = [sp+96]
    r2 = 0x400 - r2
    r3_r2 = r1 * r2 (s)
    r1 = 1024
    r3_r2 = r3_r2 / r1 (s)
    r0 = r0 + r2
    if (r12 == 0) goto L01c09418
    r4 = [sp+80]
    r1 = r0 - r4
    r3_r2 = r1 * r12 (s)
    r3_r2 >>= 31
    r4 = r4 + r2
    r0 = r0 - r4  #
    [sp+80] = r4
    goto L01c0942a
L01c09418:
    r2 = [sp+80]
    if (r2 != 0) {
    r0 = r0 - r2
    r1 = r2 >>> 9
    r2 = r2 - r1
    [sp+80] = r2
    } else {
    r1 = 0
    [sp+80] = r1
    }
L01c0942a:
    r2 = r11  #
    r4 = [sp+84]
    r6 = [sp+40]
    r7 = [sp+44]
    r1 = r0 - r4
    r12 = [r2+0]
    r2 = [sp+56]
    r3 = [sp+60]
    r3_r2 = r1 * r2 (s)
    r3_r2 >>= 16
    r4 = r4 + r2
    r13 = r12 >>> 31  #
    [sp+84] = r4
    r7_r6 = r4 * r6 (s)  #
    r1 = [sp+88]
    r3_r2 = r13_r12
    if (r1 != 0) goto L01c0945a
    r2 = 0
    r3 = 0
L01c0945a:
    r4 = [sp+32]
    r5 = [sp+36]
    r7_r6 += r2 * r4 (s)
    r7_r6 >>>= 16
    r1 = 1073741823
    r1 = r6 - r1
    r2 = 0
    r2 = r7 - r2 - !c
    r3 = psr
    r5 = sextra(r3, p:0, l:1)  #
    r4 = [sp+96]
    r3 = sextra(r3, p:3, l:1)
    r3 ^= r5
    r5 = r1 | r2
    r1 = r4 + -1
    r2 = ~r3
    if (r4 == 0) goto L01c09492
    [sp+96] = r1
L01c09492:
    r1 = 1073741823
    r4 = r8
    r8 = r9
    if ((r5 & r2) != 0) goto L01c094c8
    r1 = r6 - 0xC0000000
    r2 = -1
    r2 = r7 - r2 - !c
    r3 = psr
    r5 = sextra(r3, p:0, l:1)
    r3 = sextra(r3, p:3, l:1)
    r3 ^= r5
    r3 = ~r3
    r1 |= r2
    if ((r1 & r3) == 0) {
    r6 = 0xC0000000
    r7 = -1
    }
    r1 = r6
L01c094c8:
    r2 = [sp+88]
    if (r2 == 0) goto L01c094dc
    r2 = abs(r1)
    r3 = r2 >> 26
    if (r3 == 0) goto L01c094e6
    r3 = [sp+72]
    r3 = umax(r2, r3)
    goto L01c094e4
L01c094dc:
    r2 = r0 >>> 31
    r2 ^= r0  #
    r3 = [sp+72]
    r3 |= r2
L01c094e4:
    [sp+72] = r3
L01c094e6:
    r2 = [sp+48]
    r3 = [sp+52]
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 16
    r6 = r2 + r12
    r7 = r3 + r13 + c
    r0 = r6 >>> 31
    if (r7 != r0) goto L01c0938c
L01c09500:
    [r11++=4] = r6
    r0 = r10 & 0xF  #
    r3 = [sp+28]
    [r3+r0<<2] = r1
    r5 = [sp+92]
    r6 = [sp+24]
    if (r0 == 15) {
    r2 = r10 >> 4
    r0 = r5
    r1 = r4
    call effect_parameter_lifecycle_resource_encode_group
    }
    r1 = 0
    r0 = 1
    r12 = [sp+64]
    r13 = [sp+68]
    r2 = [sp+96]
    if (r2 == 0) goto L01c09530
    r0 = 0
L01c09530:
    r2 = r10 + 1
    if (r2 != r4) {
    r1 = r2
    }
    r10 = r1
    if (--r8 != 0) goto L01c0939a
    r8 = [sp+80]
    [sp+144] = r8
L01c09544:
    r2 = [sp+8]
    r3 = [sp+96]
    r3 = r2  #
    [r2+8] = r3
    [r3+0] = r14
    r2 = 0
    if (r0 != 0) goto L01c09556
    r2 = r15
L01c09556:
    r10 = [sp+72]
    r7_r6 = r13_r12  #
    r0 = [sp+76]
    if (r15 != r0) {
    r2 = r15
    }
    [r3+4] = r2
L01c09564:
    r11 = [sp+4]
    [sp+24] = r11
    r5 = [sp]
    r12 = [sp+32]
    r13 = [sp+36]
L01c0956e:
    [r5+0] = r1
    r0 = [sp+84]
    [r5+20] = r0
    if (r6 != 0) goto L01c09584
    r1 = r8 + 511
    r0 = 0
    if (r1 >= 1023) {
    r0 = r8
    }
    r8 = r0
L01c09584:
    [r3+20] = r8
    r0 = [sp+24]
    if (r0 == r11) {
    [r5+32] = r11
    }
    r0 = [sp+88]
    if (r0 == 0) goto L01c095e0
    if (r10 == 0) goto L01c095b6
    r0 = 62259
    r0 *= r12
    r1 = r10 >> 10
    r12 = r0 / r1 (u)
    ifs (r12 <= 1) {
    r12 = 1
    }
    r0 = 24
    goto L01c095da
L01c095b6:
    r0 = [r5+28]
    if (r0 == 0) goto L01c095be
    r0 += -1
    goto L01c095da
L01c095be:
    r0 = 0
    ifs (r12 >= 65536) goto L01c095da
    r1 = 0x10000 - r12
    r1 = r1 >>> 6
    r1 += r12
    r12 = r1 + 1
    ifs (r12 >= 65536) {
    r12 = 0x10000
    }
L01c095da:
    [r5+24] = r12
    [r5+28] = r0
L01c095e0:
    r0 = 0
    r1 = [sp+88]
    if (r1 != 0) goto L01c095e8
    r0 = r10
L01c095e8:
    sp += 148
    {pc, r15-r4} = [sp++]
L01c095ec:
    r0 = r7 >> 31
    r0 = r0 << 1
    r2 = r15 + 0x40000000
    r6 = r0 + r2
    goto L01c0976a
L01c095f8:
    r4 = [sp+24]
    r0 = r11 - r4
    r0 = r0 >>> 11
    if (r0 != 0) goto L01c09612
    r1 = -1
    if (r11 >= r4) {
    r1 = 0
    }
    r0 = 1
    if (r11 <= r4) {
    r0 = r1
    }
L01c09612:
    r2 = r0  #
    r1 = [sp+20]
    r1 = r1 << 12
    r1 += r13
    ifs (r0 <= -2048) {
    r2 = -2048
    }
    r3 = 2048
    ifs (r0 <= 2048) {
    r3 = r2
    }
    r4 = r4 + r3
    r0 = r1 - r4
    r1 = 0
    r2 = 0
    if (r0 >= r13) {
    r2 = r13
    }
    r2 = r0 - r2  #
    [sp+24] = r4
    r0 = r2 >> 16
    r0 = b[r14+r0] (u)
    r3 = r2 >> 12
    r4 = h[r12+r3<<1] (s)
    r0 = r4 << r0
    r3 = r3 + 1
    if (r3 != r9) {
    r1 = r3
    }
    r3 = h[r12+r1<<1] (s)
    r1 = r1 >> 4
    r1 = b[r14+r1] (u)
    r1 = r3 << r1
    r1 = r1 - r0
    r3 = 4095
    r2 &= r3
    r3_r2 = r2 * r1 (s)
    r3_r2 >>= 12
    r11 = r2 + r0
    if (r6 == 0) goto L01c09692
    r0 = [sp+80]
    r1 = r11 - r0
    r3_r2 = r1 * r6 (s)
    r3_r2 >>= 31
    r0 = r0 + r2
    r11 = r11 - r0  #
    [sp+80] = r0
    goto L01c096a4
L01c09692:
    r0 = [sp+80]
    if (r0 != 0) {
    r11 = r11 - r0
    r1 = r0 >>> 9
    r0 = r0 - r1
    } else {
    r0 = 0
    }
    [sp+80] = r0
L01c096a4:
    r12 = r10  #
    r0 = [sp+84]
    r6 = [sp+40]
    r7 = [sp+44]
    r1 = r11 - r0
    r2 = [r10+0]
    r4 = [sp+56]
    r5 = [sp+60]
    r5_r4 = r1 * r4 (s)
    r5_r4 >>= 16
    r0 = r0 + r4
    r3 = r2 >>> 31
    r7_r6 = r0 * r6 (s)  #
    [sp+84] = r0
    r5_r4 = r3_r2  #
    r0 = [sp+88]
    if (r0 != 0) goto L01c096d4
    r4 = 0
    r5 = 0
L01c096d4:
    r0 = [sp+96]
    r1 = [sp+100]
    r7_r6 += r4 * r0 (s)
    r7_r6 >>>= 16
    r10 = r15
    r1 = r6 - r10
    r0 = 0
    r4 = r7 - r0 - !c
    r5 = psr
    r0 = sextra(r5, p:0, l:1)
    r5 = sextra(r5, p:3, l:1)
    r0 ^= r5
    r0 = ~r0
    r4 |= r1
    r1 = r10
    if ((r4 & r0) != 0) goto L01c0972e
    r0 = r6 - 0xC0000000
    r1 = -1
    r1 = r7 - r1 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r0 |= r1
    if ((r0 & r4) == 0) {
    r6 = 0xC0000000
    r7 = r15 + 0xC0000000
    }
    r1 = r6
L01c0972e:
    r0 = [sp+88]
    if (r0 == 0) goto L01c09744
    r4 = abs(r1)
    r0 = r4 >> 26
    if (r0 == 0) goto L01c09752
    r0 = [sp+72]
    r0 = umax(r4, r0)
    [sp+72] = r0
    goto L01c09752
L01c09744:
    r0 = r11 >>> 31  #
    r4 = [sp+72]
    r0 = r0 ^ r11
    r4 |= r0
    [sp+72] = r4
L01c09752:
    r4 = [sp+48]
    r5 = [sp+52]
    r5_r4 = r11 * r4 (s)
    r5_r4 >>>= 16
    r6 = r4 + r2
    r7 = r5 + r3 + c
    r0 = r6 >>> 31
    if (r7 != r0) goto L01c095ec
L01c0976a:
    r10 = r12
    [r10++=4] = r6
    r4 = [sp+20]
    r0 = r4 & 0xF  #
    r3 = [sp+28]
    [r3+r0<<2] = r1
    r5 = [sp]
    r11 = [sp+4]
    r12 = [sp+92]
    if (r0 == 15) {
    r2 = r4 >> 4
    r0 = r12
    r1 = r9
    call effect_parameter_lifecycle_resource_encode_group
    }
    r0 = r4 + 1
    r1 = 0
    [sp+20] = r1
    r6 = [sp+64]
    r7 = [sp+68]
    if (r0 != r9) {
    [sp+20] = r0
    }
    if (--r8 != 0) goto L01c095f8
    r8 = [sp+80]
    [sp+144] = r8
    r10 = [sp+72]
L01c097aa:
    r0 = [sp+24]
    [r5+32] = r0
    r1 = [sp+20]
    r12 = [sp+32]
    r13 = [sp+36]
    r3 = [sp+8]
    goto L01c0956e
