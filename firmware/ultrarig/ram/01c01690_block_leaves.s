; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; block_leaves: 6 functions, 0x01c01690..0x01c019d8

; block_leaves_meter: 0x01c01690..0x01c01722, module block-leaves (meter)
.type block_leaves_meter,@function
block_leaves_meter:
    [--sp] = {rets, r11-r4}
    r2 = 0
    r3 = 0
    r10 = 0
    r9_r8 = 0
    goto L01c016e4
L01c0169c:
    r6 = r0 + r10
    r7 = [r6+12]
    r1 = [r6+8]
    r11 = smin(r1, r7)  #
    r5 = [r6+4]
    r6 = [r6+0]
    r4 = smin(r6, r5)
    r4 = smin(r4, r11)
    r9 = smin(r9, r4)
    r11 = smax(r1, r7)
    r4 = smax(r6, r5)
    r4 = smax(r4, r11)
    r8 = smax(r8, r4)
    r4 = r6 >>> 8
    r3_r2 += r4 * r4 (s)
    r4 = r5 >>> 8
    r3_r2 += r4 * r4 (s)
    r1 = r1 >>> 8
    r3_r2 += r1 * r1 (s)
    r1 = r7 >>> 8
    r3_r2 += r1 * r1 (s)
    r10 = r10 + 16
L01c016e4:
    if (r10 != 512) goto L01c0169c
    r0 = 0x0 - r9
    if (r9 == 2147483648) {
    r0 = 2147483647
    }
    r4 = L01c26890
    r5 = [r4+284]
    r0 = smax(r8, r0)
    if (r0 > r5) {
    [r4+284] = r0
    }
    r0 = r4 + 1600
    r5_r4 = d[r0+0]
    r6 = r4 + r2
    r7 = r5 + r3 + c
    d[r0+0] = r7_r6
    {pc, r11-r4} = [sp++]

; block_leaves_shift: 0x01c01722..0x01c0174e, module block-leaves (shift)
.type block_leaves_shift,@function
block_leaves_shift:
    [--sp] = {rets, r6-r4}
    r2 = 0
    goto L01c01746
L01c01728:
    r3 = r0 + r2
    r4 = [r3+4]
    r4 >>>= r1  #
    r5 = [r3+12]
    r6 = [r3+8]
    [r3+0] >>>= r1
    r4 = r6 >>> r1  #
    [r3+4] = r4
    r4 = r5 >>> r1  #
    [r3+8] = r4
    [r3+12] = r4
    r2 += 16  ; @add.ri.u5
L01c01746:
    if (r2 != 512) goto L01c01728
    {pc, r6-r4} = [sp++]

; block_leaves_scale: 0x01c0174e..0x01c0179e, module block-leaves (scale)
.type block_leaves_scale,@function
block_leaves_scale:
    [--sp] = {rets, r11, r10, r8-r4}
    r10 = r1
    r11 = r1 >>> 31
    r1 = 0
    goto L01c01794
L01c0175c:
    r4 = r0
    r5 = [++r4=r1]
    r7_r6 = r5 * r10 (s)  #
    r5 = [r4+4]
    r7_r6 >>= 20  #
    r2 = [r4+8]
    r8 = [r4+12]
    r7_r6 = r5 * r10 (s)  #
    [r4+0] = r6
    r7_r6 >>= 20
    r3_r2 = r2 * r10 (s)  #
    [r4+4] = r6
    r3_r2 >>= 20
    r3_r2 = r8 * r10 (s)  #
    [r4+8] = r2
    r3_r2 >>= 20
    [r4+12] = r2
    r1 += 16  ; @add.ri.u5
L01c01794:
    if (r1 != 512) goto L01c0175c
    {pc, r11, r10, r8-r4} = [sp++]

; block_leaves_ramp: 0x01c0179e..0x01c01800, module block-leaves (ramp)
.type block_leaves_ramp,@function
block_leaves_ramp:
    [--sp] = {rets, r13-r4}
    r8 = r2 << 2
    r9 = r2 * 0x3
    r12 = r2 << 1
    r6 = 0
    goto L01c017f8
L01c017b0:
    r7 = r0
    r3 = [++r7=r6]
    r4 = r2 + r1
    r11_r10 = r3 * r4 (s)
    r11_r10 >>= 27
    r13 = [r7+12]
    r5_r4 = d[r7+4]
    [r7+0] = r10
    r3 = r12 + r1
    r11_r10 = r4 * r3 (s)
    r11_r10 >>= 27
    [r7+4] = r10
    r3 = r9 + r1
    r5_r4 = r5 * r3 (s)
    r5_r4 >>= 27
    r1 += r8  #
    [r7+8] = r4
    r5_r4 = r13 * r1 (s)
    r5_r4 >>= 27
    [r7+12] = r4
    r6 += 16  ; @add.ri.u5
L01c017f8:
    if (r6 != 512) goto L01c017b0
    {pc, r13-r4} = [sp++]

