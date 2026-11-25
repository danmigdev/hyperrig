; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_sample_processing: 4 functions, 0x01c0b5d6..0x01c0be92

; effect_sample_processing_transition: 0x01c0b5d6..0x01c0ba14, module effect-sample-processing (transition)
.type effect_sample_processing_transition,@function
effect_sample_processing_transition:
    [--sp] = {rets, r15-r4}
    sp += -28
    r8 = r0 + 364
    r14 = [r8+0]
    r15 = [r8+4]
    r4 = 0
    r5 = 0
    r2 = r0 + 292
    [r2+72] = r4
    [r2+76] = r5
    r6 = [r8+8]
    r7 = [r8+12]
    [sp+8] = r6
    [sp+12] = r7
    [r2+80] = r4
    [r2+84] = r5
    r6 = [r8+16]
    r7 = [r8+20]
    [r2+88] = r4
    [r2+92] = r5
    r10 = [r8+24]
    r11 = [r8+28]
    r1 = 0
    [r8+28] = r1
    [r8+24] = r1
    r13 = r0 + 404
    b[r13+3] = r1
    r0 = 2
    b[r13+2] = r0
    r0 = b[r13+5] (u)
    if (r0 == 0) {
    r4 = r1 + 0x40000000
    } else {
    r4 = r1 + 0x400000
    }
    r1 = r10 - r4
    r1 = r11 - r5 - !c
    r1 = psr
    r3 = r1 >> 3
    r1 ^= r3
    if ((r1 & 0x1) != 0) goto L01c0ba10
    r9 = 2147483647
    r1 = 0
    r4 = r10 + r9
    r5 = r11 + r1 + c
    r3 = -2
    r3 = r4 - r3
    r1 = r5 - r1 - !c
    r4 = psr
    r3 |= r1
    r1 = sextra(r4, p:1, l:1)
    [sp+16] = r14
    [sp+20] = r15
    if (r0 == 0) {
    r12 = 0x44000000
    } else {
    r12 = 0x46000000
    }
    r14 = [r2+16]
    [sp+4] = r12
    if ((r1 & r3) != 0) goto L01c0b6a6
    r0 = itof(r10)
    r15 = -2
    goto L01c0b746
L01c0b6a6:
    r15 = r9
    r9 = r13
    r1_r0 = r11_r10
    r1_r0 >>>= 63
    r4 = r10 + r0
    r5 = r11 + r1 + c
    r13 = r5 ^ r1
    r12 = r4 ^ r0
    r3 = 0
    r0 = r12 - 0x80000000
    r0 = r13 - r3 - !c
    r0 = psr
    if ((r0 & 2) == 0) goto L01c0b718
    r0 = 0
L01c0b6d4:
    r1 = r12
    r4 = r13
    r13_r12 >>= 1
    r1 = r1 & 0x1
    r0 |= r1
    r3 = r3 + 1
    if (r4 != 0) goto L01c0b6d4
    r0 = r0 | r12
    r0 = itof(r0)
    if (r3 < 16) goto L01c0b728
    r1 = 0x47800000
    r4 = r3
    r13 = r9
    r12 = [sp+4]
L01c0b6fc:
    r4 += -16
    r0 = r0 * r1 (f)
    if (r4 > 15) goto L01c0b6fc
    r9 = r15
    if ((r3 & 0xF) == 0) goto L01c0b73c
    r3 = r3 & 0xF
    r15 = -2
    goto L01c0b732
L01c0b718:
    r0 = itof(r12)
    r13 = r9
    r9 = r15
    r15 = -2
    r12 = [sp+4]
    goto L01c0b740
L01c0b728:
    r13 = r9
    r9 = r15
    r15 = -2
    r12 = [sp+4]
L01c0b732:
    r0 = r0 + r0 (f)
    if (--r3 != 0) goto L01c0b732
    goto L01c0b740
L01c0b73c:
    r15 = -2
L01c0b740:
    ifs (r11 < 0) {
    r0 ^= 2147483648
    }
