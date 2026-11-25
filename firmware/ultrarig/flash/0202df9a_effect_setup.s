; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 11 functions, 0x0202df9a..0x0202eabc

; effect_setup_saturating_double: 0x0202df9a..0x0202dfb6, module effect-setup (saturating_double)
.type effect_setup_saturating_double,@function
effect_setup_saturating_double:
    r1 = r0
    ifs (r1 >= 1073741824) {
    r0 = 2147483647
    rts
    }
    r2 = r1 << 1
    r0 = 0x80000000
    ifs (r1 > 3221225472) {
    r0 = r2
    }
    rts

; effect_setup_phase_pair: 0x0202dfb6..0x0202dfe4, module effect-setup (phase_pair)
.type effect_setup_phase_pair,@function
effect_setup_phase_pair:
    [--sp] = {rets, r7-r4}
    r4 = r1
    r1 = r4 + 256
    r6 = 1023
    r1 &= r6
    r7 = r0 + 3020
    r0 = [r7+r1<<2]
    r5 = r2
    call effect_setup_saturating_double
    r0 = r4 & r6  #
    [r5+0] = r0
    r0 = [r7+r0<<2]
    r0 = 0x0 - r0
    call effect_setup_saturating_double
    [r3+0] = r0
    {pc, r7-r4} = [sp++]

; effect_setup_initialize29: 0x0202dfe4..0x0202e328, module effect-setup (initialize29)
.type effect_setup_initialize29,@function
effect_setup_initialize29:
    [--sp] = {rets, r15-r4}
    sp += -12
    r11 = r0
    r6 = 0
    r0 = 0
    r1 = 1
    r5 = 1
    call effect_setup_layout29  ; @call.xl
    r0 = r0 >> 2
    if (r0 == 0) goto L0202e004
    r1 = r11
L0202dffe:
    [r1++=4] = r6
    if (--r0 != 0) goto L0202dffe
L0202e004:
    r1 = 1
    r0 = r11
    call effect_setup_layout29  ; @call.xl
    r0 = 1
    r1 = r0 + 1023
    [r11+36] = r0
    [r11+40] = r1
    r0 = r0 + 511
    r1 = r0 + 1
    [r11+44] = r0
    [r11+48] = r1
    [r11+52] = 0x200
    r0 = L01c1f7d8
    r0 = 12280  #
    r0 = [r0+0]
    [++r0=r11] = r5
    [r0+20] = 0x800
    r0 = 4
    r1 += 127
    [r11+56] = r0
    [r11+60] = r1
    r0 = 2047
    [r11+64] = r0
    r12 = r11 + 0x3040
    r0 = [r12+12]
    [r12+16] = r0
    [r11+0] = 0x10000
    [r11+20] = 0x2
    [r11+12] = 0x580
    r5 = r11 + 3020
    r7 = 1070141403
    r4 = r6 + 0x3B800000
    r13 = r4 + 0x13000000
    r14 = r4 + 0x3800000
L0202e084:
    r0 = utof(r6)
    r0 = r0 * r7 (f)
    r0 = r0 * r4 (f)
    call biquad_generator_sine
    r0 = r0 * r13 (f)
    r0 = r0 + r14 (f)
    r0 = ftoi(r0) (trunc)
    [r5+r6<<2] = r0
    r6 = r6 + 1
    if (r6 != 257) goto L0202e084
    r0 = 1011
    r1 = 0x40000000
    [r11+r0<<2] = r1
    r0 += -1
    r1 = 0
    r2 = r11 + 4048
L0202e0be:
    r3 = r1 + 257
    if (r3 > 512) goto L0202e0cc
    r3 = [r11+r0<<2]
    goto L0202e0e2
L0202e0cc:
    r6 = r0 + -243
    r4 = r1 + -255
    if (r3 >= 769) {
    r4 = r6
    }
    r3 = [r5+r4<<2]
    r3 = 0x0 - r3
L0202e0e2:
    [r2+r1<<2] = r3
    r1 = r1 + 1
    r0 += -1
    if (r1 != 768) goto L0202e0be
    r0 = [r12+8]
    r1 = 0
    r10 = 1023
    r15 = 2147483647
    r2 = r15
    r3 = 0
    [sp] = r2
    [sp+4] = r3
    r2 = 0
