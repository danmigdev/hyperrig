; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_stage: 10 functions, 0x01c10818..0x01c11b00

; dsp_stage_clock: 0x01c10818..0x01c1082c, module dsp-stage (clock)
.type dsp_stage_clock,@function
dsp_stage_clock:
    [--sp] = rets
    r0 = L01c34198
    r0 = [r0+0]
    if (r0 == 0) goto L01c10828
    call r0
    pc = [sp++]
L01c10828:
    r0 = 0
    pc = [sp++]

; dsp_stage_stereo_prepare: 0x01c1082c..0x01c10968, module dsp-stage (stereo_prepare)
.type dsp_stage_stereo_prepare,@function
dsp_stage_stereo_prepare:
    [--sp] = {rets, r15-r4}
    r15 = L01c32db0
    r4 = b[r15+12] (u)
    r10 = r3
    r9 = r2
    r11 = r1
    r7 = r0
    r0 = r4 << 9
    r1 = L01c327ac
    r13 = r0 + r1
    r2 = b[r15+9] (u)
    r1_r0 = 0
    r12 = L01c1f7f0
    r5 = 0
    if (r2 == 0) goto L01c10892
    r1 = L01c34488
    r3 = b[r1+0] (u)
    r1 = 1
    if (r3 != 0) goto L01c1086a
    r1 = r3
L01c1086a:
    if (r3 != 0) goto L01c10890
    if (r2 == 0) goto L01c10890
    r2 = r7 * 0x3
    r2 += r11
    r2 += r15
    r2 = b[r2+192] (u)
    if (r2 == 0) goto L01c10890
    r2 = r15 + 256
    r3 = [r12+20]
    r2 = [r2+r11<<2]
    r3 += -1
    r5 = 1
    if (r2 == r3) goto L01c10892
L01c10890:
    r5 = 0
L01c10892:
    [r15+152] = r13
    [r15+156] = r0
    r0 = r1 | r5
    r1 = L01c32dac
    b[r1+0] = r0
    b[r1+1] = r0
    r1 = L01c32dae
    b[r1+0] = r5
    if (r0 != 1) goto L01c10966
    call dsp_stage_clock
    r8 = r0
    r14 = L01c341c4
    if (r5 == 0) goto L01c108cc
    r2 = 128
    r0 = r14
    r1 = r10
    call dsp_stage_copy  ; @call.xl
L01c108cc:
    r2 = 128
    r0 = r13
    r1 = r14
    call dsp_stage_copy  ; @call.xl
    r0 = r7 * 0x3
    r0 += r11
    r0 += r15
    r0 = b[r0+192] (u)
    if (r0 == 0) goto L01c10956
    r10 = r15 + 256
    r0 = [r10+r11<<2]
    r1 = [r12+20]
    if (r1 == r0) goto L01c10936
    r1 += -1
    if (r1 == r0) goto L01c10936
    r0 = r11 * 0x50
    r1 = L01c33320
    r0 = r0 + r1
    r4 = r0 + 220
    r0 = r11 << 8
    r1 = r7 * 0x300
    r0 = r0 + r1
    r1 = L01c2f3a0
    r0 = r0 + r1
    r7 = r0 + 20
    r6 = 0
L01c10922:
    r0 = r4 + r6
    r2 = 5
    r1 = r7
    call dsp_stage_copy  ; @call.xl
    r6 = r6 + 20
    r7 += 44
    if (r6 != 80) goto L01c10922
L01c10936:
    if (r5 != 0) goto L01c10940
    r0 = [r12+20]
    [r10+r11<<2] = r0
L01c10940:
    r0 = r13
    if (r9 != 1) {
    r0 = r14
    }
    [r15+144] = r0
    if (r9 != 1) {
    r14 = r13
    }
    [r15+148] = r14
L01c10956:
    call dsp_stage_clock
    [r15+160] = r0
    r0 = r0 - r8
    [r15+156] = r0
L01c10966:
    {pc, r15-r4} = [sp++]

; dsp_stage_swap: 0x01c10968..0x01c10984, module dsp-stage (swap)
.type dsp_stage_swap,@function
dsp_stage_swap:
    [--sp] = {rets, r4}
    r2 = 0
L01c1096c:
    r3 = [r1+r2<<2]
    r4 = [r0+r2<<2]
    [r0+r2<<2] = r3
    [r1+r2<<2] = r4
    r2 = r2 + 1
    if (r2 != 5) goto L01c1096c
    {pc, r4} = [sp++]

; dsp_stage_branch_filters: 0x01c10984..0x01c10a4a, module dsp-stage (branch_filters)
.type dsp_stage_branch_filters,@function
dsp_stage_branch_filters:
    [--sp] = {rets, r11-r4}
    r10 = [sp+36]
    r8 = r2
    r7 = r1
    r11 = r0
    r4 = 0
    r9 = r3 << 2
    r6 = r11
L01c10996:
    r0 = r7
    ifs (r4 >= 2) {
    r0 = r8
    }
    r1 = b[r6+41] (u)
    r0 += r9
    if (r1 == 0) goto L01c109b6
    if (r10 == 0) goto L01c109c4
    r1 = r10
    r2 = r6
    call biquad_residual  ; @call.xl
    goto L01c109c4
L01c109b6:
    if (r10 != 0) {
    r1 = r10
    r2 = r6
    call biquad_rounded  ; @call.xl
    }
L01c109c4:
    r4 = r4 + 1
    r6 += 44
    if (r4 != 4) goto L01c10996
    r8 = L01c32db0
    r5 = [r8+144]
    if (r5 == 0) goto L01c10a48
    r0 = L01c2f6a0
    r0 = r11 - r0
    r0 = r0 >>> 8
    r0 = r0 * 0x50
    r1 = L01c33320
    r0 = r0 + r1
    r6 = r0 + 220
    r4 = 0
    goto L01c10a04
L01c109f8:
    r5 = [r8+144]
    r4 = r4 + 1
    r6 = r6 + 20
    r11 = r11 + 44
L01c10a04:
    r7 = r11 + 20
    r0 = r7
    r1 = r6
    call dsp_stage_swap
    ifs (r4 >= 2) {
    r5 = [r8+148]
    }
    r1 = b[r11+41] (u)
    r0 = r5 + r9
    if (r1 == 0) goto L01c10a30
    if (r10 == 0) goto L01c10a3e
    r1 = r10
    r2 = r11
    call biquad_residual  ; @call.xl
    goto L01c10a3e
L01c10a30:
    if (r10 != 0) {
    r1 = r10
    r2 = r11
    call biquad_rounded  ; @call.xl
    }
L01c10a3e:
    r0 = r7
    r1 = r6
    call dsp_stage_swap
    if (r4 != 3) goto L01c109f8
L01c10a48:
    {pc, r11-r4} = [sp++]

