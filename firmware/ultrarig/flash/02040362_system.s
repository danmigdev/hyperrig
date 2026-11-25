; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02040362..0x0204176a: system layer code (not reversed), as instructions
L02040362:
    [--sp] = {rets, r4}
    r2 = r0
    if (r2 == 0) goto L020403a8
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L02040386
    lockset
L02040386:
    csync
    r3 = [r2+56]
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0204039e
    lockclr
L0204039e:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r4} = [sp++]
L020403a8:
    call L0203eed8
L020403ac:
    goto L020403ac
L020403ae:
    [--sp] = {rets, r7-r4}
    r4 = r0
    if (r4 == 0) goto L020403e8
    r5 = r4 + 64
    if (r1 != 0) goto L020403be
    r0 = [r5+0]
    if (r0 != 0) goto L020403e8
L020403be:
    r7 = [r4+56]
    if (r7 == 0) goto L020403d8
    r0 = r4  #
    r6 = b[r5+4] (u)
    call L0203febe
    r0 = r7 + -1
    [r4+56] = r0
    if (r6 == 255) goto L020403da
    r0 = r6 + 1
    b[r5+4] = r0
L020403d8:
    {pc, r7-r4} = [sp++]
L020403da:
    r0 = [++r4=16]
    if (r0 == 0) goto L020403d8
    r0 = r4
    call L0203f15c
    {pc, r7-r4} = [sp++]
L020403e8:
    call L0203eed8
L020403ec:
    goto L020403ec
L020403ee:
    [--sp] = {rets, r5, r4}
    r1 = rets
    r1 = icfg
    r2 = r0
    if ((r1 & 0xFF) == 0) goto L0204046c
    if (r2 == 0) goto L02040488
    r5 = r2 + 64
    r0 = [r5+0]
    if (r0 != 0) goto L02040488
    r0 = [r2+0]
    if (r0 != 0) goto L02040412
    r0 = [r2+4]
    if (r0 != 0) goto L02040488
L02040412:
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fc4c
    r0 = cnum
    r1 = [r4+r0<<2]
    r3 = r1 + 1
    [r4+r0<<2] = r3
    if (r1 != 0) goto L02040430
    lockset
L02040430:
    csync
    r1_r0 = d[r2+56]
    r3 = 0
    if (r0 >= r1) goto L0204044a
    r1 = b[r5+5] (u)
    r0 += 1  ; @add.ri.u5
    [r2+56] = r0
    if (r1 == 255) goto L02040474
    r0 = r1 + 1
    b[r5+5] = r0
L0204044a:
    csync
    r0 = cnum
    r1 = [r4+r0<<2]
    r1 += -1
    [r4+r0<<2] = r1
    if (r1 != 0) goto L0204045e
    lockclr
L0204045e:
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 == 0) goto L02040472
    call L0203ea6e
    {pc, r5, r4} = [sp++]
L0204046c:
    r1 = 0
    call L0203f9de
L02040472:
    {pc, r5, r4} = [sp++]
L02040474:
    r0 = [++r2=36]
    if (r0 == 0) goto L0204044a
    r0 = r2
    call L0203f15c
    r3 = 1
    if (r0 != 0) goto L0204044a
    r3 = r0
    goto L0204044a
L02040488:
    call L0203eed8
L0204048c:
    goto L0204048c
L0204048e:
    [--sp] = {rets, r10-r4}
    sp += -4
    r4 = r0
    call L0203fdd8
    r6 = r0
    goto L020404a2
L0204049c:
    r0 = 2
    call L0203feb8
L020404a2:
    r0 = r6
    call L0203fe26
    r5 = r0
    if (r5 == 0) goto L0204049c
    r9 = r4 + 4
    r8 = r4 + 16
    r10 = L01c1fc4c
    goto L020405bc
L020404bc:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r10+r0<<2]
    r2 = r1 + 1
    [r10+r0<<2] = r2
    if (r1 != 0) goto L020404d4
    lockset
L020404d4:
    csync
    r0 = r5
    call L02040362
    if (r0 == 0) goto L02040562
    r1 = sp + 0
    r0 = r5
    call L020403ae
    r7 = r9  #
    r0 = [sp]
    r1 = r0 >> 8
    [r4+0] = r1
    r6 = 0
    goto L02040502
L020404f2:
    r0 = r5
    r1 = r7
    call L020403ae
    r0 = b[sp] (u)
    r7 += 4  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02040502:
    r0 = r0.b0 (u)
    ifs (r6 < r0) goto L020404f2
    csync
    r0 = cnum
    r1 = [r10+r0<<2]
    r1 += -1
    [r10+r0<<2] = r1
    if (r1 != 0) goto L0204051c
    lockclr
L0204051c:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r4+0]
    r0 = r0 & 0xF00000
    if (r0 != 3145728) goto L020405d0
    r0 = [r4+8]
    r6 = r0.b0 (u)
    r7 = r6 + 1
    r1 = r6
    if ((r0 & 0x100) != 0) {
    r1 = r7
    }
    r2 = b[sp] (u)
    r3 = uextra(r0, p:9, l:1)
    r3 |= 2
    r1 += r3  ; @add.rr
    r2 += 1  ; @add.ri.u5
    if (r1 >= r2) goto L020405bc
    r1 = r0.b0 (u)
    if (r1 == 2) goto L0204057e
    if (r1 != 1) goto L0204058e
    r0 = [r4+12]
    r1 = [r9+0]
    call r1
    goto L0204059c
L02040562:
    csync
    r0 = cnum
    r1 = [r10+r0<<2]
    r1 += -1
    [r10+r0<<2] = r1
    if (r1 != 0) goto L02040576
    lockclr
L02040576:
    call storage_coordination_irq_leave  ; @call.xl
    goto L020405bc
L0204057e:
    if ((r0 & 1024) != 0) goto L0204058e
    r1_r0 = d[r4+12]
    r2 = [r9+0]
    call r2
    goto L0204059c
L0204058e:
    r1 = r6 + -1  #
    r0 = [r4+12]
    r3 = [r9+0]
    r2 = r8
    call r3
L0204059c:
    r1 = [r4+8]
    if ((r1 & 0x100) != 0) {
    r1 = r4 + 12
    r1 = [r1+r6<<2]
    [r1+0] = r0
    r1 = [r4+8]
    } else {
    r7 = r6
    }
    if ((r1 & 512) == 0) goto L020405bc
    r0 = r4 + 12
    r0 = [r0+r7<<2]
    call L020403ee
L020405bc:
    r1 = sp + 0
    r2 = -1
    r3 = 1
    r0 = r5
    call L0203ff2c
    if (r0 != 0) goto L020404bc
    r0 = 22
    goto L020405d2
L020405d0:
    r0 = 13
L020405d2:
    sp += 4
    {pc, r10-r4} = [sp++]
L020405d6:
    [--sp] = {rets, r5, r4}
    r1 = rets
    call L0204048e
    r5 = 29884172
    r1 = [r5+224]
    r2 = L02041656
    r4 = r0
    if (r1 != r2) goto L02040608
    call L0201d056  ; @call.xl
    r1 = [r5+0]
    r0 ^= r1
    r0 = r0.l (u)
    if (r0 != 0) goto L02040608
    r0 = r4
    {pc, r5, r4} = [sp++]
L02040608:
    call L0203e742
    call storage_fault_fatal  ; @call.xl
L02040612:
    goto L02040612
L02040614:
    [--sp] = {rets, r6-r4}
    r1 = rets
    r1 = icfg
    r4 = r0
    if ((r1 & 0xFF) != 0) goto L0204062e
    call L01c00e62  ; @call.xl
    if (r0 == 0) goto L0204063e
L0204062e:
    r0 = L01c1fca0
    r0 = b[r0+0] (u)
    r3 = 3
    if (r0 != 0) goto L02040730
L0204063a:
    r0 = r3
    {pc, r6-r4} = [sp++]
L0204063e:
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r2 = [r1+r0<<2]
    r3 = r2 + 1
    [r1+r0<<2] = r3
    r0 = L01c1fa20
    if (r2 != 0) goto L0204066a
    csync
L02040662:
    testset b[r0]
    ifeq goto L02040662
    csync
L0204066a:
    r2 = 80640
    r3 = [r2+4]
    r2 = [r2+0]
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L0204068a
    csync
    r1 = 0
    b[r0+0] = r1
L0204068a:
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 == 0) goto L02040746
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L020406b0
    lockset
L020406b0:
    csync
    r6 = [r4+4]
    call L0203fdd8
    if (r6 == r0) goto L02040704
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L020406d0
    lockclr
L020406d0:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = 0
    r2 = -1
    r3 = 0
    r6 = 0
    r0 = r4
    call L0203ff2c
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    if (r1 != 0) goto L020406fe
    lockset
L020406fe:
    csync
    if (r2 != 0) goto L02040706
    goto L0204070c
L02040704:
    r2 = 1
L02040706:
    [r4+12] += 1  ; @rmw.add.s12
    r6 = r2
L0204070c:
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02040720
    lockclr
L02040720:
    r3 = 0
    if (r6 != 1) {  ; @if.ne.ri.s12
    r3 = 11
    }
    call storage_coordination_irq_leave  ; @call.xl
    goto L0204063a
L02040730:
    call L0203e742
    r0 = icfg
    call L01c00e62  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02040744:
    goto L02040744
L02040746:
    call L0203eed8
L0204074a:
    goto L0204074a
L0204074c:
    [--sp] = {rets, r6-r4}
    r1 = rets
    r1 = icfg
    r4 = r0
    if ((r1 & 0xFF) != 0) goto L02040766
    call L01c00e62  ; @call.xl
    if (r0 == 0) goto L02040772
L02040766:
    r0 = L01c1fca0
    r0 = b[r0+0] (u)
    if (r0 != 0) goto L020407e8
L02040770:
    {pc, r6-r4} = [sp++]
L02040772:
    if (r4 == 0) goto L020407fe
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L02040792
    lockset
L02040792:
    csync
    r6 = [r4+4]
    call L0203fdd8
    if (r6 == r0) goto L020407ba
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L020407b2
    lockclr
L020407b2:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]
L020407ba:
    r0 = [r4+12]
    r3 = r0 + -1
    [r4+12] = r3
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L020407d6
    lockclr
L020407d6:
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 != 0) goto L02040770
    r1 = 0
    r0 = r4
    call L0203f9de
    {pc, r6-r4} = [sp++]
L020407e8:
    call L0203e742
    r0 = icfg
    call L01c00e62  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020407fc:
    goto L020407fc
L020407fe:
    call L0203eed8
L02040802:
    goto L02040802
L02040804:
    [--sp] = {rets, r4}
    r2 = r0
    if (r2 == 0) goto L0204084a
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L02040828
    lockset
L02040828:
    csync
    [r2+56] = 0x0
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L02040842
    lockclr
L02040842:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]
L0204084a:
    call L0203eed8
L0204084e:
    goto L0204084e
L02040850:
    [--sp] = {rets, r4}
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fc4c
    r0 = cnum
    r1 = [r4+r0<<2]
    r2 = r1 + 1
    [r4+r0<<2] = r2
    if (r1 != 0) goto L02040870
    lockset
L02040870:
    csync
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r4+r0<<2]
    r2 = r1 + 1
    [r4+r0<<2] = r2
    if (r1 != 0) goto L0204088a
    lockset
L0204088a:
    csync
    r0 = L01c1fc64
    r1 = cnum
    r3 = [r0+r1<<2]
    csync
    r0 = cnum
    r1 = [r4+r0<<2]
    r1 += -1
    [r4+r0<<2] = r1
    if (r1 != 0) goto L020408ae
    lockclr
L020408ae:
    call storage_coordination_irq_leave  ; @call.xl
    r3 = [r3+116]
    csync
    r0 = cnum
    r1 = [r4+r0<<2]
    r1 += -1
    [r4+r0<<2] = r1
    if (r1 != 0) goto L020408cc
    lockclr
L020408cc:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r4} = [sp++]
L020408d6:
    [--sp] = {rets, r10-r4}
    r4 = r0
    if (r4 >= 31) {  ; @if.ge.ri.s12
    call L0203e7a0
    }
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fc4c
    r1 = cnum
    r0 = [r6+r1<<2]
    r2 = r0 + 1
    [r6+r1<<2] = r2
    if (r4 >= 30) {  ; @if.ge.ri.s12
    r4 = 30
    }
    if (r0 != 0) goto L02040906
    lockset
L02040906:
    csync
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L02040920
    lockset
L02040920:
    csync
    r9 = L01c1fc64
    r0 = cnum
    r7 = [r9+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02040944
    lockclr
L02040944:
    call storage_coordination_irq_leave  ; @call.xl
    r5 = r7 + 76
    r3 = [r5+56]
    if (r3 == r4) goto L02040a4c
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0204096c
    lockset
L0204096c:
    csync
    r0 = cnum
    r10 = [r9+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0204098a
    lockclr
L0204098a:
    r0 = 1
    r1 = 1
    if (r7 != r10) {
    r1 = 0
    }
    if (r4 > r3) {
    r0 = 0
    }
    r8 = r0 & r1
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 <= r3) goto L020409f6
    if (r7 == r10) goto L020409f6
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L020409c4
    lockset
L020409c4:
    csync
    r0 = cnum
    r3 = [r9+r0<<2]
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020409e2
    lockclr
L020409e2:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r3+116]
    r8 = 1
    if (r4 < r0) {
    r8 = 0
    }