L0202e10a:
    r6 = r2 + 256
    r6 = r6 & r10
    r8 = [r5+r6<<2]
    r9 = r8 >>> 31
    r6 = 0x40000000 - r8
    r7 = r1 - r9 - !c
    r4 = r6 - r15
    r4 = r7 - r1 - !c
    r4 = psr
    r3 = r4 >> 3
    r3 ^= r4
    if ((r3 & 0x1) == 0) {
    r6 = [sp]
    r7 = [sp+4]
    }
    [r0+r2<<2] = r6
    r3 = [r11+40]
    r2 = r2 + 1
    r3 = r3 >> 1
    if (r2 <= r3) goto L0202e10a
    r10 = r11 + 1008
    r6 = 0
    r9 = 268435452
L0202e156:
    r1 = r6 + r9
    r0 = r6 << 2
    if (r6 >= 4) {
    r0 = r1
    }
    r4 = r0 << 4
    r5 = 3
    r3 = r10
    r7 = r4
L0202e16a:
    r1 = r7 & 0x3F0
    r2 = r3 + -4
    r0 = r11
    call effect_setup_phase_pair
    r7 = r7 + r4
    r3 = r3 + 8
    if (--r5 != 0) goto L0202e16a
    r6 = r6 + 1
    r10 = r10 + 24
    if (r6 != 20) goto L0202e156
    r5 = 0
L0202e18c:
    r0 = r11 + r5
    r2 = r0 + 1484
    r3 = r0 + 1488
    r0 = r11
    r1 = r5
    call effect_setup_phase_pair
    r5 = r5 + 8
    if (r5 != 512) goto L0202e18c
    r3 = r11 + 2000
    r5 = 0
L0202e1ae:
    r2 = r3 + -4
    r0 = r11
    r1 = r5
    call effect_setup_phase_pair
    r5 = r5 + 4
    r3 = r3 + 8
    if (r5 != 512) goto L0202e1ae
    r5_r4 = 0
L0202e1c6:
    r0 = [r12+12]
    r2 = r0 + r4
    r3 = r2 + 4
    r0 = r11
    r1 = r5
    call effect_setup_phase_pair
    r5 = r5 + 2
    r4 = r4 + 8
    if (r5 != 512) goto L0202e1c6
    r0 = [r11+48]
    if (r0 != 0) goto L0202e304
L0202e1e8:
    r0 = [r11+44]
    if (r0 == 0) goto L0202e22c
    r1 = [r12+0]
    r3_r2 = 0
    r5 = 0
L0202e1f6:
    r4 = r5 & 0x2
    r6 = r2 & 0x4
    r4 |= r6
    r6 = uextra(r5, p:2, l:1)
    r4 |= r6
    r6 = r3 & 0x30
    r7 = r5 >> 3
    r7 = r7 & 0xC
    r6 |= r7
    r7 = uextra(r5, p:7, l:2)
    r6 |= r7
    r6 <= insert(r4, p:6, l:3)
    r4 = r6 << 3
    h[r1+r3] = r4
    r2 = r2 + 4
    r5 = r5 + 1
    r3 = r3 + 2
    if (r5 < r0) goto L0202e1f6
L0202e22c:
    r0 = 11764
    r0 += r11
    r10 = r11 + 7120  #
    [sp] = r0
    r5 = 0
    r15 = 1078530011
    r11 = r5 + 0x3F800000
    r7 = 0
    r8 = r5 + 0xBF000000
L0202e24a:
    r0 = utof(r5)
    r1 = r8 + 0x3800000
    r0 = r0 + r1 (f)
    r1 = r1 + 0x79800000
    r9 = r0 * r1 (f)
    r12 = r9 * r15 (f)
    r0 = r12
    call biquad_generator_sine
    r1 = r5 << 2
    r1 += r10
    r2 = r0 ^ 0x80000000
    r3 = -4
L0202e272:
    if (r5 != 64) goto L0202e28c
    r6 = r11
    if (r3 == 0) goto L0202e2a8
    r4 = r8
    if (r3 != 4294967295) {
    r4 = 0
    }
    r6 = r8
    if (r3 != 1) {
    r6 = r4
    }
    goto L0202e2a8
