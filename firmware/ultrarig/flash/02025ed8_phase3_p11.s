; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 3 functions, 0x02025ed8..0x02026624

; phase3_p11_low_power_suspend: 0x02025ed8..0x02026020, module phase3-p11 (low_power_suspend)
.type phase3_p11_low_power_suspend,@function
phase3_p11_low_power_suspend:
    [--sp] = {rets, r12-r4}
    r8 = r1
    r7 = r0
    r9 = 0
    r10 = L02035902  ; "sys"
    r5 = r7
    goto L02025f2c
L02025eea:
    r0 = [r5+16]
    if (r0 == 0) goto L02025f2c
    r6 = [r0+12]
    if (r6 == 0) goto L02025f2c
    r1 = b[r5+12] (u)
    if (r1 != 0) goto L02025f2c
    r11 = r10 + 303  #
    r4 = [r0+0]
    r0 = r4
    r1 = r11
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02025f14
    r0 = r4
    r1 = r10
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02025f2c
L02025f14:
    r0 = [r5+8]
    call r6
    r1 = r11  #
    r0 = [r5+16]
    r0 = [r0+0]
    call L02028308  ; @call.xl
    r1 = 1
    if (r0 == 0) goto L02025f2a
    r1 = r9
L02025f2a:
    r9 = r1
L02025f2c:
    r5 = [r5+0]
    if (r5 != r7) goto L02025eea
    r11 = 0
    r5 = r7
    goto L02025f6a
L02025f38:
    r0 = [r5+16]
    if (r0 == 0) goto L02025f6a
    r6 = [r0+12]
    if (r6 == 0) goto L02025f6a
    r1 = b[r5+12] (u)
    if (r1 != 0) goto L02025f6a
    r1 = r10 + 28  #
    r4 = [r0+0]
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02025f62
    r1 = r10 + 60
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02025f6a
L02025f62:
    r0 = [r5+8]
    call r6
    r11 = 1
L02025f6a:
    r5 = [r5+0]
    if (r5 != r7) goto L02025f38
    r12 = 1
    r6 = r7
    goto L02025faa
L02025f78:
    r0 = [r6+16]
    if (r0 == 0) goto L02025faa
    r5 = [r0+16]
    if (r5 == 0) goto L02025faa
    r1 = b[r6+12] (u)
    if (r1 != 0) goto L02025faa
    r1 = r10 + 303  #
    r4 = [r0+0]
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02025fa0
    r0 = r4
    r1 = r10
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02025faa
L02025fa0:
    r1 = r8  #
    r0 = [r6+8]
    call r5
    b[r6+12] = r12
L02025faa:
    r6 = [r6+0]
    if (r6 != r7) goto L02025f78
    if ((r9 & 0xFF) != 0) goto L02025fdc
    if ((r11 & 0xFF) == 0) goto L02025fdc
    r0 = 81932
    [r0+0] |= 0x10000
L02025fc6:
    r1 = [r0+0]
    if ((r1 & 131072) != 0) goto L02025fc6
    r1 = [r0+0]
    [r0+0] &= 0xFFFEFFFF
    r0 = r1 >> 18
    r1 = L01c2688c
    [r1+0] = r0
L02025fdc:
    r9 = 1
    r6 = r7
    goto L02026018
L02025fe4:
    r0 = [r6+16]
    if (r0 == 0) goto L02026018
    r5 = [r0+16]
    if (r5 == 0) goto L02026018
    r1 = b[r6+12] (u)
    if (r1 != 0) goto L02026018
    r1 = r10 + 28  #
    r4 = [r0+0]
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0202600e
    r1 = r10 + 60
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02026018
L0202600e:
    r1 = r8  #
    r0 = [r6+8]
    call r5
    b[r6+12] = r9
L02026018:
    r6 = [r6+0]
    if (r6 != r7) goto L02025fe4
    {pc, r12-r4} = [sp++]

; phase3_p11_enter_soft_hold: 0x02026020..0x02026066, module phase3-p11 (enter_soft_hold)
.type phase3_p11_enter_soft_hold,@function
phase3_p11_enter_soft_hold:
    [--sp] = rets
    csync
    r0 = L01c1fa2d
L0202602a:
    testset b[r0]
    ifeq goto L0202602a
    csync
    r1 = L01c3740c
    r0 = [r1+44]
    if (r0 != 0) goto L02026040
    [r1+44] = 0xA