L01c0b746:
    r4 = [sp+16]
    r5 = [sp+20]
    r5_r4 >>>= 2
    r7_r6 >>>= 2
    r10 = r6 - r4
    [sp+16] = r4
    [sp+20] = r5
    r11 = r7 - r5 - !c
    r3 = 0
    r4 = r10 + r9
    r5 = r11 + r3 + c
    r1 = r4 - r15
    r4 = r5 - r3 - !c
    r5 = psr
    r1 |= r4
    r4 = sextra(r5, p:1, l:1)
    if ((r4 & r1) != 0) goto L01c0b788
    r3 = itof(r10)
    r4 = [sp+8]
    r5 = [sp+12]
    goto L01c0b83c
L01c0b788:
    r9 = r14
    [sp] = r13
    r5_r4 = r11_r10
    r5_r4 >>>= 63
    r14 = r10 + r4
    r15 = r11 + r5 + c
    r13 = r15 ^ r5
    r12 = r14 ^ r4
    r1 = r12 - 0x80000000
    r1 = r13 - r3 - !c
    r1 = psr
    if ((r1 & 2) == 0) goto L01c0b800
    r15 = 0
L01c0b7b4:
    r1 = r12
    r4 = r13
    r13_r12 >>= 1
    r1 = r1 & 0x1
    r3 |= r1
    r15 = r15 + 1
    if (r4 != 0) goto L01c0b7b4
    r1 = r12 | r3
    r3 = itof(r1)
    r14 = r9
    if (r15 < 16) goto L01c0b816
    r1 = 0x47800000
    r4 = r15
    r13 = [sp]
    r9 = 2147483647
    r12 = [sp+4]
L01c0b7e6:
    r4 += -16
    r3 = r3 * r1 (f)
    if (r4 > 15) goto L01c0b7e6
    if ((r15 & 0xF) == 0) goto L01c0b82e
    r15 = r15 & 0xF
    r4 = [sp+8]
    r5 = [sp+12]
    goto L01c0b824
L01c0b800:
    r3 = itof(r12)
    r13 = [sp]
    r14 = r9
    r4 = [sp+8]
    r5 = [sp+12]
    r9 = 2147483647
    r12 = [sp+4]
    goto L01c0b832
L01c0b816:
    r13 = [sp]
    r4 = [sp+8]
    r5 = [sp+12]
    r9 = 2147483647
    r12 = [sp+4]
L01c0b824:
    r3 = r3 + r3 (f)
    if (--r15 != 0) goto L01c0b824
    goto L01c0b832
L01c0b82e:
    r4 = [sp+8]
    r5 = [sp+12]
L01c0b832:
    ifs (r11 < 0) {
    r3 ^= 2147483648
    }
    r15 = -2
L01c0b83c:
    r12 = r12 * r0 (f)
    r5_r4 >>>= 2
    r5_r4 <<= 1
    r0 = r6 - r4
    r1 = r7 - r5 - !c
    r4 = [sp+16]
    r5 = [sp+20]
    r6 = r0 + r4
    r7 = r1 + r5 + c
    r4 = 0
    r0 = r6 + r9
    r1 = r7 + r4 + c
    r5 = r0 - r15
    r0 = r1 - r4 - !c
    r1 = psr
    r0 |= r5
    r1 = sextra(r1, p:1, l:1)
    r9 = r4 + 0x40800000
    if ((r1 & r0) != 0) goto L01c0b882
    r4 = itof(r6)
    goto L01c0b908
L01c0b882:
    r9 = r14
    r1_r0 = r7_r6
    r1_r0 >>>= 63
    r14 = r6 + r0
    r15 = r7 + r1 + c
    r11 = r15 ^ r1
    r10 = r14 ^ r0
    r0 = r10 - 0x80000000
    r0 = r11 - r4 - !c
    r0 = psr
    if ((r0 & 2) == 0) goto L01c0b8ea
    r5 = 0
L01c0b8ac:
    r1_r0 = r11_r10
    r11_r10 >>= 1
    r0 = r0 & 0x1
    r4 |= r0
    r5 = r5 + 1
    if (r1 != 0) goto L01c0b8ac
    r0 = r10 | r4
    r4 = itof(r0)
    r14 = r9
    if (r5 < 16) goto L01c0b8f6
    r1 = 0x47800000
    r0 = r5
    r9 = r1 + 0xF9000000