L0202e28c:
    r4 = itof(r3)
    r4 = r4 - r9 (f)
    r6 = r4 * r15 (f)
    r4 = r4 * r4 (f)
    r4 = r11 - r4 (f)
    r4 = r6 * r4 (f)
    r6 = r2 / r4 (f)
L0202e2a8:
    r4 = r14
    iff (r6 u< r7) {
    r4 = r8
    }
    r6 = r6 * r13 (f)
    r4 = r6 + r4 (f)
    r4 = ftoi(r4) (trunc)
    r3 = r3 + 1
    [r1++=516] = r4
    if (r3 != 5) goto L0202e272
    if (r5 != 64) goto L0202e2d8
    r1 = 0x40000000  #
    r0 = [sp]
    [r0+r5<<2] = r1
    r5 = 65
    goto L0202e24a
L0202e2d8:
    r1 = r9 * r9 (f)
    r1 = r11 - r1 (f)
    r1 = r12 * r1 (f)
    r0 = r1 / r0 (f)  #
    r1 = [sp]
    r0 = r0 * r13 (f)
    r0 = r0 + r14 (f)
    r0 = ftoi(r0) (trunc)
    [r1+r5<<2] = r0
    r5 = r5 + 1
    if (r5 != 129) goto L0202e24a
    sp += 12
    {pc, r15-r4} = [sp++]
L0202e304:
    r5 = 0
    r4 = 4
L0202e308:
    r0 = [r12+4]
    r3 = r0 + r4
    r2 = r3 + -4
    r0 = r11
    r1 = r5
    call effect_setup_phase_pair
    r0 = [r11+48]
    r5 = r5 + 1
    r4 = r4 + 8
    if (r5 < r0) goto L0202e308
    goto L0202e1e8

; effect_setup_refresh29: 0x0202e328..0x0202e346, module effect-setup (refresh29)
.type effect_setup_refresh29,@function
effect_setup_refresh29:
    [--sp] = rets
    r1 = b[r0+0] (u)
    if (r1 != 29) goto L0202e33e
    r1 = h[r0+82] (u)
    if (r1 == 0) goto L0202e33e
    call effect_parameter_support_extra  ; @call.xl
    if (r0 != 0) goto L0202e340
L0202e33e:
    pc = [sp++]
L0202e340:
    call effect_setup_initialize29
    pc = [sp++]

; effect_setup_initialize30: 0x0202e346..0x0202e3ce, module effect-setup (initialize30)
.type effect_setup_initialize30,@function
effect_setup_initialize30:
    [--sp] = {rets, r14-r4}
    r8 = r1
    r9 = r0
    r0 = 5102
    r1 = 0
    r2 = r9
L0202e354:
    [r2++=4] = r1
    if (--r0 != 0) goto L0202e354
    [r9+12] = 0x280
    r0 = 1397904945
    [r9+0] = r0
    r0 = 17324
    r6 = r9 + r0
    r0 = 15280
    r7 = r9 + r0
    r4 = 0
    r10 = r1 + 0x3F000000
    r11 = 1078530011
    r12 = r1 + 0x3B000000
    r14 = r1 + 0x4F000000
    r13 = 2147483647
    r5 = r1 + 0x3F800000
L0202e396:
    r0 = utof(r4)
    r0 = r0 + r10 (f)
    r0 = r0 * r11 (f)
    r0 = r0 * r12 (f)
    call biquad_generator_sine
    r1 = r0 * r14 (f)
    r1 = ftoi(r1) (trunc)
    iff (r0 >= r5) {
    r1 = r13
    }
    [r6++=-4] = r1
    [r7+r4<<2] = r1
    r4 = r4 + 1
    if (r4 != 256) goto L0202e396
    r0 = r9
    r1 = r8
    call effect_model_construction_signature_coefficients
    {pc, r14-r4} = [sp++]

; effect_setup_refresh30: 0x0202e3ce..0x0202e3f6, module effect-setup (refresh30)
.type effect_setup_refresh30,@function
effect_setup_refresh30:
    [--sp] = rets
    r1 = b[r0+0] (u)
    if (r1 != 30) goto L0202e3ea
    r2 = [r0+84]
    if (r2 == 0) goto L0202e3ea
    r1 = [r0+88]
    r1 = r1 << 1
    r1 = r1 >> 3
    if (r1 >= 2551) goto L0202e3ec
