; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0202541c..0x0202578e: vendor code (JieLi SDK or library, not reversed), as instructions
L0202541c:
    [--sp] = rets
    r2 = L01c26890
    if (r0 != 0) {  ; @if.ne.ri.s12
    r0 = 358
    } else {
    r0 = 357
    }
    r0 = [r2+r0<<2]
    if (r0 == 0) goto L0202543a
    call phase3_p11_lbuf_alloc_btctrler
    pc = [sp++]
L0202543a:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02025444:
    goto L02025444
sdk___tcnt_us:
    [--sp] = {rets, r7-r4}
    r1 = L01c1fa30
    r1 = [r1+460]
    r1_r0 = r1 * r0 (u)
    r4 = 1000000
    r3_r2 = r1_r0 / r4 (u)
    r5 = r3 * r4
    r7_r6 = r2 * r4 (u)
    r7 += r5  ; @add.rr
    r4 = r0 - r6
    r5 = r1 - r7 - !c
    r0 = r4 | r5
    r4 = 1
    if (r0 != 0) goto L0202547a
    r4 = r0
L0202547a:
    r5 = 0
    r0 = r4 + r2
    r1 = r5 + r3 + c
    {pc, r7-r4} = [sp++]
L02025484:
    [--sp] = {rets, r5, r4}
    r2 = r0
    call storage_fault_acquire  ; @call.xl
    r5 = 81416
    [r5+0] &= 0xFFFFFEFF
    [r5+0] |= 0x1
    r0 = 128
    call storage_fault_exchange  ; @call.xl
    r0 = r2
    call storage_fault_exchange  ; @call.xl
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r2 = r0
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r3 = r0
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r4 = r0
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r1 = -258
    [r5+0] &= r1
    r1 = r2 << 24
    r1 <= insert(r3, p:16, l:8)
    r1 <= insert(r4, p:8, l:8)
    r0 |= r1
    r1 = 1000000
    r5_r4 = r0 * r1 (u)
    call storage_fault_release  ; @call.xl
    r0 = L01c1fa30
    r0 = [r0+460]
    r1_r0 = r5_r4 / r0 (u)
    {pc, r5, r4} = [sp++]
L02025506:
    [--sp] = {rets, r12-r4}
    r12 = L01c1fa30
    r1 = b[r12+89] (u)
    r10 = r0
    if (r1 == 0) goto L02025624
    r0 = 1
    b[r12+98] = r0
    r4 = [r12+0]
    r8 = 0
    r11 = L0203591e  ; "edr"
    goto L02025552
L0202552c:
    r0 = [r5+16]
    r4 = [r5+0]
    if (r0 == 0) goto L02025552
    r6 = [r0+20]
    if (r6 == 0) goto L02025552
    r1 = b[r5+12] (u)
    if (r1 == 0) goto L02025552
    r1 = r11 + 275  #
    r0 = [r0+0]
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02025552
    r1 = r10  #
    r0 = [r5+8]
    call r6
    r8 = 1
L02025552:
    r5 = r4
    if (r5 != r12) goto L0202552c
    r4 = [r12+0]
    goto L0202558e
L0202555e:
    r0 = [r5+16]
    r4 = [r5+0]
    if (r0 == 0) goto L0202558e
    r7 = [r0+20]
    if (r7 == 0) goto L0202558e
    r1 = b[r5+12] (u)
    if (r1 == 0) goto L0202558e
    r1 = r11  #
    r6 = [r0+0]
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02025588
    r1 = r11 + 32
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 != 0) goto L0202558e
L02025588:
    r1 = r10  #
    r0 = [r5+8]
    call r7
L0202558e:
    r5 = r4
    if (r5 != r12) goto L0202555e
    r5 = [r12+0]
    r9 = 0
    goto L020255d2
L0202559c:
    r7 = [r4+16]
    r5 = [r4+0]
    if (r7 == 0) goto L020255d2
    r0 = [r7+20]
    if (r0 == 0) goto L020255d2
    r0 = b[r4+12] (u)
    if (r0 == 0) goto L020255d2
    r1 = r11  #
    r6 = [r7+0]
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020255c6
    r1 = r11 + 32
    r0 = r6
    call L02028308  ; @call.xl
    if (r0 != 0) goto L020255d2
L020255c6:
    r1 = r10  #
    r0 = [r4+8]
    r2 = [r7+24]
    call r2
    b[r4+12] = r9
L020255d2:
    r4 = r5
    if (r4 != r12) goto L0202559c
    r5 = [r12+0]
    r4 = 0
    goto L02025606
