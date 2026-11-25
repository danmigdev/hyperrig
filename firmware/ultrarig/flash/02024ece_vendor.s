; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02024ece..0x02025392: vendor code (JieLi SDK or library, not reversed), as instructions
L02024ece:
    r0 = 81960
    [r0+0] |= 0x10
    [r0+0] |= 0x10
    [r0+0] |= 0x10
    [r0+0] |= 0x10
    [r0+0] |= 0x10
    [r0+0] &= 0xFFFFFFEF
    [r0+0] &= 0xFFFFFFEF
    [r0+0] &= 0xFFFFFFEF
    [r0+0] &= 0xFFFFFFEF
    [r0+0] &= 0xFFFFFFEF
    rts
L02024efe:
    [--sp] = {rets, r4}
    sp += -20
    r4 = r0
    r0 = L0203510d
    r1 = r4
    rep 20 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r1 = sp + 0
    r0 = 108
    r2 = 20
    call L02024a78
    if (r0 != 20) goto L02024f38
    r0 = sp + 0
    rep 20 {
    r1 = b[r0++=1] (u)
    b[r4++=1] = r1
    }
    r0 = L01c26890
    r1 = b[r0+57] (u)
    r1 |= 4
    b[r0+57] = r1
L02024f38:
    sp += 20
    {pc, r4} = [sp++]
L02024f3c:
    [--sp] = rets
    sp += -40
    r0 = sp + 20
    r1 = L020355e8
    rep 20 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = sp + 0
    call L02024efe
    r0 = 0
L02024f54:
    r1 = sp + 0
    r1 = b[r1+r0] (u)
    if (r1 == 0) goto L02024f62
    r2 = sp + 20
    b[r2+r0] = r1
L02024f62:
    r0 += 1  ; @add.ri.u5
    if (r0 != 20) goto L02024f54
    r1 = b[sp+20] (u)
    r0 = 11
    call L02055a4e  ; @call.xl
    r1 = b[sp+21] (u)
    r0 = 13
    call L02055a4e  ; @call.xl
    r1 = b[sp+22] (u)
    r0 = 15
    call L02055a4e  ; @call.xl
    r1 = b[sp+23] (u)
    r0 = 17
    call L02055a4e  ; @call.xl
    r1 = b[sp+25] (u)
    r0 = 27
    call L02055a4e  ; @call.xl
    r1 = b[sp+27] (u)
    r0 = 29
    call L02055a4e  ; @call.xl
    r1 = b[sp+29] (u)
    r0 = 31
    call L02055a4e  ; @call.xl
    r1 = b[sp+31] (u)
    r0 = 33
    call L02055a4e  ; @call.xl
    r1 = b[sp+32] (u)
    r0 = 19
    call L02055a4e  ; @call.xl
    r1 = b[sp+34] (u)
    r0 = 21
    call L02055a4e  ; @call.xl
    r1 = b[sp+36] (u)
    r0 = 23
    call L02055a4e  ; @call.xl
    r1 = b[sp+39] (u)
    r0 = 25
    call L02055a4e  ; @call.xl
    sp += 40
    pc = [sp++]
sdk_wlc_wreg:
    r1 = r1 << 16
    r1 <= insert(r0, p:4, l:8)
    r0 = r1 | 0x1
    r1 = 81924
    [r1+0] = r0
    rts
L02025010:
    [--sp] = {rets, r4}
    r3 = r1
    r4 = r0
    r0 = 6
    r1 = r2
    call sdk_wlc_wreg
    r0 = r3 << 5
    r1 = r4 << 2
    r0 |= r1
    r1 = r0 | 0x1
    r0 = 7
    call sdk_wlc_wreg
    {pc, r4} = [sp++]
sdk_list_add_tail_0202502c:
    r2 = [r1+4]
    [r1+4] = r0
    [r0+] = {r2, r1}
    [r2+0] = r0
    rts
L02025038:
    [--sp] = rets
    r3 = r0
    if ((r3 & 0x3) != 0) {
    r0 = r3 & 0x3
    r0 = 0x4 - r0
    r3 += r0  ; @add.rr
    r1 = r1 - r0
    }
    if ((r3 & 0x3) != 0) goto L0202506e
    r0 = 65504
    r0 += r1  ; @add.rr
    h[r3+28] = r0
    [r3+0] = r3
    [r3+4] = r3
    r1 = r3 + 8
    [r3+8] = r1
    [r3+12] = r1
    r0 = r3 + 20
    call sdk_list_add_tail_0202502c
    r0 = r3
    pc = [sp++]
L0202506e:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02025078:
    goto L02025078
L0202507a:
    [--sp] = {rets, r6-r4}
    r5 = r0
    if (r5 == 0) goto L020250cc
    r4 = L01c25c90
    r0 = r4
    call L02040614  ; @call.xl
    r1 = 0
    r0 = 79104
    [r0+4] = r1
    r3 = b[r5+0] (u)
    r2 = r5 + 1