L01c0b8d4:
    r0 += -16
    r4 = r4 * r1 (f)
    if (r0 > 15) goto L01c0b8d4
    if ((r5 & 0xF) == 0) goto L01c0b902
    r5 = r5 & 0xF
    goto L01c0b8fa
L01c0b8ea:
    r4 = itof(r10)
    r14 = r9
    r9 = 0x40800000
    goto L01c0b902
L01c0b8f6:
    r9 = 0x40800000
L01c0b8fa:
    r4 = r4 + r4 (f)
    if (--r5 != 0) goto L01c0b8fa
L01c0b902:
    ifs (r7 < 0) {
    r4 ^= 2147483648
    }
L01c0b908:
    r5 = r14 + 0x10000
    r0 = r4 * r9 (f)
    r1 = 3114780076
    r4 = r12 * r1 (f)
    r1 = r3 * r9 (f)
    iff (r0 u>= r4) goto L01c0b930
    r3 = r9 + 0x7F800000
    r1 = r1 * r3 (f)
    r0 = r1 / r0 (f)
    goto L01c0b940
L01c0b930:
    r0 = 0
    iff (r1 u<= r0) {
    r0 = 3251109888
    } else {
    r0 = r9 + 0x1480000
    }
L01c0b940:
    r1 = r5 >> 17
    r4 = 3251109888
    iff (r0 u>= r4) {
    r4 = r0
    }
    r3 = r9 + 0x1480000
    iff (r0 u<= r3) {
    r3 = r4
    }
    r0 = utof(r1)  #
    r1 = [r2+36]
    r0 = r0 + r3 (f)
    r4 = r9 + 0x7800000
    r0 = r0 * r4 (f)
    r0 = ftoi(r0) (trunc)
    r4 = r2 + 36
    ifs (r0 >= r1) goto L01c0b980
    r0 = r2 + 40
    if (r14 != r1) goto L01c0b990
    goto L01c0b992
L01c0b980:
    r1 = r2
    r5 = [++r1=40]
    ifs (r0 <= r5) goto L01c0b994
    if (r14 != r5) {
    r4 = r1
    }
L01c0b990:
    r0 = r4
L01c0b992:
    r0 = [r0+0]
L01c0b994:
    r1 = r9 + 0x7E800000
    iff (r3 u<= r1) goto L01c0b9aa
    r1 = r1 + 0x80000000
    iff (r3 < r1) {
    r1 = 8
    b[r13+2] = r1
    }
L01c0b9aa:
    r4 = [r2+0]
    r3 = r4 ^ 0x80000000  #
    r5 = [r2+8]
    r1 = r4
    ifs (r5 <= 536870912) {
    r1 = r3
    }
    r3 = r1 ^ 0x80000000
    r5 = itof(r3)
    r3 = itof(r0)
    r6 = itof(r14)
    r6 = r6 / r3 (f)
    r5 = r6 * r5 (f)
    r5 = ftoi(r5) (trunc)
    r6 = r5 + 0xA000000
    if (r6 > 335544320) goto L01c0ba10
    r1 = r4 - r1
    r4 = r5 ^ 0x80000000
    r1 = r1 + r4
    [r2+0] = r1
    [r2+16] = r0
    r1 = [r2+28]
    r4 = r0 >>> 1
    r1 = r1 - r4
    [r2+12] = r1
    if (r0 == 0) goto L01c0ba0c
    r0 = [r8+36]
    r1 = r9 + 0x17000000
    r1 = r1 / r3 (f)
    r0 = r1 * r0 (f)
    r0 = ftoi(r0) (trunc)
    goto L01c0ba0e
L01c0ba0c:
    r0 = 0
L01c0ba0e:
    [r2+4] = r0
L01c0ba10:
    sp += 28
    {pc, r15-r4} = [sp++]

; effect_sample_processing_mixer: 0x01c0ba14..0x01c0bbce, module effect-sample-processing (mixer)
.type effect_sample_processing_mixer,@function
effect_sample_processing_mixer:
    [--sp] = {rets, r15-r4}
    sp += -44
    r14 = r0  #
    r5 = [sp+108]
    r8 = [sp+104]
    r10 = [sp+100]
    r4 = [sp+96]
    [sp+40] = r4
    [sp+36] = r2
    if (r5 == 0) goto L01c0ba44
    if (r5 != 2) goto L01c0ba68
    r0 = [sp+36]
    if (r0 == 0) goto L01c0bbca
    r6 = 0
    r9 = 92682
    r8 = 2147483647
    r5 = 0
    goto L01c0ba86
