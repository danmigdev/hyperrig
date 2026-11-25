; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; noise_gate: 1 function, 0x01c0767e..0x01c07986

; noise_gate_gate: 0x01c0767e..0x01c07986, module noise-gate (gate)
.type noise_gate_gate,@function
noise_gate_gate:
    [--sp] = {rets, r15-r4}
    sp += -124
    r4 = r0 + 352
    r5 = r0 + 288  #
    r3 = [r4+8]
    r9 = r1  #
    [sp+52] = r3
    r3 = [r4+4]
    [sp+108] = r3
    r3 = [r4+0]
    [sp+104] = r3
    r12 = [r5+60]
    r13 = [r5+48]
    r7 = [r5+44]
    r0 = [r5+40]
    [sp+88] = r0
    r14 = [r5+36]
    r0 = [r5+32]
    [sp+68] = r0
    r0 = [r5+28]
    [sp+48] = r0
    r0 = [r5+16]
    [sp+64] = r0
    r0 = [r5+12]
    [sp+36] = r0
    r0 = [r5+8]
    [sp+32] = r0
    r0 = [r5+4]
    [sp+60] = r0
    r15 = [r5+52]
    r0 = [r5+0]
    [sp+100] = r0
    r10 = [r5+24]
    [sp+80] = r10
    [sp+84] = r11
    r10 = [r5+20]
    [sp+16] = r10
    [sp+20] = r11
    [sp+112] = r15
    r6 = [r5+56]
    r0 = L01c1f7f0
    r8 = [r0+16]
    [sp+116] = r6
    r0 = 0
    [sp+120] = r0
    r3 = 1
    r1 = 1
    [sp+76] = r2
    if (r2 != 128) {
    r1 = 0
    }
    r0 = L01c32db0
    r0 = b[r0+0] (u)
    if (r0 != 0) goto L01c07706
    r3 = r0
L01c07706:
    r0 = sp + 112
    [sp+72] = r0
    r0 = [sp+76]
    if (r0 >= 16) goto L01c07714
    r1 = [sp+52]
    goto L01c07960
L01c07714:
    r0 = r1 & r3  #
    [sp+4] = r5
    [sp+8] = r4
    r0 = r8 + -20  #
    [sp+56] = r0
    r1 = 1
    r8 = 0  #
    [sp+28] = r1
    [sp+92] = r0
    if (r0 <= 34) {
    r0 = 0
    [sp+28] = r0
    }
    r0 = [sp+80]
    r1 = [sp+84]
    r1 = r0 >>> 31
    [sp+80] = r0
    [sp+84] = r1
    r0 = [sp+16]
    r1 = [sp+20]
    r1 = r0 >>> 31
    [sp+16] = r0
    [sp+20] = r1
    r10 = 16  #
    r0 = [sp+48]
    r0 = 0x10000 - r0
    r1 = r0 >>> 31
    [sp+40] = r0
    [sp+44] = r1
    r0 = [sp+100]
    r0 = r0 * 0x9
    r0 = r0 >> 16
    r0 = r0 + 1
    [sp+12] = r0
    r1 = 0
    r5 = [sp+88]
L01c07766:
    r3 = r7  #
    r0 = [sp+56]
    [sp+96] = r1
    if (r0 == 0) goto L01c07782
    r0 = L01c32db0
    r0 = r0 + 416  #
    r7 = [sp+104]
    r1 = [r0+r1<<2]
    r11 = [sp+108]
    goto L01c077b6
L01c07782:
    r1 = 0
    r11 = [sp+108]
    r7 = [sp+104]
    if (r8 >= r10) goto L01c077b6
    r2 = 0
L01c0778e:
    r0 = r9 + r2
    r6 = [r0+r8<<2]
    ifs (r6 > -1) goto L01c077ac
    r4 = 0x0 - r6
    r0 = 2147483647
    if (r6 != 2147483648) {
    r0 = r4
    }
    r6 = r0
L01c077ac:
    r2 = r2 + 4
    r1 = smax(r6, r1)
    if (r2 != 64) goto L01c0778e
L01c077b6:
    r0 = [sp+92]
    if (r0 > 34) goto L01c077d6
    r7 = r7 + 1
    r11 = smax(r1, r11)
    ifs (r7 > 44) {
    r0 = r11
    r11 = 0
    r7 = 0
    } else {
    r0 = [sp+52]
    }
    r2 = smax(r11, r0)  #
    [sp+52] = r0
    goto L01c077d8
L01c077d6:
    r2 = r1
L01c077d8:
    ifs (r2 >= r14) goto L01c077f0
    r6 = 1
    ifs (r7 <= 0) {
    r6 = 0
    }
    r0 = [sp+28]
    r0 &= r6
    if (r0 != 1) goto L01c077fa
    r7 += -1
    goto L01c07814
