; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201ef24..0x0201f12e: vendor code (JieLi SDK or library, not reversed), as instructions
L0201ef24:
    [--sp] = {rets, r5, r4}
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r5 = L01c26890
    r0 = r5 + 70
L0201ef3a:
    testset b[r0]
    ifeq goto L0201ef3a
    csync
    r1_r0 = d[r3+0]
    call phase3_p13_list_del_entry
    r0 = r3
    call L0201d1f0
    r4 = r0
    csync
    r0 = 0
    b[r5+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 != 0) goto L0201ef6a
    r0 = r3
    call L0203d218  ; @call.xl
L0201ef6a:
    {pc, r5, r4} = [sp++]
L0201ef6c:
    sp += -16
    r12 = sp + 0
    r9 = L01c26890
    r4 = L01c1f180
    r10 = 0
    r13 = 1342177270
    r14 = 1
    r8 = L02035d46  ; "app_core"
L0201ef90:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r15 = r9 + 70
L0201ef9c:
    testset b[r15]
    ifeq goto L0201ef9c
    csync
    r5 = [r4+172]
    goto L0201f0c8
L0201efaa:
    r11 = r6 + 24  #
    r5 = [r6+0]
    r0 = b[r11+3] (u)
    if ((r0 & 1) != 0) goto L0201f03e
    call L0204180e  ; @call.xl
    r1 = [r6+20]
    r0 += 1  ; @add.ri.u5
    r0 = r0 >> 1
    r2 = r1 - r0
    if (r1 <= r0) goto L0201efe2
    if (r2 <= 1073741824) goto L0201efe2
    r2 = 2952790026
    r2 += r1  ; @add.rr
    if (r1 <= r13) {
    r2 = r0
    }
    r1 = r2  #
    [r6+20] = r2
L0201efe2:
    ifs (r0 < r1) goto L0201f0c8
    b[r11+6] = r14
    csync
    b[r9+70] = r10
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r6+8]
    [sp] = r0
    [r12+4] = r14
    r0 = [r6+12]
    [r12+8] = r0
    r1 = h[r6+28] (u)
    r1 = r1 | 0x300000  #
    r0 = [r6+16]
    r3 = sp + 0
    r2 = 3
    call L02040bae  ; @call.xl
    if (r0 == 14) goto L0201f076
    if (r0 == 4) goto L0201f076
    if (r0 != 0) goto L0201f0aa
    b[r11+6] = r10
    r0 = b[r11+3] (u)
    if ((r0 & 2) != 0) goto L0201f0b2
    call L02041866  ; @call.xl
    r1 = [r6+24]
    r1 = r1 & 0xFFFFFF
    r0 += r1  ; @add.rr
    [r6+20] = r0
    goto L0201f0b8
L0201f03e:
    r0 = r5  #
    r1 = [r6+4]
    call phase3_p13_list_del_entry
    r0 = r6
    call L0201d1f0
    if (r0 != 0) goto L0201f0c8
    csync
    r7 = r9
    b[++r7=70] = r10
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r6
    call L0203d218  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201f06c:
    testset b[r7]
    ifeq goto L0201f06c
    csync
    goto L0201f0c8
L0201f076:
    [r6+16] = r8
    r0 = h[r6+28] (u)
    r1 = r0 | 0x300000
    r3 = sp + 0
    r2 = 3
    r0 = r8
    call L02040bae  ; @call.xl
    b[r11+6] = r10
    if (r0 != 0) goto L0201f0b8
    r0 = [r6+24]
    if ((r0 & 33554432) != 0) goto L0201f0b2
    r0 = r0 & 0xFFFFFF  #
    r1 = [r4+24]
    r2 = 10
    r0 = r0 / r2 (u)
    r0 += r1  ; @add.rr
    [r6+20] = r0
    goto L0201f0b8
L0201f0aa:
    b[r11+6] = r10
    if (r0 == 21) goto L0201f0b8
L0201f0b2:
    r0 = r6
    call L0201ef24
L0201f0b8:
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201f0c0:
    testset b[r15]
    ifeq goto L0201f0c0
    csync
L0201f0c8:
    r0 = r4 + 172
    r6 = r5
    if (r6 != r0) goto L0201efaa
    r5 = -1
    r1 = r0
    goto L0201f0de
L0201f0d8:
    r2 = [r1+20]
    r5 = umin(r5, r2)
L0201f0de:
    r1 = [r1+0]
    if (r1 != r0) goto L0201f0d8
    call phase3_p13_get_min_precesion
    call phase3_p13_timer1_run
    csync
    b[r9+70] = r10
    call storage_coordination_irq_leave  ; @call.xl
    if (r5 == -1) goto L0201f120
    call L02041866  ; @call.xl
    r0 = r5 - r0
    if (r0 < 10) {  ; @if.lt.ri.s12
    r0 = r9 + 3908
    r1 = 2
    } else {
    r1 = 10
    r1 = r0 / r1 (u)
    r0 = r9 + 3908
    }
    call L02040d34  ; @call.xl
    goto L0201ef90
L0201f120:
    r0 = r9 + 3908
    r1 = 0
    call L02040d34  ; @call.xl
    goto L0201ef90