L01c0ba44:
    if (r2 == 0) goto L01c0bbca
    r4 = r8 - r10
    r5 = r4 >>> 31
    [sp] = r4
    [sp+4] = r5
    r9 = r8 >>> 31
    r11 = r10 >>> 31
    [sp+24] = r10
    [sp+28] = r11
    r5 = 0
    [sp+16] = r8
    [sp+20] = r9
    [sp+12] = r1
    goto L01c0bad8
L01c0ba68:
    r0 = [sp+36]
    if (r0 == 0) goto L01c0bbca
    r9 = r8 >>> 31
    r11 = r10 >>> 31
    r5 = 0
    goto L01c0bb6c
L01c0ba7a:
    r1 = r11 >> 31
    r1 = r1 << 1
    r10 = r1 + r8
    goto L01c0baac
L01c0ba86:
    if ((r5 & 0x3) != 0) goto L01c0ba98
    r1 = [sp+40]
    r3 = r3 + r1
    r7_r6 = r3 * r9 (s)
    r7_r6 >>= 16
L01c0ba98:
    r1 = [r14+r5<<2]
    r11_r10 = r1 * r6 (s)
    r11_r10 >>>= 16
    r1 = r10 >>> 31
    if (r11 != r1) goto L01c0ba7a
L01c0baac:
    [r14+r5<<2] = r10
    r5 = r5 + 1
    if (r0 != r5) goto L01c0ba86
    goto L01c0bbca
L01c0bab8:
    r4 = r13 >> 31
    r4 = r4 << 1
    r0 = 2147483647
    r12 = r4 + r0
    goto L01c0bb22
L01c0baca:
    r4 = r7 >> 31
    r4 = r4 << 1
    r0 = 2147483647
    r6 = r4 + r0
    goto L01c0bb46
L01c0bad8:
    r6 = [sp+40]
    if ((r5 & 0x3) != 0) {
    r6 = 0
    }
    r4 = [r1+r5<<2]
    r2 = r14
    r14 = [r2+r5<<2]
    r3 = r3 + r6
    r7_r6 = r4 * r3 (s)
    r7_r6 >>= 16
    r4 = r14 - r6
    r0 = [sp]
    r1 = [sp+4]
    r7_r6 = r4 * r0 (s)
    r11_r10 = r7_r6
    r0 = [sp+24]
    r1 = [sp+28]
    r11_r10 += r14 * r0 (s)
    r11_r10 >>>= 16
    r15 = r14 >>> 31
    r12 = r10 + r14
    r13 = r11 + r15 + c
    r4 = r12 >>> 31
    if (r13 != r4) goto L01c0bab8
L01c0bb22:
    r9_r8 = r14 * r8 (s)
    r10 = r8 - r6
    r11 = r9 - r7 - !c
    r11_r10 >>>= 16
    r6 = r10 + r14
    r7 = r11 + r15 + c
    r4 = r6 >>> 31
    [r2+r5<<2] = r12
    r14 = r2
    if (r7 != r4) goto L01c0baca
L01c0bb46:
    r1 = [sp+12]
    [r1+r5<<2] = r6
    r5 = r5 + 1
    r8 = [sp+16]
    r9 = [sp+20]
    r0 = [sp+36]
    if (r0 != r5) goto L01c0bad8
    goto L01c0bbca
L01c0bb5a:
    r4 = r15 >> 31
    r4 = r4 << 1
    r6 = 2147483647
    r14 = r4 + r6
    goto L01c0bbb8