L0202e3ea:
    pc = [sp++]
L0202e3ec:
    r1 = r0 + 70
    r0 = r2
    call effect_setup_initialize30
    pc = [sp++]

; effect_setup_pool_claim: 0x0202e3f6..0x0202e432, module effect-setup (pool_claim)
.type effect_setup_pool_claim,@function
effect_setup_pool_claim:
    [--sp] = {rets, r6-r4}
    r1 = L01c32db0
    r2 = b[r1+6] (u)
    r4 = 0
    r0 = L01c2fa38
    r5 = 1
L0202e40a:
    r3 = r5 << r4
    if ((r2 & r3) == 0) goto L0202e420
    r4 = r4 + 1
    r0 = r0 + 888
    ifs (r4 < 4) goto L0202e40a
    r0 = 0
    {pc, r6-r4} = [sp++]
L0202e420:
    r4 = 222
    r5 = 0
    r6 = r0
L0202e426:
    [r6++=4] = r5
    if (--r4 != 0) goto L0202e426
    r2 |= r3
    b[r1+6] = r2
    {pc, r6-r4} = [sp++]

; effect_setup_pool_attach: 0x0202e432..0x0202e4c2, module effect-setup (pool_attach)
.type effect_setup_pool_attach,@function
effect_setup_pool_attach:
    [--sp] = {rets, r10-r4}
    r4 = r1
    r6 = r0
    call effect_setup_pool_claim
    r5 = r0
    if (r5 != 0) goto L0202e44c
    r0 = L01c3448b
    r1 = 1
    b[r0+0] = r1
    r0 = -3
    {pc, r10-r4} = [sp++]
L0202e44c:
    [r6+288] = r5
    r7 = b[r6+0] (u)
    r0 = r7
    call effect_setup_object_count
    r8 = r0
    r0 = r7
    call effect_model_construction_object_mode  ; @call.xl
    r9 = r5 + 624
    b[r9+8] = r0
    ifs (r8 >= 1) goto L0202e49c
L0202e46e:
    if (r7 == 31) goto L0202e480
    if (r7 == 34) {
    r0 = [r4+r8<<2]
    [r9+52] = r0
    }
    goto L0202e494
L0202e480:
    r0 = [r4+r8<<2]
    [r9+52] = r0
    r0 = [r4+r8<<2]
    r0 = r0 + 0x2000
    [r9+56] = r0
L0202e494:
    r0 = 0
    [r9+0] = r0
    {pc, r10-r4} = [sp++]
L0202e49c:
    r10 = 0
    r6 = 0
L0202e4a0:
    r0 = r7
    r1 = r6
    call effect_setup_object_segment
    r1 = r6 << 2
    r1 = r1 + r5
    [r1+80] = r0
    [r1+160] = r10
    r0 = [r4+r6<<2]
    r6 = r6 + 1
    [r1+0] = r0
    if (r8 != r6) goto L0202e4a0
    goto L0202e46e

; effect_setup_allocate: 0x0202e4c2..0x0202e710, module effect-setup (allocate)
.type effect_setup_allocate,@function
effect_setup_allocate:
    [--sp] = {rets, r15-r4}
    sp += -292
    r4 = h[r0+82] (s)
    r11 = r0  #
    r0 = b[r0+0] (u)
    r9 = r1
    r2 = sp + 208
    r3 = sp + 120
    r1 = r4
    call effect_setup_partition_sizes
    r12 = r0
    r0 = 0
    b[r11+7] = r0
    r0 = r9 << 1
    r0 = r0 + 2
    r14 = r0 & 0xFFFFFFFC
    r0 = r14
    call effect_parameter_lifecycle_resource_allocate
    r15 = r11 + 84
    [r15+0] = r0
    if (r0 == 0) goto L0202e574
    r1 = r9
    call effect_parameter_support_clear_halfwords  ; @call.xl
    [r15+4] = r9
    ifs (r12 < 1) goto L0202e60c
    r0 = 0
    r1 = sp + 99
    r2 = sp + 124
    r3 = sp + 208
    r4 = r12
    r5 = 0
L0202e51c:
    b[r1++=1] = r0
    [r2++=4] = r5
    r6 = [r3++=4]
    r5 = r5 + r6
    if (--r4 != 0) goto L0202e51c