; dsp_stage_branch_prepare: 0x01c10a4a..0x01c10b58, module dsp-stage (branch_prepare)
.type dsp_stage_branch_prepare,@function
dsp_stage_branch_prepare:
    [--sp] = {rets, r15-r4}
    sp += -16
    r10 = r3
    r14 = r2
    r8 = r1
    r9 = r0
    r7 = r1 << 8
    r1 = r0 * 0x300
    r0 = r8 << 1
    r2 = r9 * 0x6
    r0 = r0 + r2
    r12 = L01c32db0
    r4 = r0 + r12
    r0 = h[++r4=230] (u)
    r13 = [sp+68]
    r3 = r1 + r7
    r2 = L01c2f3a0
    r6 = r3 + r2
    if (r0 == 0) goto L01c10b18
    r1 = r1 + r2  #
    [sp+4] = r4
    r5 = r13 >> 2  #
    [sp+12] = r1
    r15 = 0  #
    [sp+8] = r5
L01c10a90:
    r4 = 0
    if (r0 == 0) goto L01c10aec
    r9 = r6  #
    r1 = [sp+12]
    r8 = r13
    r13 = r10
    r10 = 0
    r12 = r1
    r4 = r1
L01c10aa2:
    r5 = 5
    r2 = r12
    r3 = r4
L01c10aa8:
    r1 = [r7+r2]
    if (r0 != 1) {
    r6 = r7 + r3
    r6 = [r6+216]
    r11 = r6 + r1
    } else {
    r1 = r7 + r3
    r11 = [r1+176]
    }
    r1 = r7
    [++r1=r2] = r11
    [r1+44] = r11
    r2 = r2 + 4
    r3 = r3 + 4
    if (--r5 != 0) goto L01c10aa8
    r12 = r12 + 88
    r10 = r10 + 1
    r4 = r4 + 20
    if (r10 != 2) goto L01c10aa2
    r4 = r0 + -1  #
    r5 = [sp+8]
    r10 = r13
    r13 = r8
    r6 = r9
L01c10aec:
    r3 = r15 * r5
    r0 = r13 - r3
    if (r15 != 3) {
    r0 = r5
    }
    r0 = r6  #
    [sp] = r0
    r1 = r14
    r2 = r10
    call dsp_stage_branch_filters
    r15 = r15 + 1
    r0 = r4
    if (r15 != 4) goto L01c10a90
    r0 = [sp+4]
    h[r0+0] = r4
    sp += 16
    {pc, r15-r4} = [sp++]
L01c10b18:
    r3 = 0
    [sp] = r13
    r0 = r6
    r1 = r14
    r2 = r10
    call dsp_stage_branch_filters
    r0 = r9 * 0x3
    r0 += r8
    r0 += r12
    r2 = r0
    r1 = b[++r2=198] (u)
    if (r1 == 0) goto L01c10b54
    r3 = r1 + 255
    b[r2+0] = r3
    if (r1 != 1) goto L01c10b54
    r1 = 0
    b[r0+192] = r1
    r0 = r9 * 0xC
    r0 += r12
    r0 = r0 + 392
    [r0+r8<<2] = r1
L01c10b54:
    sp += 16
    {pc, r15-r4} = [sp++]

; dsp_stage_mix_ramp: 0x01c10b58..0x01c10cac, module dsp-stage (mix_ramp)
.type dsp_stage_mix_ramp,@function
dsp_stage_mix_ramp:
    [--sp] = {rets, r15-r4}
    sp += -64
    [sp+20] = r2
    [sp+24] = r3
    r4 = r3 << 3
    r3 = r2 * 0x18
    r2 = r3 + r4
    r3 = L01c32fa0
    r4 = r2
    r6 = [++r4=r3]
    r7 = r0  #
    [sp+12] = r4
    r4 = [sp+116]
    r0 = r2 + r3  #
    [sp+16] = r4
    if (r4 != 1) goto L01c10b8c
    r3 = [r0+4]
    r2 = [r0+48]
    [sp+32] = r3
    r3 = [r0+52]
    goto L01c10b9c
L01c10b8c:
    r3 = [r0+4]
    r4 = [r0+96]
    r2 = [r0+100]
    r3 = r3 + r2  #
    [sp+32] = r3
    r2 = r4 + r6
L01c10b9c:
    r0 = r0 + 4
    r15 = 0  #
    [sp] = r0
    [sp+4] = r3
    r0 = [sp+32]
    r0 = r3 - r0  #
    r3 = [r7+16]
    r14 = r0 & 0x3
    r9 = r0 >>> 2  #
    r0 = [r7+8]
    r2 = r2 - r6  #
    [sp+8] = r2
    r8 = r2 & 0x3  #
    [sp+28] = r1
    r5 = r2 >>> 2
    r10 = r3 + r0
    r12 = r10 >> 2
    r13 = sp + 36
    r11 = r1 & 0x1
L01c10bd0:
    r0 = r15 * r12
    r2 = r0 + r12
    r1 = r10
    if (r15 != 3) {
    r1 = r2
    }
    if (r1 <= r0) goto L01c10c10
    r2 = [r7+0]
    r3 = r0 << 2
    r2 = r2 + r3
    [sp+36] = r2
    r2 = [r7+8]
    if (r0 >= r2) goto L01c10c1a
    r2 = umin(r1, r2)  #
    r4 = [r7+4]
    r3 = r3 + r4
    [r13+4] = r3
    r2 = r2 - r0
    [r13+8] = r2
    r0 = r1 - r0  #
    r3 = [r7+12]
    [r13+12] = r3
    r0 = r0 - r2
    goto L01c10c32
L01c10c10:
    r15 = r15 + 1
    if (r15 != 4) goto L01c10bd0
    goto L01c10c7a
L01c10c1a:
    r2 = r0 - r2  #
    r3 = [r7+12]
    r2 = r2 << 2
    r2 = r2 + r3
    [r13+4] = r2
    r0 = r1 - r0
    [r13+8] = r0
    [r13+12] = r2
    r0 = 0
L01c10c32:
    r15 = r15 + 1  #
    r3 = [sp+32]
    r1 = r5 * r15
    r1 = r1 + r6
    r2 = r8 * r15
    r2 = r2 >>> 2
    r1 = r1 + r2
    r2 = r9 * r15
    r2 = r2 + r3
    r3 = r14 * r15
    r3 = r3 >>> 2
    r2 = r2 + r3
    [r13+16] = r0
    r0 = r2
    if (r11 == 0) {
    r0 = r1
    }
    [r13+20] = r0
    if (r11 == 0) {
    r1 = r2
    }
    [r13+24] = r1
    r0 = sp + 36
    call dsp_stage_mix  ; @call.xl
    if (r15 != 4) goto L01c10bd0
L01c10c7a:
    r0 = [sp+28]
    if ((r0 & 2) != 0) goto L01c10ca8
    r0 = [sp+12]
    r1 = [sp+8]
    [r0+0] = r1
    r0 = [sp+4]
    r1 = [sp]
    [r1+0] = r0
    r0 = [sp+20]
    r1 = [sp+24]
    r0 = r0 * 0x3
    r0 = r0 + r1
    r1 = L01c32db0
    r0 = r0 + r1  #
    r1 = [sp+16]
    r1 = r1 + 255
    b[r0+174] = r1
