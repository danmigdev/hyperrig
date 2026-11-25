; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 3 functions, 0x01c0588e..0x01c05d02

; effect_processing_capture_probe: 0x01c0588e..0x01c058bc, module effect-processing (capture_probe)
.type effect_processing_capture_probe,@function
effect_processing_capture_probe:
    r1 = r0
    r3 = r1 + 84
    r2 = [r3+0]
    r0 = 0
    if (r2 == 0) goto L01c058ba
    r1 = b[r1+7] (u)
    if (r1 == 0) goto L01c058a2
    r1 = [r3+8]
    goto L01c058b0
L01c058a2:
    r1 = [r3+4]
    r1 = r1 >> 4
    if (r1 < 2021) goto L01c058ba
    r1 = r2 + 0x2000
L01c058b0:
    if (r1 == 0) goto L01c058ba
    r0 = [r1+40]
    if (r0 != 0) goto L01c058b8
    r1 = r0
L01c058b8:
    r0 = r1
L01c058ba:
    rts

; effect_processing_cost: 0x01c058bc..0x01c05c08, module effect-processing (cost)
.type effect_processing_cost,@function
effect_processing_cost:
    [--sp] = {rets, r9-r4}
    r2 = b[r0+0] (u)
    r4 = r2 + -4
    r7 = effect_processing_costs
    r8 = r0 + 288
    if (r4 > 35) goto L01c059c6
    r5 = r4 << 1
    r6 = r0 + 328
    r9 = r0 + 372
    r3 = r0 + 416
    tbh [r5]
