; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201c816..0x0201cada: vendor code (JieLi SDK or library, not reversed), as instructions
L0201c816:
    [--sp] = {rets, r12-r4}
    r8 = r3
    r10 = r2
    r11 = r1
    r6 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r9 = L01c26890
    r12 = r9 + 70
L0201c832:
    testset b[r12]
    ifeq goto L0201c832
    r7 = [sp+40]
    csync
    r0 = 0
    r5 = L01c25cf8
    goto L0201c850
L0201c846:
    r1 = b[r5+31] (u)
    if (r1 == 0) goto L0201c870
    r5 += 32
    r0 += 1  ; @add.ri.u5
L0201c850:
    if (r0 <= 14) goto L0201c846
    csync
    r4 = 0
    b[r9+70] = r4
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 32
    call L0203d940  ; @call.xl
    r5 = r0
    if (r5 != 0) goto L0201c884
    goto L0201c95a
L0201c870:
    r0 = 1
    b[r5+31] = r0
    csync
    r0 = 0
    b[r9+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
L0201c884:
    d[r5+8] = r11_r10
    r0 = [r5+24]
    r1 = 0
    b[r5+30] = r1
    r1 = r8 & 0xFFFFFF
    r2 = r7 << 25
    r2 = r2 & 0x2000000
    r1 |= r2
    r0 = r0 & 0xFC000000
    r0 |= r1
    [r5+24] = r0
    call L02041866  ; @call.xl
    r0 += r8
    [r5+20] = r0
    if (r6 == 0) goto L0201c8b8
    r1 = r5
    [++r1=16] = r6
    goto L0201c8c6
L0201c8b8:
    call L0204178c  ; @call.xl
    r1 = r5
    [++r1=16] = r0
    if (r0 == 0) goto L0201c8d0
L0201c8c6:
    r0 = icfg
    if ((r0 & 0xFF) == 0) goto L0201c8d8
L0201c8d0:
    r0 = L02035d46  ; "app_core"
    [r1+0] = r0
L0201c8d8:
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201c8e0:
    testset b[r12]
    ifeq goto L0201c8e0
    csync
    call phase3_p13_get_min_precesion
    r1 = h[r9+86] (u)
    r3 = r0
    r0 = r1 + 1
    h[r9+86] = r0
    r1 = r0.l (u)  #
    h[r5+28] = r0
    if (r1 != 0) goto L0201c906
    r0 = 1
    h[r5+28] = r0
    h[r9+86] = r0
L0201c906:
    r1 = L01c1f22c
    r4 = r0
    goto L0201c914
L0201c910:
    r4 += 1  ; @add.ri.u5
    h[r5+28] = r4
L0201c914:
    r2 = r1
L0201c916:
    r2 = [r2+0]
    if (r2 == r1) goto L0201c926
    r7 = r4.l (u)  #
    r6 = h[r2+28] (u)
    if (r7 != r6) goto L0201c916
    goto L0201c910
L0201c926:
    r2 = r4.l (u)
    if (r2 == 0) goto L0201c910
    r0 = r0.l (u)
    if (r2 != r0) {
    h[r9+86] = r4
    }
    r0 = r5
    call phase3_p13_list_add_tail
    if (r3 > r8) {
    call phase3_p13_timer1_run
    }
    csync
    r0 = 0
    b[r9+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r9 + 3908
    call L020403ee  ; @call.xl
L0201c95a:
    r0 = r4.l (u)
    {pc, r12-r4} = [sp++]
L0201c95e:
    [--sp] = {rets, r6-r4}
    sp += -4
    r4 = r2
    r5 = r1
    r6 = r0
    call L0204178c  ; @call.xl
    r1 = 0
    r1 = r6  #
    [sp] = r1
    r2 = r5
    r3 = r4
    call L0201c816
    sp += 4
    {pc, r6-r4} = [sp++]
L0201c980:
    [--sp] = {rets, r8-r4}
    r3 = r1
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r8 = L01c2683c
L0201c994:
    testset b[r8]
    ifeq goto L0201c994
    csync
    r1 = b[r4+13] (u)
    r5 = b[r4+12] (u)
    r5 <= insert(r1, p:8, l:8)  #
    r6 = b[r4+14] (u)
    r5 <= insert(r6, p:16, l:8)  #
    r7 = b[r4+15] (u)
    r5 <= insert(r7, p:24, l:8)
    r1 = 266752
    [r1+8] = r5
    r5 = b[r4+9] (u)
    r6 = b[r4+8] (u)
    r6 <= insert(r5, p:8, l:8)  #
    r7 = b[r4+10] (u)
    r6 <= insert(r7, p:16, l:8)  #
    r0 = b[r4+11] (u)
    r6 <= insert(r0, p:24, l:8)
    [r1+8] = r6
    r0 = b[r4+5] (u)
    r5 = b[r4+4] (u)
    r5 <= insert(r0, p:8, l:8)  #
    r6 = b[r4+6] (u)
    r5 <= insert(r6, p:16, l:8)  #
    r7 = b[r4+7] (u)
    r5 <= insert(r7, p:24, l:8)
    [r1+8] = r5
    r0 = b[r4+1] (u)
    r5 = b[r4+0] (u)
    r5 <= insert(r0, p:8, l:8)  #
    r6 = b[r4+2] (u)
    r5 <= insert(r6, p:16, l:8)  #
    r4 = b[r4+3] (u)
    r5 <= insert(r4, p:24, l:8)
    [r1+8] = r5
    [r1+0] &= 0xFFFFFFBF
    [r1+0] |= 0x10
L0201ca02:
    r0 = [r1+0]
    if ((r0 & 32) == 0) goto L0201ca02
    [r1+0] |= 0x2000
    r0 = b[r3+13] (u)
    r4 = b[r3+12] (u)
    r4 <= insert(r0, p:8, l:8)  #
    r5 = b[r3+14] (u)
    r4 <= insert(r5, p:16, l:8)  #
    r6 = b[r3+15] (u)
    r4 <= insert(r6, p:24, l:8)
    [r1+4] = r4
    r0 = b[r3+9] (u)
    r4 = b[r3+8] (u)
    r4 <= insert(r0, p:8, l:8)  #
    r5 = b[r3+10] (u)
    r4 <= insert(r5, p:16, l:8)  #
    r6 = b[r3+11] (u)
    r4 <= insert(r6, p:24, l:8)
    [r1+4] = r4
    r0 = b[r3+5] (u)
    r4 = b[r3+4] (u)
    r4 <= insert(r0, p:8, l:8)  #
    r5 = b[r3+6] (u)
    r4 <= insert(r5, p:16, l:8)  #
    r6 = b[r3+7] (u)
    r4 <= insert(r6, p:24, l:8)
    [r1+4] = r4
    r0 = b[r3+1] (u)
    r4 = b[r3+0] (u)
    r4 <= insert(r0, p:8, l:8)  #
    r5 = b[r3+2] (u)
    r4 <= insert(r5, p:16, l:8)  #
    r3 = b[r3+3] (u)
    r4 <= insert(r3, p:24, l:8)
    [r1+4] = r4
    [r1+0] |= 0x1
L0201ca68:
    r0 = [r1+0]
    if ((r0 & 4) == 0) goto L0201ca68
    [r1+0] |= 0x1000
    r0 = [r1+12]
    b[r2+0] = r0
    r0 = [r1+12]
    r0 = r0 >> 8
    b[r2+1] = r0
    r0 = [r1+12]
    r0 = r0 >> 16
    b[r2+2] = r0
    r0 = [r1+12]
    r0 = r0 >> 24
    b[r2+3] = r0
    r0 = [r1+16]
    b[r2+4] = r0
    r0 = [r1+16]
    r0 = r0 >> 8
    b[r2+5] = r0
    r0 = [r1+16]
    r0 = r0 >> 16
    b[r2+6] = r0
    r0 = [r1+16]
    r0 = r0 >> 24
    b[r2+7] = r0
    r0 = [r1+20]
    b[r2+8] = r0
    r0 = [r1+20]
    r0 = r0 >> 8
    b[r2+9] = r0
    r0 = [r1+20]
    r0 = r0 >> 16
    b[r2+10] = r0
    r0 = [r1+20]
    r0 = r0 >> 24
    b[r2+11] = r0
    r0 = [r1+24]
    b[r2+12] = r0
    r0 = [r1+24]
    r0 = r0 >> 8
    b[r2+13] = r0
    r0 = [r1+24]
    r0 = r0 >> 16
    b[r2+14] = r0
    r0 = [r1+24]
    r0 = r0 >> 24
    b[r2+15] = r0
    csync
    r0 = 0
    b[r8+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r8-r4} = [sp++]
