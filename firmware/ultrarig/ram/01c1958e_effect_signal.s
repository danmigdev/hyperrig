; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_signal: 2 functions, 0x01c1958e..0x01c19bee

; effect_signal_allpass: 0x01c1958e..0x01c19a8a, module effect-signal (allpass)
.type effect_signal_allpass,@function
effect_signal_allpass:
    [--sp] = {rets, r15-r4}
    sp += -12
    [sp] = r2
    r9 = r0
    r1 = r1 + 15
    r1 = r1 >> 4
    [sp+8] = r1
    r5 = [r2+8]
    r7 = [r2+12]
    r11 = [r2+20]
    r12 = [r2+36]
    r13 = [r2+40]
    r14 = [r2+44]
    r15 = [r2+48]
    r8 = 1
L01c195b8:
    r4 = [sp]
    r0 = [r4+4]
    r1 = [r4+0]
    r0 = r0 << 4
    r1 = r1 + r0
    [r4+0] = r1
    r0 = r1 >>> 31
    r0 ^= r1
    r1 = 0x40000000
    r0 = r0 - r1
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r1 = 0x40000000
    r0 = r0 + r1
    r2 = r0 >> 26
    r2 = r2 << 2
    r3 = r0 >> 10
    r3 = r3.l (u)
    r4 = [sp]
    r4 += 52
    r0 = [r4+r2]
    r2 = r2 + 4
    r1 = [r4+r2]
    r4 = r0
    r2 = r1 - r4
    r1_r0 = r2 * r3 (s)
    r1_r0 >>>= 16
    r0 = r0 + r4
    [sp+4] = r0
    r6 = r0 - r5
    r6 = r6 >>> 4
    r10 = 4
L01c19618:
    r4 = [r9+0]
    r5 = r5 + r6
    r4 = r4 >>> 1
    r1_r0 = r15 * r7 (s)
    r1_r0 >>>= 16
    r1_r0 += r4 * r8 (s)
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c1990a
L01c19634:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r12 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r11 * r8 (s)
    r11 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c19918
L01c19656:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r13 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r12 * r8 (s)
    r12 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c19926
L01c19678:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r14 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r13 * r8 (s)
    r13 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c19934
L01c1969a:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r15 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r14 * r8 (s)
    r14 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c19942
L01c196bc:
    r2 = r0
    r15 = r2
    r1_r0 = r4 * r8 (s)
    r1_r0 += r2 * r8 (s)
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c19950
L01c196d0:
    [r9+0] = r0
    r4 = [r9+4]
    r5 = r5 + r6
    r4 = r4 >>> 1
    r1_r0 = r15 * r7 (s)
    r1_r0 >>>= 16
    r1_r0 += r4 * r8 (s)
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c19960
L01c196f0:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r12 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r11 * r8 (s)
    r11 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1996e
L01c19712:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r13 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r12 * r8 (s)
    r12 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c1997c
L01c19734:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r14 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r13 * r8 (s)
    r13 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1998a
L01c19756:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r15 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r14 * r8 (s)
    r14 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c19998
L01c19778:
    r2 = r0
    r15 = r2
    r1_r0 = r4 * r8 (s)
    r1_r0 += r2 * r8 (s)
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c199a6
L01c1978c:
    [r9+4] = r0
    r4 = [r9+8]
    r5 = r5 + r6
    r4 = r4 >>> 1
    r1_r0 = r15 * r7 (s)
    r1_r0 >>>= 16
    r1_r0 += r4 * r8 (s)
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c199b6
L01c197ac:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r12 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r11 * r8 (s)
    r11 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c199c4
L01c197cc:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r13 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r12 * r8 (s)
    r12 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c199d2
L01c197ec:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r14 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r13 * r8 (s)
    r13 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c199e0
L01c1980c:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r15 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r14 * r8 (s)
    r14 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c199ee
L01c1982c:
    r2 = r0
    r15 = r2
    r1_r0 = r4 * r8 (s)
    r1_r0 += r2 * r8 (s)
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c199fc
L01c1983e:
    [r9+8] = r0
    r4 = [r9+12]
    r5 = r5 + r6
    r4 = r4 >>> 1
    r1_r0 = r15 * r7 (s)
    r1_r0 >>>= 16
    r1_r0 += r4 * r8 (s)
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c19a0c
L01c1985c:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r12 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r11 * r8 (s)
    r11 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c19a1a
L01c1987c:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r13 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r12 * r8 (s)
    r12 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c19a28
L01c1989c:
    r2 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r2 * r5 (s)
    r1_r0 -= r14 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r13 * r8 (s)
    r13 = r2
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c19a36
L01c198bc:
    r3 = r0
    r0 = 0x20000000
    r1 = 0
    r1_r0 += r3 * r5 (s)
    r1_r0 -= r15 * r5 (s)
    r1_r0 >>>= 30
    r1_r0 += r14 * r8 (s)
    r14 = r3
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c19a44
L01c198dc:
    r2 = r0
    r15 = r2
    r1_r0 = r4 * r8 (s)
    r1_r0 += r2 * r8 (s)
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c19a52
L01c198ee:
    [r9+12] = r0
    r9 = r9 + 16
    if (--r10 != 0) goto L01c19618
    r5 = [sp+4]
    r0 = [sp+8]
    r0 += -1
    [sp+8] = r0
    if (r0 != 0) goto L01c195b8
    goto L01c19a62
