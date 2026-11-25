; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 2 functions, 0x0201ec16..0x0201ee48

; phase3_p12_cbuf_read: 0x0201ec16..0x0201ecb4, module phase3-p12 (cbuf_read)
.type phase3_p12_cbuf_read,@function
phase3_p12_cbuf_read:
    [--sp] = {rets, r10-r4}
    r4 = r2
    r8 = r1
    r5 = r0
    r7 = 0
    if (r5 == 0) goto L0201ecb0
    if (r4 == 0) goto L0201ecb0
    r2 = [r5+24]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r10 = r5 + 32
L0201ec32:
    testset b[r10]
    ifeq goto L0201ec32
    csync
    r0 = [r5+4]
    r7 = [r5+8]
    if (r7 >= r0) {
    r7 = [r5+0]
    [r5+8] = r7
    }
    if (r2 >= r4) goto L0201ec66
    csync
    r7 = 0
    b[r10+0] = r7
    call storage_coordination_irq_leave  ; @call.xl
    r1 = 0
    r0 = r8
    r2 = r4
    call effect_enable_memset  ; @call.xl
    goto L0201ecb0
L0201ec66:
    r0 = r0 - r7
    r6 = umin(r0, r4)
    r0 = r8
    r1 = r7
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r9 = r4 - r6
    if (r9 == 0) goto L0201ec94
    r0 = r8 + r6  #
    r1 = [r5+0]
    r2 = r9
    call effect_parameter_support_memmove  ; @call.xl
    r0 = [r5+0]
    r0 += r9
    goto L0201ec96
L0201ec94:
    r0 = r7 + r6
L0201ec96:
    [r5+24] -= r4
    [r5+20] -= r4
    [r5+8] = r0
    csync
    r0 = 0
    b[r10+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r7 = r4
L0201ecb0:
    r0 = r7
    {pc, r10-r4} = [sp++]

; phase3_p12_sys_event_task: 0x0201ecb4..0x0201ee48, module phase3-p12 (sys_event_task)
.type phase3_p12_sys_event_task,@function
phase3_p12_sys_event_task:
    sp += -24
    r11 = sp + 0
    r7 = L01c1f180
    r8 = 0
    r15 = L020558dc
    r6 = L020558f4
    r12 = L01c26890
    r13 = 514
L0201ecd8:
    r0 = [r7+332]
    r4 = r7 + 504
    r2 = 4
    r1 = r4
    call phase3_p12_cbuf_read
    if (r0 == 0) goto L0201ee2e
    r0 = 507
    r2 = b[r7+r0] (u)
    r0 = [r7+332]
    r1 = r7 + 508
    call phase3_p12_cbuf_read
    r5 = r15
    goto L0201ed04
L0201ed00:
    r0 = r5 + 4
    r5 = r0 + 8
L0201ed04:
    if (r5 >= r6) goto L0201ed22
    r1 = [r5+4]
    if (r1 == 0) goto L0201ed00
    r0 = h[r5+0] (u)
    r2 = h[r7+504] (u)
    r0 &= r2
    r0 = r0.l (u)
    if (r0 == 0) goto L0201ed00
    r0 = r4
    call r1
    if (r0 != -22) goto L0201ed00
    goto L0201ecd8
L0201ed22:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r14 = r12 + 68
L0201ed2e:
    testset b[r14]
    ifeq goto L0201ed2e
    csync
    r10 = [r7+496]
    goto L0201edf6
L0201ed3c:
    r0 = b[r9+20] (u)
    r10 = [r9+0]
    if (r0 != 0) goto L0201edf6
    r0 = [r9+12]
    if (r0 == 0) goto L0201edf6
    r0 = h[r9+22] (u)
    r1 = h[r7+504] (u)
    r0 &= r1
    r0 = r0.l (u)
    if (r0 == 0) goto L0201edf6
    r0 = [r9+24]
    if (r0 == 0) goto L0201ed6c
    r1 = 506
    r1 = b[r7+r1] (u)
    if (r0 != r1) goto L0201edf6
L0201ed6c:
    csync
    b[r12+68] = r8
    call storage_coordination_irq_leave  ; @call.xl
    r5 = r7 + 416
    r0 = r5
    call L0203fdba  ; @call.xl
    r0 = [r9+12]
    [sp] = r0
    [r11+4] = r13
    [r11+8] = r4
    r0 = [r9+8]
    [r11+12] = r0
    [r11+16] = r5
    goto L0201eda8
L0201eda0:
    r0 = 2
    call L0203feb8  ; @call.xl
L0201eda8:
    r0 = b[r9+20] (u)
    if (r0 != 0) goto L0201eddc
    r0 = [r9+16]
    r3 = sp + 0
    r1 = 0x300000
    r2 = 5
    call L02040bae  ; @call.xl
    if (r0 == 21) goto L0201eda0
    if (r0 != 0) goto L0201eddc
    r0 = h[r7+330] (u)
    r1 = 10
    r1 = r0 / r1 (u)
    r0 = r5
    call L02040d34  ; @call.xl
    if (r0 == 11) goto L0201ee3c
L0201eddc:
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201ede4:
    testset b[r14]
    ifeq goto L0201ede4
    csync
    r0 = [r9+0]
    if (r0 != r10) {
    r10 = r0
    }
L0201edf6:
    r0 = r7 + 496
    r9 = r10
    if (r9 != r0) goto L0201ed3c
    csync
    b[r12+68] = r8
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r15
    goto L0201ee28
L0201ee10:
    r1 = [r0+8]
    r5 = r0 + 8
    if (r1 == 0) goto L0201ee26
    r0 = h[r0+0] (u)
    r2 = h[r7+504] (u)
    r0 &= r2
    r0 = r0.l (u)
    if (r0 == 0) goto L0201ee26
    r0 = r4
    call r1
L0201ee26:
    r0 = r5 + 4
L0201ee28:
    if (r0 < r6) goto L0201ee10
    goto L0201ecd8
L0201ee2e:
    r0 = r7 + 336
    r1 = 0
    call L02040d34  ; @call.xl
    goto L0201ecd8
L0201ee3c:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0201ee46:
    goto L0201ee46
