; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0202731a..0x020274e0: vendor code (JieLi SDK or library, not reversed), as instructions
L0202731a:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = L020357ff
    r2 = 12
    call capture_journal_compare  ; @call.xl
    r1 = r0
    r0 = 0
    if (r1 != 0) goto L02027340
    r0 = b[r4+15] (u)
    r1 = b[r4+14] (u)
    r1 <= insert(r0, p:8, l:8)
    r0 = 1
    if (r1 == 0) goto L02027340
    r0 = 0
L02027340:
    {pc, r4} = [sp++]
L02027342:
    [--sp] = {rets, r6-r4}
    r4 = r1  #
    r2 = h[r0+8] (u)
    r5 = 0
    if (r2 == 0) goto L02027370
    r1 = b[r0+7] (u)
    r6 = [r0+12]
    if ((r1 & 2) != 0) goto L02027358
    r1 = 0
    goto L02027360
L02027358:
    r0 = r6
    call L0202731a
    if (r0 == 0) goto L02027370
    r1 = 12
L02027360:
    r0 = r6
    call L0204cb74  ; @call.xl
    r5 = 1
    if (r0 != r4) {
    r5 = 0
    }
L02027370:
    r0 = r5
    {pc, r6-r4} = [sp++]
L02027374:
    [--sp] = {rets, r6-r4}
    r5 = r0
    r6 = r1  #
    r0 = h[r5+8] (u)
    r4 = 0
    if (r0 == 0) goto L020273d4
    if (r2 != 2) goto L02027398
    r1 = 0
    r0 = r6
    call L0204cb74  ; @call.xl
    r1 = r0
    r0 = r5
    call L02027342
    r4 = r0
    goto L020273d4
L02027398:
    r0 = b[r5+7] (u)
    if ((r0 & 2) != 0) goto L020273c4
    r0 = r6
    call L0202731a
    if (r0 == 0) goto L020273d4
    r1 = 12
    r0 = r6
    call L0204cb74  ; @call.xl
    r3 = r0  #
    r2 = [r5+12]
    r1 = 0
    r0 = r2
    call L0204cb74  ; @call.xl
    r4 = 1
    if (r3 != r0) goto L020273d2
    goto L020273d4
L020273c4:
    r0 = [r5+12]
    r2 = 16
    call capture_journal_compare  ; @call.xl
    r4 = 1
    if (r0 == 0) goto L020273d4
L020273d2:
    r4 = 0
L020273d4:
    r0 = r4
    {pc, r6-r4} = [sp++]
L020273d8:
    [--sp] = {rets, r5, r4}
    r5 = r1 >> 12
    r3 = r5 & 0xF
    r4 = r3 + 1
    r2 = 0
    if ((r5 & 0xF) != 0) {
    r2 = r4
    }
    if ((r1 & 1024) == 0) goto L020273f2
    r4 = b[r0+7] (u)
    if (r4 == 0) goto L02027412
L020273f2:
    if ((r1 & 2048) == 0) goto L020273fa
    r1 = b[r0+8] (u)
    if (r1 == 0) goto L02027416
L020273fa:
    r1 = 1
    if (r3 != 0) goto L02027400
    r1 = r3
L02027400:
    r3 = b[r0+6] (u)
    if (r3 != 0) goto L02027408
    r0 = 15
    if (r1 != 0) goto L02027418
L02027408:
    r0 = 12
    if (r2 <= r3) {
    r0 = 0
    }
    goto L02027418
L02027412:
    r0 = 5
    goto L02027418
L02027416:
    r0 = 8
L02027418:
    r0 = r0.b0 (u)
    {pc, r5, r4} = [sp++]
L0202741c:
    [--sp] = rets
    sp += -12
    r3 = r0
    r1 = L01c21c78
    r0 = sp + 0
    call L0204cc32  ; @call.xl
L02027430:
    r0 = sp + 0
    call L0204cb98  ; @call.xl
    if (r0 == 0) goto L02027450
    r0 = sp + 0
    call L0204cbb4  ; @call.xl
    r1 = h[r0+4] (u)
    if (r1 > r3) goto L02027430
    r1 = h[r0+6] (u)
    if (r1 < r3) goto L02027430
    goto L02027452
L02027450:
    r0 = 0
L02027452:
    sp += 12
    pc = [sp++]
L02027456:
    [--sp] = rets
    call L0202741c
    r2 = r0 + 8
    r1 = L01c21c6c
    if (r0 == 0) goto L02027466
    r1 = r2
L02027466:
    r0 = [r1+0]
    pc = [sp++]
L0202746a:
    [--sp] = {rets, r6-r4}
    sp += -4
    r5_r4 = r1_r0
    r0 = b[r4+7] (u)
    if ((r0 & 1) == 0) goto L0202748c
    r0 = h[r4+8] (u)
    call L02027456
    r6 = r0
    if (r6 == 0) goto L0202748c
    r3_r2 = 0  #
    r1 = h[r4+8] (u)
    r0 = 0
    r0 = r5  #
    [sp] = r0
    call r6
    h[r4+16] = r0
L0202748c:
    sp += 4
    {pc, r6-r4} = [sp++]
L02027490:
    [--sp] = {rets, r8-r4}
    sp += -4
    r5 = r0
    r6 = r3  #
    r0 = b[r5+7] (u)
    r8 = r2
    r7 = r1
    if ((r0 & 1) != 0) goto L020274be
    r0 = h[r5+16] (u)
    r0 = r0 - r7
    r1 = r0.l (u)
    if (r1 <= r6) {
    r6 = r0
    }
    r5 = r6.l (u)  #
    r1 = [r5+20]
    r0 = r8
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    goto L020274da
L020274be:
    r0 = h[++r5=8] (u)
    call L02027456
    r4 = r0
    if (r4 == 0) goto L020274d8
    r2 = r7  #
    r0 = [sp+28]
    r3 = r8  #
    r1 = h[r5+0] (u)
    [sp] = r6
    call r4
    r5 = r0
    goto L020274da
L020274d8:
    r5 = 0
L020274da:
    r0 = r5
    sp += 4
    {pc, r8-r4} = [sp++]
