; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tap_oscillator: 1 function, 0x01c06cb8..0x01c06f3c

; tap_oscillator_tap_oscillator: 0x01c06cb8..0x01c06f3c, module tap-oscillator (tap_oscillator)
.type tap_oscillator_tap_oscillator,@function
tap_oscillator_tap_oscillator:
    [--sp] = {rets, r15-r4}
    sp += -88
    r4 = [sp+164]
    r8 = [r4+8]
    r10 = [r4+4]
    [sp+20] = r4
    r12 = [r4+0]
    r14 = [sp+168]
    if (r3 == 0) goto L01c06f28
    [sp+4] = r2
    r2 = [sp+172]
    [sp+48] = r2
    r9 = [sp+160]
    r2 = [sp+156]
    r2 = ~r3  #
    [sp+84] = r2
    r6 = [sp+152]
    r4 = [sp+144]
    r5 = [sp+148]
    r7 = [sp+140]
    [sp] = r2
    r2 = r6 << 4
    [sp+44] = r2
    r2 = r5 << 4
    [sp+40] = r2
    r6 = 0
    r2 = -17
    [sp+80] = r3
    [sp+36] = r9
L01c06cfc:
    [sp+24] = r14
    r5 = r6
    [sp+12] = r8
    [sp+16] = r10
    [sp+32] = r12
    r2 = r2 - r5  #
    [sp+28] = r5
L01c06d0a:
    r15 = r8  #
    [sp+56] = r2
    r8 = r12  #
    r2 = [sp+44]
    r4 = r4 + r2
    r2 = r4 >>> 31
    r2 ^= r4  #
    [sp+72] = r4
    r2 = r2 + 0xC0000000
    r5_r4 = r2 * r2 (s)
    r5_r4 >>= 30
    r3 = r4 >>> 1
    r3 = 0x60000000 - r3
    r5_r4 = r3 * r2 (s)
    r5_r4 >>= 30
    r3 = 0x0 - r4
    r2 = r6
    ifs (r9 >= 0) {
    r3 = r4
    }
    r5 = [sp+84]
    r4 = [r5+20]
    r13_r12 = r4 * r3 (s)  #
    r5 = [r5+16]
    r13_r12 >>= 30
    r14 = r12 + r5
    r3 = r14 - r15
    r3 = r3 >>> 4
    [sp+52] = r3
    r3 = [sp+40]
    r7 = r7 + r3
    r3 = r7 >>> 31
    r3 ^= r7  #
    [sp+68] = r7
    r3 = r3 + 0xC0000000
    r5_r4 = r3 * r3 (s)
    r5_r4 >>= 30
    r4 = r4 >>> 1
    r4 = 0x60000000 - r4
    r13_r12 = r4 * r3 (s)
    r13_r12 >>= 30
    r10 = 0x0 - r12
    ifs (r9 >= 0) {
    r10 = r12
    }
    r4 = [sp+84]
    r3 = [r4+4]
    r13_r12 = r3 * r10 (s)  #
    r6 = [r4+0]
    r13_r12 >>= 30
    r3 = r12 + r6
    r3 = r3 - r8  #
    [sp+64] = r3
    r9 = r3 >>> 4  #
    r5 = [r4+8]
    r13 = [r4+12]
    r11 = r10 >>> 31  #
    r3 = [sp+80]
    r4 = r2 + 16
    r12 = umin(r4, r3)  #
    [sp+60] = r4
    r3 = [sp+48]
    [sp+76] = r14
    if (r3 != 0) goto L01c06e30
    if (r2 >= r12) goto L01c06e18
    r7 = r8 + r9  #
    r4 = [sp+52]
    r3 = r15 + r4
    r3 = r3 << 1
    r6 = r4 << 1
    goto L01c06de8
L01c06dd2:
    r4 = r15 >> 31
    r4 = r4 << 1
    r8 = r5
    r5 = 2147483647
    r14 = r4 + r5
    r5 = r8
    goto L01c06e0a
