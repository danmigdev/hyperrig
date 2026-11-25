; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0203e18c..0x02040362: system layer code (not reversed), as instructions
L0203e18c:
    [--sp] = {rets, r9-r4}
    if (r0 <= 32) {  ; @if.le.ri.s12
    r0 = 32
    }
    r2 = r0 + -1
    if ((r2 & r0) == 0) goto L0203e1a8
    r2 = 64
L0203e19e:
    r5 = r2
    r2 = r5 << 1
    if (r5 < r0) goto L0203e19e
    goto L0203e1aa
L0203e1a8:
    r5 = r0
L0203e1aa:
    r0 = -128
    r0 = r0 - r5
    r8 = L01c26890
    if (r0 <= r1) goto L0203e25a
    r0 = r1 + 35
    r0 = r0 & 0xFFFFFFE0
    r6 = 32
    if (r1 >= 27) {  ; @if.ge.ri.s12
    r6 = r0
    }
    r0 = r6 | 0x1C
    r0 += r5  ; @add.rr
    call L0203c15c
    r2 = r0
    if (r2 == 0) goto L0203e25e
    r0 = 8216
    r0 = b[r8+r0] (u)
    if ((r0 & 2) == 0) goto L0203e1fc
    r0 = 8220
    r3 = r8 + r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0203e1f4:
    testset b[r3]
    ifeq goto L0203e1f4
    csync
L0203e1fc:
    r9 = r5 + -1
    r7 = r2 + -8
    if ((r2 & r9) == 0) goto L0203e26e
    r0 = r2 + r5
    r0 += -1
    r1 = 0x0 - r5
    r0 &= r1
    r4 = r0 + -8
    r0 = r4 + r5
    r1 = r4 - r7
    if (r1 <= 31) {  ; @if.le.ri.s12
    r4 = r0
    }
    r1 = r4 - r7  #
    r3 = [r2+-4]
    r0 = r3 & 0xFFFFFFF8
    r0 = r0 - r1
    if ((r3 & 0x3) == 0) goto L0203e264
    r3 = [r4+4]
    r3 = r3 & 0x1
    r3 |= r0
    r3 |= 2
    r0 += r4  #  ; @add.rr.p
    [r4+4] = r3
    [r0+4] |= 0x1
    r0 = [r2+-4]
    r0 = r0 & 0x1
    r0 |= r1
    r0 |= 2
    r0 = r7  #
    [r2+-4] = r0
    [r4+4] |= 0x1
    call L0203d992
    goto L0203e26c
L0203e25a:
    [r8+96] = 0xC
L0203e25e:
    r3 = 0
L0203e260:
    r0 = r3
    {pc, r9-r4} = [sp++]
L0203e264:
    r2 = [r2+-8]
    r1 += r2  ; @add.rr
    [r4+0] = r1
    [r4+4] = r0
L0203e26c:
    r7 = r4
L0203e26e:
    r0 = [r7+4]
    if ((r0 & 0x3) == 0) goto L0203e2a2
    r1 = r0 & 0xFFFFFFF8
    r2 = r6 + 32
    if (r1 <= r2) goto L0203e2a2
    r0 = r0 & 0x1
    r0 |= r6
    r0 |= 2
    r0 = r7 + r6  #
    [r7+4] = r0
    r1 = r1 - r6
    r2 = r1 | 0x3
    r2 = r0 + r1  #
    [r0+4] = r2
    [r2+4] |= 0x1
    call L0203d992
    r0 = [r7+4]
L0203e2a2:
    r0 = r0 & 0xFFFFFFF8
    r3 = r7 + 8
    if (r0 >= r6) goto L0203e2ae
L0203e2ac:
    goto L0203e2ac
L0203e2ae:
    if ((r3 & r9) == 0) goto L0203e2b4
L0203e2b2:
    goto L0203e2b2
L0203e2b4:
    r0 = 8216
    r0 = b[r8+r0] (u)
    if ((r0 & 2) == 0) goto L0203e260
    csync
    r0 = 8220
    r1 = 0
    b[r8+r0] = r1
    call storage_coordination_irq_leave  ; @call.xl
    goto L0203e260
    [--sp] = {rets, r5, r4}
    r4 = r0
    if (r1 != 32) goto L0203e2ea
    r0 = r2
    call L0203c15c
L0203e2e2:
    if (r0 == 0) goto L0203e310
    [r4+0] = r0
    r0 = 0
    {pc, r5, r4} = [sp++]
L0203e2ea:
    r0 = 22
    if ((r1 & 0x3) != 0) goto L0203e30e
    r3 = r1 >> 2
    if (r3 == 0) goto L0203e30e
    r5 = 1073741823
    r5 += r3  ; @add.rr
    if ((r5 & r3) != 0) goto L0203e30e
    r0 = -128
    r3 = r0 - r1
    r0 = 12
    if (r3 >= r2) goto L0203e314
L0203e30e:
    {pc, r5, r4} = [sp++]
L0203e310:
    r0 = 12
    {pc, r5, r4} = [sp++]
L0203e314:
    if (r1 <= 32) {  ; @if.le.ri.s12
    r1 = 32
    }
    r0 = r1
    r1 = r2
    call L0203e18c
    goto L0203e2e2
    [--sp] = {rets, r5, r4}
    r1 = 524
    r5 = L01c26890
    r1 = [r5+r1<<2]
    r4 = r0
    if (r1 != 0) goto L0203e33c
    call L0203c018
L0203e33c:
    r0 = 525
    r0 = [r5+r0<<2]
    if (r0 > 32) goto L0203e350
    r0 = r4
    call L0203c15c
    {pc, r5, r4} = [sp++]
L0203e350:
    r1 = r4
    call L0203e18c
    {pc, r5, r4} = [sp++]
L0203e358:
    rts
L0203e35a:
    [--sp] = {rets, r10-r4}
    r9 = 1
    r3 = 1
    ifs (r0 <= 0) {  ; @ifs.le.ri.s12
    r3 = 0
    }
    r8 = L01c26840
    r7 = [r8+0]
    if (r7 != 0) {  ; @if.ne.ri.s12
    r5 = r7
    } else {
    r5 = 0  ; @li.u32
    }
    r6 = r5 + r0
    r10 = 0  ; @li.u32
    r2 = 1
    if (r6 < r10) {
    r2 = 0
    }
    r1 = -1
    if ((r3 & r2) == 0) {
    r1 = r5
    }
    r4 = 1
    ifs (r0 >= 1) {  ; @ifs.ge.ri.s12
    r4 = 0
    }
    if (r6 >= r10) {
    r9 = 0
    }
    if (r7 == 0) goto L0203e3ac
    r0 = r4 | r9
    if (r0 == 0) goto L0203e3b8
L0203e3ac:
    r0 = r3 & r2
    if (r0 != 0) goto L0203e3b4
    r5 = r6
L0203e3b4:
    [r8+0] = r5
L0203e3b8:
    r0 = r1
    {pc, r10-r4} = [sp++]
L0203e3bc:
    [--sp] = {rets, r10-r4}
    r2 = 32  ; @li.u32
    r3 = 0
    r0 = 1
    r4 = 0  ; @li.u32
    r1 = 1
    if (r2 <= r4) {
    r1 = 0
    }
    r2 = 0  ; @li.u32
    if (r2 >= 32) {  ; @if.ge.ri.s12
    r0 = 0
    }
    r0 |= r1
    if (r0 != 0) goto L0203e654
    r0 = rets
    r1 = 359
    r9 = L01c26890
    [r9+r1<<2] = r0
    r4 = 2864
    r0 = b[r9+r4] (u)
    if (r0 != 0) goto L0203e45a
    r0 = L0203a22a  ; "MEM_HEAP"
    r5 = r9 + 2816
    r8 = 0  #
    [r5+24] = r0
    [r5+16] = r8
    r0 = 36
    call L0203e35a
    r1 = r0 + 3
    r1 = r1 & 0xFFFFFFFC
    [r5+0] = r1
    r2 = [r5+16]
    r3 = r1 + r2
    r7 = r3 + 16
    [r1+0] = r7
    [r1+4] = r1
    r6 = 2779500015
    [r1+8] = r6
    [r5+4] = r7
    r6 = 1515907758
    [r3+24] = r6
    [r3+16] = r7
    [r3+20] = r1
    r0 += 36
    r0 = 2836  #
    [r5+12] = r0
    [r5+8] = r1
    [r5+28] = r2
    b[r9+r0] = r8
    r0 = 1
    b[r9+r4] = r0
L0203e45a:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r6 = r9 + 2820
    r8 = r6 + 16
L0203e46a:
    testset b[r8]
    ifeq goto L0203e46a
    csync
    r1 = [r6+12]
    r0 = [r6+0]
    r1 = r1 >> 2
    if (r1 >= 1435) goto L0203e572
