; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; block_gain: 5 functions, 0x01c01c92..0x01c01e5e

; block_gain_ramp: 0x01c01c92..0x01c01cf4, module block-gain (ramp)
.type block_gain_ramp,@function
block_gain_ramp:
    [--sp] = {rets, r15, r14, r12-r4}
    r8 = r3 << 1
    r9 = [sp+48]  ; @ld.w.sp.l
    r12 = 0
    r5_r4 = 0
    goto L01c01ce8
L01c01ca4:
    r7 = r1
    r6 = [++r7=r12]
    r10 = r3 + r2
    r6 = r6 >>> r9
    r11_r10 = r6 * r10 (s)  #
    r6 = [r7+4]
    r11_r10 >>= 23
    r7 = r0
    [++r7=r12] = r10
    r2 += r8
    r6 = r6 >>> r9
    r15_r14 = r6 * r2 (s)
    r15_r14 >>= 23
    [r7+4] = r14
    r6 = smin(r4, r10)
    r4 = smin(r6, r14)
    r6 = smax(r5, r10)
    r5 = smax(r6, r14)
    r12 = r12 + 8
L01c01ce8:
    if (r12 != 512) goto L01c01ca4
    r1_r0 = r5_r4
    {pc, r15, r14, r12-r4} = [sp++]

; block_gain_shift: 0x01c01cf4..0x01c01d52, module block-gain (shift)
.type block_gain_shift,@function
block_gain_shift:
    [--sp] = {rets, r12-r4}
    r12 = 0
    r10 = 0
    r8 = 0
    goto L01c01d46
L01c01cfe:
    r7 = r1
    r6 = [++r7=r12]
    r6 >>>= r2  #
    r4 = [r7+4]
    r9 = [r7+12]
    r5 = r0  #
    r7 = [r7+8]
    [++r5=r12] = r6
    r4 >>>= r2
    r7 >>>= r2  #
    [r5+4] = r4
    r3 = r9 >>> r2  #
    [r5+8] = r7
    r9 = smin(r7, r3)  #
    [r5+12] = r3
    r5 = smin(r6, r4)
    r5 = smin(r5, r9)
    r10 = smin(r10, r5)
    r3 = smax(r7, r3)
    r4 = smax(r6, r4)
    r3 = smax(r4, r3)
    r8 = smax(r8, r3)
    r12 = r12 + 16
L01c01d46:
    if (r12 != 512) goto L01c01cfe
    r11 = r8
    r1_r0 = r11_r10
    {pc, r12-r4} = [sp++]

; block_gain_scale: 0x01c01d52..0x01c01daa, module block-gain (scale)
.type block_gain_scale,@function
block_gain_scale:
    [--sp] = {rets, r15, r14, r12-r4}
    r8 = r2
    r9 = r2 >>> 31
    r2 = 0
    r12 = 0
    r6 = 0
    goto L01c01d9c
L01c01d64:
    r5 = r1
    r4 = [++r5=r2]
    r4 >>>= r3  #
    r5 = [r5+4]
    r11_r10 = r4 * r8 (s)
    r11_r10 >>= 16
    r4 = r0
    [++r4=r2] = r10
    r5 >>>= r3
    r15_r14 = r5 * r8 (s)
    r15_r14 >>= 16
    [r4+4] = r14
    r4 = smin(r10, r14)
    r6 = smin(r6, r4)
    r4 = smax(r10, r14)
    r12 = smax(r12, r4)
    r2 += 8  ; @add.ri.u5
L01c01d9c:
    if (r2 != 512) goto L01c01d64
    r7 = r12
    r1_r0 = r7_r6
    {pc, r15, r14, r12-r4} = [sp++]

; block_gain_clip: 0x01c01daa..0x01c01de4, module block-gain (clip)
.type block_gain_clip,@function
block_gain_clip:
    [--sp] = {rets, r7-r4}
    r2 = 0
    r3 = 8388607
    r4 = 4286578688
    r5 = r3 + 0xFF000000
    r1 = 0
    goto L01c01ddc
L01c01dc2:
    r7 = [r0+r2<<2]
    r6 = r3
    ifs (r7 >= 8388608) goto L01c01dd4
    r6 = r4
    ifs (r7 > r5) goto L01c01dda
L01c01dd4:
    [r0+r2<<2] = r6
    r1 += 1  ; @add.ri.u5
L01c01dda:
    r2 += 1  ; @add.ri.u5
L01c01ddc:
    if (r2 != 128) goto L01c01dc2
    r0 = r1
    {pc, r7-r4} = [sp++]

; block_gain_gain: 0x01c01de4..0x01c01e5e, module block-gain (gain)
.type block_gain_gain,@function
block_gain_gain:
    [--sp] = {rets, r8-r4}
    sp += -4
    r4 = r0  #
    r5 = [sp+28]
    if (r3 != r2) goto L01c01dfe
    if (r3 != 65536) goto L01c01e0a
    r2 = r5
    call block_gain_shift
    goto L01c01e10
L01c01dfe:
    r3 = r3 - r2  #
    [sp] = r5
    r2 = r2 << 7
    call block_gain_ramp
    goto L01c01e10
L01c01e0a:
    r2 = r3
    r3 = r5
    call block_gain_scale
L01c01e10:
    r7_r6 = r1_r0
    r5 = 4286578688
    r8 = L01c26890
    ifs (r6 < r5) goto L01c01e28
    ifs (r7 < 8388608) goto L01c01e42
L01c01e28:
    r0 = r4
    call block_gain_clip
    r1 = r8 + 4148
    [r1+0] += r0
    r6 = smax(r6, r5)
    r0 = 8388607
    r7 = smin(r7, r0)
L01c01e42:
    r1 = 1026
    r2 = [r8+r1<<2]
    r0 = 0x0 - r6
    r0 = smax(r7, r0)
    if (r0 > r2) {
    [r8+r1<<2] = r0
    }
    sp += 4
    {pc, r8-r4} = [sp++]