L0202e528:
    r0 = 1
    b[r11+5] = r0
    ifs (r12 < 1) goto L0202e54c
    r3 = sp + 99
    r4 = sp + 124
    r5 = sp + 12
L0202e538:
    r0 = r11  #
    r1 = b[r3++=1] (u)
    call effect_setup_buffer_selector  ; @call.xl
    r1 = [r4++=4]
    r0 = r0 + r1
    [r5++=4] = r0
    if (--r12 != 0) goto L0202e538
L0202e54c:
    r0 = r11
    call effect_setup_refresh29
    r0 = r11
    call effect_setup_refresh30
    r0 = b[r11+0] (u)
    r0 += -27
    r13 = 0
    if (r0 > 8) goto L0202e56e
    r1 = 497
    r0 = r1 & (1 << r0)
    if (r0 != 0) goto L0202e5f6
L0202e56e:
    r0 = r13
    sp += 292
    {pc, r15-r4} = [sp++]
L0202e574:
    r13 = -3
    ifs (r12 < 2) goto L0202e56e
    r0 = L01c343d4
    r1 = [r0+0]
    if (r1 == 0) goto L0202e56e
    r0 = 1
    r0 = r0 << r12
    r4 = r0 + -1
    if (r4 != 0) goto L0202e614
L0202e592:
    r0 = b[sp+99] (u)
    if (r0 == 0) goto L0202e528
    r1 = r0 + -1
    r2 = r1 << 2
    r2 += r11
    r3 = [r2+92]
    r4 = [r15+4]
    r5 = [r15+0]
    [r15+0] = r3
    r1 = r1 << 1
    r1 += r11
    r3 = h[r1+104] (u)
    r3 = r3 << 1
    [r15+4] = r3
    [r2+92] = r5
    r2 = r4 >> 1
    h[r1+104] = r2
    ifs (r12 < 1) goto L0202e60c
    r1 = 0
    b[sp+99] = r1
    if (r12 == 1) goto L0202e528
    r1 = sp + 99
    r1 = r1 + 1
    r2 = r12 + -1
L0202e5de:
    r4 = r0  #
    r3 = b[r1+0] (u)
    if (r3 == 0) goto L0202e5e6
    r4 = r3
L0202e5e6:
    r5 = 0
    if (r3 != r0) {
    r5 = r4
    }
    b[r1++=1] = r5
    if (--r2 != 0) goto L0202e5de
    goto L0202e528
L0202e5f6:
    r1 = sp + 12
    r0 = r11
    call effect_setup_pool_attach
    if (r0 == 0) goto L0202e56e
    r0 = r11
    call effect_ownership_release
    r13 = -3
    goto L0202e56e
L0202e60c:
    r0 = 1
    b[r11+5] = r0
    goto L0202e54c
L0202e614:
    r5 = [sp+120]
    call r1
    r1 = r0 + -16  #
    [sp+4] = r5
    r3 = r1 - r5
    r1 = r5 + 16
    [sp] = r1
    if (r0 <= r1) {
    r3 = 0
    }
    r0 = sp + 208
    r1 = r12  #
    [sp+8] = r4
    r2 = r4
    call effect_setup_partition_pack
    r8 = [sp+8]
    r4 = r0
    r6 = L01c343d4
    r10 = r6
    if (r4 == 0) goto L0202e6f6
    r7 = 0
L0202e648:
    r1_r0 = 0  #
    r6 = [sp+4]
L0202e64c:
    r2 = r4 & (1 << r1)
    if (r2 == 0) goto L0202e668
    r2 = sp + 99
    r3 = sp + 208
    r3 = [r3+r1<<2]
    b[r2+r1] = r7
    r2 = sp + 124
    [r2+r1<<2] = r0
    r0 = r0 + r3
L0202e668:
    r1 = r1 + 1
    if (r12 != r1) goto L0202e64c
    r5 = r6 + r0
    r0 = r5 >> 18
    if (r0 != 0) goto L0202e6f2
    r0 = r5
    call effect_parameter_lifecycle_resource_allocate
    r9 = r0
    if (r0 == 0) goto L0202e6f2
    r1 = r5 >> 1
    [sp+8] = r1
    call effect_parameter_support_clear_halfwords  ; @call.xl
    if (r7 == 0) goto L0202e6a6
    r0 = r5 >> 2
    r1 = r7 + -1
    r2 = r11 + 92
    [r2+r1<<2] = r9
    r2 = r11 + 104
    h[r2+r1<<1] = r0
    b[r11+7] = r7
    goto L0202e6b0