L020409f6:
    r7 = [r5+40]
    r0 = [r5+56]
    if (r0 == r7) {
    [r5+40] = r4
    }
    [r5+56] = r4
    r0 = [r5+20]
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r0 = r4 ^ 0x1F
    [r5+20] = r0
    }
    r1 = r7 * 0x14  #
    r0 = [r5+16]
    r4 = L01c344b4
    r1 += r4  ; @add.rr
    if (r0 != r1) goto L02040a44
    r0 = r5
    call L0203efb6
    r1 = L01c1fc74
    if (r0 != 0) goto L02040a32
    [r1+0] &= ~(1 << r7)
L02040a32:
    r0 = [r5+40]
    [r1+0] |= 1 << r0
    r0 = r0 * 0x14
    r0 += r4  ; @add.rr
    r1 = r5
    call L0203e8cc
L02040a44:
    if (r8 != 0) {  ; @if.ne.ri.s12
    call L0203ea6e
    }
L02040a4c:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02040a60
    lockclr
L02040a60:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r10-r4} = [sp++]
L02040a68:
    [--sp] = {rets, r9-r4}
    r2 = [r0+0]
    if (r2 == 0) goto L02040ab2
    r2 = [r0+4]
    r3 = [r2+4]
    r4 = r0 + 8
    r8 = r0 + 4  #
    [r0+4] = r3
    if (r3 == r4) {
    r3 = [r3+4]
    [r0+4] = r3
    }
    r9 = [r3+12]
L02040a86:
    r3 = [r3+4]
    [r0+4] = r3
    if (r3 == r4) {
    r3 = [r0+12]
    [r8+0] = r3
    }
    r2 = [r3+12]
    r7 = 0
L02040a98:
    if (r7 > 63) goto L02040aae
    r6 = b[r1+r7] (u)
    r5 = r2 + r7
    r5 = b[r5+12] (u)
    if (r5 != r6) goto L02040aae
    r7 += 1  ; @add.ri.u5
    if (r5 != 0) goto L02040a98
    goto L02040ab4
L02040aae:
    if (r2 != r9) goto L02040a86
L02040ab2:
    r2 = 0
L02040ab4:
    r0 = r2
    {pc, r9-r4} = [sp++]
L02040ab8:
    [--sp] = {rets, r7-r4}
    r4 = r0
    call L020283a8  ; @call.xl
    if (r0 >= 64) {  ; @if.ge.ri.s12
    call L0203e7a0
    }
    call L0203f252
    r0 = 600
    r6 = L01c344b4
L02040ad8:
    r7 = r0
    r0 = r7 + r6
    r1 = r4
    call L02040a68
    r5 = r0
    if (r5 != 0) goto L02040aea
    r0 = r7 + -20
    if (r7 != 0) goto L02040ad8
L02040aea:
    if (r5 != 0) goto L02040b1e
    r0 = L01c34784
    r0 = [r0+0]
    call L02040a68
    r5 = r0
    if (r5 != 0) goto L02040b1e
    r0 = L01c34788
    r0 = [r0+0]
    call L02040a68
    r5 = r0
    if (r5 != 0) goto L02040b1e
    r0 = L01c34770
    call L02040a68
    r5 = r0
    if (r5 != 0) goto L02040b1e
    r0 = L01c3475c
    call L02040a68
    r5 = r0
L02040b1e:
    call L0203f8f6
    r0 = r5
    {pc, r7-r4} = [sp++]
L02040b26:
    [--sp] = {rets, r8-r4}
    r8 = r2
    r2 = r1
    r5 = r0
    if (r5 == 0) goto L02040ba8
    r7 = r5 + 64
    if (r2 != 0) goto L02040b3a
    r0 = [r7+0]
    if (r0 != 0) goto L02040ba8
L02040b3a:
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fc4c
    r0 = cnum
    r1 = [r6+r0<<2]
    r3 = r1 + 1
    [r6+r0<<2] = r3
    if (r1 != 0) goto L02040b58
    lockset
L02040b58:
    csync
    r1_r0 = d[r5+56]
    if (r0 >= r1) goto L02040b74
    r0 = r5  #
    r4 = b[r7+5] (u)
    r1 = r2
    call L0203f014
    if (r4 == 255) goto L02040b90
    r0 = r4 + 1
    b[r7+5] = r0
L02040b74:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02040b88
    lockclr
L02040b88:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r8-r4} = [sp++]
L02040b90:
    r0 = [++r5=36]
    if (r0 == 0) goto L02040b74
    r0 = r5
    call L0203f15c
    if (r8 == 0) goto L02040b74
    if (r0 == 0) goto L02040b74
    [r8+0] = 0x1
    goto L02040b74
L02040ba8:
    call L0203eed8
L02040bac:
    goto L02040bac
L02040bae:
    [--sp] = {rets, r8-r4}
    sp += -8
    r4 = r3
    r5 = r2
    r7 = r1
    r1 = rets
    r1 = rets
    r1 = 0
    [sp] = r1
    ifs (r5 >= 18) {  ; @ifs.ge.ri.s12
    r5 = 18
    }
    call L02040ab8
    r2 = r0
    if (r2 == 0) goto L02040c64
    call storage_coordination_irq_enter  ; @call.xl
    r8 = L01c1fc4c
    r0 = cnum
    r1 = [r8+r0<<2]
    r3 = r1 + 1
    [r8+r0<<2] = r3
    if (r1 != 0) goto L02040bf0
    lockset
L02040bf0:
    csync
    r0 = r2
    call L0203fe26
    r6 = r0
    if (r6 == 0) goto L02040c68
    r0 = r5.b0 (u)
    r0 <= insert(r7, p:8, l:24)
    [sp+4] = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    if (r1 != 0) goto L02040c1c
    lockset
L02040c1c:
    csync
    r0 = [r6+60]
    r1 = [r6+56]
    csync
    r2 = cnum
    r3 = [r8+r2<<2]
    r7 = r3 + -1
    [r8+r2<<2] = r7
    r3 = r0 - r1
    if (r7 != 0) goto L02040c3a
    lockclr
L02040c3a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r5 + 1
    if (r3 >= r0) goto L02040c86
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L02040c5a
    lockclr
L02040c5a:
    call storage_coordination_irq_leave  ; @call.xl
    r4 = 21
    goto L02040cca
L02040c64:
    r4 = 14
    goto L02040cca
L02040c68:
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L02040c7c
    lockclr
L02040c7c:
    call storage_coordination_irq_leave  ; @call.xl
    r4 = 4
    goto L02040cca
L02040c86:
    r1 = sp + 4
    r2 = sp + 0
    r0 = r6
    call L02040b26
    r7 = 0
    goto L02040ca2
L02040c94:
    r2 = sp + 0
    r0 = r6
    r1 = r4
    call L02040b26
    r4 += 4  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L02040ca2:
    ifs (r7 < r5) goto L02040c94
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L02040cba
    lockclr
L02040cba:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [sp]
    r4 = 0
    if (r0 == 0) goto L02040cca
    call L0203ea6e
L02040cca:
    r0 = r4
    sp += 8
    {pc, r8-r4} = [sp++]
L02040cd0:
    [--sp] = rets
    r3 = r0
    if (r3 != 0) goto L02040d1e
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L02040cf4
    lockset
L02040cf4:
    csync
    r1 = L01c1fc64
    r2 = cnum
    r3 = [r1+r2<<2]
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L02040d18
    lockclr
L02040d18:
    call storage_coordination_irq_leave  ; @call.xl
L02040d1e:
    r1 = [r3+120]
    r0 = 0
    goto L02040d28
L02040d26:
    r0 += 1  ; @add.ri.u5
L02040d28:
    r2 = b[r1+r0] (u)
    if (r2 == 165) goto L02040d26
    r0 = r0 >> 2
    pc = [sp++]
L02040d34:
    [--sp] = {rets, r4}
    r2 = r1
    r1 = rets
    r1 = icfg
    r4 = 3
    if ((r1 & 0xFF) != 0) goto L02040d64
    if (r2 == 0) goto L02040d52
    if (r2 == -1) {  ; @if.eq.ri.s12
    r2 = 0
    }
    goto L02040d54
L02040d52:
    r2 = -1
L02040d54:
    r1 = 0
    r3 = 0
    r4 = 0
    call L0203ff2c
    if (r0 != 1) {  ; @if.ne.ri.s12
    r4 = 11
    }
L02040d64:
    r0 = r4
    {pc, r4} = [sp++]
L02040d68:
    [--sp] = rets
    r1 = 10000
    r0 = r0 / r1 (u)
    call L0203feb8
    pc = [sp++]
L02040d78:
    [--sp] = {rets, r12-r4}
    sp += -68
    r12 = r1
    call L02040ab8
    r2 = r0
    if (r2 == 0) goto L02040e82
    call storage_coordination_irq_enter  ; @call.xl
    r8 = L01c1fc4c
    r0 = cnum
    r1 = [r8+r0<<2]
    r3 = r1 + 1
    [r8+r0<<2] = r3
    if (r1 != 0) goto L02040da4
    lockset
L02040da4:
    csync
    r0 = r2
    call L0203fe26
    r5 = r0
    if (r5 == 0) goto L02040e68
    call L02040362
    r6 = r0
    r9 = r12 & 0xF00000
    r10 = sp + 4
    r11 = -14
    goto L02040e50
L02040dc4:
    r1 = sp + 0
    r3_r2 = 0
    r4 = 0
    r0 = r5
    call L0203ff2c
    r7 = sp + 4
    goto L02040de2
L02040dd4:
    r3_r2 = 0
    r0 = r5
    r1 = r7
    call L0203ff2c
    r7 += 4  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02040de2:
    r0 = [sp]
    r1 = r0.b0 (u)
    if (r4 > 15) goto L02040dee
    ifs (r4 < r1) goto L02040dd4
L02040dee:
    r2 = r6 + -1
    r0 = r0 >> 8
    r6 = r2 - r1
    if (r0 == r12) goto L02040e1e
    r1 = sp + 0
    r0 = r5
    call L0203f9de
    r4 = 0
    r7 = sp + 4
    goto L02040e14
L02040e08:
    r0 = r5
    r1 = r7
    call L0203f9de
    r7 += 4  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02040e14:
    r0 = b[sp] (u)
    ifs (r4 < r0) goto L02040e08
    goto L02040e50
L02040e1e:
    if (r9 != 3145728) goto L02040e50
    r1 = [r10+4]
    r0 = r1.b0 (u)
    if ((r1 & 256) == 0) goto L02040e40
    r1 = sp + 4
    r1 += 8  ; @add.ri.u5
    r1 = [r1+r0<<2]
    [r1+0] = r11
    r1 = [r10+4]
    r0 += 1  ; @add.ri.u5
L02040e40:
    if ((r1 & 512) == 0) goto L02040e50
    r1 = sp + 4
    r1 += 8  ; @add.ri.u5
    r0 = [r1+r0<<2]
    call L020403ee
L02040e50:
    if (r6 != 0) goto L02040dc4
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L02040e7c
    lockclr
    goto L02040e7c
L02040e68:
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L02040e7c
    lockclr
L02040e7c:
    call storage_coordination_irq_leave  ; @call.xl
L02040e82:
    sp += 68
    {pc, r12-r4} = [sp++]
L02040e86:
    [--sp] = rets
    call L02040d78
    pc = [sp++]
L02040e8e:
    r0 = 32436460
    r1 = 0
    b[r0+0] = r1
    rts
L02040e9a:
    [--sp] = {rets, r4}
    r4 = 32436460
    [r4+4] = 0x0
    r0 = L0204176a  ; "sys"
    call L020009ee  ; @call.xl
    r1 = 100
    r0 = r0 / r1 (s)
    [r4+8] = r0
    r0 = 64
    b[r4+0] = r0
    r0 = 1
    b[r4+0] = r0
    {pc, r4} = [sp++]
L02040ec4:
    [--sp] = {psr, rets, reti}
    [--sp] = {r3-r0}
    r0 = 32436460
    r1 = b[r0+0] (u)
    r1 |= 64
    b[r0+0] = r1
    r0 = L01c1f180
    [r0+24] += 1  ; @rmw.add.s12
    call L0203f772
    if (r0 == 0) goto L02040ee8
    call L0203ea6e