L01c0bb6c:
    r6 = [sp+40]
    if ((r5 & 0x3) != 0) {
    r6 = 0
    }
    r7 = [r1+r5<<2]
    r3 = r3 + r6
    r12 = [r14+r5<<2]
    r7_r6 = r7 * r3 (s)
    r2 = r1
    r1 = L01c31c94
    r4 = [r1+r5<<2]
    r7_r6 >>= 16
    r6 = r12 - r6
    r7_r6 = r6 * r10 (s)
    r7_r6 += r4 * r8 (s)
    r7_r6 >>>= 16
    r13 = r12 >>> 31
    r1 = r14
    r14 = r6 + r12
    r15 = r7 + r13 + c
    r4 = r14 >>> 31
    if (r15 != r4) goto L01c0bb5a
L01c0bbb8:
    [r1+r5<<2] = r14
    [r2+r5<<2] = r12
    r5 = r5 + 1
    r14 = r1
    r1 = r2
    if (r0 != r5) goto L01c0bb6c
L01c0bbca:
    sp += 44
    {pc, r15-r4} = [sp++]

; effect_sample_processing_width: 0x01c0bbce..0x01c0bd8c, module effect-sample-processing (width)
.type effect_sample_processing_width,@function
effect_sample_processing_width:
    [--sp] = {rets, r15-r4}
    if (r0 == 0) goto L01c0bc98
    if (r1 == 0) goto L01c0bca0
    r1 = 0x64 - r0
    r1 = r1 << 16
    r8 = 100
    r5 = r1 / r8 (u)
    r11_r10 = r5 * r5 (u)
    r11_r10 >>= 16
    r1 = 4569
    r4 = r11 * r1
    r13_r12 = r10 * r1 (u)
    r13 += r4
    r13_r12 >>= 16
    r9 = 4294925390
    r6 = -1
    r14 = r12 + r9
    r15 = r13 + r6 + c
    r4 = r14 * r11
    r13_r12 = r14 * r10 (u)
    r4 += r13
    r7 = r15 * r10
    r13 = r4 + r7
    r13_r12 >>= 16
    r7 = r1 + 0x18000
    r14 = 0
    r10 = r12 + r7
    r11 = r13 + r14 + c
    r4 = r11 * r5
    r11_r10 = r10 * r5 (u)
    r11 += r4
    r11_r10 >>= 16
    r4 = r10 - 0x10000
    r0 = r0 << 16
    r0 = r0 / r8 (u)  #
    [r2+0] = r4
    r11_r10 = r0 * r0 (u)
    r11_r10 >>= 16
    r2 = r11 * r1
    r5_r4 = r10 * r1 (u)
    r5 = r5 + r2
    r5_r4 >>= 16
    r12 = r4 + r9
    r13 = r5 + r6 + c
    r1 = r12 * r11
    r9_r8 = r12 * r10 (u)
    r1 += r9
    r2 = r13 * r10
    r9 = r1 + r2
    r9_r8 >>= 16
    r4 = r8 + r7
    r5 = r9 + r14 + c
    r1 = r5 * r0
    r5_r4 = r4 * r0 (u)
    r5 = r5 + r1
    r5_r4 >>= 16
    [r3+0] = r4
    {pc, r15-r4} = [sp++]
L01c0bc98:
    r0 = 0
    [r3+0] = r0
    [r2+0] = r0
    {pc, r15-r4} = [sp++]
L01c0bca0:
    r1 = r0 << 13
    r1 = r1 + 0xC8000
    r4 = 25
    r5 = r1 / r4 (u)
    r11_r10 = r5 * r5 (u)
    r11_r10 >>= 16
    r1 = 4569
    r4 = r11 * r1
    r13_r12 = r10 * r1 (u)
    r13 += r4
    r13_r12 >>= 16
    r9 = 4294925390
    r8 = -1
    r14 = r12 + r9
    r15 = r13 + r8 + c
    r4 = r14 * r11
    r13_r12 = r14 * r10 (u)
    r4 += r13
    r7 = r15 * r10
    r13 = r4 + r7
    r13_r12 >>= 16
    r7 = r1 + 0x18000
    r6 = 0
    r10 = r12 + r7
    r11 = r13 + r6 + c
    r4 = r5 * r11
    r11_r10 = r5 * r10 (u)
    r11 += r4
    r11_r10 <<= 16
    r11_r10 >>>= 32
    r5 = 92682
    r11_r10 = r10 * r5 (s)
    r11_r10 >>= 16
    r4 = r10 - 0x10000
    r0 = 0x64 - r0  #
    [r2+0] = r4
    r0 = r0 << 13
    r2 = 25
    r0 = r0 / r2 (u)
    r11_r10 = r0 * r0 (u)
    r11_r10 >>= 16
    r2 = r11 * r1
    r13_r12 = r10 * r1 (u)
    r13 += r2
    r13_r12 >>= 16
    r14 = r12 + r9
    r15 = r13 + r8 + c
    r1 = r14 * r11
    r9_r8 = r14 * r10 (u)
    r1 += r9
    r2 = r15 * r10
    r9 = r1 + r2
    r9_r8 >>= 16
    r10 = r8 + r7
    r11 = r9 + r6 + c
    r2 = r0 * r11
    r1_r0 = r0 * r10 (u)
    r1 = r1 + r2
    r1_r0 <<= 16
    r1_r0 >>>= 32
    r1_r0 = r0 * r5 (s)
    r1_r0 >>= 16
    r0 = r0 - 0x10000
    [r3+0] = r0
    {pc, r15-r4} = [sp++]