L0202509c:
    r3 = r3.b0 (s)
    [r0+0] = r3
    r3 = b[r2+r1] (u)
    r1 += 1  ; @add.ri.u5
    if (r3 != 0) goto L0202509c
    csync
    r6 = [r0+4]
    [r0+4] = 0x0
L020250b0:
    r2 = b[r5+r1] (s)
    [r0+0] = r2
    if (--r1 != 0) goto L020250b0
    csync
    r0 = r4  #
    r5 = [r0+4]
    call L0204074c  ; @call.xl
    r0 = r5 << 16
    r0 |= r6
    {pc, r6-r4} = [sp++]
L020250cc:
    r0 = 0
    {pc, r6-r4} = [sp++]
L020250d0:
    [--sp] = {rets, r9-r4}
    r6 = r3
    r8 = r2
    r9 = r1
    r5 = r0
    r0 = r9
    call L0202507a
    r7 = r0
    r4 = r6
L020250e2:
    r4 = [r4+0]
    if (r4 == r6) goto L020250f2
    r0 = [r4+12]
    call L0202507a
    if (r7 != r0) goto L020250e2
    goto L02025126
L020250f2:
    [r5+16] = r8
    r0 = 1
    b[r5+21] = r0
    r0 = 0
    b[r5+22] = r0
    [r5+12] = r9
    [r5+8] = r6
    r0 = [r6+0]
    if (r0 != r6) goto L0202511c
    r2 = [r6+8]
    r0 = L02025d66
    r1 = 0
    call r2
    if (r0 != 0) goto L02025128
L0202511c:
    r0 = [r6+4]
    [r6+4] = r5
    [r5+0] = r6
    [r5+4] = r0
    [r0+0] = r5
L02025126:
    r0 = 0
L02025128:
    {pc, r9-r4} = [sp++]
L0202512a:
    [--sp] = {rets, r5, r4}
    sp += -4
    [sp] = r1
    r1 = 0
    if (r0 == 0) goto L02025204
    r2 = sp + 0
    goto L020251fe
L02025138:
    r4 = r3 + -65
    if (r4 <= 11) goto L02025152
    r4 = r3 + -49
    if (r4 >= 4) goto L02025168
    [r2+0] += 4  ; @rmw.add.s12
    r1 += r3  ; @add.rr
    r1 += -48
    goto L020251fc
L02025152:
    tbb [r4]
L02025154:
    .byte (L02025160 - L02025154) / 2, (L02025182 - L02025154) / 2, (L02025188 - L02025154) / 2, (L020251fc - L02025154) / 2, (L020251fc - L02025154) / 2, (L020251fc - L02025154) / 2, (L020251fc - L02025154) / 2, (L020251ae - L02025154) / 2
    .byte (L020251fc - L02025154) / 2, (L020251fc - L02025154) / 2, (L020251fc - L02025154) / 2, (L020251b6 - L02025154) / 2
L02025160:
    [r2+0] += 4  ; @rmw.add.s12
    r1 += 6  ; @add.ri.u5
    goto L020251fc
L02025168:
    if (r3 == 98) goto L020251c2
    if (r3 == 99) goto L020251e4
    if (r3 != 108) goto L020251fc
    r3 = [sp]
    r4 = r3 + 4
    [sp] = r4
    r3 = [r3+0]
    r1 += r3  ; @add.rr
    r1 += 1  ; @add.ri.u5
    goto L020251fc
L02025182:
    [r2+0] += 4  ; @rmw.add.s12
    goto L020251fc
L02025188:
    r3 = b[r0+1] (s)
    r4 = b[r0+2] (s)
    r5 = b[r0+3] (s)
    [r2+0] += 4  ; @rmw.add.s12
    r3 = r3 * 0x64
    r1 += r3  ; @add.rr
    r1 += r5  ; @add.rr
    r3 = r4 * 0xA
    r1 += r3  ; @add.rr
    r1 = r1 + -5328
    r0 += 3  ; @add.ri.u5
    goto L020251fc
L020251ae:
    [r2+0] += 4  ; @rmw.add.s12
    r1 += 2  ; @add.ri.u5
    goto L020251fc
L020251b6:
    r3 = [sp]
    r4 = r3 + 4
    [sp] = r4
    r3 = [r3+0]
    r1 += r3  ; @add.rr
    goto L020251fc
L020251c2:
    r1 = b[r0+1] (s)
    r3 = b[r0+2] (s)
    r1 = r1 * 0xA
    r1 += r3  ; @add.rr
    r1 = r1 + -528
    r0 += 2  ; @add.ri.u5
    r3 = r1
    goto L020251e0
L020251da:
    [r2+0] += 4  ; @rmw.add.s12
    r3 += -1
L020251e0:
    if (r3 != 0) goto L020251da
    goto L020251fc
L020251e4:
    r3 = b[r0+1] (s)
    r4 = b[++r0=2] (s)
    [r2+0] += 4  ; @rmw.add.s12
    r1 += r4  ; @add.rr
    r3 = r3 * 0xA
    r1 += r3  ; @add.rr
    r1 = r1 + -528
L020251fc:
    r0 += 1  ; @add.ri.u5
L020251fe:
    r3 = b[r0+0] (s)
    if (r3 != 0) goto L02025138