L0203e47e:
    r0 = [r0+4]
    r0 = [r0+8]
    r5 = 2779500015
    if (r0 != r5) goto L0203e4bc
    r0 = 0
    r4 = 0
    call L0203e35a
    r1 = 707
    r1 = [r9+r1<<2]
    if (r1 != r0) goto L0203e4b0
    r0 = 705
    r0 = [r9+r0<<2]
    r1 = [r0+4]
    r2 = -16
    r1 = r2 - r1
    r4 = r1 + r0
L0203e4b0:
    r0 = 5780
    r4 = r0 - r4
    r10 = 1
    goto L0203e4c2
L0203e4bc:
    r4 = 5780
    r10 = 0
L0203e4c2:
    r0 = r4
    call L0203e35a
    if (r0 == -1) goto L0203e4ee
    r1 = 707
    r2 = [r9+r1<<2]
    if (r2 == r0) goto L0203e52c
    r2 = 705
    r2 = [r9+r2<<2]
    r3 = r0 + 3
    r7 = r3 & 0xFFFFFFFC
    [r7+4] = r2
    [r7+8] = r5
    [r2+0] = r7
    goto L0203e52e
L0203e4ee:
    [r6+36] += 1  ; @rmw.add.s12
    csync
    r0 = 0
    b[r8+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0203e508:
    testset b[r8]
    ifeq goto L0203e508
    csync
    r0 = [r6++=4]
L0203e512:
    r6 = [r6+0]
    if (r6 != r0) goto L0203e512
    csync
    r0 = 2836
    r3 = 0
    b[r9+r0] = r3
    call storage_coordination_irq_leave  ; @call.xl
    goto L0203e654
L0203e52c:
    r7 = -1
L0203e52e:
    r0 += r4  ; @add.rr
    [r9+r1<<2] = r0
    r1 = r0 & 0xFFFFFFFC
    r0 = 1515907758
    r0 = r1 + -16  #
    [r1+-8] = r0
    [r1+-16] = r0
    if (r7 == -1) goto L0203e550
    [r1+-12] = r7
    [r7+0] = r0
    goto L0203e566
L0203e550:
    r2 = 705
    r7 = [r9+r2<<2]
    if (r10 == 0) goto L0203e57c
    r2 = [r7+4]
    [r1+-12] = r2
    r7 = r2  #
    r1 = [r7+4]
    [r1+0] = r0
L0203e566:
    [r6+0] = r0
    r1 = [r6+12]
    r1 += r4  ; @add.rr
    [r6+12] = r1
    [r6+24] = r1
    if (r7 != 0) goto L0203e58c
L0203e572:
    r1 = 706
    r7 = [r9+r1<<2]
    goto L0203e58c
L0203e57c:
    [r1+-12] = r7
    [r7+0] = r0
    [r7+8] = r5
    [r6+0] = r0
    r1 = [r6+12]
    r1 += r4  ; @add.rr
    [r6+12] = r1
    [r6+24] = r1
L0203e58c:
    r1 = 2779500015
    goto L0203e5ae
L0203e594:
    r2 = [r7+8]
    if (r2 != r1) goto L0203e5ac
    r2 = [r7+0]
    r3 = r7 + 16
    r4 = r2 - r3
    r5 = r4 >> 2
    if (r5 > 1434) goto L0203e5b4
    r7 = r2
    goto L0203e5ae
L0203e5ac:
    r7 = [r7+0]
L0203e5ae:
    if (r7 != r0) goto L0203e594
    goto L0203e47e
L0203e5b4:
    if (r4 >= 5760) goto L0203e5d2
    r0 = 1515907758
    r1 = r9 + 2848  #
    [r7+8] = r0
    r4 = -16
    r4 = r4 - r7  #
    r0 = [r1+0]
    r2 += r4  ; @add.rr
    r0 += r2  ; @add.rr
    goto L0203e5f4
L0203e5d2:
    r0 = r7 + 5756
    [r0+8] = r1
    [r0+] = {r7, r2}
    [r7+0] = r0
    r1 = 1515907758
    [r7+8] = r1
    r1 = [r0+0]
    r1 = r9 + 2848  #
    [r1+4] = r0
    r0 = [r1+0]
    r0 = r0 + 5756
L0203e5f4:
    [r1+0] = r0
    r1 = [r1+4]
    if (r1 < r0) {
    r1 = 713
    [r9+r1<<2] = r0
    }
    r0 = 706
    r0 = [r9+r0<<2]
    if (r7 != r0) goto L0203e638
    r0 = 705
    r1 = [r9+r0<<2]
    r2 = 1515907758
    r4 = r2
    r0 = r7
    goto L0203e62c
L0203e624:
    if (r0 == r1) goto L0203e630
    r0 = [r0+0]
    r4 = [r0+8]
L0203e62c:
    if (r4 == r2) goto L0203e624
L0203e630:
    r1 = 706
    [r9+r1<<2] = r0
L0203e638:
    csync
    r0 = 2836
    r1 = 0
    b[r9+r0] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 359
    r0 = [r9+r0<<2]
    [r7+12] = r0
L0203e654:
    r0 = r3
    {pc, r10-r4} = [sp++]
L0203e658:
    [--sp] = {rets, r8-r4}
    r1 = 0  ; @li.u32
    r2 = r0
    if (r2 < r1) goto L0203e734
    r0 = 0  ; @li.u32
    if (r2 > r0) goto L0203e734
    if (r2 == 0) goto L0203e732
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = L01c26890
    r1 = r0 + 2836
L0203e684:
    testset b[r1]
    ifeq goto L0203e684
    csync
    r8 = 2779500015
    [r2+-8] = r8
    r4 = 706
    r5 = [r0+r4<<2]
    r3 = r2 + -16
    if (r3 < r5) {
    [r0+r4<<2] = r3
    r5 = r3
    }
    r7 = r4 + 6
    r6 = [r2+-16]
    r4 = [r0+r7<<2]
    r1 = r3 + 16
    r1 = r1 - r6
    r4 += r1  ; @add.rr
    [r0+r7<<2] = r4
    if (r6 == r3) goto L0203e6f4
    r1 = [r6+8]
    if (r1 != r8) goto L0203e6f4
    r1 = 705
    r1 = [r0+r1<<2]
    if (r6 == r1) goto L0203e6f4
    if (r5 == r6) {
    r1 = 706
    [r0+r1<<2] = r3
    r5 = r3
    }
    r1 = [r6+0]
    [r2+-16] = r1
    r6 = [r6+0]
    r6 = r7  #
    [r6+4] = r3
    r4 += -16
    [r0+r6<<2] = r4
    r6 = r1
L0203e6f4:
    r7 = [r2+-12]
    if (r7 == 0) goto L0203e720
    if (r7 == r3) goto L0203e720
    r1 = [r7+8]
    if (r1 != r8) goto L0203e720
    if (r5 == r3) {
    r1 = 706
    [r0+r1<<2] = r7
    }
    [r7+0] = r6
    r2 = 712  #
    r1 = [r2+-16]
    r1 = r4 + -16  #
    [r1+4] = r7
    [r0+r2<<2] = r1
L0203e720:
    csync
    r1 = 2836
    r2 = 0
    b[r0+r1] = r2
    call storage_coordination_irq_leave  ; @call.xl
L0203e732:
    {pc, r8-r4} = [sp++]
L0203e734:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0203e740:
    goto L0203e740
L0203e742:
    [--sp] = {rets, r4}
    r0 = cnum
    r2 = L01c1fc64
    r3 = [r2+r0<<2]
    if (r3 != 0) goto L0203e79c
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L0203e772
    lockset
L0203e772:
    csync
    r1 = cnum
    r3 = [r2+r1<<2]
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203e790
    lockclr
L0203e790:
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 != 0) goto L0203e79c
    call L0203e7a0
    r3 = 0
L0203e79c:
    r0 = r3 + 12
    {pc, r4} = [sp++]
L0203e7a0:
    [--sp] = rets
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fa24
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0203e7ce
    csync
    r0 = L01c1fa20
L0203e7c6:
    testset b[r0]
    ifeq goto L0203e7c6
    csync
L0203e7ce:
    call L0203e742
    call storage_fault_fatal  ; @call.xl
L0203e7d6:
    goto L0203e7d6
L0203e7d8:
    [--sp] = {rets, r12-r4}
    r9 = r3  #
    r7 = [sp+44]
    r5 = r7 + 72
    r10 = [r5+48]
    r4 = r2
    r6 = r1
    r8 = r0
    r11 = r4 << 2
    r1 = 165
    r0 = r10
    r2 = r11
    call effect_enable_memset  ; @call.xl
    r12 = r7 + 136  #
    [r7+8] = r4
    r0 = [r5+48]
    [r12+24] = 0xFFFFFFFF
    r0 += r11
    r10 = r0 + -4
    r1 = L0204176e  ; "IDLE0"
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0203e84e
    r1 = L02041774  ; "IDLE1"
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0203e84e
    r0 = b[r6+0] (u)
    if (r0 != 35) goto L0203e84e
    r0 = b[r6+1] (u)
    if (r0 != 67) goto L0203e84e
    r0 = b[r6+2] (s)
    r0 += -48
    [r12+24] = r0
    r1 = -2
    r6 += 3  ; @add.ri.u5
    if ((r0 & r1) != 0) {
    call L0203e7a0
    }