L01c10ca8:
    sp += 64
    {pc, r15-r4} = [sp++]

; dsp_stage_mix_select: 0x01c10cac..0x01c10cdc, module dsp-stage (mix_select)
.type dsp_stage_mix_select,@function
dsp_stage_mix_select:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = r2 * 0x3
    r4 = r4 + r3
    r5 = L01c32db0
    r4 = r4 + r5
    r4 = b[r4+174] (u)
    if (r4 == 0) goto L01c10cce
    [sp] = r4
    call dsp_stage_mix_ramp
    sp += 4
    {pc, r5, r4} = [sp++]
L01c10cce:
    r1 = [sp+16]
    if (r1 == 0) goto L01c10cd8
    call dsp_stage_mix  ; @call.xl
L01c10cd8:
    sp += 4
    {pc, r5, r4} = [sp++]

; dsp_stage_stereo_finish: 0x01c10cdc..0x01c10de8, module dsp-stage (stereo_finish)
.type dsp_stage_stereo_finish,@function
dsp_stage_stereo_finish:
    [--sp] = {rets, r15-r4}
    sp += -8
    r11 = r3  #
    r6 = [sp+60]
    r12 = r2
    r9 = r1
    r4 = r0
    r0 = 0
    r10 = L01c32db0
    r13 = 0
    if (r6 == 0) goto L01c10d02
    r1 = r2 * 0x3
    r1 = r1 + r3
    r1 += r10
    r13 = b[r1+180] (s)
L01c10d02:
    r1 = L01c32dac
    r7 = b[r1+1] (u)
    r8 = b[r1+0] (u)
    r1 = L01c1f7f0
    r5 = L01c341c4
    r1 = r7 | r8  #
    [r1+40] = r5
    r2 = L01c34488
    b[r2+0] = r0
    if ((r1 & 0xFF) == 0) goto L01c10dc4
    call dsp_stage_clock
    r14 = [r4+12]
    r15 = [r4+4]
    [sp+4] = r0
    if (r8 != 0) goto L01c10d4c
    r2 = 128
    r0 = r5
    r1 = r9
    call dsp_stage_copy  ; @call.xl
L01c10d4c:
    [r4+0] = r5
    if (r7 == 0) goto L01c10d84
    r0 = [r10+152]
    [r4+12] = r0
    if (r6 == 0) goto L01c10d82
    r0 = r13 + r10
    r1 = b[r0+22] (u)
    r0 = r15
    if (r1 == 0) goto L01c10d82
    r0 = L01c1f7f0
    r0 += r13  #
    r1 = [r4+8]
    r0 = b[r0+6] (u)
    r0 = r0 << 9
    r1 = 0x80 - r1
    r1 = r1 << 2
    r0 = r0 + r1
    r1 = L01c327ac
    r0 = r0 + r1
L01c10d82:
    [r4+4] = r0
L01c10d84:
    r0 = 128
    r0 = r6  #
    [sp] = r0
    if (r6 != 1) {
    r0 = 0
    }
    r1 = r0 | 0x2
    r0 = r4
    r2 = r12
    r3 = r11
    call dsp_stage_mix_select
    [r4+0] = r9
    [r4+4] = r15
    [r4+12] = r14
    r0 = 1
    r1 = L01c34488
    b[r1+0] = r0
    r0 = [r10+156]
    r1 = [sp+4]
    r4 = r0 - r1
    call dsp_stage_clock
    r0 = r0 + r4
    [r10+156] = r0
L01c10dc4:
    if (r6 == 0) goto L01c10de4
    if (r7 == 0) goto L01c10ddc
    r0 = L01c1f7f0
    r0 += r13
    r1 = b[r0+6] (u)
    r2 = b[r10+12] (u)
    b[r10+12] = r1
    b[r0+6] = r2
L01c10ddc:
    r0 = r13 + r10
    b[r0+22] = r7
L01c10de4:
    sp += 8
    {pc, r15-r4} = [sp++]

; dsp_stage_clear: 0x01c10de8..0x01c10e06, module dsp-stage (clear)
.type dsp_stage_clear,@function
dsp_stage_clear:
    [--sp] = {rets, r5, r4}
    r1 = 0
    r2 = 0
    r3 = 0
    r4 = 0
L01c10df2:
    r5 = r0 + r4
    [r5+20] = r2
    [r5+24] = r3
    [r5+28] = r2
    [r5+32] = r3
    r4 += 44
    [r5+36] = r1
    if (r4 != 176) goto L01c10df2
    {pc, r5, r4} = [sp++]

; dsp_stage_stage: 0x01c10e06..0x01c11b00, module dsp-stage (stage)
.type dsp_stage_stage,@function
dsp_stage_stage:
    [--sp] = {rets, r15-r4}
    sp += -156
    r14 = r2  #
    [sp+120] = r2
    r8 = r1
    r11 = L01c32db0
    r7 = L01c2c220
    [sp+100] = r0
    [sp+104] = r1
    if (r0 != 0) goto L01c10fe8
    r1 = 0
    r0 = r11 + 316
    b[r0+0] = r1
    b[r0+1] = r1
    b[r0+2] = r1
    b[r0+3] = r1
    b[r0+4] = r1
    b[r0+5] = r1
    b[r0+6] = r1
    b[r0+7] = r1
    b[r0+8] = r1
    b[r0+9] = r1
    b[r0+10] = r1
    b[r0+11] = r1
    b[r0+12] = r1
    b[r0+13] = r1
    b[r0+14] = r1
    b[r0+15] = r1
    r12 = L01c2e5a0
    r0 = -1
    [sp+112] = r0
    [sp+116] = r1
    r7 = 0
L01c10e58:
    r2 = r7 * 0x1C0
    r6 = r2
    r3 = b[++r6=r12] (u)
    if (r3 == 0) goto L01c10f9a
    r4 = r2 + r12
    r11 = b[r4+3] (u)
    r5 = b[r4+1] (u)
    if (r11 == 0) goto L01c10f9e
    r1 = r12  #
    [sp+96] = r6
    [sp+108] = r7
L01c10e7a:
    r15 = r2 + r12
    r0 = b[r15+5] (u)
    r6 = b[r15+45] (u)
    r0 = r0 << 2
    r13 = r5 * 0x1E0
    r0 += r13
    r7 = L01c2c220
    r14 = r0 + r7
    r10 = [++r14=288]
    r0 = r2 + r1
    r8 = [r0+128]
    if (r6 == 1) goto L01c10eb6
    if (r6 == 2) goto L01c10ecc
    if (r6 != 7) goto L01c10ee2
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L01c10f74
    r8 = r10
    goto L01c10f74
L01c10eb6:
    if (r3 != 1) {
    r0 = [r0+288]
    r8 = r0 + r10
    } else {
    r6 = r8 - r10
    [r0+288] = r6
    }
    goto L01c10f74