L02026040:
    call phase3_p3_timer_get_ms
    r3_r2 = d[r1+40]
    r2 = r0 - r2
    r0 = -22
    if (r2 < r3) goto L02026064
    r0 = icfg
    r1 += 32
    r0 = L0201df28
    call storage_platform_enter  ; @call.xl
    r0 = 0
L02026064:
    pc = [sp++]

; phase3_p11_low_power_request: 0x02026066..0x02026624, module phase3-p11 (low_power_request)
.type phase3_p11_low_power_request,@function
phase3_p11_low_power_request:
    [--sp] = {rets, r13-r4}
    r4 = L01c1fa30
    r1 = b[r4+91] (u)
    r5 = r0
    if (r1 != 0) goto L02026622
    r0 = b[r4+93] (u)
    if ((r0 & 0x8) == 0) goto L02026622
    r0 = b[r4+89] (u)
    if (r0 != 0) goto L02026622
    r0 = [r4+0]
    if (r0 == r4) goto L02026622
    r11 = [r4+80]
    call storage_coordination_irq_enter  ; @call.xl
    r9 = L01c1fa24
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L020260c6
    csync
L020260be:
    testset b[r8]
    ifeq goto L020260be
    csync
L020260c6:
    r0 = b[r4+89] (u)
    r1 = b[r4+91] (u)
    r0 |= r1
    if ((r0 & 0xFF) != 0) goto L02026104
    r7 = [r4+0]
    if (r7 == r4) goto L02026104
    r6 = -1
    goto L020260f6
L020260e0:
    r1 = [r7+16]
    r0 = -1
    if (r1 == 0) goto L020260f0
    r1 = [r1+4]
    if (r1 == 0) goto L020260f0
    r0 = [r7+8]
    call r1
    if (r0 == 0) goto L0202611c
L020260f0:
    r6 = umin(r6, r0)  #
    r7 = [r7+0]
L020260f6:
    if (r7 != r4) goto L020260e0
    r10 = 0
    if (r6 != -1) {  ; @if.ne.ri.s12
    r10 = r6
    }
    goto L0202611e
L02026104:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0202661c
    csync
    goto L02026616
L0202611c:
    r10 = 0
L0202611e:
    r0 = 9500
    r0 += r11
    if (r10 < r0) goto L02026604
    r0 = b[r4+99] (u)
    r1 = b[r4+100] (u)
    if (r1 == r0) goto L020262c2
    r1 = r0 + -2
    if (r1 < 2) goto L0202614a
    if (r0 != 0) goto L0202614a
    r1 = 24000000
    r0 = 0
    goto L0202614c
L0202614a:
    r1 = 0
L0202614c:
    b[r4+100] = r0
    r7 = r4 + 460
    [r7+0] = r1
    r12 = 1000000
    r0 = 6
    if (r1 <= r12) {
    r0 = 0
    }
    r0 = r1 >> r0
    r1 = 1000000000
    r6 = r1 / r0 (u)
    r0 = 10000
    r0 = r0 / r6 (u)
    call L02025eaa
    r13 = r0
    r0 = 500000
    r0 = r0 / r6 (u)
    r0 = r0.l (u)
    call L02025eaa
    r1 = r7 + 5
    rep 4 {
    b[r1++=1] = r13
    }
    r0 = r12 / r6 (u)  #
    b[r7+9] = r0
    b[r7+10] = r13
    r0 = r0.l (u)
    call L02025eaa
    b[r7+11] = r0
    call storage_fault_acquire  ; @call.xl
    r6 = 0x13E00
    [r6+8] &= 0xFFFFFEFF
    [r6+8] |= 0x1
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r0 = 56
    call storage_fault_exchange  ; @call.xl
    r0 = b[r7+6] (u)
    r1 = b[r7+5] (u)
    r0 = r0 << 4
    r0 |= r1
    r0 = r0.b0 (u)
    call storage_fault_exchange  ; @call.xl
    r0 = b[r7+8] (u)
    r1 = b[r7+7] (u)
    r0 = r0 << 4
    r0 |= r1
    r0 = r0.b0 (u)
    call storage_fault_exchange  ; @call.xl
    r0 = b[r7+10] (u)
    r1 = b[r7+9] (u)
    r0 = r0 << 4
    r0 |= r1
    r0 = r0.b0 (u)
    call storage_fault_exchange  ; @call.xl
    r0 = b[r7+11] (u)
    call storage_fault_exchange  ; @call.xl
    r0 = -258
    [r6+8] &= r0
    call storage_fault_release  ; @call.xl
    r0 = b[r4+99] (u)
    if (r0 != 0) goto L0202621c
    [r7+0] >>= 6