L0203e84e:
    r1 = r10 & 0xFFFFFFFC  #
    r0 = [sp+40]
    r2 = 0
L0203e856:
    if (r2 > 63) goto L0203e86a
    r3 = b[r6+r2] (u)
    r4 = r7 + r2
    b[r4+12] = r3
    r3 = b[r6+r2] (u)
    r2 += 1  ; @add.ri.u5
    if (r3 != 0) goto L0203e856
L0203e86a:
    r2 = 0
    b[r5+3] = r2
    if (r9 >= 30) {  ; @if.ge.ri.s12
    r9 = 30
    }
    [r5+44] = r9
    [r5+60] = r9
    [r12+0] = r2
    r3 = r9 ^ 0x1F  #
    [r5+20] = r2
    r10 = 0  #
    [r5+40] = r2
    r11 = 0  #
    [r5+16] = r7
    [r5+24] = r3
    [r5+36] = r7
    b[r7+157] = r2
    d[r7+148] = r11_r10
    d[r7+140] = r11_r10
    r3 = [r5+48]
    r3 = r1 - r3
    [r7+8] = r3
    r1 += -76
    [r1+12] = r2
    [r1+8] = r2
    [r1+4] = r2
    [r1+0] = r8
    [r7+0] = r1
    if (r0 == 0) goto L0203e8b8
    [r0+0] = r7
L0203e8b8:
    {pc, r12-r4} = [sp++]
L0203e8ba:
    r1 = r0 + 8
    [r0+4] = r1
    [r0+8] = 0xFFFFFFFF
    [r0+12] = r1
    [r0+16] = r1
    [r0+0] = 0x0
    rts
L0203e8cc:
    r2 = [r0+4]
    [r1+4] = r2
    r3 = [r2+8]
    [r1+8] = r3
    r3 = [r2+8]
    [r3+4] = r1
    [r2+8] = r1
    [r1+16] = r0
    [r0+0] += 1  ; @rmw.add.s12
    rts
L0203e8e2:
    [--sp] = {rets, r11-r4}
    r0 = L01c1fc84
    r1 = [r0+0]
    r0 = L01c1fc8c
    if (r1 == 0) goto L0203e8fc
    [r0+0] = 0x1
    r0 = 0
    {pc, r11-r4} = [sp++]
L0203e8fc:
    r10 = 0
    [r0+0] = r10
    call storage_coordination_irq_enter  ; @call.xl
    r8 = L01c1fc4c
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    if (r1 != 0) goto L0203e920
    lockset
L0203e920:
    csync
    r0 = L01c1fc74
    r1 = [r0+0]
    r0 = clz(r1)  #
    r5 = [r0+0]
    r4 = r0 ^ 0x1F
    r11 = L01c344b4
    r6 = L01c1fc78
    r9 = L01c1fc64
    r0 = 0
L0203e948:
    r1 = r4 * 0x14
    r2 = [r1+r11]
    r3 = r0.b0 (s)
    if (r2 <= r3) goto L0203e972
    r2 = r1 + r11
    r1 = [r2+4]
    r1 = [r1+4]
    r3 = r2 + 8
    [r2+4] = r1
    if (r1 == r3) {
    r1 = [r1+4]
    [r2+4] = r1
    }
    r1 = [r1+12]
    [r6+0] = r1
    r0 += 1  ; @add.ri.u5
    goto L0203e9a6
L0203e972:
    r5 = r5 & ~(1 << r4)
    r0 = clz(r5)
    r4 = r0 ^ 0x1F
    r7 = r4 * 0x14
    r0 = [r7+r11]
    if (r0 != 0) goto L0203e98c
    call L0203e7a0
L0203e98c:
    r1 = r7 + r11
    r0 = [r1+4]
    r0 = [r0+4]
    r2 = r1 + 8
    [r1+4] = r0
    if (r0 == r2) {
    r0 = [r0+4]
    [r1+4] = r0
    }
    r0 = [r0+12]
    [r6+0] = r0
    r0 = 1
L0203e9a6:
    if (r10 != 0) goto L0203ea08
L0203e9aa:
    r1 = r4 * 0x14
    r2 = [r1+r11]
    r3 = r0.b0 (s)
    if (r2 <= r3) goto L0203e9d4
    r2 = r1 + r11
    r1 = [r2+4]
    r1 = [r1+4]
    r3 = r2 + 8
    [r2+4] = r1
    if (r1 == r3) {
    r1 = [r1+4]
    [r2+4] = r1
    }
    r1 = [r1+12]
    [r6+4] = r1
    r0 += 1  ; @add.ri.u5
    goto L0203ea08
L0203e9d4:
    r5 = r5 & ~(1 << r4)
    r0 = clz(r5)
    r4 = r0 ^ 0x1F
    r7 = r4 * 0x14
    r0 = [r7+r11]
    if (r0 != 0) goto L0203e9ee
    call L0203e7a0
L0203e9ee:
    r1 = r7 + r11
    r0 = [r1+4]
    r0 = [r0+4]
    r2 = r1 + 8
    [r1+4] = r0
    if (r0 == r2) {
    r0 = [r0+4]
    [r1+4] = r0
    }
    r0 = [r0+12]
    [r6+4] = r0
    r0 = 1
L0203ea08:
    r1 = [r6+4]
    r1 = [r1+160]
    if (r1 == 0) goto L0203e9aa
    r1 = [r6+0]
    r1 = [r1+160]
    if (r1 != 0) goto L0203ea22
    r1 = [r9+0]
    r2 = [r6+4]
    if (r1 == r2) goto L0203e9aa
L0203ea22:
    r10 = 1  #
    r1 = [r6+0]
    r1 = [r1+160]
    if (r1 == 1) goto L0203e948
    r1 = [r6+4]
    r1 = [r1+160]
    if (r1 != 1) goto L0203ea44
    r1 = [r9+4]
    r2 = [r6+0]
    if (r1 == r2) goto L0203e948
L0203ea44:
    r0 = [r6+0]
    r1 = [r6+4]
    if (r0 == r1) {
    call L0203e7a0
    }
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203ea64
    lockclr
L0203ea64:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 1
    {pc, r11-r4} = [sp++]
L0203ea6e:
    [--sp] = {rets, r9-r4}
    call storage_coordination_irq_enter  ; @call.xl
    r8 = L01c1fc4c
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    if (r1 != 0) goto L0203ea8e
    lockset
L0203ea8e:
    csync
    call L0203e8e2
    if (r0 == 0) goto L0203eb3a
    r0 = 0
    r6 = L01c1fc78
    r7 = L01c1fc64
    goto L0203eac6
L0203eaa6:
    r2 = 0
    r1 = r6
L0203eaaa:
    ifs (r2 > 1) goto L0203eac4
    r3 = [r7+r0<<2]
    r4 = [r1++=4]
    r2 += 1  ; @add.ri.u5
    if (r3 != r4) goto L0203eaaa
    r2 = [r6+r0<<2]
    [r1+-4] = r2
    [r6+r0<<2] = r3
L0203eac4:
    r0 += 1  ; @add.ri.u5
L0203eac6:
    if (r0 != 2) goto L0203eaa6
    r0 = [r6+4]
    r1 = [r6+0]
    if (r1 == r0) goto L0203eb56
    call phase3_p3_timer_get_ms  ; @call.xl
    r4 = r0
    r5 = 7
    r9 = 32436640
    goto L0203eb20
L0203eae4:
    r0 = [r7+0]
    r1 = [r6+0]
    if (r0 == r1) goto L0203eb0c
    [r9+0] |= 1 << r5
    call phase3_p3_wdt_clear  ; @call.xl
    r0 = [r6+0]
    h[r0+152] = r4
    r0 = [r7+0]
    r1 = h[++r0=152] (u)
    r1 = r4 - r1  #
    r2 = h[r0+2] (u)
    r1 += r2  ; @add.rr
    h[r0+2] = r1
    goto L0203eb1a
L0203eb0c:
    r1 = h[++r0=152] (u)
    r1 = r4 - r1  #
    r2 = h[r0+2] (u)
    r1 += r2  ; @add.rr
    h[r0+2] = r1
    h[r0+0] = r4
L0203eb1a:
    r7 += 4  ; @add.ri.u5
    r6 += 4  ; @add.ri.u5
    r5 += -1