L01c10ecc:
    if (r3 != 1) {
    r0 = [r0+288]
    r8 = r10 + r0 (f)
    } else {
    r6 = r8 - r10 (f)
    [r0+288] = r6
    }
    goto L01c10f74
L01c10ee2:
    if (r3 == 1) goto L01c10f74
    r0 = r6 + -3
    r0 = r0.b0 (u)
    if (r0 > 1) goto L01c10f4a
    if (r6 != 3) {
    r8 = -1
    r9 = r8 + 0x4000
    } else {
    r8 = -1
    r9 = r8 + 1024
    }
    r0 = b[r15+85] (u)
    r6 = r7
    r6 += r13
    r6 = r6 + 288
    r0 = [r6+r0<<2]
    r6 = [sp+112]
    r7 = [sp+116]
    r7 = r9
    ifs (r0 <= 1) {
    r0 = 1
    }
    [sp+112] = r6
    [sp+116] = r7
    r9_r8 = r7_r6 / r0 (u)
    r0 = 2147483647
    r0 = r8 - r0
    r0 = 0
    r0 = r9 - r0 - !c
    r0 = psr
    if ((r0 & 0x2) != 0) {
    r8 = 2147483647
    r9 = 0
    }
    goto L01c10f74
L01c10f4a:
    if (r6 != 5) goto L01c10f64
    r0 = b[r15+85] (u)
    r6 = r7
    r6 += r13
    r6 = r6 + 288
    r0 = [r6+r0<<2]
    r8 = 0x0 - r0
    goto L01c10f74
L01c10f64:
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L01c10f6c
    r8 = r10
    goto L01c10f74
L01c10f6c:
    if (r6 == 0) goto L01c10f70
    r6 = r10
L01c10f70:
    r8 = r8 | r6
L01c10f74:
    [r14+0] = r8
    r1 = r1 + 4
    r12 = r12 + 1
    if (--r11 != 0) goto L01c10e7a
    r5 = b[r4+1] (u)
    r14 = [sp+120]
    r8 = [sp+104]
    r11 = L01c32db0
    r12 = L01c2e5a0
    r7 = [sp+108]
    r6 = [sp+96]
    goto L01c10fa4
L01c10f9a:
    r0 = r7 + 1
    goto L01c10fd2
L01c10f9e:
    r11 = L01c32db0
L01c10fa4:
    r0 = 1
    r2 = r5 + r11  #
    b[r4+2] = r0
    r4 = 316  #
    r1 = b[r4+4] (u)
    r0 = r7 + 1
    b[r2+r4] = r0
    r4 = r4 + 16
    b[r2+r4] = r1
    r1 = r3 + -1
    b[r6+0] = r1
    if (r3 == 1) {
    r1 = r7 + r11
    r2 = 0
    b[r1+210] = r2
    }
L01c10fd2:
    r7 = r0
    if (r0 != 8) goto L01c10e58
    r0 = [r11+92]
    r0 = r0 + 1
    [r11+92] = r0
    r7 = L01c2c220
L01c10fe8:
    r0 = L01c34198
    r0 = [r0+0]
    if (r0 == 0) goto L01c10ff8
    call r0
    [r11+96] = r0
L01c10ff8:
    r0 = [sp+100]
    if (r0 != 1) goto L01c11136
    r1 = b[r11+3] (u)
    r0 = 0
    if (r1 != 0) goto L01c1100e
    r0 = L01c1f7f0
    r0 = b[r0+0] (u)
L01c1100e:
    r1 = L01c1f7f0
    r1 = [r1+20]
    r2 = b[r11+2] (u)
    r3 = -1
    if (r2 <= r0) {
    r3 = 0
    }
    r4 = 1
    if (r2 >= r0) {
    r4 = r3
    }
    r0 = r4 + r2
    b[r11+2] = r0
    r1 = r1 + 1
    r2 = L01c1f7f0
    [r2+20] = r1
    b[r11+9] = r0
    if (r0 == 0) goto L01c1111c
    r1 = b[r11+8] (u)
    r0 = b[r11+15] (u)
    r5 = 0
    r2 = 0
    if (r1 == 0) goto L01c1105c
    r3 = r11 + 88
L01c11052:
    r4 = b[r3++=1] (u)
    r2 = r2 | (1 << r4)
    if (--r1 != 0) goto L01c11052
L01c1105c:
    r3 = sp + 124
    r1 = 1
    r8 = 1
    call dsp_stage_route_mask
    r4 = r7  #
    r1 = [sp+124]
    [r11+40] = r0
    [r11+44] = r1
    r9 = effect_stage_capabilities
L01c1107a:
    r0 = r5 + r11
    r0 = r0 + 268
    r11 = r0 + 32
    r6 = b[r11+0] (u)
    r12 = r0 + 16
    r7 = b[r12+0] (u)
    r1 = b[r4+2] (u)
    b[r0+0] = r7
    if (r1 == 0) goto L01c1110c
    r10 = r8 << r5
    r0 = r4
    call dsp_stage_active
    r1 = L01c32db0
    r3 = r0  #
    r2 = [r1+40]
    r1 = 0
    if ((r2 & r10) == 0) goto L01c110d0
    r0 = r4
    r1 = r3
    call dsp_stage_capability
    r1 = 0
    if (r0 == 0) goto L01c110d0
    if (r0 == 1) goto L01c110ce
    r0 = L01c32db0
    r0 = [r0+44]
    if ((r0 & r10) == 0) goto L01c110d0
L01c110ce:
    r1 = 64
L01c110d0:
    r0 = -1
    if (r7 <= r1) {
    r0 = 0
    }
    r2 = 1
    if (r7 >= r1) {
    r2 = r0
    }
    r1 = r2 + r7  #
    r0 = b[r4+0] (u)
    r0 = b[r0+r9] (u)
    b[r12+0] = r1
    if (r0 < 32) goto L01c1110c
    r0 = 0
    if (r3 != 0) goto L01c110f6
    r0 = 100
L01c110f6:
    r1 = -1
    if (r6 <= r0) {
    r1 = 0
    }
    r2 = 1
    if (r6 >= r0) {
    r2 = r1
    }
    r0 = r2 + r6
    b[r11+0] = r0
L01c1110c:
    r5 = r5 + 1
    r4 = r4 + 480
    r11 = L01c32db0
    if (r5 != 16) goto L01c1107a
L01c1111c:
    r1 = b[r11+15] (u)
    if (r1 == 0) goto L01c1113e
    r2 = r11 + 358
    r0 = 0
    r8 = [sp+104]
L01c1112a:
    r3 = b[r2++=1] (u)
    r0 = r0 | (1 << r3)
    if (--r1 != 0) goto L01c1112a
    goto L01c11142
L01c11136:
    r0 = 0
    b[r11+9] = r0
    goto L01c11156
L01c1113e:
    r0 = 0
    r8 = [sp+104]
L01c11142:
    [r11+36] = r0
    r1 = b[r11+9] (u)
    r0 = 1
    if (r1 != 0) goto L01c11150
    r0 = r1
