; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_link_start: 1 function, 0x02004d36..0x02005130

; audio_link_start_link_start: 0x02004d36..0x02005130, module audio-link-start (link_start)
.type audio_link_start_link_start,@function
audio_link_start_link_start:
    [--sp] = {rets, r15-r4}
    r0 = 4172
    r9 = L01c26890
    r0 = b[r9+r0] (u)
    r2 = -1
    if (r0 != 0) goto L02005120
    r0 = 1748
    r0 = b[r9+r0] (u)
    r1 = 1749
    r1 = b[r9+r1] (u)
    r0 &= r1
    if ((r0 & 0xFF) != 0) goto L02005124
    r0 = 1750
    r0 = b[r9+r0] (u)
    r1 = 331824
    if (r0 == 2) goto L02004d8c
    if (r0 == 1) goto L02004d96
    if (r0 != 0) goto L02005120
    [r1+0] &= 0xFFFFFF7F
    r2 = [r1+0]
    r2 |= 64
    goto L02004d9c
L02004d8c:
    [r1+0] &= 0xFFFFFFBF
    r2 = [r1+0]
    r2 |= 128
    goto L02004d9c
L02004d96:
    r2 = [r1+0]
    r2 = r2 & 0xFFFFFF3F
L02004d9c:
    r6 = r9 + 1748  #
    [r1+0] = r2
    r1 = r9 + 4176
    [r1+48] = r6
    r2 = h[r6+12] (u)
    r2 = 0x12E00  #
    [r1+0] = r2
    [r1+44] = r2
    r1 = 0
    h[r2+0] = r1
    h[r2+4] = r1
    r3 = r2 + 32  #
    b[r2+12] = r1
    h[r3+0] = r1
    [r2+16] = r1
    [r2+20] = r1
    [r2+24] = r1
    [r2+28] = r1
    r1 = b[r6+5] (u)
    if (r1 != 0) goto L02004dea
    r3 = b[r2+12] (u)
    r3 = r3 | 0x3
    b[r2+12] = r3
    r3 = h[r2+0] (u)
    r3 |= 128
    r3 = 1752  #
    h[r2+0] = r3
    r3 = b[r9+r3] (u)
    if (r3 == 0) goto L02004dea
    r3 = h[r2+0] (u)
    r3 |= 256
    h[r2+0] = r3
L02004dea:
    r3 = h[r2+0] (u)
    r3 &= 4294967231
    r3 = 1754  #
    h[r2+0] = r3
    r3 = b[r9+r3] (u)
    if (r3 == 0) goto L02004e00
    r3 = h[r2+0] (u)
    r3 |= 1024
    h[r2+0] = r3
L02004e00:
    r3 = 1755
    r3 = b[r9+r3] (u)
    if (r3 == 0) goto L02004e10
    r3 = h[r2+0] (u)
    r3 |= 512
    h[r2+0] = r3
L02004e10:
    r2 = 881
    r3 = h[r9+r2<<1] (u)
    r2 = 160
    if (r3 == 0) goto L02004e1e
    r2 = r3
L02004e1e:
    r3 = 2087
    h[r9+r3<<1] = r2
    r10 = L02035360
    if (r1 == 0) goto L02004ee8
    r8 = r10 + 4
    r0 = r0 * 0x7
    r0 = b[r0+r8] (u)
    r1 = 1
    call phase3_p5_gpio_set_die
    r4 = r9 + 1750
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r7 = r10 + 5
    r0 = b[r0+r7] (u)
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r5 = r10 + 6
    r0 = b[r0+r5] (u)
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r8] (u)
    call L02004ad6
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r7] (u)
    call L02004ad6
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r5] (u)
    call L02004ad6
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r8] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r7] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r5] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r8] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r7] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    goto L02004f84
L02004ee8:
    r1 = 1752
    r1 = b[r9+r1] (u)
    if (r1 == 0) goto L02004f2a
    r4 = r10 + 4
    r0 = r0 * 0x7
    r0 = b[r0+r4] (u)
    r1 = 0
    call phase3_p5_gpio_direction_output
    r5 = r9 + 1750
    r0 = b[r5+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r4] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r5+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r4] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r0 = b[r5+0] (u)
L02004f2a:
    r5 = r10 + 5
    r0 = r0 * 0x7
    r0 = b[r0+r5] (u)
    r1 = 0
    call phase3_p5_gpio_direction_output
    r4 = r9 + 1750
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r5] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r5] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r5 = r10 + 6
    r0 = b[r0+r5] (u)
    r1 = 0
    call phase3_p5_gpio_direction_output
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r5] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
L02004f84:
    r0 = b[r4+0] (u)
    r0 = r0 * 0x7
    r0 = b[r0+r5] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r5_r4 = 0
    r7 = 3
    r11 = 1
    r12 = 1749
    r13 = 1748
    r14 = 1751
    r15 = 1055
    goto L02005076