L0203eb20:
    if (r5 != 5) goto L0203eae4
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203eb4e
    lockclr
    goto L0203eb4e
L0203eb3a:
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203eb4e
    lockclr
L0203eb4e:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r9-r4} = [sp++]
L0203eb56:
    call L0203e742
    call storage_fault_fatal  ; @call.xl
L0203eb60:
    goto L0203eb60
L0203eb62:
    [--sp] = {rets, r10-r4}
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L0203eb84
    lockset
L0203eb84:
    csync
    r10 = L01c1fc60
    [r10+0] += 1  ; @rmw.add.s12
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L0203eba8
    lockset
L0203eba8:
    csync
    r9 = L01c1fc64
    r0 = cnum
    r6 = [r9+r0<<2]
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0203ebcc
    lockclr
L0203ebcc:
    call storage_coordination_irq_leave  ; @call.xl
    r7 = L01c344b4
    r8 = L01c1fc6c
    r4 = r3 + 76
    if (r6 == 0) goto L0203ec3a
    r0 = [r8+0]
    if (r0 != 0) goto L0203eca2
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L0203ec02
    lockset
L0203ec02:
    csync
    r0 = cnum
    r6 = [r9+r0<<2]
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0203ec20
    lockclr
L0203ec20:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r4+40]
    r1 = [r6+116]
    if (r1 > r0) goto L0203eca2
    r0 = cnum
    [r9+r0<<2] = r3
    goto L0203eca2
L0203ec3a:
    r0 = cnum
    [r9+r0<<2] = r3
    r0 = [r10+0]
    if (r0 != 1) goto L0203eca2
    r2 = 0
    goto L0203ec56
L0203ec4e:
    r0 = r2 + r7
    call L0203e8ba
    r2 += 20  ; @add.ri.u5
L0203ec56:
    if (r2 != 620) goto L0203ec4e
    r2 = L01c34720
    r0 = r2
    call L0203e8ba
    r3 = L01c34734
    r0 = r3
    call L0203e8ba
    r0 = L01c34748
    call L0203e8ba
    r0 = L01c3475c
    call L0203e8ba
    r0 = L01c34770
    call L0203e8ba
    r0 = L01c34784
    [r0+0] = r2
    r0 = L01c34788
    [r0+0] = r3
L0203eca2:
    r0 = L01c1fc70
    r1 = [r0+0]
    r1 += 1  ; @add.ri.u5
    [r0+0] = r1
    [r4+48] = r1
    r0 = [r4+40]
    r1 = L01c1fc74
    [r1+0] |= 1 << r0
    r0 = r0 * 0x14
    r0 += r7  ; @add.rr
    r1 = r4
    call L0203e8cc
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0203ecdc
    lockclr
L0203ecdc:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r8+0]
    if (r0 == 0) goto L0203ed32
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L0203ed00
    lockset
L0203ed00:
    csync
    r0 = cnum
    r3 = [r9+r0<<2]
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0203ed1e
    lockclr
L0203ed1e:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r4+40]
    r1 = [r3+116]
    if (r1 < r0) {
    call L0203ea6e
    }
L0203ed32:
    {pc, r10-r4} = [sp++]
L0203ed34:
    [--sp] = {rets, r10-r4}
    sp += -8
    r8 = r3
    r5 = r2
    r9 = r1
    r10 = r0
    r0 = r5 << 2
    call L0203d210  ; @call.xl
    r7 = r0
    r4 = -1
    if (r7 == 0) goto L0203ed88
    r0 = 164
    call L0203d210  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L0203ed80
    r2 = r5  #
    r0 = [sp+40]
    [r6+120] = r7
    r1 = 0
    b[r6+156] = r1
    r1 = r9  #
    [sp+4] = r6
    r0 = r10  #
    [sp] = r0
    r3 = r8
    call L0203e7d8
    r0 = r6
    call L0203eb62
    r4 = 1
    goto L0203ed88
L0203ed80:
    r0 = r7
    call L0203d85a  ; @call.xl
L0203ed88:
    r0 = r4
    sp += 8
    {pc, r10-r4} = [sp++]
L0203ed8e:
    [--sp] = {rets, r6-r4}
    sp += -4
    r0 = cnum
    r4 = L01c1fc9c
    [sp] = r4
    if (r0 != 0) {  ; @if.ne.ri.s12
    r1 = L02041774  ; "IDLE1"
    } else {
    r1 = L0204176e  ; "IDLE0"
    }
    r0 = L02040fba
    r2 = 256
    r3 = 0
    call L0203ed34
    r2 = [r4+0]
    r1 = L01c1fc64
    r3 = cnum
    [r1+r3<<2] = r2
    if (r0 == -1) goto L0203eed0
    if (r0 != 1) goto L0203eed4
    r0 = cnum
    if (r0 != 0) goto L0203edf8
    r0 = L01c1fc88
    [r0+0] = 0xFFFFFFFF
    r0 = L01c1fc6c
    [r0+0] = 0x1
    r0 = L01c1fc94
    [r0+0] = 0x0
L0203edf8:
    r2 = cnum
    r0 = 1
    if (r2 == 1) {  ; @if.eq.ri.s12
    r0 = 0
    }
    r2 = L01c1fc84
    [r2+0] = r0
    r0 = cnum
    r0 = cnum
    r1 = [r1+r0<<2]
    r0 = cnum
    if (r1 == 0) goto L0203eed4
    r1 = cnum
    r3 = r1.b0 (u)
    r0 = 0x7F - r0
    r0 = r0.b0 (u)
    r2 = L0203291c
    r1 = 0
    r4 = 0
    call storage_platform_register  ; @call.xl
    r0 = cnum
    if (r0 != 0) goto L0203ee74
    r5 = 32436460
    b[r5+0] = r4
    r2 = L02040ec4
    r0 = 3
    r1 = 1
    r3 = 0
    r6 = 1
    call storage_platform_register  ; @call.xl
    [r5+4] = r4
    r0 = L0204176a  ; "sys"
    call L020009ee  ; @call.xl
    r1 = 100
    r0 = r0 / r1 (s)
    [r5+8] = r0
    b[r5+0] = r6
L0203ee74:
    r0 = cnum
    if (r0 != 0) goto L0203eea4
    r0 = 29884408
    r1 = phase3_p14_cpu1_start
    [r0+0] = r1
    r0 = L01c3748d
    r1 = 0
    b[r0+0] = r1
    r1 = 32432132
    [r1+0] |= 0x8
    [r1+0] &= 0xFFFFFFFD
L0203eea0:
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L0203eea0
L0203eea4:
    lockset
    r0 = L01c1fc64
    r1 = cnum
    r0 = [r0+r1<<2]
    r0 = [r0+0]
    sp = r0
    {r0} = [sp++]
    {psr, rets} = [sp++]
    rets = r0
    {r15-r0} = [sp++]
    usp = sp
    lockclr
    rts
L0203eece:
    goto L0203eece
L0203eed0:
    call L0203e7a0
L0203eed4:
    sp += 4
    {pc, r6-r4} = [sp++]
L0203eed8:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fa24
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0203ef04
    csync
    r0 = L01c1fa20
L0203eefc:
    testset b[r0]
    ifeq goto L0203eefc
    csync
L0203ef04:
    call L0203e742
    call storage_fault_fatal  ; @call.xl
L0203ef0e:
    goto L0203ef0e
L0203ef10:
    [--sp] = {rets, r7-r4}
    sp += -4
    if (r0 == 0) goto L0203efb2
    if (r3 == 0) goto L0203efb2
    if (r1 != 0) goto L0203ef1c
    if (r2 != 0) goto L0203efb2
L0203ef1c:
    if (r1 == 0) goto L0203ef20
    if (r2 == 0) goto L0203efb2
L0203ef20:
    r4 = 80
    [sp] = r4
    r4 = [sp]
    if (r4 != 80) goto L0203efb2
    r5 = 1
    r4 = r3 + 64
    r5 = r3  #
    b[r4+6] = r5
    if (r1 == 0) goto L0203ef38
    r5 = r2
L0203ef38:
    [r3+0] = r5
    [r3+60] = r0
    [r4+0] = r1
    call storage_coordination_irq_enter  ; @call.xl
    r2 = L01c1fc4c
    r0 = cnum
    r1 = [r2+r0<<2]
    r5 = r1 + 1
    [r2+r0<<2] = r5
    if (r1 != 0) goto L0203ef5c
    lockset
L0203ef5c:
    csync
    r0 = [r3+60]
    r1 = [r4+0]
    r7 = r1 * r0  #
    r6 = [r3+0]
    r7 += r6  #  ; @add.rr.p
    r5 = [sp+24]
    [r3+4] = r7
    [r3+56] = 0x0
    r0 += -1
    r0 *= r1  #
    [r3+8] = r6
    r0 += r6  ; @add.rr
    [r3+12] = r0
    r0 = 255
    b[r4+4] = r0
    b[r4+5] = r0
    r0 = r3 + 16
    call L0203e8ba
    r0 = r3 + 36
    call L0203e8ba
    csync
    r0 = cnum
    r1 = [r2+r0<<2]
    r1 += -1
    [r2+r0<<2] = r1
    if (r1 != 0) goto L0203efa4
    lockclr