L01c11150:
    r7 = L01c2c220
L01c11156:
    r1 = L01c34488
    r13 = 0
    b[r1+0] = r13
    r1 = L01c3448d
    b[r1+0] = r0
    r0 = [sp+100]
    if (r0 != 1) {
    r0 = 0
    } else {
    r0 = b[r11+8] (u)
    }
    r2 = [sp+100]
    r1 = r2 + r11
    r12 = b[r1+14] (u)
    r0 += r12
    r15 = r2  #
    [sp+72] = r0
    r0 = L01c34470
    if (r2 == 0) goto L01c11192
    r15 = [r0+0]
L01c11192:
    if (r12 == 0) goto L01c111ca
    r10 = 0  #
    r0 = [sp+100]
    r4 = r0 * 0xA
    r0 = r4 + r11
    r0 = r0 + 349  #
    [sp+28] = r0
    r0 = r14 << 2  #
    [sp+76] = r0
    r0 = 0x0 - r14  #
    [sp+16] = r0
    r0 = 0x80 - r14  #
    [sp+8] = r0
    [sp+12] = r0
    r0 = sp + 128
    [sp+68] = r0
    r0 = 0
    [sp+112] = r0
    r3 = 0
    goto L01c11256
L01c111ca:
    r10 = 0
    goto L01c11964
L01c111ce:
    r3 = r11  #
    [sp+84] = r3
    r5 = b[++r3=16] (u)
    r2 = 0
    r8 = 0
    if (r5 == 0) goto L01c111ec
    r3 = r11
    r5 = b[++r3=17] (u)
    if (r5 != 0) goto L01c1153e
    r8 = 1
L01c111ec:
    r5 = 1
    r3 = r8 + r11  #
    b[r3+0] = r5
    r5 = 0
    [sp+108] = r5
    b[r3+18] = r2
    b[r1+0] = r8
    r3 = [sp+84]
L01c11202:
    r5 = r3  #
    r2 = [sp+80]
    r1 = r3 - r2
    r3 = r2 - r5
    ifs (r5 >= r2) {
    r3 = r1
    }
    if (r3 >= 127) {
    r3 = 127
    }
    [sp+20] = r3
    r1 = 1
    [sp+84] = r1
    r1 = [sp+108]
    if (r1 != r6) goto L01c11226
    r6 = r0
    goto L01c11564
L01c11226:
    r3 = r8 + r11
    r1 = b[r3+20] (u)
    r1 = r1 << 9
    r2 = L01c321ac
    r5 = r1 + r2
    r2 = 0
    r0 = [sp+88]
    r1 = [sp+92]
L01c1123e:
    [r5+r2<<2] = r1
    r2 = r2 + 1
    if (r2 != 128) goto L01c1123e
    b[r3+18] = r6
    b[r3+22] = r1
    goto L01c11564
L01c11252:
    r2 = [sp+80]
    goto L01c114f6
L01c11256:
    [sp+88] = r2
    [sp+92] = r3
L01c1125a:
    r0 = r4 + r13
    r0 += r11
    r9 = r0 + 348
    r0 = b[r9+0] (u)
    r1 = r0 * 0x1E0
    r2 = r1 + r7
    r3 = b[r2+4] (u)
    ifs (r10 > 2) goto L01c1127a
    if (r14 > 128) goto L01c1127a
    if (r3 != 0) goto L01c1133e
L01c1127a:
    if (r14 > 128) goto L01c11320
    if (r3 != 0) goto L01c11320
    r2 = b[r2+6] (u)
    r2 |= 2
    r2 = r2.b0 (u)
    if (r2 != 3) goto L01c11320
    r1 = b[r1+r7] (u)
    r1 += -3
    if (r1 > 20) goto L01c11320
    r2 = 2089153
    r1 = r2 >> r1
    if ((r1 & 1) == 0) goto L01c11320
    r1 = [sp+76]
    r1 += r13
    r2 = r13 + 1
    r5 = 0
L01c112ac:
    r3 = r5
    r5 = r2 + r3
    ifs (r5 >= r12) goto L01c112ea
    r5 = b[r1+r3] (u)
    r5 = r5 * 0x1E0
    r6 = L01c2c220
    r6 = r6 + r5
    r7 = b[r6+4] (u)
    if (r7 != 0) goto L01c112ea
    r6 = b[r6+6] (u)
    if (r6 != 1) goto L01c112ea
    r6 = L01c2c220
    r5 = b[r5+r6] (u)
    r5 += -9
    if (r5 > 14) goto L01c112ea
    r6 = 28419
    r6 >>= r5
    r5 = r3 + 1
    if ((r6 & 1) != 0) goto L01c112ac
L01c112ea:
    r5 = r3 + 1
    r7 = L01c2c220
    ifs (r5 < 2) goto L01c11320
    r6 = b[r11+9] (u)
    r0 = [sp+88]
    r1 = [sp+92]
    b[r11+9] = r1
    r0 = r9
    r1 = r5
    r2 = r8
    r3 = r14
    call effect_processing_grouped
    b[r11+9] = r6
    r1 = [r11+100]
    r15 += r0  #
    r0 = [sp+112]
    r0 = r0 + r1
    [sp+112] = r0
    goto L01c11336
L01c11320:
    r1 = r8
    r2 = r14
    call effect_processing_individual
    if (r0 == 4294967295) {
    r0 = [sp+112]
    r0 = r0 + 1
    [sp+112] = r0
    } else {
    r15 += r0
    }
    r5 = 1
L01c11336:
    r13 += r5
    ifs (r13 < r12) goto L01c1125a
    goto L01c1195e
L01c1133e:
    [sp+36] = r4
    r0 = [sp+76]
    r0 += r13
    r0 = r13 + 1  #
    [sp+108] = r0
    r1 = 0
L01c1134c:
    r4 = r1
    r3 = r0 + r4
    ifs (r3 >= r12) goto L01c11366
    r1 = [sp+108]
    r1 = b[r1+r4] (u)
    r1 = r1 * 0x1E0
    r1 = r1 + r7
    r2 = b[r1+4] (u)
    r1 = r4 + 1
    if (r2 != 0) goto L01c1134c
L01c11366:
    [sp+64] = r3
    [sp+40] = r15
    r0 = b[r11+9] (u)
    [sp+60] = r0
    r2 = [sp+88]
    r3 = [sp+92]
    if (r14 != 128) {
    b[r11+9] = r3
    r0 = L01c34488
    b[r0+0] = r3
    }
    r0 = [r11+96]
    r15 = r4 + 1  #
    [sp+56] = r0
    ifs (r15 < 1) goto L01c11530
    r0 = 0
    r3_r2 = 0  #
    [sp+96] = r0
L01c11398:
    [sp+80] = r2
L01c1139a:
    [sp+84] = r3
    r2 = [sp+96]
