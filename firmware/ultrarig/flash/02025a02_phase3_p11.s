; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 4 functions, 0x02025a02..0x02025b76

; phase3_p11_low_power_hw_unsleep_lock: 0x02025a02..0x02025ad6, module phase3-p11 (low_power_hw_unsleep_lock)
.type phase3_p11_low_power_hw_unsleep_lock,@function
phase3_p11_low_power_hw_unsleep_lock:
    [--sp] = {rets, r7-r4}
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fa24
    r0 = cnum
    r1 = [r4+r0<<2]
    r2 = r1 + 1
    [r4+r0<<2] = r2
    r5 = L01c1fa20
    if (r1 != 0) goto L02025a30
    csync
L02025a28:
    testset b[r5]
    ifeq goto L02025a28
    csync
L02025a30:
    call phase3_p11_low_power_exit_request
    r6 = L01c1fa30
    r7 = r6 + 91
    r0 = b[r7+3] (u)
    r0 += 1  ; @add.ri.u5
    b[r7+3] = r0
    call L020259de
    r1 = 1
    b[r7+0] = r1
    r1 = cnum
    r2 = [r4+r1<<2]
    r3 = r0
    r0 = r2 + -1
    [r4+r1<<2] = r0
    if (r0 != 0) goto L02025a64
    csync
    r0 = 0
    b[r5+0] = r0
L02025a64:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = icfg
    if ((r0 & 0xFF) != 0) goto L02025ad4
    call L01c00e62  ; @call.xl
    if (r0 != 0) goto L02025ad4
    r7 = 0
    goto L02025ac8
L02025a80:
    r0 = 1
    call L0203feb8  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r4+r0<<2]
    r2 = r1 + 1
    [r4+r0<<2] = r2
    if (r1 != 0) goto L02025aa8
    csync
L02025aa0:
    testset b[r5]
    ifeq goto L02025aa0
    csync
L02025aa8:
    call L020259de
    r1 = cnum
    r2 = [r4+r1<<2]
    r3 = r0
    r0 = r2 + -1
    [r4+r1<<2] = r0
    if (r0 != 0) goto L02025ac2
    csync
    b[r5+0] = r7
L02025ac2:
    call storage_coordination_irq_leave  ; @call.xl
L02025ac8:
    r0 = b[r6+89] (u)
    r0 |= r3
    if ((r0 & 0xFF) != 0) goto L02025a80
L02025ad4:
    {pc, r7-r4} = [sp++]

; phase3_p11_low_power_hw_unsleep_unlock: 0x02025ad6..0x02025b56, module phase3-p11 (low_power_hw_unsleep_unlock)
.type phase3_p11_low_power_hw_unsleep_unlock,@function
phase3_p11_low_power_hw_unsleep_unlock:
    [--sp] = {rets, r4}
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r2 = [r1+r0<<2]
    r3 = r2 + 1
    [r1+r0<<2] = r3
    r0 = L01c1fa20
    if (r2 != 0) goto L02025b04
    csync
L02025afc:
    testset b[r0]
    ifeq goto L02025afc
    csync
L02025b04:
    r2 = L01c1fa30
    r3 = b[r2+94] (u)
    if (r3 == 0) goto L02025b1c
    r3 += -1
    b[r2+94] = r3
    if ((r3 & 0xFF) == 0) goto L02025b34
L02025b1c:
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L02025b4e
    csync
    r1 = 0
    b[r0+0] = r1
    goto L02025b4e
L02025b34:
    r3 = 0
    b[r2+91] = r3
    r2 = cnum
    r4 = [r1+r2<<2]
    r4 += -1
    [r1+r2<<2] = r4
    if (r4 != 0) goto L02025b4e
    csync
    b[r0+0] = r3
L02025b4e:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]

; phase3_p11_btctler_reverse_bytes: 0x02025b56..0x02025b6e, module phase3-p11 (btctler_reverse_bytes)
.type phase3_p11_btctler_reverse_bytes,@function
phase3_p11_btctler_reverse_bytes:
    [--sp] = {rets, r4}
    r1 += r2  ; @add.rr
    r1 += -1
    r3 = 0
    goto L02025b68
L02025b60:
    r4 = b[r0+r3] (u)
    b[r1++=-1] = r4
    r3 += 1  ; @add.ri.u5
L02025b68:
    ifs (r3 < r2) goto L02025b60
    {pc, r4} = [sp++]

; phase3_p11_btctler_reverse_128: 0x02025b6e..0x02025b76, module phase3-p11 (btctler_reverse_128)
.type phase3_p11_btctler_reverse_128,@function
phase3_p11_btctler_reverse_128:
    [--sp] = rets
    r2 = 16
    call phase3_p11_btctler_reverse_bytes
    pc = [sp++]