L0203efa4:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3  #
    b[r4+12] = r5
    sp += 4
    {pc, r7-r4} = [sp++]
L0203efb2:
    call L0203eed8
L0203efb4:
    goto L0203efb4
L0203efb6:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L0203efd8
    lockset
L0203efd8:
    csync
    r4 = [r2+4]
    r1 = [r2+8]
    r3 = [r2+16]
    [r4+8] = r1
    r1 = [r2+8]
    [r1+4] = r4
    r4 = [r3+4]
    if (r4 == r2) {
    [r3+4] = r1
    }
    [r2+16] = 0x0
    [r3+0] += -1  ; @rmw.add.s12
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203f00a
    lockclr
L0203f00a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+0]
    {pc, r4} = [sp++]
L0203f014:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r6 = [r4+56]
    r2 = [r4+64]
    if (r2 == 0) goto L0203f040
    r0 = [r4+8]
    call effect_parameter_support_memmove  ; @call.xl
    r0 = [r4+64]
    r1 = [r4+8]
    r1 += r0  ; @add.rr
    [r4+8] = r1
    r2 = [r4+4]
    r0 = 0
    if (r1 >= r2) {
    r1 = [r4+0]
    [r4+8] = r1
    }
    goto L0203f132
L0203f040:
    r1 = [r4+0]
    r0 = 0
    if (r1 != 0) goto L0203f132
    r8 = 0  #
    r5 = [r4+4]
    if (r5 == 0) goto L0203f12e
    call storage_coordination_irq_enter  ; @call.xl
    r7 = L01c1fc4c
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L0203f06a
    lockset
L0203f06a:
    csync
    r0 = L01c1fc64
    r1 = cnum
    r3 = [r0+r1<<2]
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0203f08e
    lockclr
L0203f08e:
    call storage_coordination_irq_leave  ; @call.xl
    if (r5 != r3) {
    call L0203e7a0
    }
    r5 += 76
    r0 = [r5+60]
    if (r0 != 0) goto L0203f0a8
    call L0203e7a0
    r0 = [r5+60]
L0203f0a8:
    r1 = r0 + -1
    [r5+60] = r1
    r0 = 0
    if (r1 != 0) goto L0203f12e
    r1 = [r5+56]
    r2 = [r5+40]
    if (r2 == r1) goto L0203f12e
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L0203f0d2
    lockset
L0203f0d2:
    csync
    r0 = r5
    call L0203efb6
    r1 = L01c344b4
    r2 = L01c1fc74
    if (r0 != 0) goto L0203f0f8
    r0 = [r5+40]
    r3 = r0 * 0x14
    r3 = [r3+r1]
    if (r3 != 0) goto L0203f0f8
    [r2+0] &= ~(1 << r0)
L0203f0f8:
    r0 = [r5+56]
    r3 = 0x1F - r0  #
    [r5+40] = r0
    [r5+20] = r3
    [r2+0] |= 1 << r0
    r0 = r0 * 0x14
    r0 += r1  ; @add.rr
    r1 = r5
    call L0203e8cc
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0203f126
    lockclr
L0203f126:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 1
L0203f12e:
    [r4+4] = r8
L0203f132:
    r1 = r6 + 1
    [r4+56] = r1
    {pc, r8-r4} = [sp++]
L0203f138:
    r0 = L01c34784
    r1 = [r0+0]
    r1 = [r1+0]
    if (r1 != 0) {  ; @if.ne.ri.s12
    r0 = [r0+0]
    r0 = [r0+12]
    r0 = [r0+12]
    r0 = [r0+76]
    } else {
    r0 = -1
    }
    r1 = L01c1fc88
    [r1+0] = r0
    rts
L0203f15c:
    [--sp] = {rets, r6-r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    if (r1 != 0) goto L0203f17e
    lockset
L0203f17e:
    csync
    r0 = [r2+12]
    r6 = [r0+12]
    if (r6 != 0) goto L0203f18a
    call L0203e7a0
L0203f18a:
    r4 = r6 + 96
    r0 = r4
    call L0203efb6
    r0 = L01c1fc84
    r0 = [r0+0]
    if (r0 == 0) goto L0203f1ae
    r0 = L01c34748
    r1 = r4
    call L0203e8cc
    r6 += 116
    goto L0203f1d8
L0203f1ae:
    r4 = r6 + 76
    r0 = r4
    call L0203efb6
    r0 = [++r6=116]
    r1 = L01c1fc74
    [r1+0] |= 1 << r0
    r0 = r0 * 0x14
    r1 = L01c344b4
    r0 += r1  ; @add.rr
    r1 = r4
    call L0203e8cc
L0203f1d8:
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0203f1ec
    lockclr
L0203f1ec:
    call storage_coordination_irq_leave  ; @call.xl
    r3 = [r6+0]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L0203f20c
    lockset
L0203f20c:
    csync
    r0 = L01c1fc64
    r1 = cnum
    r4 = [r0+r1<<2]
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0203f230
    lockclr
L0203f230:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r4+116]
    r2 = 0
    if (r3 > r0) {
    r0 = L01c1fc8c
    r2 = 1
    [r0+0] = r2
    }
    call L0203f138
    r0 = r2
    {pc, r6-r4} = [sp++]
L0203f252:
    [--sp] = rets
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0203f272
    lockset
L0203f272:
    csync
    r0 = L01c1fc84
    [r0+0] += 1  ; @rmw.add.s12
    pc = [sp++]
L0203f280:
    [--sp] = {rets, r4}
    r4 = r0
    if (r4 != 0) goto L0203f28a
    call L0203e7a0
L0203f28a:
    r0 = L01c1fc98
    r0 = [r0+0]
    [r4+0] = r0
    r0 = L01c1fc94
    r0 = [r0+0]
    [r4+4] = r0
    {pc, r4} = [sp++]
L0203f2a0:
    [--sp] = {rets, r8-r4}
    r5_r4 = r1_r0
    if (r4 != 0) goto L0203f2aa
    call L0203e7a0
L0203f2aa:
    if (r5 != 0) goto L0203f2b0
    call L0203e7a0
L0203f2b0:
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fc4c
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f2ce
    lockset
L0203f2ce:
    csync
    r0 = L01c1fc94
    r8 = [r0+0]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f2f2
    lockset
L0203f2f2:
    csync
    r3 = L01c1fc64
    r0 = cnum
    r7 = [r3+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f316
    lockclr
L0203f316:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = b[r7+157] (u)
    if (r0 == 0) goto L0203f384
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f33a
    lockset
L0203f33a:
    csync
    r0 = cnum
    r3 = [r3+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f358
    lockclr
L0203f358:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 0
    b[r3+157] = r0
    r3 = 1
L0203f366:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f37a
    lockclr
L0203f37a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r8-r4} = [sp++]
L0203f384:
    r0 = [r5+0]
    r3 = 0
    if (r0 == -1) goto L0203f366
    r1 = L01c1fc98
    r2 = [r1+0]
    r7 = [r4+0]
    r1 = [r4+4]
    r3 = 1
    if (r2 == r7) goto L0203f3a2
    if (r8 >= r1) goto L0203f366
L0203f3a2:
    r1 = r8 - r1
    if (r0 <= r1) goto L0203f366
    r0 = r0 - r1
    r0 = r4  #
    [r5+0] = r0
    call L0203f280
    r3 = 0
    goto L0203f366
L0203f3b8:
    [--sp] = {rets, r5, r4}
    r4 = [r1+0]
    if (r4 == -1) goto L0203f3ce
    r3 = r0 + 8
L0203f3c2:
    r2 = r3
    r3 = [r2+4]
    r5 = [r3+0]
    if (r5 <= r4) goto L0203f3c2
    goto L0203f3d2
L0203f3ce:
    r2 = [r0+16]
    r3 = [r2+4]
L0203f3d2:
    [r1+4] = r3
    [r3+8] = r1
    [r1+8] = r2
    [r2+4] = r1
    [r1+16] = r0
    [r0+0] += 1  ; @rmw.add.s12
    {pc, r5, r4} = [sp++]
L0203f3e2:
    [--sp] = {rets, r8-r4}
    r2 = L01c1fc94
    r8 = [r2+0]
    r5_r4 = r1_r0
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fc4c
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f40e
    lockset
L0203f40e:
    csync
    r7 = L01c1fc64
    r0 = cnum
    r3 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f432
    lockclr
L0203f432:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 0
    b[r3+157] = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f456
    lockset
L0203f456:
    csync
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f470
    lockset
L0203f470:
    csync
    r0 = cnum
    r3 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f48e
    lockclr
L0203f48e:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3 + 76
    call L0203efb6
    if (r0 != 0) goto L0203f4e8
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f4b6
    lockset
L0203f4b6:
    csync
    r0 = cnum
    r3 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f4d4
    lockclr
L0203f4d4:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+116]
    r1 = L01c1fc74
    [r1+0] &= ~(1 << r0)