L01c06de8:
    r4 = L01c30818
    r4 = [r4+r2<<2]
    r8 = [r1+r2<<2]
    r15_r14 = r4 * r3 (s)
    r15_r14 += r8 * r7 (s)
    r15_r14 >>>= 16
    r4 = r14 >>> 31
    if (r15 != r4) goto L01c06dd2
L01c06e0a:
    [r0+r2<<2] = r14
    r3 = r3 + r6
    r2 = r2 + 1
    r7 += r9
    if (r2 < r12) goto L01c06de8
L01c06e18:
    r2 = [sp+56]
    r2 += -16
    r8 = [sp+76]
    r3 = [sp+80]
    r9 = [sp+36]
    r4 = [sp+72]
    r7 = [sp+68]
    r12 = [sp+64]
    r6 = [sp+60]
    if (r6 < r3) goto L01c06d0a
    goto L01c06f1a
L01c06e30:
    r3_r2 = r13 * r10 (s)  #
    r7 = [sp+28]
    r3_r2 >>= 30
    r2 = r2 + r5
    [sp+8] = r2
    if (r7 >= r12) goto L01c06e90
    r5 = [sp+16]
    r2 = r2 - r5
    r6 = r2 >>> 4
    r2 = [sp+32]
    r13 = r2 + r9
    r3 = r7 << 2
    r2 = L01c30818
    r2 = r2 + r3
    r11 = r0 + r3  #
    [sp+32] = r2
    r2 = [sp]
    r4 = [sp+56]
    r4 = umax(r4, r2)
    r7 = r7 + r4
    r2 = r1 + r3
    [sp+56] = r2
    r2 = [sp+4]
    r12 = r2 + r3  #
    r2 = [sp+12]
    r4 = [sp+52]
    r3 = r2 + r4
    r10 = r3 << 1
    r5 = r5 + r6
    r5 = r5 << 1
    r8 = r7 + 1
    r2 = r4 << 1
    [sp+52] = r2
    r2 = r6 << 1
    [sp+28] = r2
    r14 = [sp+24]
    goto L01c06ea2
L01c06e90:
    r14 = [sp+24]
    goto L01c06f00
L01c06e94:
    r2 = r7 >> 31
    r2 = r2 << 1
    r4 = 2147483647
    r6 = r2 + r4
    goto L01c06eea
L01c06ea2:
    r6 = [r12++=4]
    r4 = r6 >>> 1
    r6 = r14 - r4
    r2 = 1450961768
    r7_r6 = r6 * r2 (s)
    r15_r14 = r7_r6
    r15_r14 >>= 31
    r14 += r4  #
    r4 = [sp+32]
    r7_r6 >>= 62  #
    r2 = [r4++=4]
    r6 = r6 & 0x1  #
    [sp+32] = r4
    r14 += r6  #
    r3 = [sp+56]
    r7_r6 = r2 * r10 (s)  #
    r4 = [r3++=4]
    r7_r6 += r4 * r13 (s)  #
    [sp+56] = r3
    r7_r6 += r14 * r5 (s)
    r7_r6 >>>= 16
    r2 = r6 >>> 31
    if (r7 != r2) goto L01c06e94
L01c06eea:
    [r11++=4] = r6
    r2 = [sp+52]
    r10 += r2  #
    r2 = [sp+28]
    r5 = r5 + r2
    r8 = r8 + 1
    r13 += r9
    if (r8 != 0) goto L01c06ea2
L01c06f00:
    r8 = [sp+76]
    r3 = [sp+80]
    r9 = [sp+36]
    r4 = [sp+72]
    r7 = [sp+68]
    r2 = -17
    r12 = [sp+64]
    r6 = [sp+60]
    r10 = [sp+8]
    if (r6 < r3) goto L01c06cfc
    goto L01c06f28
L01c06f1a:
    r1_r0 = r13 * r10 (s)
    r1_r0 >>= 30
    r10 = r0 + r5
    r14 = [sp+24]
L01c06f28:
    r0 = [sp+20]
    [r0+0] = r12
    [r0+4] = r10
    [r0+8] = r8
    r0 = r14
    sp += 88
    {pc, r15-r4} = [sp++]