L01c1139e:
    r3 = b[r9+r2] (u)
    if (r14 > 128) goto L01c11482
    r0 = r3 * 0x1E0
    r1 = r0 + r7
    r6 = b[r1+6] (u)
    r6 |= 2
    r6 = r6.b0 (u)
    if (r6 != 3) goto L01c1146e
    r0 = b[r0+r7] (u)
    r0 += -3
    if (r0 > 20) goto L01c1146e
    r5 = 2089153
    r0 = r5 >> r0
    if ((r0 & 1) == 0) goto L01c1146e
    r7 = 0
    r0 = r2
L01c113d2:
    r0 = r0 + 1
    r6 = r7
    ifs (r0 >= r15) goto L01c1141e
    r7 = b[r9+r0] (u)
    r7 = r7 * 0x1E0
    r5 = L01c2c220
    r14 = r7 + r5
    r11 = b[r14+4] (u)
    r8 = b[r1+4] (u)
    if (r11 != r8) goto L01c1141e
    r5 = b[r14+6] (u)
    if (r5 != 1) goto L01c1141e
    r5 = L01c2c220
    r5 = b[r7+r5] (u)
    r7 = r5 + -9
    if (r7 > 14) goto L01c1141e
    r5 = 28419
    r5 >>= r7
    r7 = r6 + 1
    if ((r5 & 1) != 0) goto L01c113d2
L01c1141e:
    r5 = r0 - r2
    ifs (r5 < 2) goto L01c11472
    r14 = [sp+120]
    r11 = L01c32db0
    r7 = L01c2c220
    ifs (r0 <= r2) goto L01c11454
    r3 = b[r1+1] (u)
    r5 = r2 + 1
    if (r0 == r5) goto L01c11452
    r5 = [sp+108]
    r2 = r2 + r5
L01c11442:
    r5 = b[r2++=1] (u)
    r5 = r5 * 0x1E0
    r5 = r5 + r7
    r5 = b[r5+1] (u)
    r3 |= r5
    if (--r6 != 0) goto L01c11442
L01c11452:
    if (r3 != 0) goto L01c1145c
L01c11454:
    r2 = r0
    ifs (r0 < r15) goto L01c1139e
    goto L01c114f2
L01c1145c:
    r1 = b[r1+4] (u)
    if (r1 == 2) goto L01c114e4
    r3 = [sp+84]
    r3 = r3 + 9
    [sp+96] = r0
    ifs (r0 < r15) goto L01c1139a
    goto L01c11252
L01c1146e:
    [sp+96] = r2
    goto L01c11482
L01c11472:
    [sp+96] = r2
    r14 = [sp+120]
    r11 = L01c32db0
    r7 = L01c2c220
L01c11482:
    r0 = r3 * 0x1E0
    r1 = r0 + r7
    r2 = b[r1+0] (u)
    r0 = b[r1+1] (u)
    if (r2 != 7) goto L01c114a6
    if (r0 == 0) goto L01c114ce
    r0 = [r1+288]
    if (r0 == 0) goto L01c114a8
    r5 = b[r1+4] (u)
    call dsp_stage_ir_delay  ; @call.xl
    if (r5 == 2) goto L01c114c6
    goto L01c114d2
L01c114a6:
    if (r0 == 0) goto L01c114ce
L01c114a8:
    r2 = b[r1+6] (u)
    if (r2 == 0) goto L01c114ce
    r5 = r2 | 0x1
    r0 = 9
    r3 = 9
    if (r5 != 3) {
    r3 = 12
    }
    if (r2 != 1) {
    r0 = r3
    }
    r1 = b[r1+4] (u)
    if (r1 != 2) goto L01c114d2
L01c114c6:
    r2 = [sp+80]
    r3 = [sp+84]
    r2 = r2 + r0
    goto L01c114d8
L01c114ce:
    r3 = [sp+84]
    goto L01c114d6
L01c114d2:
    r3 = [sp+84]
    r3 = r3 + r0
L01c114d6:
    r2 = [sp+80]
L01c114d8:
    r0 = [sp+96]
    r0 = r0 + 1
    [sp+96] = r0
    ifs (r0 < r15) goto L01c11398
    goto L01c114f6
L01c114e4:
    r2 = [sp+80]
    r2 = r2 + 9
    [sp+96] = r0
    r3 = [sp+84]
    ifs (r0 < r15) goto L01c11398
    goto L01c114f6
L01c114f2:
    r2 = [sp+80]
    r3 = [sp+84]
L01c114f6:
    r0 = 1
    ifs (r3 >= r2) {
    r0 = 2
    }
    r6 = 0
    if (r3 != r2) {
    r6 = r0
    }
    r1 = [sp+100]
    r1 = r1 * 0x3
    r1 += r10
    r1 += r11
    r1 = r1 + 180
    if (r3 == r2) goto L01c1153e
    [sp+80] = r2
    r8 = b[r1+0] (s)
    ifs (r8 < 0) goto L01c111ce
    r1 = r8 + r11
    r1 = b[r1+18] (u)
    [sp+108] = r1
    goto L01c11202
L01c11530:
    r0 = [sp+100]
    r0 = r0 * 0x3
    r0 += r10
    r0 += r11
    r1 = r0 + 180
L01c1153e:
    r0 = b[r1+0] (s)
    r8 = -1
    ifs (r0 < 0) goto L01c1155a
    r3_r2 = 0
    r0 += r11  #
    [sp+84] = r2
    b[r0+16] = r3
    r0 = 255
    b[r1+0] = r0
    goto L01c1155e
L01c1155a:
    r0 = 0
    [sp+84] = r0
L01c1155e:
    r6 = 0
    r0 = 0
    [sp+20] = r0
L01c11564:
    r0 = b[r11+7] (u)
    r0 = r0 << 9
    r1 = L01c321ac
    r3 = r0 + r1  #
    r5 = [sp+104]
    [sp+80] = r3
    if (r14 == 0) goto L01c11588
    r0 = r3
    r1 = r5
    r2 = r14
    call dsp_stage_copy  ; @call.xl
    r3 = [sp+80]
L01c11588:
    [sp+96] = r3
    [sp+108] = r5
    if (r6 != 1) {
    r0 = [sp+104]
    [sp+96] = r0
    [sp+108] = r3
    }
    r1 = r10  #
    r5 = [sp+100]
    r0 = r5
    r2 = r6
    call dsp_stage_stereo_prepare
    r0 = r5 * 0x3
    r0 += r10
    r0 += r11
    r0 = b[r0+192] (u)
    if (r14 == 0) goto L01c115c2
    if (r0 == 0) goto L01c115c2
    [sp] = r14
    r1 = r10  #
    r0 = [sp+100]
    r2 = [sp+96]
    r3 = [sp+108]
    call dsp_stage_branch_prepare