L0202e6a6:
    [r15+0] = r9
    r0 = [sp+8]
    [r15+4] = r0
L0202e6b0:
    r7 = r7 + 1
    r8 = r8 & ~r4
    if (r7 > 3) goto L0202e6f2
    if (r8 == 0) goto L0202e6f2
    [sp+8] = r7
    r0 = [r10+0]
    call r0
    r1 = r0 + -16
    r3 = r1 - r6  #
    r1 = [sp]
    if (r0 <= r1) {
    r3 = 0
    }
    r0 = sp + 208
    r1 = r12
    r2 = r8
    call effect_setup_partition_pack
    r8 = r2  #
    r7 = [sp+8]
    r4 = r0
    r6 = L01c343d4
    r10 = r6
    if (r4 != 0) goto L0202e648
    goto L0202e6f6
L0202e6f2:
    if (r8 == 0) goto L0202e592
L0202e6f6:
    r0 = r11
    call effect_ownership_release
    r0 = L01c34434
    r1 = [r0+0]
    if (r1 == 0) goto L0202e56e
    r0 = r14 + 16
    call r1
    goto L0202e56e

; effect_setup_create: 0x0202e710..0x0202ea90, module effect-setup (create)
.type effect_setup_create,@function
effect_setup_create:
    [--sp] = {rets, r15-r4}
    sp += -4
    r8 = r1
    r11 = r0
    call biquad_coefficients_counter  ; @call.xl
    r14 = L01c3448b
    r0 = 0
    b[r14+0] = r0
    r1 = 0
    r0 = r2
    call preset_preflight_convert_effect
    r12 = r0
    r0 = -1
    if (r11 > 1) goto L0202e780
    r1 = r12 + -1
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on.
.if MINI_PRODUCT
    if (r1 <= 38) goto Lhr_create_known
    r0 = r12
    call hyperrig_effect_rows  ; @call.xl
    r1 = r0
    r0 = -1
    if (r1 == 0) goto L0202e780
Lhr_create_known:
.else
    if (r1 > 38) goto L0202e780
.endif
    r15 = L01c32db0
    r0 = r11 + r15
    r2 = b[r0+14] (u)
    r0 = -2
    if (r2 > 9) goto L0202e780
.if MINI_PRODUCT
Lhr_create_again:
.endif
    r13 = L01c2e074
    r7 = L01c2c220
    r5 = 0
    r6 = 0
L0202e764:
    r1 = b[r7+2] (u)
    if (r1 == 0) goto L0202e77c
    r13 = r13 + 88
    r5 = r5 + 256
    r6 = r6 + 1
    r7 = r7 + 480
    ifs (r6 < 16) goto L0202e764
; HyperRig MINI, product option: no place left, but the sound of a block that was taken away may still ring in one.
.if MINI_PRODUCT
    call hyperrig_take_ringing  ; @call.xl
    if (r0 != 0) goto Lhr_create_again
    r0 = -2
.endif
    goto L0202e780
L0202e77c:
    ifs (r6 >= 0) goto L0202e784
L0202e780:
    sp += 4
    {pc, r15-r4} = [sp++]
L0202e784:
    r4 = L01c343c4
    r3 = [r4+0]
    if (r3 == 0) goto L0202e79a
    r0 = r12 | r5
    r1 = r0 | 0x10000
    r0 = 0
    call r3
L0202e79a:
    r0 = r12
    call effect_setup_default_mode  ; @call.xl
    r9 = r0
    ifs (r0 < 1) goto L0202e7d2
L0202e7a8:
    call effect_setup_total_cost
    r10 = r0
    r0 = r11
    r1 = r8
    r2 = r12
    r3 = r9
    call effect_setup_insertion_cost
    r1 = [r15+48]
    r0 += r10
    if (r0 <= r1) goto L0202e7d2
    r0 = r9
    call effect_setup_next_mode  ; @call.xl
    r9 = r0
    ifs (r0 > 0) goto L0202e7a8