L0203f4e8:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f4fc
    lockclr
L0203f4fc:
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 != -1) goto L0203f554
    if (r5 == 0) goto L0203f554
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f520
    lockset
L0203f520:
    csync
    r0 = cnum
    r3 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f53e
    lockclr
L0203f53e:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = r3 + 76
    r0 = L01c34770
    call L0203e8cc
    {pc, r8-r4} = [sp++]
L0203f554:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f56c
    lockset
L0203f56c:
    csync
    r0 = cnum
    r3 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r4 += r8
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f58c
    lockclr
L0203f58c:
    call storage_coordination_irq_leave  ; @call.xl
    [r3+76] = r4
    if (r4 >= r8) goto L0203f5ea
    r0 = L01c34788
    r3 = [r0+0]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f5ba
    lockset
L0203f5ba:
    csync
    r0 = cnum
    r4 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f5d8
    lockclr
L0203f5d8:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = r4 + 76
    r0 = r3
    call L0203f3b8
    {pc, r8-r4} = [sp++]
L0203f5ea:
    r0 = L01c34784
    r3 = [r0+0]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203f60a
    lockset
L0203f60a:
    csync
    r0 = cnum
    r5 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203f628
    lockclr
L0203f628:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = r5 + 76
    r0 = r3
    call L0203f3b8
    r0 = L01c1fc88
    r1 = [r0+0]
    if (r4 < r1) {
    [r0+0] = r4
    }
    {pc, r8-r4} = [sp++]
L0203f648:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    if (r5 != 0) goto L0203f654
    call L0203e7a0
L0203f654:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0203f672
    lockset
L0203f672:
    csync
    r1 = L01c1fc64
    r2 = cnum
    r3 = [r1+r2<<2]
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203f696
    lockclr
L0203f696:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = r3 + 96
    r0 = r5
    call L0203f3b8
    r1 = 1
    r0 = r4
    call L0203f3e2
    {pc, r5, r4} = [sp++]
L0203f6b0:
    [--sp] = {rets, r8-r4}
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r8 = L01c1fc4c
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    if (r1 != 0) goto L0203f6d2
    lockset
L0203f6d2:
    csync
    r6 = r4 + 68
    r5 = b[r6+1] (u)
    r7 = L01c1fc8c
    goto L0203f6f6
L0203f6e2:
    r0 = r4
    r1 = [++r0=36]
    if (r1 == 0) goto L0203f6fc
    call L0203f15c
    if (r0 == 0) goto L0203f6f4
    [r7+0] = 0x1
L0203f6f4:
    r5 += -1
L0203f6f6:
    r0 = r5.b0 (s)
    ifs (r0 >= 1) goto L0203f6e2
L0203f6fc:
    r0 = 255
    b[r6+1] = r0
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203f714
    lockclr
L0203f714:
    call storage_coordination_irq_leave  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    if (r1 != 0) goto L0203f732
    lockset
L0203f732:
    csync
    r5 = b[r6+0] (u)
    goto L0203f74c
L0203f738:
    r0 = r4
    r1 = [++r0=16]
    if (r1 == 0) goto L0203f752
    call L0203f15c
    if (r0 == 0) goto L0203f74a
    [r7+0] = 0x1
L0203f74a:
    r5 += -1
L0203f74c:
    r0 = r5.b0 (s)
    ifs (r0 >= 1) goto L0203f738
L0203f752:
    r0 = 255
    b[r6+0] = r0
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203f76a
    lockclr
L0203f76a:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r8-r4} = [sp++]
L0203f772:
    [--sp] = {rets, r13-r4}
    r0 = L01c1fc84
    r0 = [r0+0]
    if (r0 == 0) goto L0203f78c
    r0 = L01c1fc90
    [r0+0] += 1  ; @rmw.add.s12
    r11 = 0
    goto L0203f8e4
L0203f78c:
    r8 = L01c1fc94
    r0 = [r8+0]
    r6 = r0 + 1
    [r8+0] = r6
    r4 = L01c34784
    if (r6 != 0) goto L0203f7ca
    r0 = [r4+0]
    r0 = [r0+0]
    if (r0 == 0) goto L0203f7ae
    call L0203e7a0
L0203f7ae:
    r0 = [r4+0]
    r1 = L01c34788
    r2 = [r1+0]
    [r4+0] = r2
    [r1+0] = r0
    r0 = L01c1fc98
    [r0+0] += 1  ; @rmw.add.s12
    call L0203f138
L0203f7ca:
    r12 = L01c1fc88
    r0 = [r12+0]
    r11 = 0
    r9 = L01c1fc4c
    r10 = L01c344b4
    r7 = L01c1fc64
    if (r6 < r0) goto L0203f880
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L0203f804
    lockset
L0203f804:
    csync
    r0 = 0
    r13 = L01c1fc74
L0203f80e:
    r11 = r0
L0203f810:
    r0 = [r4+0]
    r0 = [r0+0]
    if (r0 == 0) goto L0203f860
    r0 = [r4+0]
    r0 = [r0+12]
    r5 = [r0+12]
    r0 = [++r5=76]
    if (r6 < r0) goto L0203f862
    r0 = r5
    call L0203efb6
    r0 = [r5+36]
    if (r0 == 0) goto L0203f834
    r0 = r5 + 20
    call L0203efb6
L0203f834:
    r0 = [r5+40]
    [r13+0] |= 1 << r0
    r0 = r0 * 0x14
    r0 += r10
    r1 = r5
    call L0203e8cc
    r1 = [r5+40]
    r0 = [r7+0]
    r2 = [r0+116]
    r0 = 1
    if (r1 >= r2) goto L0203f80e
    r2 = [r7+4]
    r2 = [r2+116]
    if (r1 < r2) goto L0203f810
    goto L0203f80e
L0203f860:
    r0 = -1
L0203f862:
    [r12+0] = r0
    csync
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0203f87a
    lockclr
L0203f87a:
    call storage_coordination_irq_leave  ; @call.xl
L0203f880:
    r0 = [r8+0]
    r1 = 5
    r1 = r0 / r1 (u)
    r1 = r1 * 0x5
    r0 = r0 - r1
    if (r0 != 0) goto L0203f8e4
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L0203f8aa
    lockset
L0203f8aa:
    csync
    r0 = cnum
    r3 = [r7+r0<<2]
    csync
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0203f8c8
    lockclr
L0203f8c8:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+116]
    r0 = r0 * 0x14
    r1 = [r0+r10]
    r0 = 1
    if (r1 <= 1) {  ; @if.le.ri.s12
    r0 = r11
    }
    r11 = r0
L0203f8e4:
    r0 = L01c1fc8c
    r0 = [r0+0]
    if (r0 == 0) goto L0203f8f2
    r11 = 1
L0203f8f2:
    r0 = r11
    {pc, r13-r4} = [sp++]
L0203f8f6:
    [--sp] = {rets, r10-r4}
    r4 = L01c1fc84
    r0 = [r4+0]
    if (r0 != 0) goto L0203f906
    call L0203e7a0
L0203f906:
    [r4+0] += -1  ; @rmw.add.s12
    r0 = [r4+0]
    r3 = 0
    if (r0 == 0) goto L0203f934
L0203f910:
    csync
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203f92a
    lockclr
L0203f92a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r10-r4} = [sp++]
L0203f934:
    r0 = L01c1fc60
    r0 = [r0+0]
    if (r0 == 0) goto L0203f910
    r7 = 0
    r6 = L01c34748
    r8 = L01c1fc8c
    r9 = L01c1fc74
    r10 = L01c344b4
    r5 = L01c1fc64
    goto L0203f9a6
L0203f960:
    r0 = [r6+12]
    r7 = [r0+12]
    r0 = r7 + 96
    call L0203efb6
    r4 = r7 + 76
    r0 = r4
    call L0203efb6
    r0 = [r7+116]
    [r9+0] |= 1 << r0
    r0 = r0 * 0x14
    r0 += r10
    r1 = r4
    call L0203e8cc
    r0 = [r7+116]
    r1 = [r5+0]
    r1 = [r1+116]
    if (r0 >= r1) goto L0203f9a2
    r1 = [r5+4]
    r1 = [r1+116]
    if (r0 < r1) goto L0203f9a6
L0203f9a2:
    [r8+0] = 0x1
L0203f9a6:
    r0 = [r6+0]
    if (r0 != 0) goto L0203f960
    if (r7 == 0) goto L0203f9b0
    call L0203f138