L01c115c2:
    r0 = L01c34198
    r1 = [r0+0]
    if (r1 == 0) {
    r0 = 0
    } else {
    call r1
    }
    [r11+96] = r0
    r1 = [r11+144]
    if (r1 == 0) goto L01c115f2
    r5 = r11 + 144
    r1 = [r5+12]
    r2 = [r5+16]
    r2 = r0 - r2
    r2 = r2 >> 1
    r1 = r1 + r2
    [r5+12] = r1
    r2 = [sp+88]
    r3 = [sp+92]
    [r5+0] = r3
L01c115f2:
    [sp+44] = r8
    r1 = r13 + r4  #
    [sp+24] = r0
    [sp+52] = r6
    [sp+48] = r1
    ifs (r15 < 1) goto L01c1172e
    r11 = 0  #
    r0 = [sp+28]
    r0 += r13
    r13 = 0  #
    [sp+32] = r0
    r8 = [sp+104]
L01c1160e:
    r0 = r9  #
    r2 = [sp+108]
    r1 = b[++r0=r13] (u)
    r6 = r1 * 0x1E0
    r7 = r7 + r6
    r3 = b[r7+4] (u)
    if (r3 != 2) {
    r2 = [sp+96]
    }
    r5 = 1
    if (r14 > 128) goto L01c116ae
    r7 = b[r7+6] (u)
    r7 |= 2
    r7 = r7.b0 (u)
    if (r7 != 3) goto L01c116ae
    r7 = L01c2c220
    r6 = b[r6+r7] (u)
    r6 += -3
    if (r6 > 20) goto L01c116ae
    r4 = 2089153
    r6 = r4 >> r6
    if ((r6 & 1) == 0) goto L01c116ae
    r4 = [sp+32]
    r4 += r13
    r7 = 1
L01c11658:
    r5 = r7
    r7 = r13 + r5
    ifs (r7 >= r15) goto L01c116ae
    r7 = r4 + r5
    r6 = 348
    r7 = b[r7+r6] (u)
    r7 = r7 * 0x1E0
    r6 = L01c2c220
    r14 = r7 + r6
    r6 = b[r14+4] (u)
    if (r6 != r3) goto L01c116ac
    r6 = b[r14+6] (u)
    if (r6 != 1) goto L01c116ac
    r6 = L01c2c220
    r6 = b[r7+r6] (u)
    r7 = r6 + -9
    r14 = [sp+120]
    if (r7 > 14) goto L01c116ae
    r6 = 28419
    r6 >>= r7
    r7 = r5 + 1
    if ((r6 & 1) != 0) goto L01c11658
    goto L01c116ae
L01c116ac:
    r14 = [sp+120]
L01c116ae:
    if (r2 == r8) {
    r3 = L01c341c4
    } else {
    r3 = L01c32db0
    r3 = [r3+152]
    }
    r6 = L01c1f7f0
    [r6+40] = r3
    r6 = 1
    r7 = L01c2c220
    if (r2 == r8) {
    r6 = 0
    }
    r3 = L01c32dac
    r3 = b[r6+r3] (u)
    r4 = L01c34488
    b[r4+0] = r3
    ifs (r5 < 2) goto L01c11702
    r1 = r5
    r3 = r14
    call effect_processing_grouped
    r0 = L01c32db0
    r1 = [r0+100]
    goto L01c11716
L01c11702:
    r0 = r1
    r1 = r2
    r2 = r14
    call effect_processing_individual
    r5 = 1
    r1 = 1
    if (r0 != 4294967295) {
    r1 = 0
    }
L01c11716:
    r0 = r4
    r13 += r5  #
    r0 = b[r0+0] (u)
    r2 = L01c32dac
    b[r6+r2] = r0
    r11 += r1
    ifs (r13 < r15) goto L01c1160e
    goto L01c11732
L01c1172e:
    r11 = 0
    r8 = [sp+104]
L01c11732:
    r0 = [sp+48]
    r13 = r0 + 1  #
    r1 = [sp+100]
    r0 = r10 << 3
    r1 = r1 * 0x18
    r0 = r0 + r1
    r1 = L01c32fa0
    r0 = r0 + r1
    r1 = L01c32db0
    r7 = [r1+96]
    r1 = [r0+4]
    r0 = [r0+0]
    [sp+128] = r8
    r2 = r1  #
    r4 = [sp+52]
    if (r4 != 1) {
    r2 = r0
    }
    r5 = r4  #
    r3 = [sp+68]
    [r3+20] = r2
    r6 = L01c341c4
    if (r4 != 1) {
    r0 = r1
    }
    [r3+24] = r0
    r0 = [sp+84]
    [sp+108] = r7
    if (r0 == 0) goto L01c117b0
    r0 = L01c32db0
    r1 = [sp+44]
    r0 = r0 + r1  #
    r2 = [sp+20]
    r1 = b[r0+20] (u)
    r0 = umin(r2, r14)
    r0 = r14 - r0  #
    [r3+8] = r0
    r1 = r1 << 9
    r2 = 0x80 - r2
    r2 = r2 << 2
    r1 = r1 + r2
    r2 = L01c321ac
    r1 = r1 + r2  #
    r2 = [sp+80]
    goto L01c117ba
L01c117b0:
    [r3+8] = r14
    r0 = 0
    r2 = [sp+80]
    r1 = r2
L01c117ba:
    r7 = r5  #
    [r3+4] = r1
    r1 = r8  #
    [r3+16] = r0
    r3 = r10  #
    [r3+12] = r2
    r4 = sp + 128
    r0 = r4  #
    [sp] = r7
    r5 = [sp+100]
    r2 = r5
    call dsp_stage_stereo_finish
    [sp] = r14
    if (r7 != 1) {
    r7 = 0
    }
    r0 = r4
    r1 = r7
    r2 = r5
    r3 = r10
    call dsp_stage_mix_select
    r0 = L01c32dae
    r0 = b[r0+0] (u)
    r5 = [sp+104]
    r14 = [sp+88]
    r15 = [sp+92]
    if (r0 == 0) goto L01c1185a
    r0 = L01c34488
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L01c1185a
    r0 = L01c1f7f0
    [r0+40] = r6
    r0 = 0
L01c1180e:
    r2 = r0 + 1
    r3 = r2 >>> 31
    r9_r8 = r3_r2
    r9_r8 <<= 25
    r6 = 0x0 - r8
    r7 = r15 - r9 - !c
    r1 = L01c341c4
    r1 = [r1+r0<<2]
    r14 = [r5+r0<<2]
    r7_r6 >>= 16
    r4 = r6 + 0x10000
    r7_r6 = r1 * r4 (s)
    r7_r6 -= r14 * r4 (s)
    r7_r6 >>= 16
    r8 = r6 + r14
    r9 = r7 + r15 + c
    r1 = L01c341c4
    [r1+r0<<2] = r8
    r0 = r2
    if (r2 != 128) goto L01c1180e