L02040ee8:
    {r3-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
L02040eee:
    r0 = cnum
    r1 = L01c1fc78
    r0 = [r1+r0<<2]
    r2 = L01c1fc64
    r3 = cnum
    [r2+r3<<2] = r0
    r0 = cnum
    r0 = 0x7 - r0
    r2 = 1
    r0 = r2 << r0
    r2 = 32436644
    [r2+0] = r0
    r0 = cnum
    r0 = [r1+r0<<2]
    r0 = [r0+120]
    r2 = cnum
    r2 = r2 << 9
    r3 = 8109113
    [r2+r3<<2] = r0
    r0 = cnum
    r0 = [r1+r0<<2]
    r0 = [r0+8]
    r1 = cnum
    r1 = r1 << 9
    r1 = [r1+r3<<2]
    r0 += r1  ; @add.rr
    r1 = cnum
    r1 = r1 << 9
    r2 = r3 + -1
    [r1+r2<<2] = r0
    rts
L02040f62:
    [--sp] = {rets, r6-r4}
    r5 = r0
    if (r5 != 0) goto L02040f6c
    call L0203e7a0
L02040f6c:
    r4 = 0
    r6 = r5 + 148
    r5 = r5 + 144
    goto L02040f88
L02040f78:
    r2 = [r6+r4<<2]
    if (r2 == 0) goto L02040f86
    r1 = [r5+r4<<2]
    r0 = r4
    call r2
L02040f86:
    r4 += 1  ; @add.ri.u5
L02040f88:
    if (r4 != 1) goto L02040f78
    {pc, r6-r4} = [sp++]
L02040f8e:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = b[r4+156] (u)
    if (r0 == 2) goto L02040fb8
    if (r0 == 1) goto L02040faa
    if (r0 != 0) goto L02040fb4
    r0 = [r4+120]
    call L0203d85a  ; @call.xl
L02040faa:
    r0 = r4
    call L0203d85a  ; @call.xl
    {pc, r4} = [sp++]
L02040fb4:
    call L0203e7a0
L02040fb8:
    {pc, r4} = [sp++]
L02040fba:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = cnum
    if (r0 == 1) {  ; @if.eq.ri.s12
    call L0203ea6e
    }
    r5 = L01c1fc80
    r8 = L01c344b4
    r7 = L01c3475c
    r6 = L01c1fc4c
    r9 = L01c1fc60
L02040fea:
    r0 = [r5+0]
    if (r0 == 0) goto L0204104c
    call L0203f252
    r0 = [r7+0]
    if (r0 == 0) goto L02041046
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    if (r1 != 0) goto L0204100e
    lockset
L0204100e:
    csync
    r0 = [r7+12]
    r4 = [r0+12]
    r0 = r4 + 76
    call L0203efb6
    [r9+0] += -1  ; @rmw.add.s12
    [r5+0] += -1  ; @rmw.add.s12
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02041038
    lockclr
L02041038:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r4
    call L02040f62
    r0 = r4
    call L02040f8e
L02041046:
    call L0203f8f6
    goto L02040fea
L0204104c:
    r0 = [r8+0]
    if (r0 >= 3) {  ; @if.ge.ri.s12
    call L0203ea6e
    }
    idle
    call phase3_p3_wdt_clear  ; @call.xl
    goto L02040fea
L02041062:
    [--sp] = {rets, r4}
    sp += -8
    r0 = L01c3478c
    call L0203fb92
    r4 = 5
    r2 = L01c347dc
    r3 = L01c3481c
    r0 = 16
    r1 = 4
    [sp] = r4
    call L0203ef10
    r4 = L0204177a  ; "thread_fork_kill"
    r0 = r4
    call phase3_p3_get_task_priority  ; @call.xl
    if (r0 != 0) {  ; @if.ne.ri.s12
    r3 = b[r0+4] (u)
    } else {
    r3 = 31
    }
    r0 = L01c34c6c
    r2 = 256  #
    [sp+4] = r0
    r1 = L01c3486c
    r0 = L02041102
    r1 = r4  #
    [sp] = r1
    call L0203fbd4
    r0 = 0
    sp += 8
    {pc, r4} = [sp++]
L020410c4:
    [--sp] = rets
    if (r0 == 0) goto L020410fc
    r2 = 0
    b[r0+76] = r2
    r1 = L01c34d18
    goto L020410e0
L020410d6:
    r3 = [r1+4]
    if (r3 == r0) goto L020410e6
    r1 += 8  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L020410e0:
    if (r2 <= 19) goto L020410d6
    goto L020410ee
L020410e6:
    r2 = 0
    r3 = 0
    d[r1+0] = r3_r2
L020410ee:
    r1 = b[r0+70] (u)
    if (r1 != 0) goto L020410fa
    call L0203d85a  ; @call.xl
L020410fa:
    pc = [sp++]
L020410fc:
    call L0203eed8
L02041100:
    goto L02041100
L02041102:
    sp += -4
    r4 = L01c3481c
    r11 = 0
    r6 = L01c3478c
    r12 = L01c26890
    r5 = L01c1f22c
    r13 = L01c1fc4c
    r14 = L01c1fc64
    r15 = L01c1fc78
    r8 = 1
L02041134:
    r0 = icfg
    if ((r0 & 0xFF) != 0) goto L02041134
    r1 = sp + 0
    r2 = -1
    r3 = 0
    r0 = r4
    call L0203ff2c
    if (r0 != 1) goto L02041134
    r0 = r6
    call L02040614
    r0 = [sp]
    r1 = [r0+72]
    if (r1 == 0) goto L02041160
    [r1+0] = r11
L02041160:
    r0 += 68
    call L0203fe26
    if (r0 == 0) goto L0204116c
    [r0+60] = r11
L0204116c:
    r0 = [sp]
    r1 = b[r0+1] (u)
    r6 = r0 + 1
    if (r1 != 35) goto L02041182
    r1 = b[r0+2] (u)
    r0 += 4  ; @add.ri.u5
    if (r1 != 67) {  ; @if.ne.ri.s12
    r0 = r6
    }
    r6 = r0
L02041182:
    r0 = r6
    call L02040ab8
    r7 = r0
    if (r7 != 0) goto L02041196
    goto L0204143a
L0204118e:
    r0 = r3
    call L0201c622  ; @call.xl
L02041196:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r12 + 70
L020411a2:
    testset b[r0]
    ifeq goto L020411a2
    csync
    r4 = r5
L020411ac:
    r4 = [r4+0]
    if (r4 == r5) goto L020411cc
    r0 = b[r4+27] (u)
    if ((r0 & 1) != 0) goto L020411ac
    r0 = [r4+16]
    if (r0 == 0) goto L020411ac
    r1 = r6
    call L02028308  ; @call.xl
    if (r0 != 0) goto L020411ac
    r3 = h[r4+28] (u)
    goto L020411ce
L020411cc:
    r3 = 0
L020411ce:
    csync
    b[r12+70] = r11
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 != 0) goto L0204118e
    goto L02041226
L020411de:
    call storage_coordination_irq_enter  ; @call.xl
    csync
L020411e6:
    testset b[r10]
    ifeq goto L020411e6
    r0 = r5 + 16
    csync
    r1 = r0
L020411f2:
    r1 = [r1+0]
    if (r1 == r0) goto L0204120c
    r2 = r1 + 24
    r3 = h[r2+6] (u)
    if (r3 != r4) goto L020411f2
    r3 = [r2+0]
    b[r2+4] = r8
L02041206:
    r0 = b[r2+5] (u)
    if (r0 != 0) goto L02041206
    goto L0204120e
L0204120c:
    r3 = 0
L0204120e:
    csync
    b[r12+71] = r11
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 == 0) goto L02041226
    r1 = r4 | 0x300000
    r0 = r3
    call L02040e86
L02041226:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r10 = r12 + 71
L02041232:
    testset b[r10]
    ifeq goto L02041232
    r9 = r5 + 16
    csync
    r4 = r9
L02041240:
    r4 = [r4+0]
    if (r4 == r9) goto L0204125e
    r0 = b[r4+28] (u)
    if (r0 != 0) goto L02041240
    r0 = [r4+24]
    if (r0 == 0) goto L02041240
    r1 = r6
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02041240
    r4 = h[r4+30] (u)
    goto L02041260
L0204125e:
    r4 = 0
L02041260:
    csync
    b[r12+71] = r11
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 != 0) goto L020411de
    r0 = r7
    call L0203fe26
    r6 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r13+r0<<2]
    r2 = r1 + 1
    [r13+r0<<2] = r2
    if (r1 != 0) goto L0204128e
    lockset
L0204128e:
    csync
L02041290:
    r0 = 0
L02041292:
    ifs (r0 > 1) goto L020412e4
    r1 = [r15+r0<<2]
    if (r1 == r7) goto L020412a8
    r1 = [r14+r0<<2]
    r0 += 1  ; @add.ri.u5
    if (r1 != r7) goto L02041292
L020412a8:
    csync
    r0 = cnum
    r1 = [r13+r0<<2]
    r1 += -1
    [r13+r0<<2] = r1
    if (r1 != 0) goto L020412bc
    lockclr
L020412bc:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 1
    call L0203fe9a
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r13+r0<<2]
    r2 = r1 + 1
    [r13+r0<<2] = r2
    if (r1 != 0) goto L020412e0
    lockset
L020412e0:
    csync
    goto L02041290
L020412e4:
    r4 = r7 + 76
    r0 = r4
    call L0203efb6
    if (r0 != 0) goto L0204130e
    r0 = [r7+116]
    r1 = r0 * 0x14
    r2 = L01c344b4
    r1 = [r1+r2]
    if (r1 != 0) goto L0204130e
    r1 = L01c1fc74
    [r1+0] &= ~(1 << r0)
L0204130e:
    r0 = [r7+112]
    if (r0 == 0) goto L0204131c
    r0 = r7 + 96
    call L0203efb6
L0204131c:
    r0 = L01c1fc70
    [r0+0] += 1  ; @rmw.add.s12
    r0 = [r14+0]
    if (r7 == r0) goto L02041352
    r0 = [r14+4]
    if (r7 == r0) goto L02041352
    r0 = L01c1fc60
    [r0+0] += -1  ; @rmw.add.s12
    r0 = r7
    call L02040f62
    r0 = r7
    call L02040f8e
    call L0203f138
    goto L02041368
L02041352:
    r0 = L01c3475c
    r1 = r4
    call L0203e8cc
    r0 = L01c1fc80
    [r0+0] += 1  ; @rmw.add.s12
L02041368:
    r0 = L01c1fc6c
    r0 = [r0+0]
    if (r0 == 0) goto L02041394
    r0 = [r14+0]
    if (r7 == r0) goto L02041382
    r0 = [r14+4]
    if (r7 != r0) goto L02041394
L02041382:
    r0 = L01c1fc84
    r0 = [r0+0]
    if (r0 == 0) goto L02041390
    call L0203e7a0
L02041390:
    call L0203ea6e
L02041394:
    csync
    r0 = cnum
    r1 = [r13+r0<<2]
    r1 += -1
    [r13+r0<<2] = r1
    if (r1 != 0) goto L020413a8
    lockclr
L020413a8:
    call storage_coordination_irq_leave  ; @call.xl
    if (r6 == 0) goto L0204143a
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r13+r0<<2]
    r2 = r1 + 1
    [r13+r0<<2] = r2
    if (r1 != 0) goto L020413c8
    lockset
L020413c8:
    csync
    r1 = L01c34d10
    r4 = r1
L020413d2:
    r4 = [r4+0]
    if (r4 == r1) goto L0204141a
    r0 = [r4+8]
    if (r0 != r7) goto L020413d2
    r1_r0 = d[r4+0]
    [r0+4] = r1
    [r1+0] = r0
    [r4+0] = r4
    [r4+4] = r4
    csync
    r0 = cnum
    r1 = [r13+r0<<2]
    r1 += -1
    [r13+r0<<2] = r1
    if (r1 != 0) goto L020413fe
    lockclr
L020413fe:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r6
    call L020410c4
    r0 = [r4+72]
    if (r0 == 0) goto L0204143a
    r0 = r4
    call L0203d218  ; @call.xl
    goto L0204143a
L0204141a:
    csync
    r0 = cnum
    r1 = [r13+r0<<2]
    r1 += -1
    [r13+r0<<2] = r1
    if (r1 != 0) goto L0204142e
    lockclr
L0204142e:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r6
    call L020410c4
L0204143a:
    r0 = [sp]
    r1 = b[r0+0] (u)
    if (r1 != 0) goto L02041446
    call L0203d218  ; @call.xl
L02041446:
    r6 = L01c3478c
    r0 = r6
    call L0204074c
    r4 = L01c3481c
    goto L02041134
L0204145a:
    [--sp] = {rets, r4}
    r4 = L02041656
    r0 = 123
    r1 = 6
    r3 = 0
    r2 = r4
    call storage_platform_register  ; @call.xl
    r0 = 123
    r1 = 6
    r3 = 1
    r2 = r4
    call storage_platform_register  ; @call.xl
    r0 = 32436540
    [r0+0] &= 0xFFFFEFFF
    r0 = r0 + 512
    [r0+0] &= 0xFFFFEFFF
    r1 = L020414a4
    r0 = 0
    r2 = 8000
    call L0201ee98  ; @call.xl
    {pc, r4} = [sp++]