L0202621c:
    r0 = 48
    r1 = 8
    call storage_fault_write_register  ; @call.xl
    r0 = 114
    r1 = 191
    call storage_fault_write_register  ; @call.xl
    r0 = b[r4+99] (u)
    r1 = r0 + -2
    if (r1 < 2) goto L0202625c
    if (r0 == 1) goto L02026276
    if (r0 != 0) goto L02026294
    r0 = 9228
    [r6+0] = r0
    [r4+60] = 0xFA0
    r0 = 49
    r1 = 113
    call storage_fault_write_register  ; @call.xl
    r0 = 84
    r1 = 113
    goto L0202628e
L0202625c:
    r0 = 8204
    [r6+0] = r0
    [r4+60] = 0xFA0
    r0 = 49
    r1 = 68
    call storage_fault_write_register  ; @call.xl
    r0 = 84
    r1 = 68
    goto L0202628e
L02026276:
    r0 = 10252
    [r6+0] = r0
    [r4+60] = 0xFA0
    r0 = 49
    r1 = 67
    call storage_fault_write_register  ; @call.xl
    r0 = 84
    r1 = 67
L0202628e:
    call storage_fault_write_register  ; @call.xl
L02026294:
    r0 = 50
    r1 = 3
    call storage_fault_write_register  ; @call.xl
    r0 = [r4+60]
    call sdk___tcnt_us
    [r4+48] = r0
    r1 = [r4+52]
    r6 = r1 + r0
    r0 = 1550
    call sdk___tcnt_us
    r6 += r0  ; @add.rr
    r0 = 2000  #
    [r4+56] = r6
    call sdk___tcnt_us
    r0 += r6  ; @add.rr
    [r4+56] = r0
L020262c2:
    r6 = 0
    r12 = L02035912  ; "osc"
    r7 = r4
    goto L020262e8
L020262ce:
    r0 = [r7+16]
    if (r0 == 0) goto L020262e8
    r0 = [r0+0]
    if (r0 == 0) goto L020262e8
    r1 = r12 + 287
    call L02028308  ; @call.xl
    r1 = 1
    if (r0 == 0) goto L020262e6
    r1 = r6
L020262e6:
    r6 = r1
L020262e8:
    r7 = [r7+0]
    if (r7 != r4) goto L020262ce
    if ((r6 & 0xFF) != 0) goto L02026306
    r0 = 81932
    [r0+0] &= 0xFFFFFFFD
    [r0+0] |= 0x1
    [r0+0] |= 0x4
L02026306:
    r0 = 19
    r1 = 209
    call storage_fault_write_register  ; @call.xl
    r0 = 20
    r1 = 209
    call storage_fault_write_register  ; @call.xl
    r0 = 84
    r1 = 68
    call storage_fault_write_register  ; @call.xl
    r0 = 49
    r1 = 68
    call storage_fault_write_register  ; @call.xl
    r0 = 88
    r1 = 93
    call storage_fault_write_register  ; @call.xl
    r0 = -4500
    r0 = r0 - r11
    r1 = r0 + r10
    r0 = 64
    call L01c03766  ; @call.xl
    if (r0 == 0) goto L02026380
    r0 = 52
    r1 = 32
    call storage_fault_write_register  ; @call.xl
    r0 = 1
    b[r4+89] = r0
    r0 = 68
    call L02025484
    r7 = r0
    [r4+8] = r7
    if ((r6 & 0xFF) == 0) goto L02026376
    r0 = b[r4+93] (u)
    if ((r0 & 16) != 0) goto L02026398
L02026376:
    r0 = r4
    r1 = r7
    call phase3_p11_low_power_suspend
    goto L020263d4
L02026380:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0202661c
    csync
    goto L02026616
L02026398:
    r10 = 16384
    r6 = 0x10400
    [r6+0] = r10
    [r6+4] = 0x0
    r0 = r12
    call L020009ee
    r1 = 1000000
    r0 = r0 / r1 (s)
    r0 = r0 * 0x1F4
    [r6+8] = r0
    [r6+0] = 0x9
    r0 = r4
    r1 = r7
    call phase3_p11_low_power_suspend
    r0 = [r6+0]
    [r6+0] = r10
    if ((r0 & 32768) != 0) goto L0202651a
