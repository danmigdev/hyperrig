; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 2 functions, 0x02026826..0x02026906

; phase3_p10_list_del_pair: 0x02026826..0x0202682c, module phase3-p10 (list_del_pair)
.type phase3_p10_list_del_pair,@function
phase3_p10_list_del_pair:
    [r0+4] = r1
    [r1+0] = r0
    rts

; phase3_p10_lbuf_alloc: 0x0202682c..0x02026906, module phase3-p10 (lbuf_alloc)
.type phase3_p10_lbuf_alloc,@function
phase3_p10_lbuf_alloc:
    [--sp] = {rets, r8-r4}
    r3_r2 = r1_r0
    r6 = b[r2+21] (u)
    r4 = h[r2+22] (u)
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r8 = r2 + 20
L02026842:
    testset b[r8]
    ifeq goto L02026842
    r7 = r4 + 32
    r0 = r6 + -1
    r1 = r0 & r7
    r5 = r6 - r1
    r1 = 0
    r4 = 0
    if ((r0 & r7) != 0) {
    r4 = r5
    }
    r3 += r7  ; @add.rr
    r3 += r4  ; @add.rr
    r5 = r3 & r0
    r5 = r6 - r5
    r7 = 0
    if ((r3 & r0) != 0) {
    r7 = r5
    }
    csync
    r0 = r7 + r3  #
    r6 = [r2+12]
    r3 = r2 + 12
    goto L02026894
L0202687c:
    r7 = [r6+8]
    if (r7 < r0) goto L02026892
    if (r1 == 0) goto L0202688a
    r5 = [r1+8]
    if (r5 <= r7) goto L0202688c
L0202688a:
    r1 = r6
L0202688c:
    r5 = [r2+28]
    if (r6 > r5) goto L0202689a
L02026892:
    r6 = [r6+0]
L02026894:
    if (r6 != r3) goto L0202687c
    r6 = 0
L0202689a:
    if (r6 != 0) goto L0202689e
    r6 = r1
L0202689e:
    r7 = 0
    r3 = 0
    if (r6 == 0) goto L020268f6
    [r2+28] = r6
    r3 = [r6+8]
    r1 = r0 + 12
    if (r3 <= r1) goto L020268c2
    r1 = r6 + r0
    r3 = r3 - r0
    [r1+8] = r3
    {r5, r3} = [r6+]
    [r3+4] = r1
    [r1+] = {r5, r3}
    [r5+0] = r1
    goto L020268ca
L020268c2:
    r1_r0 = d[r6+0]
    call phase3_p10_list_del_pair
    r0 = r3
L020268ca:
    r1 = r6 + r4
    r0 = r1 - r2  #
    [r1+12] = r0
    [r1+16] = r0
    r0 = 0
    b[r1+21] = r0
    r0 = 1
    b[r1+20] = r0
    r0 = 305419896
    r0 = r0 + 0x11111111  #
    [r1+0] = r0
    [r1+24] = r0
    r0 = r1 + 4
    r3 = r1 + 32  #
    [r1+4] = r0
    [r1+8] = r0
L020268f6:
    csync
    b[r8+0] = r7
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r8-r4} = [sp++]