L01c077f0:
    r0 = [sp+92]
    if (r0 >= 35) {
    r7 = 45
    }
    goto L01c07816
L01c077fa:
    r0 = r2 - r14
    r2 = r12
    r4 = r13
    r12 = [sp+16]
    r13 = [sp+20]
    r13_r12 = r0 * r12 (s)
    r13_r12 >>= 16
    r14 += r12
    r13 = r4
    r12 = r2
L01c07814:
    r2 = r14
L01c07816:
    r0 = r1 - r5
    r14 = [sp+80]
    r15 = [sp+84]
    r1_r0 = r0 * r14 (s)
    r1_r0 >>= 16
    r5 = r5 + r0  #
    r1 = [sp+64]
    r0 = r5 >>> 2
    r14 = r2
    ifs (r2 >= r0) {
    r1 = [sp+36]
    }
    r2 = 0
    r0 = [sp+60]
    ifs (r14 >= r0) {
    r2 = r12
    }
    r4 = 1
    r0 = [sp+100]
    ifs (r14 <= r0) {
    r4 = r2
    }
    r2 = 0x10000
    if (r4 != 0) goto L01c0784e
    r2 = [sp+32]
L01c0784e:
    [sp+108] = r11
    r6 = r2 - r3  #
    [sp+104] = r7
    ifs (r2 >= r3) goto L01c0786a
    r0 = r13
    r13_r12 = r6 * r1 (s)
    r13_r12 >>= 16
    r7 = r12 + r3
    r13 = r0
    goto L01c07874
L01c0786a:
    r7 = r3 + 0x8000
    ifs (r6 <= 32768) {
    r7 = r2
    }
L01c07874:
    r0 = [sp+68]
    if (r0 == 0) goto L01c078ce
    r2 = 0
    r15 = r13  #
    r0 = [sp+100]
    [sp+88] = r5
    ifs (r14 <= r0) goto L01c0789a
    if (r4 == 0) goto L01c0789a
    r0 = [sp+100]
    r0 = r14 - r0  #
    r2 = [sp+12]
    r2 = r0 / r2 (u)
    if (r2 >= 65536) {
    r2 = 0x10000
    }
L01c0789a:
    r11 = r4
    r4 = [sp+40]
    r5 = [sp+44]
    r0 = r2 * r5
    r13_r12 = r2 * r4 (u)
    r13 += r0  #
    r0 = [sp+48]
    r13_r12 >>= 16
    r6 = r12 + r0
    r13 = r15
    ifs (r6 < r13) {
    r0 = r6 - r13
    r1_r0 = r0 * r1 (s)
    r1_r0 >>= 16
    r6 = r0 + r13
    }
    r5 = [sp+88]
    goto L01c078d4
L01c078ce:
    r11 = r4
    r6 = 0x10000
L01c078d4:
    if (r13 != 65536) goto L01c07900
    if (r3 != 65536) goto L01c07900
    if (r7 != 65536) goto L01c07900
    if (r6 != 65536) goto L01c07900
    r0 = r8 | 0xF  #
    r1 = [sp+72]
    r0 = [r9+r0<<2]
    r13 = 0x10000  #
    [r1+4] = r0
    [sp+112] = r0
    goto L01c0793e
L01c07900:
    r0 = r7 - r3
    r2 = r0 >>> 4
    ifs (r6 < 65536) goto L01c07928
    r0 = r8 | 0xF
    r4 = [r9+r0<<2]
    r0 = r8 << 2
    r0 += r9
    r1 = r3
    call effect_processing_ramp16  ; @call.xl
    r0 = [sp+72]
    [r0+4] = r4
    [sp+112] = r4
    goto L01c0793c
L01c07928:
    r0 = [sp+72]
    r0 = r8 << 2  #
    [r0+8] = r2
    r0 += r9
    r1 = sp + 112
    r2 = r6
    call noise_gate_filter  ; @call.xl
L01c0793c:
    r13 = r6
L01c0793e:
    r12 = r11  #
    r1 = [sp+96]
    r8 = r8 + 16  #
    r0 = [sp+76]
    r10 = r10 + 16
    r1 = r1 + 1
    if (r10 <= r0) goto L01c07766
    [sp+88] = r5
    r0 = [sp+72]
    r6 = [r0+4]
    r15 = [sp+112]
    r4 = [sp+8]
    r1 = [sp+52]
    r5 = [sp+4]
L01c07960:
    [r5+36] = r14
    r0 = [sp+88]
    [r5+40] = r0
    [r5+44] = r7
    [r5+48] = r13
    [r5+52] = r15
    [r5+56] = r6
    [r5+60] = r12
    r0 = [sp+104]
    [r4+0] = r0
    r0 = [sp+108]
    [r4+4] = r0
    [r4+8] = r1
    sp += 124
    {pc, r15-r4} = [sp++]