L0203f9b0:
    r4 = L01c1fc90
    r5 = [r4+0]
    if (r5 == 0) goto L0203f9cc
L0203f9ba:
    call L0203f772
    if (r0 == 0) goto L0203f9c4
    [r8+0] = 0x1
L0203f9c4:
    if (--r5 != 0) goto L0203f9ba
    [r4+0] = 0x0
L0203f9cc:
    r0 = [r8+0]
    if (r0 == 0) goto L0203f9da
    call L0203ea6e
    r3 = 1
    goto L0203f910
L0203f9da:
    r3 = 0
    goto L0203f910
L0203f9de:
    [--sp] = {rets, r14-r4}
    sp += -12
    r4 = r0
    r0 = 0
    r8 = r1  #
    [sp+8] = r0
    if (r4 == 0) goto L0203fb8c
    r5 = r4 + 64
    if (r1 != 0) goto L0203f9fa
    r0 = [r5+0]
    if (r0 != 0) goto L0203fb8c
L0203f9fa:
    r9 = sp + 0
    r13 = r4 + 16
    r10 = 0
    r7 = L01c1fc4c
    r11 = L01c1fc98
    r12 = L01c1fc94
    r14 = 0
    goto L0203fb06
L0203fa1a:
    r0 = [sp+8]
    if (r0 == 0) goto L0203fb60
    if (r14 != 0) goto L0203fa36
    r0 = [r11+0]
    [sp] = r0
    r0 = [r12+0]
    [r9+4] = r0
    r14 = 1
L0203fa36:
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0203fa4a
    lockclr
L0203fa4a:
    call storage_coordination_irq_leave  ; @call.xl
    call L0203f252
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L0203fa6c
    lockset
L0203fa6c:
    csync
    r0 = b[r5+4] (u)
    if (r0 == 255) {  ; @if.eq.ri.s12
    b[r5+4] = r10
    }
    r0 = b[r5+5] (u)
    if (r0 == 255) {  ; @if.eq.ri.s12
    b[r5+5] = r10
    }
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0203fa96
    lockclr
L0203fa96:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = sp + 0
    r1 = sp + 8
    call L0203f2a0
    if (r0 != 0) goto L0203fb7c
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L0203fabe
    lockset
L0203fabe:
    csync
    r3 = [r4+56]
    r6 = [r4+60]
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0203fad8
    lockclr
L0203fad8:
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 != r6) goto L0203fafc
    r0 = r13  #
    r1 = [sp+8]
    call L0203f648
    r0 = r4
    call L0203f6b0
    call L0203f8f6
    if (r0 != 0) goto L0203fb06
    call L0203ea6e
    goto L0203fb06
L0203fafc:
    r0 = r4
    call L0203f6b0
    call L0203f8f6
L0203fb06:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L0203fb1e
    lockset
L0203fb1e:
    csync
    r1_r0 = d[r4+56]
    if (r0 >= r1) goto L0203fa1a
    r0 = r4
    r1 = r8
    call L0203f014
    r1 = [++r4=36]
    if (r1 == 0) goto L0203fb3c
    r0 = r4
    call L0203f15c
L0203fb3c:
    if (r0 == 0) goto L0203fb42
    call L0203ea6e
L0203fb42:
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0203fb56
    lockclr
L0203fb56:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 1
    goto L0203fb88
L0203fb60:
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0203fb74
    lockclr
L0203fb74:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0203fb86
L0203fb7c:
    r0 = r4
    call L0203f6b0
    call L0203f8f6
L0203fb86:
    r0 = 0
L0203fb88:
    sp += 12
    {pc, r14-r4} = [sp++]
L0203fb8c:
    call L0203eed8
L0203fb90:
    goto L0203fb90
L0203fb92:
    [--sp] = {rets, r4}
    sp += -4
    r3 = r0
    r0 = 4
    [sp] = r0
    r0 = 1
    r1 = 0
    r2 = 0
    r4 = 0
    call L0203ef10
    if (r0 == 0) goto L0203fbba
    r2 = 0
    r3 = 0
    d[r0+0] = r3_r2
    [r0+12] = r4
    r1 = 0
    call L0203f9de
L0203fbba:
    sp += 4
    {pc, r4} = [sp++]
L0203fbbe:
    r0 = L01c1fca0
    r1 = 1
    b[r0+0] = r1
    r0 = L01c34d10
    [r0+0] = r0
    [r0+4] = r0
    rts
L0203fbd4:
    [--sp] = {rets, r9-r4}
    sp += -12
    r8 = r3  #
    r6 = [sp+40]
    r9 = r2  #
    r4 = [sp+44]
    r7 = r1
    r5 = r0
    if (r6 != 0) goto L0203fbea
    call L0203e7a0
L0203fbea:
    if (r4 == 0) goto L0203fc14
    if (r6 == 0) goto L0203fc18
    [r4+120] = r6
    r0 = 2
    b[r4+156] = r0
    r1 = r7  #
    [sp+4] = r4
    r0 = sp + 8
    r0 = r5  #
    [sp] = r0
    r2 = r9
    r3 = r8
    call L0203e7d8
    r0 = r4
    call L0203eb62
    r0 = [sp+8]
    goto L0203fc1c
L0203fc14:
    call L0203e7a0
L0203fc18:
    r0 = 0
    [sp+8] = r0
L0203fc1c:
    sp += 12
    {pc, r9-r4} = [sp++]
L0203fc20:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L0203fc42
    lockset
L0203fc42:
    csync
    r1 = L01c34d10
    r3 = [r1+0]
    [r3+4] = r2
    [r2+0] = r3
    [r2+4] = r1
    [r1+0] = r2
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203fc68
    lockclr
L0203fc68:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]
L0203fc70:
    [--sp] = {rets, r9-r4}
    sp += -8
    r5 = r3  #
    r7 = [sp+40]
    r9 = r2  #
    r4 = [sp+36]
    r3_r2 = r1_r0
    r8 = L01c1fc4c
    if (r5 == 0) goto L0203fca0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r8+r0<<2]
    r6 = r1 + 1
    [r8+r0<<2] = r6
    if (r1 != 0) goto L0203fc9e
    lockset
L0203fc9e:
    csync
L0203fca0:
    r6 = r7 + 164
    d[sp] = r7_r6
    r0 = r2
    r1 = r4
    r2 = r9
    call L0203fbd4
    if (r0 == 0) goto L0203fcee
    r4 = 0
    if (r5 == 0) goto L0203fd0c
    r0 = r9 << 2
    r6 += r0  ; @add.rr
    [r6+8] = r7
    r7 = 5
    r0 = 4
    r0 = r5 / r0 (s)  #
    [sp] = r7
    r2 = r6 + 92
    r3 = r6 + 12
    r1 = 4
    call L0203ef10
    r0 = r6
    call L0203fc20
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203fd06
    lockclr
    goto L0203fd06
L0203fcee:
    r4 = -1
    if (r5 == 0) goto L0203fd0c
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203fd06
    lockclr
L0203fd06:
    call storage_coordination_irq_leave  ; @call.xl
L0203fd0c:
    r0 = r4
    sp += 8
    {pc, r9-r4} = [sp++]
L0203fd12:
    [--sp] = {rets, r8-r4}
    sp += -8
    r5 = r3  #
    r4 = [sp+32]
    r3 = r1
    r6 = r0
    r8 = L01c1fc4c
    if (r5 == 0) goto L0203fd40
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r8+r0<<2]
    r7 = r1 + 1
    [r8+r0<<2] = r7
    if (r1 != 0) goto L0203fd3e
    lockset
L0203fd3e:
    csync
L0203fd40:
    r0 = sp + 4
    r0 = r6  #
    [sp] = r0
    r1 = r4
    call L0203ed34
    r4 = r0
    if (r4 != 1) goto L0203fd98
    r4 = 0
    if (r5 == 0) goto L0203fdb4
    r0 = r5 + 92
    call L0203c15c  ; @call.xl
    r6 = r0  #
    r1 = [sp+4]
    r7 = 5
    r0 = 4
    r0 = r5 / r0 (s)  #
    [r6+8] = r1
    r2 = r6 + 92  #
    [sp] = r7
    r3 = r6 + 12
    r1 = 4
    call L0203ef10
    r0 = r6
    call L0203fc20
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203fdae
    lockclr
    goto L0203fdae
L0203fd98:
    if (r5 == 0) goto L0203fdb4
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0203fdae
    lockclr
L0203fdae:
    call storage_coordination_irq_leave  ; @call.xl
L0203fdb4:
    r0 = r4
    sp += 8
    {pc, r8-r4} = [sp++]
L0203fdba:
    [--sp] = {rets, r4}
    sp += -4
    r3 = r0
    r0 = 2
    [sp] = r0
    r0 = 255
    r1 = 0
    r2 = 0
    r4 = 0
    call L0203ef10
    if (r0 == 0) goto L0203fdd4
    [r0+56] = r4