L020414a4:
    [--sp] = {rets, r11-r4}
    sp += -68
    r9 = L01c1fca4
    r8 = [r9+0]
    r6 = 80640
    r0 = [r6+0]
    r10 = r0 | 0x80000000
    [sp+64] = r10  ; @st.w.sp.l
    r11 = [sp+64]  ; @ld.w.sp.l
    r0 = [sp+64]
    ifs (r0 > -1) goto L020414d2
    r7 = [sp+64]
    [sp+48] = r7
    goto L02041500
L020414d2:
    r0 = [sp+64]
    r1 = sp + 32
    rep 32 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = [sp+64]
    r1 = 32
    call L02001776  ; @call.xl
    r11 = r0
    if (r0 == 285) goto L02041590
    r0 = 22868
    if (r11 == r0) goto L02041590
    r0 = 60060
    if (r11 == r0) goto L02041590
    r7 = [sp+48]
L02041500:
    r0 = sp + 32
    r4 = r0 + 16
    r0 = r7.l (u)
    r5 = sp + 32
    r2 = 32
    r3 = 0
    r1 = r5
    call L0201eec0  ; @call.xl
    [r4+0] = r7
    r0 = r5 + 6
    r1 = 26
    call L02001776  ; @call.xl
    r1 = h[sp+36] (u)
    r0 = r0.l (u)
    if (r1 != r0) {
    r0 = [r9+0]
    r1 = b[sp+39] (u)
    r0 ^= r1
    } else {
    r0 = [sp+64]
    r1 = 4083955352
    r0 ^= r1
    }
    [r9+0] = r0
    r0 = [sp+32]
    r1 = [r9+0]
    r3 = 1398360906
    r2 = r7
    if (r0 != r3) {
    r2 = [r6+4]
    }
    r1 ^= r2
    [r9+0] = r1
    r1 = h[sp+62] (u)
    if (r1 != 15) goto L0204156a
    r1 = b[sp+39] (u)
    goto L0204157c
L0204156a:
    r2 = [r9+0]
    r1 = b[sp+39] (u)
    r2 ^= r1  #
    r3 = [r6+0]
    r2 ^= r3
    [r9+0] = r2
L0204157c:
    r1 = r1.b0 (u)
    if (r1 == 1) {  ; @if.eq.ri.s12
    r0 = r7
    }
    [r9+0] ^= r0
    r0 = [sp+64]
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    call L020414a4
    }
L02041590:
    r0 = [r9+0]
    if (r11 != r10) goto L02041630
    if (r8 == r0) goto L02041630
    [r9+0] = r8
    r0 = [r9+0]
    r4 = 4083955352
    if (r0 == r4) goto L02041652
    [r9+0] ^= r4
    r0 = [r9+0]
    r1 = sp + 0
    r2 = r1
    rep 32 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    r5 = [sp+16]
    r0 = r5.l (u)
    r2 = 32
    r3 = 0
    call L0201eec0  ; @call.xl
    [sp+16] = r5
    r0 = [sp]
    r1 = 1398360906
    if (r0 != r1) goto L02041630
    r0 = b[sp+7] (u)
    if (r0 != 1) goto L02041630
    r0 = h[sp+30] (u)
    if (r0 != 15) goto L02041630
    r0 = sp + 0
    r0 += 6  ; @add.ri.u5
    r1 = 26
    call L02001776  ; @call.xl
    r1 = h[sp+4] (u)
    r0 = r0.l (u)
    if (r1 != r0) goto L02041630
    call L0201d056  ; @call.xl
    r1 = h[sp+24] (u)
    r2 = 65472
    if (r1 != r2) goto L0204161e
    r2 = r0 & 0x30
    if (r2 > 15) goto L02041630
L0204161e:
    r2 = h[sp+26] (u)
    r2 &= r1
    r0 &= r1
    if (r0 != r2) goto L02041630
    [r9+0] = r4
    goto L02041652
L02041630:
    r0 = [r6+0]
    r0 |= 2147483648
    r1 = 29883944
    [r1+0] = r0
    r0 = 11
    r1 += -40
    goto L0204164a
L02041642:
    r2 = [r6+0]
    [r1+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
L0204164a:
    if (r0 != 120) goto L02041642
    call L020414a4
L02041652:
    sp += 68
    {pc, r11-r4} = [sp++]
L02041656:
    [--sp] = {psr, rets, reti}
    [--sp] = {r8-r0}
    sp += -36
    r0 = cnum
    r0 = r0 << 9
    r1 = 8109161
    r2 = 8
    [r0+r1<<2] = r2
    r8 = 29884168
    r0 = [r8+0]
    [sp+32] = r0
    r4 = [sp+32]
    r0 = [sp+32]
    r7 = [sp+32]
    ifs (r0 <= -1) goto L020416b4
    r0 = sp + 0
    rep 32 {
    r1 = b[r7++=1] (u)
    b[r0++=1] = r1
    }
    r0 = [sp+32]
    r1 = 32
    call L02001776  ; @call.xl
    r4 = r0
    if (r4 == 285) goto L02041748
    r0 = 22868
    if (r4 == r0) goto L02041748
    r0 = 60060
    if (r4 == r0) goto L02041748
    r7 = [sp+16]
    goto L020416b6
L020416b4:
    [sp+16] = r7
L020416b6:
    r0 = sp + 0
    r6 = r0 + 16
    r0 = r7.l (u)
    r5 = sp + 0
    r2 = 32
    r3 = 0
    r1 = r5
    call L0201eec0  ; @call.xl
    [r6+0] = r7
    r0 = r5 + 6
    r1 = 26
    call L02001776  ; @call.xl
    r1 = h[sp+4] (u)
    r2 = r0.l (u)
    r0 = L01c1fca4
    if (r1 != r2) {
    r1 = [r0+0]
    r2 = b[sp+7] (u)
    r1 ^= r2
    } else {
    r1 = [sp+32]
    r2 = 4083955352
    r1 ^= r2
    }
    [r0+0] = r1
    r1 = [sp]
    r5 = r7  #
    r3 = [r0+0]
    r6 = 1398360906
    r2 = 80640
    if (r1 != r6) {
    r5 = [r2+4]
    }
    r3 ^= r5
    [r0+0] = r3
    r3 = h[sp+30] (u)
    if (r3 != 15) goto L02041724
    r3 = b[sp+7] (u)
    goto L02041732
L02041724:
    r5 = [r0+0]
    r3 = b[sp+7] (u)
    r5 ^= r3  #
    r2 = [r2+0]
    r2 ^= r5
    [r0+0] = r2
L02041732:
    r2 = r3.b0 (u)
    if (r2 == 1) {  ; @if.eq.ri.s12
    r1 = r7
    }
    [r0+0] ^= r1
    r0 = [sp+32]
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    call L020414a4
    }