L02025204:
    r0 = r1
    sp += 4
    {pc, r5, r4} = [sp++]
L0202520a:
    [--sp] = {rets, r8-r4}
    sp += -4
    r5 = r1  #
    [sp] = r2
    r8 = r0
    r6 = r8
    goto L0202537c
L02025218:
    r1 = r0 + -65
    if (r1 <= 11) goto L02025248
    r2 = r1 + 16
    if (r2 < 2) goto L0202526a
    r1 += 14  ; @add.ri.u5
    if (r1 < 2) goto L0202527e
    if (r0 == 83) goto L02025306
    if (r0 == 98) goto L02025324
    if (r0 == 99) goto L02025352
    if (r0 != 108) goto L0202537a
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r7 = [r0+0]
    b[r6++=1] = r7
    goto L0202537a
L02025248:
    tbb [r1]
L0202524a:
    .byte (L02025256 - L0202524a) / 2, (L020252a0 - L0202524a) / 2, (L020252b6 - L0202524a) / 2, (L0202537a - L0202524a) / 2, (L0202537a - L0202524a) / 2, (L0202537a - L0202524a) / 2, (L0202537a - L0202524a) / 2, (L020252ea - L0202524a) / 2
    .byte (L0202537a - L0202524a) / 2, (L0202537a - L0202524a) / 2, (L0202537a - L0202524a) / 2, (L020252fc - L0202524a) / 2
L02025256:
    r0 = [sp]
    r1 = r0 + 4
    r1 = r6  #
    [sp] = r1
    r0 = [r0+0]
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r6 += 6  ; @add.ri.u5
    goto L0202537a
L0202526a:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = [r0+0]
    b[r6+0] = r0
    r1 = b[r5+0] (u)
    if (r1 == 50) goto L020252f4
    r6 += 1  ; @add.ri.u5
    goto L0202537a
L0202527e:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = [r0+0]
    b[r6+0] = r0
    r1 = r0 >> 8
    b[r6+1] = r1
    r1 = r0 >> 16
    b[r6+2] = r1
    r1 = b[r5+0] (u)
    if (r1 == 52) {  ; @if.eq.ri.s12
    r0 = r0 >> 24
    b[r6+3] = r0
    r6 += 4  ; @add.ri.u5
    } else {
    r6 += 3  ; @add.ri.u5
    }
    goto L0202537a
L020252a0:
    r2 = r7  #
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = r6  #
    r1 = [r0+0]
    call effect_parameter_support_memmove  ; @call.xl
    r6 += r7  ; @add.rr
    goto L0202537a
L020252b6:
    r0 = [sp]
    r2 = b[r5+3] (s)
    r1 = b[r5+2] (s)
    r3 = b[r5+1] (s)
    r4 = r0 + 4
    r4 = r1 * 0xA  #
    [sp] = r4
    r3 = r3 * 0x64  #
    r1 = [r0+0]
    r0 = r3 + r4
    r0 += r2  ; @add.rr
    r4 = r0 + -5328
    r0 = r6
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r6 += r4  ; @add.rr
    r5 += 3  ; @add.ri.u5
    goto L0202537a
L020252ea:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = [r0+0]
    b[r6+0] = r0
L020252f4:
    r0 = r0 >> 8
    b[r6+1] = r0
    r6 += 2  ; @add.ri.u5
    goto L0202537a
L020252fc:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r7 = [r0+0]
    goto L0202537a
L02025306:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = r6  #
    r4 = [r0+0]
    r1 = r4
    call L02032bf0  ; @call.xl
    r0 = r4
    call L020283a8  ; @call.xl
    r6 += r0  ; @add.rr
    goto L0202537a
L02025324:
    r0 = b[r5+1] (s)
    r1 = b[r5+2] (s)
    r0 = r0 * 0xA
    r0 += r1  ; @add.rr
    r1 = r0 + -528
    r5 += 2  ; @add.ri.u5
    r2 = r6
    goto L02025348
L0202533c:
    r3 = [sp]
    r4 = r3 + 4
    [sp] = r4
    r3 = [r3+0]
    b[r2++=1] = r3
    r1 += -1
L02025348:
    if (r1 != 0) goto L0202533c
    r0 += r6  ; @add.rr
    r6 = r0 + -528
    goto L0202537a
L02025352:
    r0 = [sp]
    r2 = b[r5+2] (s)
    r3 = b[r5+1] (s)
    r1 = r0 + 4
    [sp] = r1
    r0 = r3 * 0xA  #
    r1 = [r0+0]
    r0 += r2  ; @add.rr
    r4 = r0 + -528
    r0 = r6
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r6 += r4  ; @add.rr
    r5 += 2  ; @add.ri.u5
L0202537a:
    r5 += 1  ; @add.ri.u5
L0202537c:
    r0 = b[r5+0] (s)
    if (r0 != 0) goto L02025218
    r0 = r6 - r8
    sp += 4
    {pc, r8-r4} = [sp++]
L0202538c:
    [r0+4] = r1
    [r1+0] = r0
    rts
