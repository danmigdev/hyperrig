; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02026a0c..0x02026b38: vendor code (JieLi SDK or library, not reversed), as instructions
L02026a0c:
    [--sp] = {rets, r10-r4}
    r2 = r0
    if (r2 == 0) goto L02026aa8
    r10 = r2 + -32  #
    r0 = [r2+-16]
    r0 = r10 - r0
    r8 = r0 + 20
    call storage_coordination_irq_enter  ; @call.xl
    csync
L02026a28:
    testset b[r8]
    ifeq goto L02026a28
    csync
    r0 = rets
    r0 = [r2+-32]
    r1 = 305419896
    if (r0 != r1) goto L02026b2c
    r1 = r1 + 0x11111111  #
    r0 = [r2+-8]
    if (r0 != r1) goto L02026b2c
    r0 = [r2+-16]
    r6 = r10 - r0
    r0 = [r6+0]
    r1 = 2271560481
    if (r0 != r1) goto L02026b2c
    r1 = r1 + 0x11111111  #
    r0 = [r6+36]
    if (r0 != r1) goto L02026b2c
    r0 = b[r2+-12] (u)
    r9 = [r2+-20]
    r1 = h[r6+22] (u)
    r3 = b[r6+21] (u)
    r0 += -1
    r5 = 131071
    r7 = r3 + r5  #
    b[r2+-12] = r0
    r4 = r1 + 32
    r1 = r7 & r4
    r1 = r1 - r3
    r3 = 0
    r5 = 0
    if ((r7 & r4) != 0) {
    r5 = r1
    }
    if ((r0 & 0xFF) == 0) goto L02026aae
L02026a98:
    csync
    r0 = 0
    b[r8+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    goto L02026aaa
L02026aa8:
    r3 = 0
L02026aaa:
    r0 = r3
    {pc, r10-r4} = [sp++]
L02026aae:
    r0 = 19088743
    r4 = r10 + r5  #
    [r2+-32] = r0
    r1_r0 = d[r2+-28]
    call phase3_p10_list_del_pair
    [r4+8] = r9
    r0 = [r6+12]
    r1 = r6 + 12
    goto L02026ae6
L02026acc:
    if (r0 <= r6) goto L02026a98
    r2 = [r6+24]
    r2 += r6  ; @add.rr
    if (r0 > r2) goto L02026a98
    if (r0 > r4) goto L02026af2
    r2 = [r0+8]
    r2 += r0  ; @add.rr
    if (r2 > r4) goto L02026a98
    r0 = [r0+0]
L02026ae6:
    if (r0 != r1) goto L02026acc
    r0 = r4
    call phase3_p10_list_add_tail_a
    r1 = [r4+4]
    goto L02026afc
L02026af2:
    r1 = [r0+4]
    [r0+4] = r4
    d[r4+0] = r1_r0
    [r1+0] = r4
L02026afc:
    r2 = [r1+8]
    r3 = r2 + r1  #
    r0 = [r4+0]
    if (r3 != r4) goto L02026b12
    r3 = [r4+8]
    r2 += r3  ; @add.rr
    [r1+8] = r2
    call phase3_p10_list_del_pair
    r4 = r1
L02026b12:
    r1 = [r4+8]
    r2 = r4 + r1
    r3 = 1
    if (r2 != r0) goto L02026a98
    r2 = [r0+8]
    r1 += r2  ; @add.rr
    [r4+8] = r1
    r1_r0 = d[r0+0]
    call phase3_p10_list_del_pair
    goto L02026a98
L02026b2c:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02026b36:
    goto L02026b36