L01c1185a:
    [sp+88] = r14
    [sp+92] = r15
    r8 = r5  #
    r0 = [sp+84]
    r14 = [sp+120]
    r9 = [sp+56]
    if (r0 == 0) goto L01c118ce
    r0 = L01c32db0
    r1 = r0  #
    r0 = [sp+44]
    r0 = r0 + r1  #
    r1 = b[r1+7] (u)
    r2 = b[r0+20] (u)
    if (r14 > 127) goto L01c118c2
    r5 = [sp+16]
    if (r14 == 0) goto L01c118a0
    r3 = r1 << 9
    r4 = L01c321ac
    r3 = r3 + r4  #
    r4 = [sp+8]
    r3 = r3 + 508
L01c11894:
    r6 = r5 + r3
    r6 = [r6+-512]
    r4 = r4 + 1
    [r3++=-4] = r6
    if (r4 != 0) goto L01c11894
L01c118a0:
    r3 = [sp+12]
    if (r3 == 0) goto L01c118c2
    r3 = r1 << 9
    r4 = L01c321ac
    r5 = r4
    r3 = r3 + r5
    r4 = r2 << 9
    r4 = r4 + r5
    r6 = r14
L01c118b6:
    r7 = [r4+r6<<2]
    r6 = r6 + 1
    [r3++=4] = r7
    if (r6 != 128) goto L01c118b6
L01c118c2:
    r3 = L01c32db0
    b[r3+7] = r2
    b[r0+20] = r1
L01c118ce:
    r0 = L01c34198
    r1 = [r0+0]
    r5 = L01c32db0
    [r5+104] = r11
    if (r1 == 0) goto L01c11934
    call r1
    r2 = [r5+156]
    [r5+96] = r0
    r1 = r10 << 2  #
    r3 = [sp+100]
    r3 = r3 * 0xC  #
    r4 = [sp+24]
    r1 = r1 + r3  #
    r6 = [sp+108]
    r1 = r1 + r5
    r3 = [++r1=392]
    r4 = r4 - r9
    r4 = r4 - r6
    r4 = r4 + r0
    r2 = r4 - r2
    r7 = L01c2c220
    if (r3 == 0) goto L01c11924
    if (r2 > r3) {
    r2 = r2 - r3
    r2 = r2 >> 2
    r2 = r2 + r3
    } else {
    r2 = r3 - r2
    r2 = r2 >> 2
    r2 = r3 - r2
    }
L01c11924:
    r15 = [sp+40]
    r0 = r0 - r9  #
    r4 = [sp+36]
    [r1+0] = r2
    r11 = [r5+104]
    goto L01c11940
L01c11934:
    r0 = 0
    r7 = L01c2c220
    r15 = [sp+40]
    r4 = [sp+36]
L01c11940:
    r2 = [sp+88]
    r3 = [sp+92]
    r1 = [sp+60]
    b[r5+9] = r1
    r1 = [sp+112]
    r1 += r11
    r15 += r0  #
    [sp+112] = r1
    r10 = r10 + 1  #
    r0 = [sp+64]
    r11 = r5
    ifs (r0 < r12) goto L01c11256
L01c1195e:
    r13 = [sp+112]
    ifs (r10 > 2) goto L01c119c6
L01c11964:
    r9 = 0  #
    r2 = [sp+100]
    r0 = r2 * 0x3
    r6 = r0 + r11
    r0 = r2 * 0xC
    r1 = r0 + r11
    r0 = r10 << 8
    r2 = r2 * 0x300
    r0 = r0 + r2
    r2 = L01c2f3a0
    r0 = r0 + r2
    r8 = 255
    r7 = r1 + 392
L01c11992:
    r1 = r6 + r10
    r2 = r1
    r3 = b[++r2=180] (s)
    ifs (r3 >= 0) {
    r3 += r11
    b[r3+16] = r9
    b[r2+0] = r8
    }
    [r7+r10<<2] = r9
    r1 = b[r1+192] (u)
    if (r1 == 0) goto L01c119b8
    call dsp_stage_clear
L01c119b8:
    r10 = r10 + 1
    r0 = r0 + 256
    if (r10 != 3) goto L01c11992
    r8 = [sp+104]
L01c119c6:
    r6 = [sp+72]
    if (r12 >= r6) goto L01c119f4
    r4 = r11 + 88
    r5 = L01c34470
L01c119d6:
    r1 = r8  #
    r0 = b[r4++=1] (u)
    r2 = r14
    call effect_processing_individual
    if (r0 != 4294967295) {
    r15 += r0
    } else {
    r13 = r13 + 1
    }
    r12 = r12 + 1
    ifs (r12 < r6) goto L01c119d6
    goto L01c119fa
L01c119f4:
    r5 = L01c34470
L01c119fa:
    if (r13 == 0) goto L01c11a0a
    r0 = L01c3445c
    r1 = [r0+0]
    r1 += r13
    [r0+0] = r1
L01c11a0a:
    r13 = r15
    [r5+0] = r13
    r0 = [sp+100]
    if (r0 != 1) goto L01c11aec
    r1 = b[r11+9] (u)
    r2 = b[r11+13] (u)
    b[r11+13] = r1
    r0 = L01c34488
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L01c11aec
    r0 = 1
    r3 = 1
    if (r1 <= 15) {
    r3 = 0
    }
    r4 = 1
    if (r2 <= 15) {
    r4 = 0
    }
    r3 &= r4
    if (r14 != 0) {
    r0 = 0
    }
    if (r14 > 128) goto L01c11aec
    r0 |= r3
    if (r0 != 0) goto L01c11aec
    r3 = 0x10000
    r12 = r3
    if (r2 > 15) goto L01c11a6a
    r0 = r2 * r2
    r0 *= r2
    r0 = r0 << 4
    r2 = 1048560
    r12 = r0 & r2
L01c11a6a:
    if (r1 > 15) goto L01c11a80
    r2 = r1 * r1
    r1 *= r2
    r1 = r1 << 4
    r2 = 1048560
    r3 = r1 & r2
L01c11a80:
    if (r14 == 0) goto L01c11aec
    r0 = L01c1f7f0
    r2 = r3 - r12  #
    r1 = [r0+40]
    r3 = 0x10000
    r3 = r3 / r14 (s)
    r3_r2 = r3 * r2 (s)
    r5 = 0
    r6 = 0
L01c11aa0:
    r8 = r6 + 1
    r9 = r8 >>> 31
    r7 = r2 * r9
    r11_r10 = r2 * r8 (u)
    r7 += r11
    r0 = r3 * r8
    r11 = r7 + r0  #
    r7 = [sp+104]
    r0 = [r1+r6<<2]
    r4 = [r7+r6<<2]
    r11_r10 >>= 16
    r7 = r10 + r12
    r11_r10 = r0 * r7 (s)
    r11_r10 -= r4 * r7 (s)
    r11_r10 >>= 16
    r14 = r10 + r4
    r15 = r11 + r5 + c
    [r1+r6<<2] = r14
    r6 = r8  #
    r0 = [sp+120]
    if (r0 != r6) goto L01c11aa0
L01c11aec:
    r0 = L01c343c8
    r1 = [r0+0]
    if (r13 > r1) {
    [r0+0] = r13
    }
    sp += 156
    {pc, r15-r4} = [sp++]