L0202e7d2:
    r10 = 0
    if (r11 != 1) goto L0202e7f2
    r0 = b[r15+3] (u)
    if (r0 != 0) goto L0202e7f2
    r0 = L01c1f7f0
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L0202e7f2
    r0 = r12
    call effect_setup_stereo_extra_cost  ; @call.xl
    r10 = r0
L0202e7f2:
    r0 = b[r15+84] (u)
    if (r0 == 0) goto L0202e8ee
L0202e7f8:
    r0 = r6
    call dsp_initialization_reset_slot
    r3 = [r4+0]
    if (r3 == 0) goto L0202e812
    r0 = r12 | r5
    r1 = r0 | 0x20000
    r0 = 0
    r2 = 480
    call r3
L0202e812:
    r0 = r7 + 70
    r2 = r7  #
    [sp] = r0
    r0 = 120
    r1 = 0
L0202e81e:
    [r2++=4] = r1
    if (--r0 != 0) goto L0202e81e
    r3 = [r4+0]
    if (r3 == 0) goto L0202e836
    r0 = r12 | r5
    r1 = r0 | 0x30000
    r0 = 0
    r2 = 0
    call r3
L0202e836:
    b[r7+0] = r12
    r0 = L01c343d8
    r1 = 0
    [r0+r6<<2] = r1
; HyperRig MINI, product option: the parameters of an effect of HyperRig.
.if MINI_PRODUCT
    if (r12 <= 39) goto Lhr_create_listed
    r0 = r12
    call hyperrig_effect_rows  ; @call.xl
    r10 = r0
    r2 = [sp]
    goto Lhr_create_rows
Lhr_create_listed:
.endif
    r0 = r12 * 0x54  #
    r2 = [sp]
    r1 = effect_parameter_metadata
    r10 = r0 + r1
.if MINI_PRODUCT
Lhr_create_rows:
.endif
    r1 = -84
L0202e85a:
    r0 = r10 + r1
    r4 = [r0+92]
    r3 = 0
    if (r4 == 0) goto L0202e86a
    r3 = h[r0+88] (u)
L0202e86a:
    r1 = r1 + 12
    h[r2++=2] = r3
    if (r1 != 0) goto L0202e85a
    r4 = r6 + r15
    r0 = 268
    r10 = 0
    b[r4+r0] = r10
    r0 = r0 + 16
    b[r4+r0] = r10
    r0 = r7
    call dsp_stage_active  ; @call.xl
    r1 = 0
    if (r0 != 0) goto L0202e892
    r1 = 100
L0202e892:
    r0 = 300
    b[r4+r0] = r1
    [r13+0] = r10
    b[r7+6] = r9
    r0 = r12
    call effect_parameter_support_selector  ; @call.xl
    ifs (r0 > 4294967295) {
    r1 = uextra(r9, p:0, l:8)
    r2 = [sp]
    h[r2+r0<<1] = r1
    }
    r10 = b[r15+84] (u)
    r4 = L01c343c4
    if (r12 != 7) goto L0202e932
    r1 = [r15+64]
    r0 = -1
    r5 = L01c3441c
    if (r1 == 0) goto L0202e8e4
    r1 = [r15+60]
    if (r1 != 0) goto L0202e928
    r1 = [r15+72]
    if (r1 == 0) goto L0202e8e4
    r1 = [r5+0]
    if (r1 != 0) goto L0202e928
L0202e8e4:
    if ((r10 & 1) != 0) goto L0202e980
    r1 = 0
    b[r7+0] = r1
    goto L0202e780
L0202e8ee:
    call effect_setup_total_cost
    r4 = r0
    r0 = r12
    call effect_setup_has_mode  ; @call.xl
    if (r0 != 0) goto L0202e908
    r0 = r12
    call effect_setup_base_cost
    r0 += r10
    goto L0202e914
L0202e908:
    r0 = r11
    r1 = r8
    r2 = r12
    r3 = r9
    call effect_setup_insertion_cost
L0202e914:
    r1 = [r15+48]
    r2 = r0 + r4
    r0 = -4
    r4 = L01c343c4
    if (r2 > r1) goto L0202e780
    goto L0202e7f8
L0202e928:
    r0 = r7
    call ir_effect_lifecycle_select_source
    if (r0 != 0) goto L0202e8e4
    goto L0202e9ac
