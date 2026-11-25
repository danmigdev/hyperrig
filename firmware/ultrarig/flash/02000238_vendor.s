; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02000238..0x02000558: vendor code (JieLi SDK or library, not reversed), as instructions
sdk_exception_irq_handler:
    trigger
    [--sp] = {sp, ssp, usp, icfg, psr, rets, retx, rete, reti}
    [--sp] = {r15-r0}
    r0 = sp
    call L0201ade8  ; @call.xl
L0200024e:
    goto L0200024e
L02000250:
    [--sp] = {rets, r7-r4}
    r4 = r2
    r2 = 1000000
    r5 = 0x7780000
    if (r3 != 0) goto L02000274
    r1 = r1 / r2 (u)
    r1 = r1 << 1
    if (r1 >= 576) {  ; @if.ge.ri.s12
    r1 = 576
    }
    r1 = r1 << 18
    r5 = r1 - 0x80000
L02000274:
    r6 = r0 / r2 (u)
    r7 = 0
    r3 = 0x16A00
    [r3+12] = r7
    [r3+8] = r7
    r0 = 10
    call sdk_RC16M_udelay  ; @call.xl
    r0 = [r3+8]
    r0 = r0 & 0xFFFFFFF8
    r0 |= 4
    [r3+8] = r0
    [r3+8] |= 0x18
    if (r4 == 0) goto L020002a2
    [r3+8] |= 0x20
    [r3+8] |= 0x40
L020002a2:
    [r3+0] = r7
    [r3+0] |= 0x1
    r0 = [r3+0]
    r0 = r0 & 0xFFFFFFE7
    r0 |= 16
    [r3+0] = r0
    r0 = [r3+0]
    r0 = r0 & 0xFFFFFF9F
    r0 |= 32
    [r3+0] = r0
    r0 = [r3+0]
    r0 = r0 & 0xFFFFFE7F
    r0 |= 128
    [r3+0] = r0
    r0 = [r3+0]
    r0 = r0 & 0xFFFFF9FF
    r0 |= 1024
    [r3+0] = r0
    [r3+0] |= 0x800
    r0 = r6 << 12
    r0 = r0 + -8192
    [r3+0] |= r0
    [r3+0] |= r5
    [r3+0] |= 0x4
    r0 = 10
    call sdk_RC16M_udelay  ; @call.xl
    [r3+0] |= 0x2
    r0 = 10
    call sdk_RC16M_udelay  ; @call.xl
    [r3+0] &= 0xFFFFFFFB
    r0 = 100
    call sdk_RC16M_udelay  ; @call.xl
    {pc, r7-r4} = [sp++]
    [--sp] = {rets, r6-r4}
    sp += -24
    r5 = 263172
    r0 = [r5+0]
    [sp+20] = r0
    r0 = [r5+8]
    [sp+16] = r0
    r4 = 65552
    r0 = [r4+0]
    [sp+12] = r0
    r0 = [r4+4]
    [sp+8] = r0
    r6 = 331804
    r0 = [r6+12]
    [sp+4] = r0
    r0 = [r6+0]
    [sp] = r0
    call L01c0344c  ; @call.xl
    r0 = 24000000
    r1 = 240000000
    r3_r2 = 0
    call L02000250
    r0 = sp + 12
    [r0+0] &= 0xFFEFFFFF
    [r0+0] |= 0x200000
    r0 = [sp+8]
    r0 = r0 & 0xFFFCFFFF
    r0 |= 131072
    [sp+8] = r0
    r0 = sp + 8
    [r0+0] &= 0xFFE7FFFF
    [r0+0] |= 0x40000
    [r0+0] |= 0x200000
    r0 = sp + 4
    [r0+0] |= 0x22000
    r0 = sp + 0
    [r0+0] |= 0x20000000
    r0 = sp + 20
    [r0+0] &= 0xFFFFFFE0
    r0 = sp + 16
    [r0+0] &= 0xFFFFFFF
    [r0+0] &= 0xFFFFF0FF
    r1 = 325  #
    r0 = [sp+20]
    r0 |= r1
    [r5+0] = r0
    r0 = 10
    call sdk_RC16M_udelay  ; @call.xl
    [r5+0] |= 0x40
    r0 = 10
    call sdk_RC16M_udelay  ; @call.xl
    [r5+0] |= 0x100
    r0 = 10
    call sdk_RC16M_udelay  ; @call.xl
    r0 = [sp+16]
    r1 = 1610613248
    r0 |= r1
    [r5+8] = r0
    r0 = 100
    call sdk_RC16M_udelay  ; @call.xl
    r0 = [sp+4]
    [r6+12] = r0
    r0 = [sp]
    [r6+0] = r0
    r0 = [sp+12]
    [r4+0] = r0
    r0 = [sp+8]
    r0 = 10000  #
    [r4+4] = r0
    call sdk_RC16M_udelay  ; @call.xl
    call sdk_sys_clk_source_rc_clk_off  ; @call.xl
    sp += 24
    {pc, r6-r4} = [sp++]
