; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 1 function, 0x01c042b0..0x01c04410

; phase3_p3_low_power_process_wait: 0x01c042b0..0x01c04410, module phase3-p3 (low_power_process_wait)
.type phase3_p3_low_power_process_wait,@function
phase3_p3_low_power_process_wait:
    [--sp] = {rets, r10-r4}
    csync
    r1 = L01c1fc54
    r2 = cnum
    r5 = [r1+r2<<2]
    r1 = cnum
    r1 = r1.b0 (u)
    r8 = L01c3740c
    r6 = r1 + r8
    r1 = L01c3748d
    r10 = b[r1+0] (u)
    r4 = r0  #
    r1 = b[r6+2] (u)
    if (r1 == 0) goto L01c0440e
    r0 = 0
    call sdk___hw_nv_timer_is_runnig
    if (r0 == 0) goto L01c042fe
    r0 = 2
    call L0201dbe2  ; @call.xl
    r1 = L01c1fa30
    [r1+84] = r0
L01c042fe:
    r7 = L01c1fa24
    r9 = L01c1fa20
    if (r10 == 0) goto L01c04338
    [r8+32] = r4
    r0 = 0
    b[r6+2] = r0
    csync
    call storage_coordination_irq_enter
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L01c043b2
    csync
L01c0432e:
    testset b[r9]
    ifeq goto L01c0432e
    csync
    goto L01c043b2
L01c04338:
    r0 = icfg
    if ((r0 & 0xFF) == 0) goto L01c0437c
    call storage_coordination_irq_enter
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L01c04360
    csync
L01c04358:
    testset b[r9]
    ifeq goto L01c04358
    csync
L01c04360:
    r0 = r4
    call phase3_p4_low_power_process  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L01c043d2
    csync
    goto L01c043cc
L01c0437c:
    [r8+32] = r4
    r3 = 0
    b[r6+2] = r3
    csync
    r4 = 0
    goto L01c043a6
L01c0438a:
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L01c043a0
    csync
    b[r9+0] = r3
L01c043a0:
    call storage_coordination_irq_leave
    r4 += 1  ; @add.ri.u5
L01c043a6:
    ifs (r4 < r5) goto L01c0438a
    goto L01c043b2
L01c043ac:
    csync
    nop
    nop
L01c043b2:
    r0 = b[r6+4] (u)
    if (r0 != 0) goto L01c043ac
    if (r10 == 0) goto L01c043d8
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L01c043d2
    csync
L01c043cc:
    r0 = 0
    b[r9+0] = r0
L01c043d2:
    call storage_coordination_irq_leave
    goto L01c04400
L01c043d8:
    r2 = 0
    goto L01c043fc
L01c043dc:
    call storage_coordination_irq_enter
    r0 = cnum
    r1 = [r7+r0<<2]
    r3 = r1 + 1
    [r7+r0<<2] = r3
    if (r1 != 0) goto L01c043fa
    csync
L01c043f2:
    testset b[r9]
    ifeq goto L01c043f2
    csync
L01c043fa:
    r2 += 1  ; @add.ri.u5
L01c043fc:
    ifs (r2 < r5) goto L01c043dc
L01c04400:
    r0 = b[r8+8] (u)
    if ((r0 & 0x2) != 0) {
    call L02025626  ; @call.xl
    }
L01c0440e:
    {pc, r10-r4} = [sp++]