L01c1990a:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c19634
L01c19918:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c19656
L01c19926:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c19678
L01c19934:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c1969a
L01c19942:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c196bc
L01c19950:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c196d0
L01c19960:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c196f0
L01c1996e:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c19712
L01c1997c:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c19734
L01c1998a:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c19756
L01c19998:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c19778
L01c199a6:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1978c
L01c199b6:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c197ac
L01c199c4:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c197cc
L01c199d2:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c197ec
L01c199e0:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c1980c
L01c199ee:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c1982c
L01c199fc:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1983e
L01c19a0c:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c1985c
L01c19a1a:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c1987c
L01c19a28:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c1989c
L01c19a36:
    r3 = r1 >> 31
    r3 = r3 + r3
    r0 = 2147483647
    r0 = r0 + r3
    goto L01c198bc
L01c19a44:
    r2 = r1 >> 31
    r2 = r2 + r2
    r0 = 2147483647
    r0 = r0 + r2
    goto L01c198dc
L01c19a52:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c198ee
L01c19a62:
    r2 = [sp]
    [r2+8] = r5
    [r2+20] = r11
    [r2+24] = r12
    [r2+28] = r13
    [r2+32] = r14
    [r2+36] = r12
    [r2+40] = r13
    [r2+44] = r14
    [r2+48] = r15
    sp += 12
    {pc, r15-r4} = [sp++]

; effect_signal_gate: 0x01c19a8a..0x01c19bee, module effect-signal (gate)
.type effect_signal_gate,@function
effect_signal_gate:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r4 = r0
    r5 = r1 + 15
    r5 = r5 >> 4
    r10 = [r2+0]
    r11 = [r2+4]
    r8 = [r2+8]
    r9 = [r2+12]
    r12 = [r2+16]
    r6 = [r2+20]
    r7 = [r2+24]
    r13 = 0
    r0 = 0x8000
    ifs (r7 > r0) {
    r13 = 1
    }
L01c19abc:
    r14 = 0
    r0 = [r4+0]
    r1 = [r4+4]
    r2 = [r4+8]
    r3 = [r4+12]
    r0 = abs(r0)
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r14 = smax(r14, r0)
    r14 = smax(r14, r1)
    r14 = smax(r14, r2)
    r14 = smax(r14, r3)
    r0 = [r4+16]
    r1 = [r4+20]
    r2 = [r4+24]
    r3 = [r4+28]
    r0 = abs(r0)
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r14 = smax(r14, r0)
    r14 = smax(r14, r1)
    r14 = smax(r14, r2)
    r14 = smax(r14, r3)
    r0 = [r4+32]
    r1 = [r4+36]
    r2 = [r4+40]
    r3 = [r4+44]
    r0 = abs(r0)
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r14 = smax(r14, r0)
    r14 = smax(r14, r1)
    r14 = smax(r14, r2)
    r14 = smax(r14, r3)
    r0 = [r4+48]
    r1 = [r4+52]
    r2 = [r4+56]
    r3 = [r4+60]
    r0 = abs(r0)
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r14 = smax(r14, r0)
    r14 = smax(r14, r1)
    r14 = smax(r14, r2)
    r14 = smax(r14, r3)
    r0 = r14 - r6
    r1 = r9
    ifs (r14 > r6) {
    r1 = r8
    }
    r3_r2 = r0 * r1 (s)
    r3_r2 >>>= 16
    r6 = r6 + r2
    ifs (r6 < r11) {
    r13 = 0
    }
    ifs (r6 > r10) {
    r13 = 1
    }
    r0 = r13 << 16
    r0 = r0 - r7
    r3_r2 = r0 * r12 (s)
    r3_r2 >>>= 16
    r14 = r7 + r2
    r3 = 0x10000
    if (r7 != r3) goto L01c19ba6
    if (r14 != r3) goto L01c19ba6
    r7 = r14
    r4 += 64
    goto L01c19bde
L01c19ba6:
    r3 = r7 | r14
    if (r3 != 0) goto L01c19bbe
    r0 = 0
    r15 = r4
    r3 = 16
L01c19bb2:
    rep r3 {
    [r15++=4] = r0
    }
    if (r3 != 0) goto L01c19bb2
    r4 += 64
    goto L01c19bde
L01c19bbe:
    r2 = r14 - r7
    r2 = r2 >>> 4
    r15 = r4
    r3 = 16
L01c19bc8:
    rep r3 {
    r0 = [r4++=4]
    r7 = r7 + r2
    r1_r0 = r0 * r7 (s)
    r1_r0 >>>= 16
    [r15++=4] = r0
    }
    if (r3 != 0) goto L01c19bc8
    r7 = r14
L01c19bde:
    r5 += -1
    if (r5 != 0) goto L01c19abc
    r2 = [sp]
    [r2+20] = r6
    [r2+24] = r7
    sp += 4
    {pc, r15-r4} = [sp++]