.if MINI_PRODUCT
effect_processing_cost_branches:
    .short (L01c05992 - effect_processing_cost_branches) / 2, (L01c059ac - effect_processing_cost_branches) / 2, (Lhr_cost_acoustic - effect_processing_cost_branches) / 2, (L01c059f0 - effect_processing_cost_branches) / 2, (L01c05a16 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c0593c - effect_processing_cost_branches) / 2
    .short (L01c0593c - effect_processing_cost_branches) / 2, (L01c05a28 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2
    .short (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (Lhr_cost_harmonizer - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c05a38 - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2
    .short (L01c059c6 - effect_processing_cost_branches) / 2, (L01c05a58 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2, (L01c05a72 - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2
    .short (L01c05950 - effect_processing_cost_branches) / 2, (L01c05950 - effect_processing_cost_branches) / 2, (L01c05a9c - effect_processing_cost_branches) / 2, (L01c05aac - effect_processing_cost_branches) / 2
.else
effect_processing_cost_branches:
    .short (L01c05992 - effect_processing_cost_branches) / 2, (L01c059ac - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059f0 - effect_processing_cost_branches) / 2, (L01c05a16 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c0593c - effect_processing_cost_branches) / 2
    .short (L01c0593c - effect_processing_cost_branches) / 2, (L01c05a28 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2
    .short (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c05a38 - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2
    .short (L01c059c6 - effect_processing_cost_branches) / 2, (L01c05a58 - effect_processing_cost_branches) / 2, (L01c059c6 - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2, (L01c05a72 - effect_processing_cost_branches) / 2, (L01c0592a - effect_processing_cost_branches) / 2
    .short (L01c05950 - effect_processing_cost_branches) / 2, (L01c05950 - effect_processing_cost_branches) / 2, (L01c05a9c - effect_processing_cost_branches) / 2, (L01c05aac - effect_processing_cost_branches) / 2
.endif
; HyperRig MINI, product option: the acoustic block costs more with 12 strings, the harmonizer with two voices.
.if MINI_PRODUCT
Lhr_cost_acoustic:
    r0 = [r7+r2<<2]
    r1 = [r8+0]
    if (r1 == 0) goto Lhr_cost_done
    r1 = 20000
    r0 = r0 + r1
    goto Lhr_cost_done
Lhr_cost_harmonizer:
    r0 = [r7+r2<<2]
    r1 = [r8+8]
    if (r1 == 0) goto Lhr_cost_done
    r1 = [r8+12]
    if (r1 == 0) goto Lhr_cost_done
    r1 = 2500
    r0 = r0 + r1
Lhr_cost_done:
    {pc, r9-r4} = [sp++]
Lhr_cost_own:
    r0 = r2
    call hyperrig_effect_cost  ; @call.xl
    {pc, r9-r4} = [sp++]
.endif
L01c0592a:
    r0 = [r7+r2<<2]
    r2 = r0 + -485
    if (r1 != 0) goto L01c05bde
    r0 = r2
    {pc, r9-r4} = [sp++]
L01c0593c:
    r3 = [r8+36]
    r0 = [r7+r2<<2]
    r1 = 1550
    if (r3 != 0) goto L01c0594c
    r1 = r3
L01c0594c:
    r0 = r0 + r1
    {pc, r9-r4} = [sp++]
L01c05950:
    r0 = [r3+56]
    r1 = r0 & 0x1
    r4 = uextra(r0, p:1, l:1)
    r1 = r1 + r4
    if (r2 != 37) goto L01c05ad4
    r2 = uextra(r0, p:2, l:1)  #
    r4 = [r3+60]
    if (r4 == 0) goto L01c0596a
    r4 = r2
L01c0596a:
    r2 = 0
    if (r0 == 0) goto L01c0597e
L01c0596e:
    r5 = r0
    r6 = r5 + -1
    r0 = r6 & r5
    r2 = r2 + 1
    if ((r6 & r5) != 0) goto L01c0596e
L01c0597e:
    r0 = r4 + r1  #
    r3 = [r3+48]
    r1 = 1
    if (r3 == 65536) {
    r1 = 0
    }
    r1 = r1 << 6
    r0 = r0 << 3
    r0 |= r2
    goto L01c05afc
L01c05992:
    r2 = b[r6+0] (u)
    r0 = b[r9+0] (u)
    r0 = r0 + r2  #
    r1 = b[r3+0] (u)
    r0 = r0 + r1
    r0 = r0 * 0x244
    r1 = 155
    if (r2 != 0) goto L01c059a8
    r1 = 100
L01c059a8:
    r0 = r0 + r1
    {pc, r9-r4} = [sp++]
L01c059ac:
    r0 = 1940
    if (r1 != 0) goto L01c059b6
    r0 = 1635
L01c059b6:
    r2 = [r9+36]
    r1 = 330
    if (r2 != 0) goto L01c059c2
    r1 = r2
L01c059c2:
    r0 = r0 + r1
    {pc, r9-r4} = [sp++]
L01c059c6:
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on.
.if MINI_PRODUCT
    if (r2 > 39) goto Lhr_cost_own
.endif
    r1 = b[r0+6] (u)
    if (r1 == 0) goto L01c05b22
    r3 = [r7+r2<<2]
    if (r1 != 3) goto L01c05b78
    r5 = r2 + -3
    r3 = r3 << 1
    r3 = r3 + 1875
    r4 = 0
    if (r5 <= 20) {
    r4 = effect_processing_oversampling_costs
    r4 = [r4+r5<<2]
    }
    goto L01c05b8e
L01c059f0:
    r0 = [r8+0]
    if (r0 == 0) goto L01c05b28
    call effect_processing_ir_active  ; @call.xl
    if (r0 == 0) goto L01c05b66
    r0 = [r8+0]
    r4 = [r8+4]
    if (r0 == 0) goto L01c05b36
    call effect_processing_ir_accelerated  ; @call.xl
    goto L01c05b3e
L01c05a16:
    r1 = [r8+20]
    r0 = 895
    ifs (r1 < 65536) goto L01c05bde
    r0 += -70
    {pc, r9-r4} = [sp++]
L01c05a28:
    r0 = 3775  #
    r1 = [r3+60]
    if (r1 != 0) goto L01c05bde
    r0 = 2225
    {pc, r9-r4} = [sp++]
L01c05a38:
    r4 = 460  #
    r1 = b[r6+0] (u)
    r2 = b[r9+0] (u)
    r1 = r1 + r2  #
    r3 = b[r3+0] (u)
    r0 = b[r0+r4] (u)
    r1 = r1 + r3
    r0 = r0 + r1
    r1 = 635
    r0 *= r1
    r0 += 100
    {pc, r9-r4} = [sp++]
L01c05a58:
    r1 = h[r0+82] (u)
    if (r1 == 0) goto L01c05b60
    call effect_processing_capture_probe
    if (r0 == 0) goto L01c05be0
    r1 = 3070
    r1 = [r0+r1<<2]
    goto L01c05bee
L01c05a72:
    r0 = h[r0+76] (s)
    r2 = r0
    ifs (r0 >= 3) {
    r2 = 3
    }
    r3 = 1
    ifs (r0 >= 1) {
    r3 = r2
    }
    r0 = effect_processing_capture_costs
    r0 = h[r0+r3<<1] (u)
    r2 = r0 + -485
    if (r1 != 0) goto L01c05bde
    r0 = r2
    {pc, r9-r4} = [sp++]
L01c05a9c:
    r1 = [r9+36]
    r0 = 1530
    if (r1 != 0) goto L01c05bde
    r0 += -40
    {pc, r9-r4} = [sp++]
L01c05aac:
    r1 = [r9+40]
    r0 = 5850
    if (r1 != 0) goto L01c05ac0
    r1 = [r9+44]
    if (r1 != 0) goto L01c05ac0
    r0 = 3680
L01c05ac0:
    r3 = 4135  #
    r2 = [r6+24]
    r1 = 680
    ifs (r2 <= r3) {
    r1 = 0
    }
    r0 = r0 + r1
    {pc, r9-r4} = [sp++]
L01c05ad4:
    r2 = uextra(r0, p:2, l:1)
    r1 = r1 + r2
    r2 = uextra(r0, p:3, l:1)
    r4 = uextra(r0, p:4, l:1)
    r2 = r2 + r4
    r0 = uextra(r0, p:5, l:1)
    r0 = r0 + r2  #
    r2 = [r3+48]
    r0 = r0 + r1
    r1 = r1 << 3
    r0 |= r1
    r1 = 1
    if (r2 == 65536) {
    r1 = 0
    }
    r1 = r1 << 6
L01c05afc:
    r0 |= r1
    r1 = 270
    if (r0 <= 63) {
    r1 = 0
    }
    r2 = r0 & 0x7
    r3 = 595
    r2 *= r3
    r1 = r1 + r2
    r0 = uextra(r0, p:3, l:3)
    r0 = r0 * 0x37
    r0 = r0 + r1
    r0 += 100
    {pc, r9-r4} = [sp++]
L01c05b22:
    r3 = [r7+r2<<2]
    goto L01c05ba0
L01c05b28:
    r0 = L01c1f7d0
    r0 = [r0+0]
    if (r0 == 0) goto L01c05b66
    r4 = [r8+4]
L01c05b36:
    r0 = L01c1fa14
    r0 = [r0+0]
L01c05b3e:
    r1 = r4 + 127
    r2 = r1 >> 7
    r1 = 377
    r1 *= r2
    r1 = r1 + 5950
    if (r2 != 0) goto L01c05b54
    r1 = 6327
L01c05b54:
    r2 = 2600
    if (r0 != 0) goto L01c05b5c
    r2 = r0
L01c05b5c:
    r0 = r1 - r2
    {pc, r9-r4} = [sp++]
L01c05b60:
    r0 = 4450
    {pc, r9-r4} = [sp++]
L01c05b66:
    r0 = [r8+4]
    r0 += 63
    r0 = r0 >> 6
    r0 = r0 * 0xE6
    r0 = r0 + 6125
    {pc, r9-r4} = [sp++]
L01c05b78:
    r5 = 3990
    if (r1 != 2) {
    r5 = 130
    }
    r4 = 1875
    if (r1 != 1) {
    r4 = r5
    }
    r3 <<= r1
L01c05b8e:
    r3 = r3 + r4
    r5 = b[r0+46] (u)
    r4 = 1875
    if (r5 != 2) {
    r4 = 0
    }
    r3 = r3 - r4
L01c05ba0:
    r4 = r2 + -17
    r5 = 0
    if (r4 >= 4) goto L01c05bb0
    r0 = r8 + 172
    goto L01c05bc6
L01c05bb0:
    r4 = r2 + -9
    if (r4 >= 2) goto L01c05bbe
    r0 = r8 + 56
    goto L01c05bc6
L01c05bbe:
    if (r2 != 3) goto L01c05bdc
    r0 = r0 + 312
L01c05bc6:
    r0 = [r0+0]
    if (r0 == 0) goto L01c05bdc
    r0 = 600
    r0 <<= r1
    r1 |= 1
    r5 = 1200
    if (r1 != 3) {
    r5 = r0
    }
L01c05bdc:
    r0 = r5 + r3
L01c05bde:
    {pc, r9-r4} = [sp++]
L01c05be0:
    r0 = L01c1f7d8
    r0 = [r0+0]
    r1 = 1
    if (r0 != 0) goto L01c05bee
    r1 = r0
L01c05bee:
    r0 = 4500
    if (r1 != 0) goto L01c05bf8
    r0 = 8140
L01c05bf8:
    r2 = b[r9+0] (u)
    r1 = 570
    if (r2 != 0) goto L01c05c04
    r1 = r2
L01c05c04:
    r0 = r0 + r1
    {pc, r9-r4} = [sp++]

; effect_processing_extra_cost: 0x01c05c08..0x01c05d02, module effect-processing (extra_cost)
.type effect_processing_extra_cost,@function
effect_processing_extra_cost:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r0 = L01c2c220
    r0 = r4 - r0  #
    r7 = b[r4+0] (u)
    r5 = 480
    r5 = r0 / r5 (s)  #
    r0 = [sp+24]
    r6 = 1
    r5 = r6 << r5
    r6 = r4 + 412
    r8 = 0
    if (r7 != 25) goto L01c05c4e
    if ((r5 & r0) == 0) goto L01c05cfe
    if (r2 == 0) goto L01c05cfe
    r1 = b[r6+8] (u)
    if (r1 == 0) goto L01c05cfe
    r0 = b[r6+9] (u)
    if (r2 != 100) goto L01c05c80
    if (r1 != 100) goto L01c05c80
    r1 = 1200
    r8 = 2350
    goto L01c05c88
L01c05c4e:
    if ((r5 & r0) == 0) goto L01c05cfe
    if (r2 == 0) goto L01c05cfe
    r0 = r5 & r3
    if (r0 == 0) goto L01c05cfe
    r0 = r4
    call dsp_stage_capability
    if (r0 == 0) goto L01c05cfe
    r1 = [sp+28]
    if ((r5 & r1) != 0) goto L01c05c6c
    ifs (r0 > 1) goto L01c05cfe
L01c05c6c:
    if (r0 != 3) goto L01c05c94
    r1 = 1
    r0 = r4
    call effect_processing_cost
    r8 = r0 + 80
    r0 = r8
    {pc, r8-r4} = [sp++]
L01c05c80:
    r1 = 2750
    r8 = 3550
L01c05c88:
    if ((r0 & 0xFF) != 0) goto L01c05cfe
    r8 = r1
    r0 = r8
    {pc, r8-r4} = [sp++]
L01c05c94:
    r0 = r7 + -5
    if (r0 > 34) goto L01c05ce4
    r8 = 300
    tbb [r0]
effect_processing_extra_cost_branches:
    .byte (L01c05cd4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05cce - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2
    .byte (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05cfe - effect_processing_extra_cost_branches) / 2, (L01c05cce - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2
    .byte (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05cd4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2
    .byte (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05cc6 - effect_processing_extra_cost_branches) / 2, (L01c05cc6 - effect_processing_extra_cost_branches) / 2, (L01c05cdc - effect_processing_extra_cost_branches) / 2, (L01c05cdc - effect_processing_extra_cost_branches) / 2, (L01c05cc6 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2
    .byte (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05ce4 - effect_processing_extra_cost_branches) / 2, (L01c05cea - effect_processing_extra_cost_branches) / 2
    .byte 0x00  ; alignment
L01c05cc6:
    r8 = 1400
    r0 = r8
    {pc, r8-r4} = [sp++]
L01c05cce:
    r8 = 2400
    goto L01c05cfe
L01c05cd4:
    r8 = 1200
    r0 = r8
    {pc, r8-r4} = [sp++]
L01c05cdc:
    r8 = 700
    r0 = r8
    {pc, r8-r4} = [sp++]
L01c05ce4:
    r8 = 0
    r0 = 0
    {pc, r8-r4} = [sp++]
L01c05cea:
    r8 = 1140  #
    r0 = [r6+0]
    if (r0 != 0) goto L01c05cfe
    r0 = [r6+4]
    if (r0 != 0) goto L01c05cfe
    r8 = 3310
    r0 = r8
    {pc, r8-r4} = [sp++]
L01c05cfe:
    r0 = r8
    {pc, r8-r4} = [sp++]