L0203fdd4:
    sp += 4
    {pc, r4} = [sp++]
L0203fdd8:
    [--sp] = rets
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0203fdf8
    lockset
L0203fdf8:
    csync
    r1 = L01c1fc64
    r2 = cnum
    r3 = [r1+r2<<2]
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203fe1c
    lockclr
L0203fe1c:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    pc = [sp++]
L0203fe26:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L0203fe48
    lockset
L0203fe48:
    r1 = L01c34d10
    csync
    r3 = r1
L0203fe52:
    r3 = [r3+0]
    if (r3 == r1) goto L0203fe7c
    r4 = [r3+8]
    if (r4 != r2) goto L0203fe52
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203fe72
    lockclr
L0203fe72:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3 + 12
    {pc, r4} = [sp++]
L0203fe7c:
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0203fe90
    lockclr
L0203fe90:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 0
    {pc, r4} = [sp++]
L0203fe9a:
    [--sp] = {rets, r4}
    r4 = r0
    if (r4 == 0) goto L0203feb2
    call L0203f252
    r1 = 0
    r0 = r4
    call L0203f3e2
    call L0203f8f6
    if (r0 != 0) goto L0203feb6
L0203feb2:
    call L0203ea6e
L0203feb6:
    {pc, r4} = [sp++]
L0203feb8:
    [--sp] = rets
    call L0203fe9a
    pc = [sp++]
L0203febe:
    [--sp] = {rets, r4}
    r2 = [r0+64]
    if (r2 == 0) goto L0203fee0
    r3 = [r0+12]
    r3 += r2  ; @add.rr
    [r0+12] = r3
    r4 = [r0+4]
    if (r3 >= r4) {
    r3 = [r0+0]
    [r0+12] = r3
    }
    r0 = r1
    r1 = r3
    call effect_parameter_support_memmove  ; @call.xl
L0203fee0:
    {pc, r4} = [sp++]
L0203fee2:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L0203ff04
    lockset
L0203ff04:
    csync
    r2 = [r2+56]
    csync
    r3 = cnum
    r1 = [r0+r3<<2]
    r1 += -1
    [r0+r3<<2] = r1
    r3 = 1
    if (r2 == 0) goto L0203ff1e
    r3 = 0
L0203ff1e:
    if (r1 != 0) goto L0203ff22
    lockclr
L0203ff22:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r4} = [sp++]
L0203ff2c:
    [--sp] = {rets, r15-r4}
    sp += -12
    r9 = r3  #
    [sp+8] = r2
    r14 = r1
    r4 = r0
    if (r4 == 0) goto L0204035c
    r7 = r4 + 64
    if (r1 != 0) goto L0203ff4c
    r0 = [r7+0]
    if (r0 != 0) goto L0204035c
L0203ff4c:
    r12 = sp + 0
    r11 = r4 + 36
    r13 = 0
    r6 = L01c1fc4c
    r8 = L01c1fc64
    r15 = L01c1fc98
    r10 = 0
    goto L02040208
L0203ff6c:
    r0 = [sp+8]
    if (r0 == 0) goto L02040242
    if (r10 != 0) goto L0203ff8e
    r0 = [r15+0]
    [sp] = r0
    r0 = L01c1fc94
    r10 = 1  #
    r0 = [r0+0]
    [r12+4] = r0
L0203ff8e:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203ffa2
    lockclr
L0203ffa2:
    call storage_coordination_irq_leave  ; @call.xl
    call L0203f252
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0203ffc4
    lockset
L0203ffc4:
    csync
    r0 = b[r7+4] (u)
    if (r0 == 255) {  ; @if.eq.ri.s12
    b[r7+4] = r13
    }
    r0 = b[r7+5] (u)
    if (r0 == 255) {  ; @if.eq.ri.s12
    b[r7+5] = r13
    }
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0203ffee
    lockclr
L0203ffee:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = sp + 0
    r1 = sp + 8
    call L0203f2a0
    if (r0 == 0) goto L02040014
    r0 = r4
    call L0203f6b0
    call L0203f8f6
    r0 = r4
    call L0203fee2
    if (r0 == 0) goto L02040208
    goto L0204025c
L02040014:
    r0 = r4
    call L0203fee2
    if (r0 == 0) goto L02040148
    r0 = [r4+0]
    if (r0 != 0) goto L020401f0
    r2 = [r4+4]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r3 = r1 + 1
    [r6+r0<<2] = r3
    if (r1 != 0) goto L0204003e
    lockset
L0204003e:
    csync
    if (r2 == 0) goto L020401d6
    r13 = r11
    r11 = r15
    r15 = r14
    r5 = r2 + 76
    r14 = r9  #
    r3 = [r5+40]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0204006a
    lockset
L0204006a:
    csync
    r0 = cnum
    r9 = r8
    r8 = [r8+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0204008a
    lockclr
L0204008a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r8+116]
    r8 = r9
    r9 = r14
    r14 = r15
    r15 = r11
    r11 = r13
    r13 = 0
    if (r3 >= r0) goto L020401d6
    r0 = [r5+20]
    ifs (r0 < 0) goto L020400f0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L020400c2
    lockset
L020400c2:
    csync
    r0 = cnum
    r3 = [r8+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020400e0
    lockclr
L020400e0:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+116]
    r0 = 0x1F - r0
    [r5+20] = r0
L020400f0:
    r0 = [r5+40]
    r0 = r0 * 0x14  #
    r1 = [r5+16]
    r2 = L01c344b4
    r0 += r2  ; @add.rr
    if (r1 == r0) goto L02040154
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0204011c
    lockset
L0204011c:
    csync
    r0 = cnum
    r3 = [r8+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0204013a
    lockclr
L0204013a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+116]
    [r5+40] = r0
    goto L020401d6
L02040148:
    r0 = r4
    call L0203f6b0
    call L0203f8f6
    goto L02040208
L02040154:
    r0 = r5
    call L0203efb6
    if (r0 != 0) goto L02040178
    r0 = [r5+40]
    r1 = r0 * 0x14
    r2 = L01c344b4
    r1 = [r1+r2]
    if (r1 != 0) goto L02040178
    r1 = L01c1fc74
    [r1+0] &= ~(1 << r0)
L02040178:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L02040190
    lockset
L02040190:
    csync
    r0 = cnum
    r3 = [r8+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020401ae
    lockclr
L020401ae:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+116]
    [r5+40] = r0
    r1 = L01c1fc74
    [r1+0] |= 1 << r0
    r0 = r0 * 0x14
    r1 = L01c344b4
    r0 += r1  ; @add.rr
    r1 = r5
    call L0203e8cc
L020401d6:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020401ea
    lockclr
L020401ea:
    call storage_coordination_irq_leave  ; @call.xl
L020401f0:
    r0 = r11  #
    r1 = [sp+8]
    call L0203f648
    r0 = r4
    call L0203f6b0
    call L0203f8f6
    if (r0 != 0) goto L02040208
    call L0203ea6e
L02040208:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L02040220
    lockset
L02040220:
    csync
    r5 = [r4+56]
    if (r5 == 0) goto L0203ff6c
    r0 = r4  #
    r7 = [r4+12]
    r1 = r14
    call L0203febe
    if (r9 == 0) goto L02040260
    [r4+12] = r7
    r0 = [r4+36]
    if (r0 == 0) goto L0204033c
    r0 = r11
    goto L02040332
L02040242:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02040256
    lockclr
L02040256:
    call storage_coordination_irq_leave  ; @call.xl
L0204025c:
    r0 = 0
    goto L02040358
L02040260:
    r0 = r5 + -1
    [r4+56] = r0
    r0 = [r4+0]
    if (r0 != 0) goto L0204032a
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L02040282
    lockset
L02040282:
    csync
    r0 = cnum
    r3 = [r8+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020402a0
    lockclr
L020402a0:
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 == 0) goto L020402ec
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L020402c0
    lockset
L020402c0:
    csync
    r0 = cnum
    r3 = [r8+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020402de
    lockclr
L020402de:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3 + 136
    [r0+0] += 1  ; @rmw.add.s12
L020402ec:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L02040304
    lockset
L02040304:
    csync
    r0 = cnum
    r3 = [r8+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02040322
    lockclr
L02040322:
    call storage_coordination_irq_leave  ; @call.xl
    [r4+4] = r3
L0204032a:
    r0 = [++r4=16]
    if (r0 == 0) goto L0204033c
    r0 = r4
L02040332:
    call L0203f15c
    if (r0 == 0) goto L0204033c
    call L0203ea6e
L0204033c:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02040350
    lockclr
L02040350:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 1
L02040358:
    sp += 12
    {pc, r15-r4} = [sp++]
L0204035c:
    call L0203eed8
L02040360:
    goto L02040360