L02041748:
    [r8+8] = r4
    [r8+4] |= 0x80000000
    sp += 36
    {r8-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
L0204175a:
    [--sp] = rets
    call L020410c4
    pc = [sp++]
L02041762:
    [--sp] = rets
    call L0204048e
    pc = [sp++]

; 0x0204176a..0x0204178c: data
    .fill ((10 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0204176a:
    .byte 0x73,0x79,0x73,0x00
L0204176e:
    .byte 0x49,0x44,0x4c,0x45,0x30,0x00
L02041774:
    .byte 0x49,0x44,0x4c,0x45,0x31,0x00
L0204177a:
    .byte 0x74,0x68,0x72,0x65,0x61,0x64,0x5f,0x66,0x6f,0x72,0x6b,0x5f,0x6b,0x69,0x6c,0x6c
    .byte 0x00,0x00

; 0x0204178c..0x0204186e: system layer code (not reversed), as instructions
L0204178c:
    [--sp] = {rets, r6-r4}
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L020417ac
    lockset
L020417ac:
    r0 = 12228
    r1 = L02035810
    r6 = r1 + r0
    csync
    call L0203e742  ; @call.xl
    r4 = r0
L020417c2:
    r0 = [++r6=20]
    if (r0 == 0) goto L020417f0
    r1 = r4
    call L02028308  ; @call.xl
    if (r0 != 0) goto L020417c2
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L020417e6
    lockclr
L020417e6:
    call storage_coordination_irq_leave  ; @call.xl
    r4 = [r6+0]
    goto L0204180a
L020417f0:
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02041804
    lockclr
L02041804:
    call storage_coordination_irq_leave  ; @call.xl
L0204180a:
    r0 = r4
    {pc, r6-r4} = [sp++]
L0204180e:
    [--sp] = {rets, r7-r4}
    r2 = L01c1f180
    r0 = [r2+24]
    r1 = 32436464
    r3 = [r1+0]
    r3 = r3 * 0x14  #
    r1 = [r1+4]
    r1 = r3 / r1 (u)
    r3 = L01c1fc5c
    r4 = r0 & 0x7FFFFFF  #
    r0 = [r3+0]
    r4 = r4 * 0x14
    r5 = r1 + r4
    r6 = 1
    r7 = 1
    ifs (r5 >= r0) {
    r7 = 0
    }
    if (r5 >= r0) {
    r6 = 0
    }
    r6 &= r7
    if (r6 != 1) goto L02041860
    r5 += 20  ; @add.ri.u5
    ifs (r5 >= r0) goto L0204185e
    [r2+24] += 1  ; @rmw.add.s12
    {pc, r7-r4} = [sp++]
L0204185e:
    r4 += 20  ; @add.ri.u5
L02041860:
    r0 = r4 + r1
    [r3+0] = r0
    {pc, r7-r4} = [sp++]
L02041866:
    [--sp] = rets
    call L0204180e
    r0 = r0 >> 1
    pc = [sp++]

; 0x0204186e..0x02041ab0: data
    .fill ((14 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0204186e:
    .byte 0x00,0x00
L02041870:
    .byte 0xff,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x07,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x00,0xf8,0xff,0xff,0xff,0xff,0x00,0x00,0x10,0x04,0x41,0x10,0x04,0x41,0x00,0x00
    .byte 0x10,0x04,0x41,0x10,0x04,0x41,0x00,0x00,0x89,0xb2,0x30,0x8d,0xf3,0x40,0x00,0x00
    .byte 0x81,0x30,0x10,0x85,0x71,0x20,0x00,0x00,0xfa,0xce,0xf7,0xfe,0x0f,0x00,0x00,0x00
    .byte 0xf2,0x4c,0xd7,0xf6,0x8d,0xe7,0x00,0x00,0xea,0xca,0xb6,0xee,0x0b,0xc7,0x00,0x00
    .byte 0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00,0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00
    .byte 0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00,0x46,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00
    .byte 0x45,0x51,0x14,0x45,0x51,0x18,0x00,0x00,0x04,0x41,0x10,0x04,0x41,0x14,0x00,0x00
    .byte 0x81,0x20,0x08,0x03,0x41,0x10,0x00,0x00,0x00,0x00,0x00,0x40,0x10,0x04,0x00,0x00
    .byte 0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00,0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00
    .byte 0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00,0x47,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00
    .byte 0x82,0x30,0x10,0x85,0x71,0x18,0x00,0x00,0x00,0x00,0x04,0x82,0x30,0x08,0x00,0x00
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00,0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00
    .byte 0x5d,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00,0x4a,0xd7,0x75,0x5d,0xd7,0x75,0x00,0x00
    .byte 0x8a,0xa2,0x28,0x8a,0xa2,0x28,0x00,0x00,0x48,0xa2,0x28,0x8a,0xa2,0x28,0x00,0x00
    .byte 0x08,0x92,0x28,0x49,0x61,0x1c,0x00,0x00,0x81,0x30,0x10,0x45,0x61,0x1c,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x57,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x4f,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x47,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb0,0x3f,0x80,0x00,0xf0,0x00,0x00,0x00,0xb0,0x36,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb1,0x2d,0x80,0x00,0xf0,0x00,0x00,0x00,0xb2,0x24,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb3,0x1b,0x80,0x00,0xf0,0x00,0x00,0x00,0xb4,0x12,0x80,0x00,0xf0,0x00,0x00,0x00
    .byte 0xb5,0x09,0x80,0x00,0xf0,0x00,0x00,0x00,0xb6,0x00,0x80,0x00,0xf0,0x00,0x00,0x00
L02041a70:
    .byte 0x0c,0x0d,0x0e,0x0f,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b
    .byte 0x1c,0x1d,0x1e,0x1f,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b
    .byte 0x2c,0x2d,0x2e,0x2f,0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3a,0x3b
    .byte 0x3c,0x3d,0x3e,0x3f,0x40,0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b

; 0x02041ab0..0x02042db2: system layer code (not reversed), as instructions
L02041ab0:
    r0 = L01c1fca8
    r1 = 26214
    h[r0+0] = r1
    rts
L02041abe:
    [--sp] = {rets, r15-r4}
    sp += -16
    r0 = 1384
    r2 = L01c26890
    r1 = b[r2+r0] (u)
    r5 = 1
    r12 = L02035810
    r3 = 65552
    r8 = 0x14000
    if (r1 != 0) goto L02042978
    r1 = 1
    b[r2+r0] = r1
    [r3+0] &= 0xFFFF3FFF
    r0 = 0
    r2 = r8 + 64
    [r2+0] = r0
    [r2+4] = r0
    [r2+8] = r0
    [r2+12] = r0
    [r2+16] = r0
    [r8+64] |= 0x100
    [r8+64] |= 0x40
    [r8+64] |= 0x1
    r4 = 262656
    r0 = [r4+0]
    if ((r0 & 0x1) != 0) {
    r0 = 8000000
    } else {
    r0 = 4000000
    }
    r3 = L01c373b8
    r1 = [r3+8]
    r0 = r1 / r0 (s)
    goto L02041b38
L02041b34:
    nop
    r0 += -1
L02041b38:
    if (r0 != 0) goto L02041b34
    [r8+64] |= 0x4
    r0 = [r4+0]
    if ((r0 & 0x1) != 0) {
    r0 = 8000000
    } else {
    r0 = 4000000
    }
    r1 = [r3+8]
    r0 = r1 / r0 (s)
    goto L02041b5c
L02041b58:
    nop
    r0 += -1
L02041b5c:
    if (r0 != 0) goto L02041b58
    [r8+64] |= 0x8
    r0 = [r4+0]
    if ((r0 & 0x1) != 0) {
    r0 = 8000000
    } else {
    r0 = 4000000
    }
    r1 = [r3+8]
    r0 = r1 / r0 (s)
    goto L02041b80
L02041b7c:
    nop
    r0 += -1
L02041b80:
    if (r0 != 0) goto L02041b7c
    [r8+64] |= 0x2
    r0 = [r4+0]
    if ((r0 & 0x1) != 0) {
    r0 = 8000000
    } else {
    r0 = 4000000
    }
    r1 = [r3+8]
    r0 = r1 / r0 (s)
    r1 = -50
    r0 *= r1
    goto L02041baa
L02041ba6:
    nop
    r0 += 1  ; @add.ri.u5
L02041baa:
    if (r0 != 0) goto L02041ba6
    r0 = [r2+28]
    r0 = r0 & 0xFFFFFF00
    r0 = r0 | 0x5
    [r2+28] = r0
    [r8+92] &= 0xFFFF00FF
    [r8+92] &= 0xFF00FFFF
    [r8+92] |= 0x7000000
    [r8+92] |= 0x40000000
    [r8+92] &= 0x7FFFFFFF
    [r8+76] |= 0x1000000
    r0 = 200448
    [r0+4] |= 0x800
    [r0+4] |= 0x400
    [r0+4] |= 0x200
    [r0+4] |= 0x20
    [r0+4] |= 0x10
    [r0+4] &= 0xFFFFFFF7
    [r0+4] |= 0x4
    [r0+4] |= 0x2
    [r0+4] |= 0x1
    [r0+0] |= 0x400
    [r0+0] &= 0xFFFFFDFF
    [r0+0] &= 0xFFFFFEFF
    r1 = [r0+0]
    r1 = r1 & 0xFFFFFF1F
    r1 = r1 | 0x60
    [r0+0] = r1
    [r0+0] &= 0xFFFFFFEF
    [r0+0] |= 0x8
    [r0+0] |= 0x4
    [r0+0] |= 0x2
    [r0+0] |= 0x1
    call L02023aac  ; @call.xl
    call L02023ada  ; @call.xl
    r1 = 37895
    r0 = 776
    call L020559cc  ; @call.xl
    call L02023aac  ; @call.xl
    r0 = 0
    r10 = 0
    call L02023b3e  ; @call.xl
    call phase3_p2_wf_phy_init  ; @call.xl
    r0 = 2571
    h[sp+14] = r0
    r4 = r12 + 258
    r0 = r4
    call L020009ee  ; @call.xl
    r7 = r0
    r0 = sp + 14
    call phase3_p2_wifi_get_xosc  ; @call.xl
    r14 = 71936
    [r14+48] |= 0x1
    [r14+48] |= 0x2
    [r14+48] |= 0x4
    [r14+48] |= 0x8
    [r14+48] |= 0x10
    r0 = [r14+48]
    r0 = r0 & 0xFFFFFF9F
    r0 |= 64
    [r14+48] = r0
    [r14+48] &= 0xFFFFFF7F
    r0 = [r14+48]
    r0 = r0 & 0xFFFFFCFF
    r0 |= 512
    [r14+48] = r0
    [r14+48] &= 0xFFFFFBFF
    [r14+48] &= 0xFFFFF7FF
    [r14+48] &= 0xFFFFEFFF
    [r14+48] &= 0xFFFDFFFF
    [r14+48] &= 0xFFFBFFFF
    r0 = [r14+48]
    r1 = b[sp+14] (u)
    r0 = r0 & 0xFFFE1FFF
    r1 = r1 & 0xFFFFFF0F
    r0 <= insert(r1, p:13, l:4)
    [r14+48] = r0
    r0 = [r14+48]
    r1 = b[sp+15] (u)
    r0 = r0 & 0xFF87FFFF
    r1 = r1 & 0xFFFFFF0F
    r0 <= insert(r1, p:19, l:4)
    [r14+48] = r0
    r5 = 40000000
    r0 = 0xD000000
    if (r7 != r5) {
    r0 = 0x5800000
    }
    r1 = [r14+48]
    r1 = r1 & 0xF07FFFFF
    r0 |= r1
    [r14+48] = r0
    r2 = r14 + 64
    [r2+16] = r10
    [r14+0] |= 0x1
    r0 = [r2+-64]
    r0 = r0 & 0xFFFFFFE1
    r0 |= 4
    [r2+-64] = r0
    [r14+0] &= 0xFFFFFFDF
    [r14+0] &= 0xFFFFFF3F
    [r14+0] &= 0xFFFFFEFF
    [r14+0] &= 0xFFFFFDFF
    [r14+0] &= 0xFFFFFBFF
    [r14+0] &= 0xFFFFC7FF
    [r14+0] &= 0xFFFBFFFF
    r0 = [r2+-64]
    r0 = r0 & 0xFFC7FFFF
    r0 |= 2097152
    [r2+-64] = r0
    [r14+4] &= 0x7FFFFFFF
    [r14+0] &= 0xFFBFFFFF
    [r14+0] &= 0xFF7FFFFF
    r0 = [r2+-64]
    r0 = r0 & 0xFCFFFFFF
    r0 |= 33554432
    [r2+-64] = r0
    [r14+0] &= 0xFBFFFFFF
    [r14+0] |= 0x8000000
    [r14+0] &= 0xEFFFFFFF
    r0 = [r2+-60]
    r0 = r0 & 0xFFFFFF00
    r0 |= 128
    [r2+-60] = r0
    [r14+0] |= 0x20000000
    [r14+0] |= 0x40000000
    [r14+0] |= 0x80000000
    r0 = [r2+-60]
    r0 = r0 & 0xFFFFF0FF
    r0 |= 2048
    [r2+-60] = r0
    r0 = [r2+-60]
    r0 = r0 & 0xFFFF8FFF
    r0 = r0 | 0x5000
    [r2+-60] = r0
    [r14+4] &= 0xFFFF7FFF
    [r14+4] |= 0x30000
    [r14+4] &= 0xFFC3FFFF
    r0 = [r2+-60]
    r0 = r0 & 0xFC3FFFFF
    r0 = r0 | 0x1C00000
    [r2+-60] = r0
    [r14+4] &= 0xC3FFFFFF
    [r14+4] &= 0xBFFFFFFF
    [r14+8] &= 0xFFFFFFF8
    r0 = [r2+-56]
    r0 = r0 & 0xFFFFFFE7
    r0 |= 16
    [r2+-56] = r0
    [r14+8] &= 0xFFFFFFDF
    [r14+8] &= 0xFFFFFFBF
    r0 = 4294901887
    [r14+8] &= r0
    [r14+8] |= 0x10000
    r0 = 4227989503
    [r14+8] &= r0
    [r14+8] |= 0x4000000
    [r14+8] |= 0x8000000
    [r14+8] |= 0x10000000
    [r14+8] &= 0xDFFFFFFF
    r0 = [r2+-56]
    r0 = r0 & 0x3FFFFFFF
    r0 |= 2147483648
    [r2+-56] = r0
    r0 = [r2+-52]
    r0 = r0 & 0xFFFFFFFC
    r0 |= 1
    [r2+-52] = r0
    r0 = [r2+-52]
    r0 = r0 & 0xFFFFFFF3
    r0 |= 8
    [r2+-52] = r0
    [r14+12] &= 0xFFFFFFEF
    [r14+12] &= 0xFFFFFFDF
    r0 = [r2+-52]
    r0 = r0 & 0xFFFFFF3F
    r0 |= 64
    [r2+-52] = r0
    r0 = [r2+-52]
    r0 = r0 & 0xFFFFF8FF
    r0 = r0 | 0x300
    [r2+-52] = r0
    r0 = [r2+-52]
    r0 = r0 & 0xFFFFE7FF
    r0 |= 4096
    [r2+-52] = r0
    [r14+12] &= 0xFFFFDFFF
    r0 = [r2+-52]
    r0 = r0 & 0xFFFF3FFF
    r0 |= 32768
    [r2+-52] = r0
    r0 = [r2+-52]
    r0 = r0 & 0xFFF8FFFF
    r0 = r0 | 0x30000
    [r2+-52] = r0
    [r14+12] |= 0x80000
    [r14+12] &= 0xFFEFFFFF
    r0 = [r2+-52]
    r0 = r0 & 0xFF9FFFFF
    r0 |= 2097152
    [r2+-52] = r0
    [r14+12] &= 0xFF7FFFFF
    [r14+12] |= 0x1000000
    r0 = [r2+-52]
    r0 = r0 & 0xF1FFFFFF
    r0 = r0 | 0x6000000
    [r2+-52] = r0
    r0 = [r2+-48]
    r0 = r0 & 0xFFFFFF80
    r0 = r0 | 0xE
    [r2+-48] = r0
    [r14+16] |= 0x80
    r0 = [r2+-48]
    r0 = r0 & 0xFFFFF0FF
    r0 = r0 | 0x900
    [r2+-48] = r0
    [r14+12] &= 0xEFFFFFFF
    r0 = [r2+-52]
    r0 = r0 & 0x1FFFFFFF
    r0 = r0 | 0x60000000
    [r2+-52] = r0
    [r14+16] &= 0xFFFFEFFF
    [r14+16] &= 0xFFFFDFFF
    r0 = [r2+-48]
    r0 = r0 & 0xFFC03FFF
    r0 |= 524288
    [r2+-48] = r0
    [r14+16] &= 0xFFBFFFFF
    [r14+16] &= 0xFF7FFFFF
    [r14+16] |= 0x1000000
    [r14+16] &= 0xFDFFFFFF
    [r14+16] |= 0x4000000
    [r14+16] &= 0xF7FFFFFF
    [r14+16] &= 0xEFFFFFFF
    [r14+16] &= 0xDFFFFFFF
    r0 = [r2+-44]
    r0 = r0 & 0xFFFFFFF8
    r0 |= 1
    [r2+-44] = r0
    [r14+20] |= 0x8
    [r14+20] |= 0x10
    [r14+20] &= 0xFFFFFF1F
    r0 = [r2+-44]
    r0 = r0 & 0xFFFFF8FF
    r0 = r0 | 0x300
    [r2+-44] = r0
    [r14+20] &= 0xFFFFF7FF
    [r14+20] &= 0xFFFFEFFF
    [r14+20] &= 0xFFFFDFFF
    [r14+20] |= 0x4000
    r0 = [r2+-44]
    r0 = r0 & 0xFFFC7FFF
    r0 |= 32768
    [r2+-44] = r0
    [r14+20] &= 0xFFFBFFFF
    [r14+20] |= 0x180000
    [r14+24] &= 0xFFFFFFFE
    [r14+24] &= 0xFFFFFFFD
    [r14+20] |= 0x200000
    r0 = [r2+-44]
    r0 = r0 & 0xFE3FFFFF
    r0 |= 4194304
    [r2+-44] = r0
    [r14+20] &= 0xFDFFFFFF
    [r14+20] &= 0xFBFFFFFF
    [r14+20] &= 0xE7FFFFFF
    r0 = [r2+-44]
    r0 = r0 & 0x9FFFFFFF
    r0 |= 1073741824
    [r2+-44] = r0
    [r14+24] |= 0x4
    r0 = [r2+-40]
    r0 = r0 & 0xFFFFFFC7
    r0 |= 32
    [r2+-40] = r0
    [r14+24] &= 0xFFFFFFBF
    [r14+24] &= 0xFFFFFF7F
    r0 = [r2+-40]
    r0 = r0 & 0xFFFFFCFF
    r0 |= 512
    [r2+-40] = r0
    r0 = [r2+-40]
    r0 = r0 & 0xFFFFE3FF
    r0 |= 2048
    [r2+-40] = r0
    [r14+24] |= 0x2000
    r0 = [r2+-40]
    r0 = r0 & 0xFFFF3FFF
    r0 |= 16384
    [r2+-40] = r0
    [r14+24] |= 0x70000
    [r14+24] &= 0xFFF7FFFF
    [r14+28] &= 0xFFFFFFFE
    r0 = [r2+-36]
    r0 = r0 & 0xFFFFFFF1
    r0 = r0 | 0x6
    [r2+-36] = r0
    [r14+28] &= 0xFFFFFFEF
    r0 = [r2+-36]
    r0 = r0 & 0xFFFFFF1F
    r0 = r0 | 0x60
    [r2+-36] = r0
    r0 = [r2+-36]
    r0 = r0 & 0xFFFF80FF
    r0 |= 16384
    [r2+-36] = r0
    [r14+28] |= 0x8000
    [r14+28] |= 0x10000
    r0 = [r2+-36]
    r0 = r0 & 0xFFF1FFFF
    r0 |= 262144
    [r2+-36] = r0
    [r14+28] |= 0x100000
    [r14+28] &= 0xFF9FFFFF
    [r14+28] &= 0xFF7FFFFF
    [r14+28] |= 0x1000000
    [r14+28] &= 0xFDFFFFFF
    r0 = [r2+-32]
    r0 = r0 & 0xFFFFFF80
    r0 |= 64
    [r2+-32] = r0
    [r14+32] |= 0x80
    [r14+32] |= 0x100
    r0 = [r2+-36]
    r0 = r0 & 0xE3FFFFFF
    r0 |= 134217728
    [r2+-36] = r0
    [r14+28] |= 0x20000000
    [r14+28] &= 0x3FFFFFFF
    [r14+32] &= 0xFFFFFDFF
    r0 = [r2+-32]
    r0 = r0 & 0xFFFC03FF
    r0 = r0 | 0x24000
    [r2+-32] = r0
    [r14+32] |= 0x40000
    [r14+32] &= 0xFFF7FFFF
    [r14+32] &= 0xFFEFFFFF
    [r14+32] |= 0x200000
    [r14+32] &= 0xFFBFFFFF
    [r14+32] |= 0x800000
    [r14+32] &= 0xF8FFFFFF
    [r14+32] &= 0xC7FFFFFF
    [r14+36] |= 0x7
    r0 = [r2+-28]
    r0 = r0 & 0xFFFFFFE7
    r0 |= 16
    [r2+-28] = r0
    [r14+36] &= 0xFFFFFFDF
    [r14+36] |= 0x40
    [r14+36] &= 0xFFFFFF7F
    [r14+36] &= 0xFFFFFEFF
    [r14+36] &= 0xFFFFF9FF
    [r14+36] &= 0xFFFFF7FF
    [r14+36] &= 0xFFFFEFFF
    [r14+36] &= 0xFFFFDFFF
    [r14+36] &= 0xFFFFBFFF
    [r14+36] &= 0xFFFF7FFF
    [r14+36] &= 0xFFFEFFFF
    [r14+36] &= 0xFFFDFFFF
    r0 = [r2+-28]
    r0 = r0 & 0xFFF3FFFF
    r0 |= 524288
    [r2+-28] = r0
    [r14+36] |= 0x300000
    [r14+36] &= 0xFFBFFFFF
    [r14+36] |= 0x800000
    r0 = [r2+-28]
    r0 = r0 & 0xF8FFFFFF
    r0 = r0 | 0x5000000
    [r2+-28] = r0
    [r14+36] &= 0xF7FFFFFF
    r0 = [r2+-28]
    r0 = r0 & 0x8FFFFFFF
    r0 = r0 | 0x60000000
    [r2+-28] = r0
    [r14+40] |= 0x7
    [r14+40] &= 0xFFFFFFF7
    r0 = [r2+-24]
    r0 = r0 & 0xFFFFFFCF
    r0 |= 32
    [r2+-24] = r0
    [r14+40] |= 0x1C0
    r0 = [r2+-24]
    r0 = r0 & 0xFFFFF1FF
    r0 = r0 | 0x600
    [r2+-24] = r0
    [r14+40] &= 0xFFFFEFFF
    [r14+40] |= 0x6000
    r0 = [r2+-24]
    r0 = r0 & 0xFFFC7FFF
    r0 = r0 | 0x28000
    [r2+-24] = r0
    [r14+40] &= 0xFFFBFFFF
    [r14+40] |= 0x80000
    [r14+40] |= 0x300000
    r0 = [r2+-24]
    r0 = r0 & 0xFC3FFFFF
    r0 = r0 | 0x2C00000
    [r2+-24] = r0
    [r14+40] &= 0xFBFFFFFF
    [r14+40] |= 0x18000000
    [r14+44] &= 0xFFFFFFF8
    [r14+44] &= 0xFFFFFFF7
    [r14+44] |= 0x10
    [r14+44] |= 0x60
    [r14+44] &= 0xFFFFFE7F
    [r14+44] &= 0xFFFFF9FF
    [r14+44] &= 0xFFFFF7FF
    r0 = [r2+-20]
    r0 = r0 & 0xFFFFCFFF
    r0 |= 8192
    [r2+-20] = r0
    [r14+44] &= 0xFFFFBFFF
    [r14+44] |= 0x8000
    r0 = [r2+-20]
    r0 = r0 & 0xFFFCFFFF
    r0 |= 131072
    [r2+-20] = r0
    [r14+44] &= 0xFFFBFFFF
    r0 = [r2+-20]
    r0 = r0 & 0xFFE7FFFF
    r0 |= 1048576
    [r2+-20] = r0
    r0 = [r2+-20]
    r0 = r0 & 0xFF9FFFFF
    r0 |= 4194304
    [r2+-20] = r0
    [r14+52] &= 0xFF000000
    r1 = -4096  #
    r0 = [r2+-8]
    r0 &= r1
    r0 = r0 | 0x33
    [r2+-8] = r0
    [r14+52] |= 0x1000000
    [r14+52] &= 0xFDFFFFFF
    [r14+52] &= 0xF3FFFFFF
    [r14+52] &= 0xCFFFFFFF
    r0 = [r2+-8]
    r0 = r0 & 0xFFFF0FFF
    r0 = r0 | 0xD000
    [r2+-8] = r0
    [r14+56] |= 0x10000
    [r14+56] |= 0x20000
    [r14+56] &= 0xFFFBFFFF
    r0 = [r2+-8]
    r0 = r0 & 0xFC07FFFF
    r0 = r0 | 0x1980000
    [r2+-8] = r0
    [r14+56] &= 0xFBFFFFFF
    [r14+56] &= 0xF7FFFFFF
    [r14+56] &= 0xEFFFFFFF
    [r14+56] &= 0xDFFFFFFF
    [r14+56] &= 0xBFFFFFFF
    [r14+56] |= 0x80000000
    r0 = [r2+-4]
    r0 = r0 & 0xFFFFFFFC
    r0 |= 2
    [r2+-4] = r0
    r0 = [r2+-4]
    r0 = r0 & 0xFFFFFFE3
    r0 |= 16
    [r2+-4] = r0
    r0 = [r2+-4]
    r0 = r0 & 0xFFFFE01F
    r0 = r0 | 0xEE0
    [r2+-4] = r0
    [r14+60] &= 0xFFFC1FFF
    r0 = [r2+-4]
    r0 = r0 & 0xFFC3FFFF
    r0 = r0 | 0x380000
    [r2+-4] = r0
    r0 = [r2+-4]
    r0 = r0 & 0xFF3FFFFF
    r0 |= 4194304
    [r2+-4] = r0
    [r14+60] &= 0xFEFFFFFF
    r0 = [r2+-4]
    r0 = r0 & 0xF9FFFFFF
    r0 |= 33554432
    [r2+-4] = r0
    [r14+60] |= 0x38000000
    [r14+60] &= 0xBFFFFFFF
    [r14+64] &= 0xFFFFFFFE
    [r14+64] &= 0xFFFFFFFD
    r0 = [r2+0]
    r0 = r0 & 0xFFFFFFE3
    r0 |= 16
    [r2+0] = r0
    [r14+64] &= 0xFFFFFFDF
    r0 = [r2+0]
    r0 = r0 & 0xFFFFFF3F
    r0 |= 128
    [r2+0] = r0
    [r14+64] &= 0xFFFFFEFF
    r0 = 9216
    if (r7 != r5) {
    r0 = 5120
    }
    [sp] = r4
    r1 = [r2+0]
    r1 = r1 & 0xFFFFC1FF
    r0 |= r1
    [r2+0] = r0
    [r14+64] &= 0xFFFFBFFF
    [r14+64] &= 0xFFFC7FFF
    [r14+64] |= 0x40000
    r0 = [r2+0]
    r0 = r0 & 0xFFE7FFFF
    r0 |= 1048576
    [r2+0] = r0
    r0 = [r2+0]
    r0 = r0 & 0xFF9FFFFF
    r0 |= 2097152
    [r2+0] = r0
    [r14+64] |= 0x800000
    [r14+64] &= 0xFEFFFFFF
    [r14+64] &= 0xFDFFFFFF
    [r14+64] &= 0xFBFFFFFF
    r0 = [r2+0]
    r0 = r0 & 0xC7FFFFFF
    r0 |= 134217728
    [r2+0] = r0
    [r14+68] &= 0xFFFFFFFC
    [r14+68] &= 0xFFFFFFF3
    [r14+68] &= 0xFFFFFFEF
    [r14+68] &= 0xFFFFFFDF
    [r14+68] &= 0xFFFFFFBF
    r0 = [r2+4]
    r0 = r0 & 0xFFFFFE7F
    r0 |= 128
    [r2+4] = r0
    r0 = [r2+4]
    r0 = r0 & 0xFFFFF9FF
    r0 |= 512
    [r2+4] = r0
    r0 = [r2+4]
    r0 = r0 & 0xFFFFE7FF
    r0 |= 2048
    [r2+4] = r0
    [r14+68] &= 0xFFFE1FFF
    [r14+68] &= 0xFFF9FFFF
    [r14+68] &= 0xFFF7FFFF
    r0 = [r2+36]
    r0 = r0 & 0xFFFCFFFF
    r0 |= 65536
    [r2+36] = r0
    r0 = 5
    call L02055a96  ; @call.xl
    call phase3_p2_set_pll_rn_en  ; @call.xl
    [r14+64] |= 0x1000000
    r0 = 73
    call L02024c28  ; @call.xl
    r6 = 120
    [sp+4] = r7
    if (r7 != r5) {
    r6 = 48
    }
    r0 = r6
    call L020337ca  ; @call.xl
    r3_r2 = r1_r0
    r1 = 1085477888
    r0 = 0
    call L02033466  ; @call.xl
    r5_r4 = r1_r0
    r0 = 4884
    r15 = r0 / r6 (u)
    r0 = r15
    call L02033816  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r5_r4
    call L020331ce  ; @call.xl
    r3 = 1097859072
    r2 = 0
    call L02033872  ; @call.xl
    call L02033776  ; @call.xl
    r11 = r0
    r5 = 7
L02042326:
    r6 = r5 + 8
    r4 = r5 + -7
    r1 = 0
    r9 = r10
    r13 = r10
L02042332:
    r0 = r10
L02042334:
    r7 = r1
    r10 = r0
    if ((r7 & 0xFF) == 0) goto L0204234a
    r0 = r7.b0 (u)
    if (r0 != 1) {  ; @if.ne.ri.s12
    r0 = r6.b0 (u)
    } else {
    r0 = r4.b0 (u)
    }
    goto L0204234c
L0204234a:
    r0 = r5.b0 (u)
L0204234c:
    call L02024c3c  ; @call.xl
    call phase3_p2_set_pll_rn_en  ; @call.xl
    call phase3_p2_get_pll_vc_res  ; @call.xl
    r1 = 1
    if ((r7 & 0xFF) == 0) goto L02042334
    r1 = r7.b0 (u)
    if (r1 != 1) {  ; @if.ne.ri.s12
    r9 = r0
    } else {
    r13 = r0
    }
    r1 = r7 + 1
    r0 = r1.b0 (u)
    if (r0 != 3) goto L02042332
    r0 = uextra(r10, p:0, l:8)
    r1 = uextra(r13, p:0, l:8)
    if (r1 != r0) goto L02042396
    r1 = uextra(r9, p:0, l:8)
    if (r1 != r0) goto L02042396
    r5 += 16  ; @add.ri.u5
    r0 = r5.b0 (u)
    if (r0 < 120) goto L02042326
    goto L02042398
L02042396:
    r10 = r5
L02042398:
    r0 = r10 | 0xF
    r9 = 2815
    r1 = L01c26890
    b[r1+r9] = r0
    r4 = 73
    r6 = 0
    r10 = 2
    r13 = 2768
    r5 = 73
    goto L020423c0
L020423ba:
    r0 = b[r3+r9] (u)
    r4 = r7
L020423c0:
    r0 = r0 - r6
    r0 = r0.b0 (u)
    call L02024c3c  ; @call.xl
    r7 = r5
L020423cc:
    r0 = r7.b0 (u)
    call L02024c28  ; @call.xl
    call phase3_p2_set_pll_rn_en  ; @call.xl
    call phase3_p2_get_pll_vc_res  ; @call.xl
    if (r0 == 1) goto L02042402
    if (r0 == 2) goto L020423f2
    r7 += 1  ; @add.ri.u5
    r0 = r7.b0 (u)
    if (r0 <= 171) goto L020423cc
    goto L02042400
L020423f2:
    r0 = r7 + 1
    r1 = r0.b0 (u)
    r5 = r7
    r7 = r0
    if (r1 <= 171) goto L020423cc
    r5 = 171
L02042400:
    r7 = 171
L02042402:
    r3 = L01c26890
    r0 = r6 + r3
    r1 = r5.b0 (u)
    r2 = r4.b0 (u)
    r1 += r2  ; @add.rr
    r1 += -3
    r1 = r1 / r10 (s)
    r6 += 1  ; @add.ri.u5
    b[r0+r13] = r1
    if (r6 != 47) goto L020423ba
    r0 = 121
    call L02024c28  ; @call.xl
    call phase3_p2_get_wfa_pll_bank  ; @call.xl
    call L02024c3c  ; @call.xl
    [r14+64] &= 0xFEFFFFFF
    [r14+52] &= 0xFDFFFFFF
    [r14+52] &= 0xF3FFFFFF
    r0 = [r14+52]
    r0 = r0 >> 24
    r11 <= insert(r0, p:24, l:8)
    [r14+52] = r11
    r0 = [r14+56]
    r1 = -4096
    r0 &= r1
    r0 = r0 | r15
    [r14+56] = r0
    [r14+64] |= 0x1
    r3 = r14 + 64
    r0 = [r3+0]
    r1 = r0 & 0xFFFFFF3F  #
    r0 = [sp+4]
    r13 = 40000000
    if (r0 == r13) {
    r1 |= 64
    r0 = 664832
    r2 = 0x200000
    } else {
    r0 = 42083616
    r2 = 0x240000
    }
    r11 = [sp]  ; @ld.w.sp.l
    r4 = 262656
    [r3+0] = r1
    r1 = [r3+-4]
    r1 = r1 & 0xFFC3FFFF
    r1 |= r2
    [r3+-4] = r1
    r1 = [r3+-4]
    r1 = r1 & 0xC7FFFFFF
    r1 |= 268435456
    [r3+-4] = r1
    [r3+20] = r0
    call phase3_p2_set_pll_rn_en  ; @call.xl
    [r14+56] &= 0xFFFBFFFF
    r0 = [r4+0]
    if ((r0 & 0x1) != 0) {
    r0 = 8000000
    } else {
    r0 = 4000000
    }
    r1 = L01c373b8
    r1 = [r1+8]
    r0 = r1 / r0 (s)
    r1 = -80
    r0 *= r1
    goto L020424e6
L020424e2:
    nop
    r0 += 1  ; @add.ri.u5
L020424e6:
    if (r0 != 0) goto L020424e2
    [r14+56] |= 0x40000
    call L01c04256  ; @call.xl
    r0 = 0
    r5 = 0
    call L02055a96  ; @call.xl
    call phase3_p2_wifi_get_pa_trim_data  ; @call.xl
    r15 = L01c1f180
    r9 = r14 + 36
    r4 = r9 + 4
    r10 = r4 + 4
    r3 = 0
L02042516:
    r0 = r5.b0 (u)
    if (r0 > 5) goto L02042580
    r1 = r3 + r15
    r6 = b[r1+156] (u)
    tbb [r0]
L02042526:
    .byte (L0204252c - L02042526) / 2, (L0204253a - L02042526) / 2, (L02042544 - L02042526) / 2, (L0204254e - L02042526) / 2, (L0204255c - L02042526) / 2, (L0204256a - L02042526) / 2
L0204252c:
    r1 = r9  #
    r0 = [r4+-4]
    r7 = r0 & 0xF8FFFFFF
    r0 = 24
    r2 = 7
    goto L02042576
L0204253a:
    r0 = [r4+0]
    r7 = r0 & 0xFFFFFFF8
    r0 = 0
    goto L02042556
L02042544:
    r0 = [r4+0]
    r7 = r0 & 0xFFFFF1FF
    r0 = 9
    goto L02042556
L0204254e:
    r0 = [r4+0]
    r7 = r0 & 0xFFFC7FFF
    r0 = 15
L02042556:
    r2 = 7
    r1 = r4
    goto L02042576
L0204255c:
    r1 = r4  #
    r0 = [r4+0]
    r7 = r0 & 0xFC3FFFFF
    r0 = 22
    r2 = 15
    goto L02042576
L0204256a:
    r1 = r10  #
    r0 = [r4+4]
    r7 = r0 & 0xFFFFFFF8
    r0 = 0
    r2 = 7
L02042576:
    r2 &= r6
    r0 = r2 << r0
    r0 |= r7
    [r1+0] = r0
L02042580:
    r3 += 1  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
    if (r3 != 7) goto L02042516
    r0 = 4
    r9 = 4
    call L02055e38  ; @call.xl
    r1 = r0
    r0 = 97
    r4 = r1 << 24
    call L02055e38  ; @call.xl
    r0 = r0 & 0xFFFFFF03
    r4 <= insert(r0, p:22, l:2)
    r0 = L01c26890
    r5 = r0 + 1388
    [r5+0] = r4
    r0 = 5
    call L02055e38  ; @call.xl
    r6 = r0
    r0 = 97
    call L02055e38  ; @call.xl
    r0 = r0 << 20
    r0 = r0 & 0xC00000
    r0 <= insert(r6, p:24, l:8)
    [r5+4] = r0
    r0 = 6
    call L02055e38  ; @call.xl
    r6 = r0
    r0 = 97
    call L02055e38  ; @call.xl
    r0 = r0 << 18
    r0 = r0 & 0xC00000
    r0 <= insert(r6, p:24, l:8)
    [r5+8] = r0
    r0 = 7
    call L02055e38  ; @call.xl
    r1 = r0
    r0 = 97
    r4 = r1 << 24
    call L02055e38  ; @call.xl
    r0 = r0 >> 6
    r4 <= insert(r0, p:22, l:2)
    r10 = 8  #
    [r5+12] = r4
    r0 = 8
    call L02055e38  ; @call.xl
    r1 = r0
    r0 = 98
    r4 = r1 << 24
    call L02055e38  ; @call.xl
    r0 = r0 & 0xFFFFFF03
    r4 <= insert(r0, p:22, l:2)
    [r5+16] = r4
    r0 = 9
    call L02055e38  ; @call.xl
    r6 = r0
    r0 = 98
    call L02055e38  ; @call.xl
    r1 = [r5+0]
    r2 = r1 >> 22
    [r5+0] = r2
    r2 = [r5+4]
    r2 = r2 >>> 22
    [r5+4] = r2
    r3 = [r5+8]
    r4 = r3 >> 22
    [r5+8] = r4
    r4 = [r5+12]
    r4 = r4 >>> 22
    [r5+12] = r4
    r7 = [r5+16]
    r7 = r7 >>> 22
    [r5+16] = r7
    r1 = r1 >> 25
    [r5+20] = r1
    r1 = r3 >> 25
    r1 = r4 + r2  #
    [r5+24] = r1
    r1 = r1 / r10 (s)
    r1 = r7 / r9 (s)  #
    [r5+28] = r1
    r0 = r0 << 20
    r0 = r0 & 0xC00000  #
    [r5+32] = r1
    r0 <= insert(r6, p:24, l:8)
    r0 = r0 >>> 22
    r0 = r0 / r9 (s)
    [r5+36] = r0
    [r14+4] |= 0x30000
    r0 = [r14+4]
    r0 = r0 & 0xFFFF8FFF
    r0 |= 16384
    [r14+4] = r0
    [r14+8] &= 0xFFFFFFF8
    r0 = [r14+12]
    r0 = r0 & 0xFFFFFF3F
    r0 |= 64
    [r14+12] = r0
    r0 = [r14+16]
    r0 = r0 & 0xFFFFF0FF
    r0 = r0 | 0x900
    [r14+16] = r0
    r0 = [r14+16]
    r0 = r0 & 0xFFFFFF80
    r0 = r0 | 0xE
    [r14+16] = r0
    r0 = 0
    r6 = 0
    call L02055f56  ; @call.xl
    call phase3_p2_wf_phy_init  ; @call.xl
    r0 = 1
    call L02023b3e  ; @call.xl
    call phase3_p2_rapp_init  ; @call.xl
    [r8+40] = r6
    [r8+44] = r6
    [r8+48] = r6
    r0 = 0x10000
    [r8+40] = r0
    goto L02042702
L020426fe:
    [r8+52] = r6
L02042702:
    r1 = [r8+40]
    if ((r1 & 0x700000) != 0) goto L020426fe
    [r8+44] = r6
    [r8+48] = r6
    r1 = 14188
    r5 = r12 + r1
    [r8+40] = r0
    call L02024ece  ; @call.xl
    r0 = r11
    call L020009ee  ; @call.xl
    r9 = r15
    if (r0 == r13) {
    r5 = L02039780
    }
    r4 = L01c26890
    r13 = r14 + -6386
    r11 = r13 + -1
    r15 = 0
L0204274a:
    r0 = [r8+40]
    if ((r0 & 0x700000) == 0) goto L0204275a
    [r8+52] = r15
    goto L0204274a
L0204275a:
    r1 = r6 << 3
    r0 = [r5+r1]
    r2 = r11 + -141
    r2 += r6  ; @add.rr
    r2 = r2.l (u)
    if (r2 > 95) goto L02042784
    r2 = 4095
    r0 &= r2
    if (r6 > 132) goto L0204279c
    r2 = 955
    r2 = h[r4+r2<<1] (u)
    r3 = 954
    goto L020427cc
L02042784:
    if (r6 < 224) goto L020427dc
    r3 = r9
    r2 = b[r3+161] (u)
    r3 = b[r3+162] (u)
    r0 = r0 & 0xFFFFFFC0
    r0 |= r2
    r2 = r3 << 3
    goto L020427da
L0204279c:
    if (r6 > 179) goto L020427ae
    r2 = 957
    r2 = h[r4+r2<<1] (u)
    r3 = 956
    goto L020427cc
L020427ae:
    if (r6 > 185) goto L020427c0
    r2 = 959
    r2 = h[r4+r2<<1] (u)
    r3 = 958
    goto L020427cc
L020427c0:
    r2 = 961
    r2 = h[r4+r2<<1] (u)
    r3 = 960
L020427cc:
    r3 = h[r4+r3<<1] (u)
    r2 = r2 << 22
    r0 |= r2
    r2 = r3 & 0xFFFF03FF
    r2 = r2 << 12
L020427da:
    r0 |= r2
L020427dc:
    [r8+44] = r0
    r7 = r6 << 8
    r0 = r7 | r13
    [r8+40] = r0
    call L02024ece  ; @call.xl
    goto L020427f6
L020427f2:
    [r8+52] = r15
L020427f6:
    r0 = [r8+40]
    if ((r0 & 0x700000) != 0) goto L020427f2
    r0 = r5 + r1
    r10 = [r0+4]
    if (r6 > 127) goto L0204281c
    r0 = uextra(r10, p:21, l:8)
    call phase3_p2_get_wfa_pll_bank  ; @call.xl
    r0 = r0 << 9
    r10 = r10 | r0
    goto L0204284e
L0204281c:
    if (r6 < 224) goto L0204284e
    r0 = r9 + 156
    r2 = 3227546111
    r2 = r2 & r10  #
    r1 = b[r0+4] (u)
    r1 = r1 << 26
    r1 |= r2  #
    r3 = b[r0+3] (u)
    r3 = r3 << 23
    r1 |= r3  #
    r2 = b[r0+2] (u)
    r3 = b[r0+1] (u)
    r2 = r2 << 18
    r1 |= r2  #
    r0 = b[r0+0] (u)
    r2 = r3 << 15
    r1 |= r2
    r0 = r0 << 9
    r10 = r1 | r0
L0204284e:
    [r8+44] = r10
    r0 = r7 | r11
    [r8+40] = r0
    call L02024ece  ; @call.xl
    r6 += 1  ; @add.ri.u5
    if (r6 != 256) goto L0204274a
    r5 = 0
    [r8+40] = r5
    [r8+40] = r5
    [r8+40] = r5
    [r8+40] = r5
    [r8+40] = r5
    [r8+40] = r5
    [r8+40] = 0x10000
    [r14+80] &= 0xFFFFFFFE
    [r14+80] &= 0xFFFFFFFD
    [r14+80] |= 0x4
    [r14+80] |= 0x8
    [r14+56] |= 0x4000000
    [r14+56] |= 0x8000000
    [r14+80] |= 0x800000
    [r14+80] &= 0xDFFFFFFF
    [r14+80] |= 0x10000000
    [r8+92] |= 0x7000000
    [r8+92] |= 0x40000000
    [r14+80] |= 0x400
    [r14+80] |= 0x800
    [r14+80] |= 0x1000
    [r14+80] |= 0x2000
    [r14+80] |= 0x40000
    [r14+80] |= 0x80000
    [r14+80] |= 0x100000
    [r14+80] |= 0x200000
    [r14+80] &= 0xFFBFFFFF
    [r14+36] |= 0x20
    [r14+36] |= 0x40
    [r14+36] |= 0x80
    [r14+36] |= 0x80
    [r14+36] |= 0x100
    [r14+80] |= 0x40000000
    [r14+80] &= 0x7FFFFFFF
    r0 = r11 + 6451
    r1 = r0
    r0 = [r1+36]
    r0 = r0 & 0x1FFFFFFF
    r0 |= 536870912
    [r1+36] = r0
    [r8+92] &= 0x7FFFFFFF
    [r14+80] |= 0x10
    [r14+80] &= 0xFFFFFFDF
    [r14+80] |= 0x40
    [r14+80] |= 0x80
    [r14+80] |= 0x100
    [r14+80] |= 0x200
    [r14+80] |= 0x4000
    [r14+80] |= 0x8000
    [r14+80] |= 0x10000
    [r14+80] |= 0x20000
    [r14+80] |= 0x1000000
    [r14+80] |= 0x2000000
    [r14+80] |= 0x4000000
    [r14+80] &= 0xF7FFFFFF
    r0 = [r1+36]
    r0 = r0 & 0xE0FFFFFF
    r0 = r0 | 0x1B000000
    r0 = r8 + 64  #
    [r1+36] = r0
    r1 = r0
    r0 = [r1+28]
    r0 = r0 & 0xFF00FFFF
    r0 = r0 | 0x60000
    [r1+28] = r0
    r0 = [r1+28]
    r0 = r0 & 0xFFFFFF00
    r0 = r0 | 0x6B
    [r1+28] = r0
    call L02024f3c  ; @call.xl
    r0 = [r14+28]
    r0 = [r14+32]
    r3 = r11 + 3
L02042978:
    [sp+8] = r5
    call L02042eec  ; @call.xl
    r2 = L01c1fca8
    r0 = 24
    b[r2+10] = r0
    r0 = 10
    b[r2+11] = r0
    [r3+0] &= 0xFFFF3FFF
    r0 = -240
    goto L0204299c
L02042998:
    nop
    r0 += 1  ; @add.ri.u5
L0204299c:
    if (r0 != 0) goto L02042998
    [r8+0] |= 0x80
    r0 = [r8+0]
    r0 = r0 & 0xFFE0FFFF
    r0 = r0 | 0xC0000
    [r8+0] = r0
    r0 = b[r2+10] (u)
    r1 = -10
    r0 *= r1
    goto L020429be
L020429ba:
    nop
    r0 += 1  ; @add.ri.u5
L020429be:
    if (r0 != 0) goto L020429ba
    [r8+0] |= 0x1
    r0 = b[r2+10] (u)
    r0 *= r1
    goto L020429ce
L020429ca:
    nop
    r0 += 1  ; @add.ri.u5
L020429ce:
    if (r0 != 0) goto L020429ca
    r1 = 0x2FC00
    [r1+64] |= 0x400
    r0 = 0x20000
    [r0+0] |= 0xC0000000
    r0 = b[r2+10] (u)
    r3 = -10
    r0 *= r3
    goto L020429ec
L020429e8:
    nop
    r0 += 1  ; @add.ri.u5
L020429ec:
    if (r0 != 0) goto L020429e8
    r3 = 65535
    r0 = r1 + 64
    r3 = -771  #
    [r0+0] = r3
    [r1+64] &= r3
    [r0+56] = 0xF
    [r1+120] |= 0x3F0
    r3 = 0
    b[r2+16] = r3
    r4 = r2 + 56
    r5 = r0 + 72
    [r5+0] = r4
    r4 = 0
    goto L02042a32
L02042a1e:
    r5 = r4 * 0xC
    r5 += r2  ; @add.rr
    r6 = r4 << 8
    r6 |= r4
    [r5+56] = r6
    [r5+60] = r3
    [r5+64] = r3
    r4 += 1  ; @add.ri.u5
L02042a32:
    r4 = r4.l (u)
    if (r4 <= 80) goto L02042a1e
    r2 = r0 + 320
    [r2+24] = 0x0
    r3 = 504
    r4 = L02041870
    goto L02042a5a
L02042a4c:
    r5 = r3 + r4
    r6 = [r3+r4]
    r5 = [r5+4]
    [r2+28] = r6
    [r2+28] = r5
    r3 += -8
L02042a5a:
    if (r3 != -8) goto L02042a4c
    [r1+32] &= 0x3FFFFFFF
    [r2+0] = 0xF0000
    r3 = 410173204
    [r2+4] = r3
    r3 += 65
    [r2+8] = r3
    r3 += -85
    [r2+12] = r3
    r3 = 0
    [r2+16] = r3
    [r2+20] = r3
    r3 += -100
    r4 = L01c26890
    goto L02042a8a
L02042a86:
    nop
    r3 += 1  ; @add.ri.u5
L02042a8a:
    if (r3 != 0) goto L02042a86
    [r2+0] |= 0x1
    [r2+0] &= 0xFFEFFFFF
    [r1+124] |= 0x1
    [r0+8] = 0xB9
    r2 = 16765252
    [r1+0] = r2
    r2 = 1309949151
    [r1+4] = r2
    [r1+8] = 0x3100000
    [r1+12] = 0x80808080
    r2 = 2147516544
    [r1+16] = r2
    [r1+20] = 0x80
    r2 = 0
    [r1+24] = r2
    [r1+28] = r2
    r2 = 911562039
    [r1+32] = r2
    r2 = 213057
    [r1+36] = r2
    [r1+40] = 0x5C000
    r3 = r4 + 1408  #
    r2 = [r1+16]
    r2 = r2 & 0xFFFFFF00  #
    r4 = b[r3+0] (u)
    r2 |= r4
    [r1+16] = r2
    r2 = [r1+16]
    r2 = r2 & 0xFFFF00FF  #
    r4 = b[r3+4] (u)
    r2 <= insert(r4, p:8, l:8)
    [r1+16] = r2
    r4 = b[r3+8] (u)
    r4 = 0x0 - r4  #
    r2 = [r1+16]
    r2 <= insert(r4, p:16, l:8)
    [r1+16] = r2
    r2 = [r1+8]
    r4 = h[r3+12] (u)
    r2 <= insert(r4, p:0, l:10)
    [r1+8] = r2
    r2 = [r1+8]
    r4 = 4293919743
    r2 &= r4  #
    r3 = h[r3+16] (u)
    r3 = r3 & 0xFFFF03FF
    r2 <= insert(r3, p:10, l:10)
    [r1+8] = r2
    [r0+92] &= 0xFFFFFFF0
    [r0+92] |= 0x8
    [r0+88] &= 0xFFFFFF00
    [r0+88] |= 0x36
    [r0+88] &= 0xFF00FFFF
    [r0+88] |= 0x360000
    [r0+88] &= 0xFFFF00FF
    [r0+88] |= 0x200
    [r0+88] &= 0xFFFFFF
    [r0+88] |= 0x2000000
    [r0+92] &= 0xFF00FFFF
    [r0+92] |= 0x360000
    [r0+92] &= 0xFFFFFF
    [r0+92] |= 0x36000000
    r1 = -10
    goto L02042b66
L02042b62:
    nop
    r1 += 1  ; @add.ri.u5
L02042b66:
    if (r1 != 0) goto L02042b62
    [r0+96] &= 0xFFFFFF00
    [r0+96] |= 0x36
    [r0+96] &= 0xFFFF00FF
    [r0+96] |= 0x3600
    r0 = [sp+8]
    if (r0 == 0) goto L02042cb8
    [r8+0] |= 0x3
    r0 = 32571393
    [r8+4] = r0
    r0 = 33554449
    [r8+4] = r0
    r0 = 983073
    [r8+4] = r0
    r0 = 169410609
    [r8+4] = r0
    r0 = 17432641
    [r8+4] = r0
    r4 = 0
    r5 = 11467
    goto L02042be2
L02042bbc:
    r7_r6 = 0
    goto L02042bdc
L02042bc0:
    r2 = 1
    if (r4 != 4) {  ; @if.ne.ri.s12
    r0 = r6 + r4
    r0 += r12
    r2 = b[r0+r5] (u)
    }
    r0 = r4.b0 (u)
    r1 = r7.b0 (u)
    call L02025010  ; @call.xl
    r6 += 4  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L02042bdc:
    if (r6 != 184) goto L02042bc0
    r4 += 1  ; @add.ri.u5
L02042be2:
    if (r4 != 5) goto L02042bbc
    r4 = 0
    r5 = 6108
    r6 = 0
    goto L02042c06
L02042bf0:
    r0 = r6 + r12
    r2 = b[r0+r5] (u)
    r1 = r4.b0 (u)
    r0 = 5
    call L02025010  ; @call.xl
    r4 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02042c06:
    if (r6 != 41) goto L02042bf0
    r0 = 2147483761
    [r8+4] = r0
    r0 = 602341505
    [r8+4] = r0
    r1 = 131217
    [r8+4] = r1
    r1 = 983201
    [r8+4] = r1
    r1 = 262321
    [r8+4] = r1
    r1 = 245760193
    [r8+4] = r1
    r1 = 738197713
    [r8+4] = r1
    r1 = 671940833
    [r8+4] = r1
    r1 = 525336817
    [r8+4] = r1
    r1 = 2521039105
    [r8+4] = r1
    r1 = 5243153
    [r8+4] = r1
    r1 = 19661089
    [r8+4] = r1
    r1 = 33751345
    [r8+4] = r1
    r1 = 587137345
    [r8+4] = r1
    r1 = 3277137
    [r8+4] = r1
    r1 = 327680353
    [r8+4] = r1
    r1 = 602210433
    [r8+4] = r1
    [r8+4] = r0
L02042cb8:
    sp += 16
    {pc, r15-r4} = [sp++]
L02042cbc:
    r0 = L01c1fca8
    r1 = b[r0+13] (u)
    if (r1 == 0) goto L02042d04
    r1 = 0
    r0 = 0x14000  #
    b[r0+13] = r1
    [r0+0] &= 0xFFFFFFE0
    r1 = -1000
    goto L02042cdc
L02042cd8:
    nop
    r1 += 1  ; @add.ri.u5
L02042cdc:
    if (r1 != 0) goto L02042cd8
    [r0+0] = 0x0
    r0 = -1000
    goto L02042cec
L02042ce8:
    nop
    r0 += 1  ; @add.ri.u5
L02042cec:
    if (r0 != 0) goto L02042ce8
    r0 = 65552
    [r0+0] |= 0xC000
    r0 = -1000
    goto L02042d02
L02042cfe:
    nop
    r0 += 1  ; @add.ri.u5
L02042d02:
    if (r0 != 0) goto L02042cfe
L02042d04:
    rts
L02042d06:
    r0 = L01c1fca8
    r0 = b[r0+16] (u)
    rts
L02042d12:
    r0 = L01c1fca8
    r1 = 0
    b[r0+16] = r1
    rts
L02042d20:
    r1 = L01c1fca8
    r2 = b[r1+16] (u)
    if (r2 != 0) goto L02042d32
    r2 = h[r1+14] (u)
    r0 += r2  ; @add.rr
    h[r1+14] = r0
L02042d32:
    rts
L02042d34:
    [--sp] = {rets, r5, r4}
    sp += -8
    r0 = L01c1fca8
    r1 = b[r0+16] (u)
    if (r1 != 0) goto L02042d90
    r1 = h[r0+14] (s)
    r0 = sp + 0
    r0 |= 2
    r2 = r1 >> 16
    h[r0+2] = r2
    h[sp+2] = r1
    r1 = 4
    call L02001776  ; @call.xl
    h[sp] = r0
    r4 = L020558f4
    r5 = L02055948
    goto L02042d80
L02042d6e:
    r0 = [r4+12]
    if (r0 == 0) goto L02042d7e
    r1 = [r4+4]
    if (r1 == 0) goto L02042d7e
    r0 = 110
    call r1
    if (r0 == 1) goto L02042d86
L02042d7e:
    r4 += 28  ; @add.ri.u5
L02042d80:
    if (r4 < r5) goto L02042d6e
    goto L02042d90
L02042d86:
    r3 = [r4+12]
    r1 = sp + 0
    r0 = 110
    r2 = 6
    call r3
L02042d90:
    sp += 8
    {pc, r5, r4} = [sp++]
L02042d94:
    r0 = L01c1fca8
    r0 = h[r0+14] (s)
    rts
L02042da0:
    r1 = L01c2688c
    r1 = [r1+0]
    r2 = 48
    r1 = r1 / r2 (u)
    r0 += r1  ; @add.rr
    rts