; effect_sample_processing_update: 0x01c0bd8c..0x01c0be92, module effect-sample-processing (update)
.type effect_sample_processing_update,@function
effect_sample_processing_update:
    [--sp] = {rets, r12-r4}
    sp += -56
    r8 = r0 + 404
    r12 = b[r8+3] (u)
    r6 = r0 + 84
    r10 = r6 + 204
    r11 = r0 + 288
    r5 = r0 + 364
    if (r12 == 0) goto L01c0bdba
    r4 = b[r10+121] (u)
    r9 = r11 + 108  #
    r2 = [r5+32]
    r6 = [r6+0]
    goto L01c0bdf8
L01c0bdba:
    r9 = r11
    r0 = [r9++=108]
    r0 = r0 + 1983
    r4 = 2047
    r2 = r0 & r4
    r1 = r2  #
    [r5+32] = r2
    r6 = [r6+0]
    r0 = 0
    r7 = 40
L01c0bdd6:
    r3 = [r6+r1<<2]
    r1 = r1 + 2028
    r1 &= r4
    r3 = abs(r3)
    r0 = umax(r3, r0)
    if (--r7 != 0) goto L01c0bdd6
    r4 = 1
    if (r0 <= 33554432) {
    r4 = 0
    }
    b[r10+121] = r4
L01c0bdf8:
    r0 = r12 * 0x50  #
    [sp] = r6
    r1 = sample_correlation_weights
    r0 = r0 + r1
    r1 = 2047  #
    [sp+4] = r0
    r0 = r2 << 2
    [sp+8] = r0
    r0 = [r11+20]
    r0 = r0 + 0x10000
    r0 = r0 >> 17
    [sp+12] = r0
    r0 = 20
    r0 = r4.b0 (u)  #
    [sp+16] = r0
    r0 = r2 + 1648  #
    [sp+20] = r0
    r0 &= r1
    [r9+0] = r0
    r0 = sp + 0
    call effect_sample_processing_correlation  ; @call.xl
    r0 = [r5+0]
    r1 = [r5+4]
    r2 = [sp+24]
    r3 = [sp+28]
    r6 = r2 + r0
    r7 = r3 + r1 + c
    [r5+0] = r6
    [r5+4] = r7
    r0 = [r5+8]
    r1 = [r5+12]
    r2 = [sp+32]
    r3 = [sp+36]
    r6 = r2 + r0
    r7 = r3 + r1 + c
    [r5+8] = r6
    [r5+12] = r7
    r0 = [r5+16]
    r1 = [r5+20]
    r2 = [sp+40]
    r3 = [sp+44]
    r6 = r2 + r0
    r7 = r3 + r1 + c
    [r5+16] = r6
    [r5+20] = r7
    r0 = [r5+24]
    r1 = [r5+28]
    r2 = [sp+48]
    r3 = [sp+52]
    r6 = r2 + r0
    r7 = r3 + r1 + c
    [r5+24] = r6
    [r5+28] = r7
    r0 = b[r8+3] (u)
    r0 = r0 + 1
    b[r8+3] = r0
    r0 = 0
    b[r8+4] = r0
    sp += 56
    {pc, r12-r4} = [sp++]