L02004fae:
    r0 = b[r9+r12] (u)
    r8 = r11 << r5
    if ((r0 & r8) == 0) goto L02004ffe
    r0 = b[r6+2] (u)
    r0 = r0 * 0x7
    r0 += r5  ; @add.rr
    r0 = b[r0+r10] (u)
    r1 = 0
    call phase3_p5_gpio_direction_output
    r0 = b[r6+2] (u)
    r0 = r0 * 0x7
    r0 += r5  ; @add.rr
    r0 = b[r0+r10] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r6+2] (u)
    r0 = r0 * 0x7
    r0 += r5  ; @add.rr
    r0 = b[r0+r10] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r0 = [r9+r15<<2]
    r1 = h[r0+4] (u)
    r1 = r1 & ~(1 << r7)
    h[r0+4] = r1
    r4 += 1  ; @add.ri.u5
L02004ffe:
    r0 = b[r9+r13] (u)
    if ((r0 & r8) == 0) goto L0200505a
    r0 = b[r6+2] (u)
    r0 = r0 * 0x7
    r0 += r5  ; @add.rr
    r0 = b[r0+r10] (u)
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = b[r6+2] (u)
    r0 = r0 * 0x7
    r0 += r5  ; @add.rr
    r0 = b[r0+r10] (u)
    call L02004ad6
    r0 = b[r6+2] (u)
    r0 = r0 * 0x7
    r0 += r5  ; @add.rr
    r0 = b[r0+r10] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r0 = b[r6+2] (u)
    r0 = r0 * 0x7
    r0 += r5  ; @add.rr
    r0 = b[r0+r10] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = [r9+r15<<2]
    r1 = h[r0+4] (u)
    r1 = r1 | (1 << r7)
    h[r0+4] = r1
    r4 += 1  ; @add.ri.u5
L0200505a:
    r0 = b[r9+r14] (u)
    if ((r0 & r8) == 0) goto L02005072
    r0 = [r9+r15<<2]
    r2 = r7 + -1  #
    r1 = h[r0+4] (u)
    r1 = r1 | (1 << r2)
    h[r0+4] = r1
L02005072:
    r7 += 4  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L02005076:
    if (r5 != 4) goto L02004fae
    if ((r4 & 0xFF) == 0) goto L02005124
    r5 = 1050
    r0 = [r9+r5<<2]
    if (r0 != 0) goto L02005124
    r6 = 2087
    r0 = h[r9+r6<<1] (u)
    r1 = r4.b0 (u)
    r0 *= r1
    r0 = r0 << 3
    call L0203c15c  ; @call.xl
    [r9+r5<<2] = r0
    r2 = -1
    if (r0 == 0) goto L02005120
    r1 = h[r9+r6<<1] (u)
    r2 = r13
    r11 = b[r9+r2] (u)
    r3 = r12
    r3 = b[r9+r3] (u)
    r8 = 0
    r10 = 1
    r7_r6 = 0
    goto L020050f2
L020050c0:
    r4 = r9 + 4204
    r5 = r10 << r6
    [r4+r6<<2] = r8
    if ((r3 & r5) == 0) goto L020050de
    r2 = r7.b0 (u)
    r2 *= r1
    r2 = r2 << 3
    r2 += r0  ; @add.rr
    [r4+r6<<2] = r2
    r7 += 1  ; @add.ri.u5
L020050de:
    if ((r11 & r5) == 0) goto L020050f0
    r2 = r7.b0 (u)
    r2 *= r1
    r2 = r2 << 3
    r2 += r0  ; @add.rr
    [r4+r6<<2] = r2
    r7 += 1  ; @add.ri.u5
L020050f0:
    r6 += 1  ; @add.ri.u5
L020050f2:
    if (r6 != 4) goto L020050c0
    r0 = r9 + 4172
    r2 = [r0+48]
    r3 = [r0+32]
    [r2+16] = r3
    r3 = [r0+36]
    [r2+20] = r3
    r3 = [r0+40]
    [r2+24] = r3
    r3 = [r0+44]
    [r2+28] = r3
    h[r2+32] = r1
    csync
    r1 = [r0+48]
    r2 = h[r1+0] (u)
    r2 |= 2048
    h[r1+0] = r2
    r1 = 1
    b[r0+0] = r1
    r2 = 0
L02005120:
    r0 = r2
    {pc, r15-r4} = [sp++]
L02005124:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0200512e:
    goto L0200512e