L020255e0:
    r7 = [r6+16]
    r5 = [r6+0]
    if (r7 == 0) goto L02025606
    r0 = [r7+20]
    if (r0 == 0) goto L02025606
    r0 = b[r6+12] (u)
    if (r0 == 0) goto L02025606
    r1 = r11 + 275  #
    r0 = [r7+0]
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02025606
    r1 = r10  #
    r0 = [r6+8]
    r2 = [r7+24]
    call r2
    b[r6+12] = r4
L02025606:
    r6 = r5
    if (r6 != r12) goto L020255e0
    if (r8 == 0) {  ; @if.eq.ri.s12
    r0 = 81932
    [r0+0] |= 0x4
    }
    r0 = 0
    b[r12+98] = r0
    b[r12+89] = r0
L02025624:
    {pc, r12-r4} = [sp++]
L02025626:
    [--sp] = {rets, r6-r4}
    r0 = 0
    call sdk___hw_nv_timer_is_runnig  ; @call.xl
    if (r0 == 0) goto L0202578c
    r5 = L01c1fa30
    r4 = [r5+60]
    call L01c03694  ; @call.xl
    r1 = [r5+460]
    r2 = 1000000
    r3_r2 = r0 * r2 (u)
    r1_r0 = r3_r2 / r1 (u)
    if (r4 >= r0) goto L020256f8
    r0 = 2
    call L0201dbe2
    r1 = [r5+60]
    r0 += r1  ; @add.rr
    call sdk___tcnt_us
    r2 = r0
    call storage_fault_acquire  ; @call.xl
    r3 = 81416
    [r3+0] &= 0xFFFFFEFF
    [r3+0] |= 0x1
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r0 = 64
    call storage_fault_exchange  ; @call.xl
    r0 = [r5+48]
    r4 = r2 - r0
    r0 = r4 >> 24
    call storage_fault_exchange  ; @call.xl
    r0 = uextra(r4, p:16, l:8)
    call storage_fault_exchange  ; @call.xl
    r0 = uextra(r4, p:8, l:8)
    call storage_fault_exchange  ; @call.xl
    r0 = r4.b0 (u)
    call storage_fault_exchange  ; @call.xl
    r0 = r2 >> 24
    call storage_fault_exchange  ; @call.xl
    r0 = uextra(r2, p:16, l:8)
    call storage_fault_exchange  ; @call.xl
    r0 = uextra(r2, p:8, l:8)
    call storage_fault_exchange  ; @call.xl
    r0 = r2.b0 (u)
    call storage_fault_exchange  ; @call.xl
    r0 = -258
    [r3+0] &= r0
    call storage_fault_release  ; @call.xl
    r0 = 52
    r1 = 32
    call storage_fault_write_register  ; @call.xl
    r0 = 68
    call L02025484
    [r5+8] = r0
L020256f8:
    r4 = 0
L020256fa:
    r0 = 88
    call storage_fault_read_register  ; @call.xl
    r6 = r0.b0 (s)
    if ((r0 & 32) == 0) goto L02025746
    r0 = 88
    r1 = 16
    call L01c00f72  ; @call.xl
    r0 = 9
    call storage_fault_read_register  ; @call.xl
    r4 = r0 & 0xFFFFFF0F
    if (r4 > 8) goto L02025730
    r0 = 9
    r1 = 0
    r2 = 4
    r3 = 9
    call storage_fault_masked_register  ; @call.xl
L02025730:
    r0 = [r5+8]
    call L02025506
    r0 = 9
    r1 = 0
    r2 = 4
    r3 = r4
    call storage_fault_masked_register  ; @call.xl
    r4 = 1
L02025746:
    ifs (r6 > -1) goto L020256fa
    r0 = 88
    r1 = 64
    call L01c00f72  ; @call.xl
    if ((r4 & 0xFF) != 0) goto L0202578c
    r0 = 9
    call storage_fault_read_register  ; @call.xl
    r4 = r0 & 0xFFFFFF0F
    if (r4 > 8) goto L02025778
    r0 = 9
    r1 = 0
    r2 = 4
    r3 = 9
    call storage_fault_masked_register  ; @call.xl
L02025778:
    r0 = [r5+8]
    call L02025506
    r0 = 9
    r1 = 0
    r2 = 4
    r3 = r4
    call storage_fault_masked_register  ; @call.xl
L0202578c:
    {pc, r6-r4} = [sp++]