L020263d4:
    r0 = b[r4+93] (u)
    r0 = r0 & 0xFFFFFF12
    if (r0 != 18) goto L02026604
    r0 = [r4+72]
    if (r0 == 0) goto L020263ec
    r7 = umin(r7, r0)
L020263ec:
    r10 = L01c3740c
    r1 = b[r10+0] (u)
    r0 = [r4+76]
    if ((r1 & 0x1) != 0) {
    r1 = [r10+36]
    r0 += r1  ; @add.rr
    r0 = r0 + 6000
    } else {
    r0 = r0 + 4000
    }
    r1 = -20000
    r1 += r7  ; @add.rr
    r11 = r1 - r0
    ifs (r11 < 2000) goto L02026604
    r6 = 1
    r7 = L02055954
    r13 = L020559b4
    goto L02026438
L0202642c:
    r0 = [r7+4]
    call r0
    r0 = [r7+4]
    call r0
    r6 &= r0
    r7 += 8  ; @add.ri.u5
L02026438:
    if (r7 < r13) goto L0202642c
    if ((r6 & 0xFF) == 0) goto L02026604
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L02026462
    csync
L0202645a:
    testset b[r8]
    ifeq goto L0202645a
    csync
L02026462:
    r0 = 1
    b[r10+2] = r0
    b[r10+4] = r0
    b[r10+3] = r0
    b[r10+5] = r0
    r0 = 0
    b[r10+8] = r0
    csync
    r1 = cnum
    r2 = [r9+r1<<2]
    r2 += -1
    [r9+r1<<2] = r2
    if (r2 != 0) goto L02026492
    csync
    b[r8+0] = r0
L02026492:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L020264b0
    csync
    r0 = 0
    b[r8+0] = r0
L020264b0:
    call storage_coordination_irq_leave  ; @call.xl
    if (r5 == 0) goto L02026532
    r7 = r12 + 287
    r0 = r5
    r1 = r7
    call L02028308  ; @call.xl
    if (r0 != 0) goto L020264e6
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L020264e0
    csync
    r0 = 0
    b[r8+0] = r0
L020264e0:
    call storage_coordination_irq_leave  ; @call.xl
L020264e6:
    call phase3_p11_enter_soft_hold
    r6 = r0
    r0 = r5
    r1 = r7
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02026538
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L02026538
    csync
L02026510:
    testset b[r8]
    ifeq goto L02026510
    csync
    goto L02026538
L0202651a:
    call L02025626
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0202661c
    csync
    goto L02026616
L02026532:
    call phase3_p11_enter_soft_hold
    r6 = r0
L02026538:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L02026558
    csync
L02026550:
    testset b[r8]
    ifeq goto L02026550
    csync
L02026558:
    if (r6 != 0) goto L02026592
    r0 = b[r4+89] (u)
    if (r0 == 0) goto L02026592
    r0 = 2
    call L0201dbe2
    r0 = r11 - r0
    ifs (r0 < 2000) goto L02026592
    call L01c03812  ; @call.xl
    if (r0 == 0) goto L02026592
    r0 = 76
    call L02025484
    r5 = r0
    r1 = r5  #
    [r4+32] = r5
    r0 = r4 + 24
    call phase3_p11_low_power_suspend
    r0 = r5
    call phase3_p3_low_power_process_wait  ; @call.xl
L02026592:
    r2 = 0
    [r4+32] = r2
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r3 = r1 + 1
    [r9+r0<<2] = r3
    if (r1 != 0) goto L020265b6
    csync
L020265ae:
    testset b[r8]
    ifeq goto L020265ae
    csync
L020265b6:
    r0 = cnum
    r0 = r0.b0 (u)
    r0 += r10
    b[r0+4] = r2
    b[r0+2] = r2
    csync
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L020265dc
    csync
    r0 = 0
    b[r8+0] = r0
L020265dc:
    call storage_coordination_irq_leave  ; @call.xl
    if (r6 != 0) goto L020265f6
    r0 = icfg
    call storage_platform_leave  ; @call.xl
    call phase3_p3_timer_get_ms
    [r10+40] = r0
L020265f6:
    csync
    r0 = L01c1fa2d
    r1 = 0
    b[r0+0] = r1
    csync
L02026604:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0202661c
    csync
L02026616:
    r0 = 0
    b[r8+0] = r0
L0202661c:
    call storage_coordination_irq_leave  ; @call.xl
L02026622:
    {pc, r13-r4} = [sp++]