L020003ec:
    if ((r0 & 0x3) != 0) goto L020003fc
    r3 = r1 | r2
    if ((r3 & 0x3) == 0) goto L02000420
L020003fc:
    if ((r0 & 1) != 0) goto L02000412
    r3 = r1 | r2
    if ((r3 & 1) != 0) goto L02000412
    r2 = r2 >> 1
    goto L0200041c
L0200040c:
    r3 = b[r1++=1] (u)
    b[r0++=1] = r3
    r2 += -1
L02000412:
    if (r2 != 0) goto L0200040c
    rts
L02000416:
    r3 = h[r1++=2] (u)
    h[r0++=2] = r3
    r2 += -1
L0200041c:
    if (r2 != 0) goto L02000416
    rts
L02000420:
    r2 = r2 >> 2
    goto L0200042a
L02000424:
    r3 = [r1++=4]
    [r0++=4] = r3
    r2 += -1
L0200042a:
    if (r2 != 0) goto L02000424
    rts
L0200042e:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = 29883724
    r0 = r5 + 16
    r1 = r4 + 4
    r2 = 8
    call L020003ec
    r0 = [r4+0]
    r1 = [r0+8]
    [r5+24] = r1
    r0 = b[r0+13] (u)
    b[r5+0] = r0
    r0 = h[r4+12] (u)
    h[r5+28] = r0
    r0 = h[r4+14] (u)
    r0 = r5 + 32  #
    h[r5+30] = r0
    r1 = r4 + 16
    r2 = 8
    call L020003ec
; HyperRig MINI v4, patch mini_absent_boot_extensions: MINI has no SDRAM or secondary application. Initialize G's private SDRAM_CFG_INFO/EX_APP_INFO to zero instead of copying unspecified incoming boot-context bytes+80..91. Preserve core boot info and mailbox.
.if TARGET_MINI
    r0 = 29883764  ; @li.u32
    r1 = 0  ; @li.u8
    [r0+0] = r1  ; @st.w
    [r0+4] = r1  ; @st.w
    [r0+8] = r1  ; @st.w
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
.else
    r1 = r4 + 80
    r0 = 29883764
    r2 = 8
    call L020003ec
    r1 = r4 + 88
    r0 = 29883772
    r2 = 4
    call L020003ec
.endif
    r0 = h[r4+12] (u)
    r1 = 29884172
    [r1+0] = r0
    {pc, r5, r4} = [sp++]
L02000484:
    rts
L02000486:
    [--sp] = {rets, r4}
    if (r0 <= r1) goto L020004c2
    r3 = r1 + r2
    if (r0 >= r3) goto L020004c2
    if ((r0 & 0x3) != 0) goto L020004a2
    r4 = r1 | r2
    if ((r4 & 0x3) == 0) goto L020004da
L020004a2:
    if ((r0 & 1) != 0) goto L020004c6
    r1 |= r2
    if ((r1 & 1) != 0) goto L020004c6
    r0 += r2  ; @add.rr
    r0 += -2
    r1 = r3 + -2
    r2 = r2 >> 1
    goto L020004be
L020004b8:
    r3 = h[r1++=-2] (u)
    h[r0++=-2] = r3
    r2 += -1
L020004be:
    if (r2 != 0) goto L020004b8
    {pc, r4} = [sp++]
L020004c2:
    call L020003ec
    {pc, r4} = [sp++]
L020004c6:
    r0 += r2  ; @add.rr
    r0 += -1
    r1 = r3 + -1
    goto L020004d6
L020004d0:
    r3 = b[r1++=-1] (u)
    b[r0++=-1] = r3
    r2 += -1
L020004d6:
    if (r2 != 0) goto L020004d0
    {pc, r4} = [sp++]
L020004da:
    r0 += r2  ; @add.rr
    r0 += -4
    r1 = r3 + -4
    r2 = r2 >> 2
    goto L020004ec
L020004e6:
    r3 = [r1++=-4]
    [r0++=-4] = r3
    r2 += -1
L020004ec:
    if (r2 != 0) goto L020004e6
    {pc, r4} = [sp++]
    r0 = 0
    rts
    r0 = L01c268f0
    rts
    [--sp] = rets
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fa24
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0200052a
    csync
    r0 = L01c1fa20
L02000522:
    testset b[r0]
    ifeq goto L02000522
    csync
L0200052a:
    pc = [sp++]
    [--sp] = rets
    r0 = cnum
    r1 = L01c1fa24
    r2 = [r1+r0<<2]
    r2 += -1
    [r1+r0<<2] = r2
    if (r2 != 0) goto L02000550
    csync
    r0 = L01c1fa20
    r1 = 0
    b[r0+0] = r1
L02000550:
    call storage_coordination_irq_leave  ; @call.xl
    pc = [sp++]