; block_leaves_glide: 0x01c01800..0x01c0198a, module block-leaves (glide)
.type block_leaves_glide,@function
block_leaves_glide:
    [--sp] = {rets, r15-r4}
    sp += -12
    r1 = 375
    r2 = L01c26890
    r13 = [r2+r1<<2]
    if (r13 == 0) goto L01c018f6
    r12 = r13
    if (r12 >= 128) {  ; @if.ge.ri.s12
    r12 = 128
    }
    r4 = r2 + 1664
    r9_r8 = d[r4+0]
    r2 = 0x800000
    r3 = 0
    d[sp] = r3_r2
    r7 = 2147483649
    r5 = 0
    goto L01c018c4
L01c0183c:
    r1 = L01c1f180
    r15_r14 = d[r1+196]
    r10 = r14 + r8
    r11 = r15 + r9 + c
    d[r1+196] = r11_r10
    r4 = [r0+r5<<2]
    r11_r10 <<= 16
    r11_r10 >>>= 32
    r15_r14 = d[sp]
    r15_r14 += r10 * r4 (s)
    r15_r14 >>>= 24
    r1 = 2147483647
    r6 = r1
    r4 = r14 - r6
    r1 = 0
    r2 = r15 - r1 - !c
    r3 = psr
    r1 = sextra(r3, p:0, l:1)
    r3 = sextra(r3, p:3, l:1)
    r1 ^= r3
    r1 = ~r1
    r2 |= r4
    r4 = r6
    if ((r2 & r1) != 0) goto L01c018be
    r1 = r14 - r7
    r2 = -1
    r2 = r15 - r2 - !c
    r3 = psr
    r4 = sextra(r3, p:0, l:1)
    r3 = sextra(r3, p:3, l:1)
    r3 ^= r4
    r3 = ~r3
    r1 |= r2
    if ((r1 & r3) == 0) {
    r14 = r6 + 2
    r15 = r6 + 0x80000000
    }
    r4 = r14
L01c018be:
    [r0+r5<<2] = r4
    r5 += 1  ; @add.ri.u5
L01c018c4:
    ifs (r5 < r12) goto L01c0183c
    r1 = r13 - r12
    r2 = 375
    r3 = L01c26890
    [r3+r2<<2] = r1
    if (r1 != 0) goto L01c018f0
    r1 = L01c1f180
    r2 = [r1+152]
    r3 = r2 >>> 31
    r3_r2 <<= 16
    d[r1+196] = r3_r2
L01c018f0:
    ifs (r12 <= 127) goto L01c018f8
    goto L01c01986
L01c018f6:
    r13 = 0
L01c018f8:
    r1 = L01c1f180
    r2 = [r1+152]
    if (r2 == 16777216) goto L01c01986
    r3 = r2 >>> 31
    r8 = 0x800000
    r9 = 0
    r14 = 2147483647
    r12 = 0
    r5 = r14 + 0x2  ; @add.modimm.rri
    r15 = 0xFFFFFFFF  ; @li.modimm
    goto L01c01982
L01c01922:
    r1 = [r0+r13<<2]
    r10 = r8
    r11 = 0
    r11_r10 += r1 * r2 (s)
    r11_r10 >>>= 24
    r1 = r10 - r14
    r6 = r11 - r12 - !c
    r7 = psr
    r4 = sextra(r7, p:0, l:1)
    r7 = sextra(r7, p:3, l:1)
    r4 ^= r7
    r4 = ~r4
    r1 |= r6
    r6 = r14
    if ((r1 & r4) != 0) goto L01c0197a
    r1 = r10 - r5
    r4 = r11 - r15 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r1 |= r4
    if ((r1 & r6) == 0) {
    r10 = r5 + 0x0  ; @add.modimm.rri
    r11 = r9 + 0xFFFFFFFF  ; @add.modimm.rri
    }
    r6 = r10
L01c0197a:
    [r0+r13<<2] = r6
    r13 = r13 + 1
L01c01982:
    ifs (r13 <= 127) goto L01c01922
L01c01986:
    sp += 12
    {pc, r15-r4} = [sp++]

; block_leaves_peak: 0x01c0198a..0x01c019d8, module block-leaves (peak)
.type block_leaves_peak,@function
block_leaves_peak:
    [--sp] = {rets, r9-r4}
    r3 = 0
    r9_r8 = 0
    goto L01c019be
L01c01992:
    r4 = r0 + r3
    r5 = [r4+12]
    r6 = [r4+8]
    {r7, r4} = [r4+]
    r1 = smin(r6, r5)
    r2 = smin(r4, r7)
    r1 = smin(r2, r1)
    r9 = smin(r9, r1)
    r1 = smax(r6, r5)
    r2 = smax(r4, r7)
    r1 = smax(r2, r1)
    r8 = smax(r8, r1)
    r3 += 16  ; @add.ri.u5
L01c019be:
    if (r3 != 512) goto L01c01992
    r0 = 0x0 - r9
    if (r9 == 2147483648) {
    r0 = 2147483647
    }
    r0 = smax(r8, r0)
    {pc, r9-r4} = [sp++]