L0202e932:
    r0 = r7
    call effect_setup_demand
    r9 = r0  #
    r3 = [r4+0]
    if (r3 == 0) goto L0202e94c
    r0 = r12 | r5
    r1 = r0 | 0x40000
    r0 = 0
    r2 = r9
    call r3
L0202e94c:
    r0 = 1
    if (r9 != 0) {
    r0 = 0
    }
    r0 = r0 | r10
    if ((r0 & 1) != 0) goto L0202e9ce
    r0 = r12 + -27
    if (r0 > 8) goto L0202e9ce
    r1 = 497
    r0 = r1 & (1 << r0)
    if (r0 == 0) goto L0202e9ce
    call effect_setup_pool_full  ; @call.xl
    if (r0 == 0) goto L0202e9ce
    r0 = 1
    b[r14+0] = r0
    r0 = -3
    goto L0202e780
L0202e980:
    r1 = [r15+64]
    r0 = 0
    if (r1 == 0) goto L0202e9a8
    r1 = [r15+60]
    if (r1 != 0) goto L0202e998
    r1 = [r15+72]
    if (r1 == 0) goto L0202e9a8
    r1 = [r5+0]
    if (r1 == 0) goto L0202e9a8
L0202e998:
    r1 = h[r7+76] (s)
    r0 = L01c1f7d0
    r0 = [r0+0]
    call ir_convolution_installation_effective
L0202e9a8:
    [r7+292] = r0
L0202e9ac:
    r0 = r7
    call effect_construction_construct
    r0 = 1
    r1 = r8  #
    b[r7+1] = r0
    r0 = r11  #
    b[r7+2] = r0
    r2 = r6
    call effect_setup_route_insert
    r0 = r11
    r1 = r6
    call effect_ownership_neighbors
L0202e9ca:
    r0 = r6
    goto L0202e780
L0202e9ce:
    if (r9 != 0) goto L0202ea22
L0202e9d2:
    r0 = r7
    call effect_construction_construct
    r0 = L01c343c4
    r3 = [r0+0]
    if (r3 == 0) goto L0202e9f0
    r0 = r12 | r5
    r1 = r0 | 0x80000
    r0 = 0
    r2 = 0
    call r3
L0202e9f0:
    r0 = 1
    r1 = r8  #
    b[r7+1] = r0
    r0 = r11  #
    b[r7+2] = r0
    r2 = r6
    call effect_setup_route_insert
    r0 = r11
    r1 = r6
    call effect_ownership_neighbors
    r0 = L01c343c4
    r3 = [r0+0]
    if (r3 == 0) goto L0202e9ca
    r0 = r12 | r5
    r1 = r0 | 0x90000
    r0 = 0
    r2 = 0
    call r3
    goto L0202e9ca
L0202ea22:
    r0 = 1
    r4 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r0 = r7
    r1 = r9
    call effect_setup_allocate
    r1 = L01c343c4
    r9 = r0  #
    r3 = [r1+0]
    if (r3 == 0) goto L0202ea50
    r2 = [r7+84]
    r0 = r12 | r5
    r1 = r0 | 0x50000
    r0 = 0
    call r3
L0202ea50:
    if (r9 != 0) {
    r4 = 0
    }
    r0 = r10 | r4
    if ((r0 & 1) != 0) goto L0202ea6a
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r0 = -3
    goto L0202e780
L0202ea6a:
    if (r9 != 0) goto L0202ea86
    r0 = L01c343c4
    r3 = [r0+0]
    if (r3 == 0) goto L0202ea86
    r0 = r12 | r5  #
    r2 = b[r7+7] (u)
    r1 = r0 | 0x70000
    r0 = 0
    call r3
L0202ea86:
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    goto L0202e9d2

; effect_setup_create_disabled: 0x0202ea90..0x0202eabc, module effect-setup (create_disabled)
.type effect_setup_create_disabled,@function
effect_setup_create_disabled:
    [--sp] = {rets, r4}
    r4 = L01c32db0
    r3 = 1
    b[r4+84] = r3
    call effect_setup_create
    r1 = 0
    b[r4+84] = r1
    ifs (r0 >= 0) {
    r2 = r0 * 0x1E0
    r3 = L01c2c220
    r2 = r2 + r3
    b[r2+1] = r1
    }
    {pc, r4} = [sp++]
