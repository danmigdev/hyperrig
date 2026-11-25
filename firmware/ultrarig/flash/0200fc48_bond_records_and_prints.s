; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; bond_records_and_prints: 6 functions, 0x0200fc48..0x0200ff48

; bond_records_and_prints_bond_lookup: 0x0200fc48..0x0200fc98, module bond-records-and-prints (bond_lookup)
.type bond_records_and_prints_bond_lookup,@function
bond_records_and_prints_bond_lookup:
    [--sp] = {rets, r5, r4}
    r4 = L01c26890
    if (r0 == 113) goto L0200fc66
    if (r0 != 109) goto L0200fc74
    r0 = r4 + 6596
    [r1+0] = r0
    [r2+0] = 0x22
    r0 = 1
    goto L0200fc92
L0200fc66:
    r0 = r4 + 6630
    [r1+0] = r0
    [r2+0] = 0xE
    r0 = 2
    goto L0200fc92
L0200fc74:
    r5 = r0 + -114
    r0 = -1
    if (r5 > 4) goto L0200fc96
    r0 = r5 * 0x34
    r0 += r4  ; @add.rr
    r0 = r0 + 6644
    [r1+0] = r0
    [r2+0] = 0x34
    r0 = 4
    r0 <<= r5
L0200fc92:
    h[r3+0] = r0
    r0 = 0
L0200fc96:
    {pc, r5, r4} = [sp++]

; bond_records_and_prints_bond_read: 0x0200fc98..0x0200fd18, module bond-records-and-prints (bond_read)
.type bond_records_and_prints_bond_read,@function
bond_records_and_prints_bond_read:
    [--sp] = {rets, r8-r4}
    sp += -12
    r5 = 1228
    r7 = L01c26890
    r3 = b[r7+r5] (u)
    r4 = r2
    r8 = r1
    r6 = r0
    if (r3 != 0) goto L0200fcbc
    call mode_and_settings_slots_clear
    r0 = 1
    b[r7+r5] = r0
L0200fcbc:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r7 + 58
L0200fcc8:
    testset b[r0]
    ifeq goto L0200fcc8
    csync
    r1 = sp + 8
    r2 = sp + 4
    r3 = sp + 2
    r0 = r6
    call bond_records_and_prints_bond_lookup
    r3 = -1
    if (r0 != 0) goto L0200fd04
    r0 = [sp+4]
    if (r0 != r4) goto L0200fd04
    r0 = 3296
    r0 = h[r7+r0<<1] (u)
    r1 = h[sp+2] (u)
    r0 &= r1
    r0 = r0.l (u)
    if (r0 == 0) goto L0200fd04
    r0 = r8  #
    r1 = [sp+8]
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r3 = r4
L0200fd04:
    csync
    r0 = 0
    b[r7+58] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    sp += 12
    {pc, r8-r4} = [sp++]

; bond_records_and_prints_bond_write: 0x0200fd18..0x0200fdca, module bond-records-and-prints (bond_write)
.type bond_records_and_prints_bond_write,@function
bond_records_and_prints_bond_write:
    [--sp] = {rets, r9-r4}
    sp += -12
    r5 = 1228
    r7 = L01c26890
    r3 = b[r7+r5] (u)
    r4 = r2
    r9 = r1
    r6 = r0
    if (r3 != 0) goto L0200fd3c
    call mode_and_settings_slots_clear
    r0 = 1
    b[r7+r5] = r0
L0200fd3c:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r7 + 58
L0200fd48:
    testset b[r0]
    ifeq goto L0200fd48
    csync
    r1 = sp + 8
    r2 = sp + 4
    r3 = sp + 2
    r0 = r6
    call bond_records_and_prints_bond_lookup
    r1 = -1
    if (r0 != 0) goto L0200fdb4
    r0 = [sp+4]
    if (r0 != r4) goto L0200fdb4
    r8 = 3296  #
    r6 = [sp+8]
    r0 = h[r7+r8<<1] (u)
    r5 = h[sp+2] (u)
    r0 &= r5
    r0 = r0.l (u)
    if (r0 == 0) goto L0200fd88
    r0 = r6
    r1 = r9
    r2 = r4
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0200fdb2
L0200fd88:
    r0 = r6
    r1 = r9
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r0 = h[r7+r8<<1] (u)
    r0 |= r5
    h[r7+r8<<1] = r0
    r0 = L01c1f180
    r1 = r7 + 1232  #
    r0 = [r0+24]
    [r1+0] = r0
    [r1+4] += 1  ; @rmw.add.s12
    goto L0200fdb6
L0200fdb2:
    r1 = r4
L0200fdb4:
    r4 = r1
L0200fdb6:
    csync
    r0 = 0
    b[r7+58] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r4
    sp += 12
    {pc, r9-r4} = [sp++]

; bond_records_and_prints_bond_reset: 0x0200fdca..0x0200fefa, module bond-records-and-prints (bond_reset)
.type bond_records_and_prints_bond_reset,@function
bond_records_and_prints_bond_reset:
    [--sp] = {rets, r10-r4}
    r6 = L01c26890
    r0 = b[r6+60] (u)
    if (r0 == 0) goto L0200feec
    r0 = 1
    b[r6+61] = r0
    r1 = 1
    r2 = 0
    r4 = 0
    call L0204c744  ; @call.xl
    r0 = h[r6+82] (u)
    if (r0 == 0) goto L0200fdf6
    call console_helpers_ble_drop
L0200fdf6:
    r8 = L01c1f180
    r9 = 150
    r10 = 65535
    r7 = 0
    goto L0200fe4c
L0200fe0a:
    r0 = 1
    call L0203feb8  ; @call.xl
    r0 = [r8+24]
    [r6+204] = r0
    r5 = h[r6+82] (u)
    if (r7 < 5) goto L0200fe24
    if (r5 == 0) goto L0200fe50
L0200fe24:
    r0 = r7 / r9 (u)
    r0 = r0 * 0x96
    r0 = r7 - r0
    if (r0 != 149) goto L0200fe3a
    if (r5 == 0) goto L0200fe3a
    r0 = r5
    call console_helpers_ble_drop
L0200fe3a:
    r0 = 1
    if ((r5 & r10) == 0) {
    r0 = r4
    }
    if (r7 != 599) {
    r0 = r4
    }
    r7 += 1  ; @add.ri.u5
    r4 = r0
L0200fe4c:
    if (r7 <= 599) goto L0200fe0a
L0200fe50:
    call L0204cb1e  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r6 + 58
L0200fe62:
    testset b[r0]
    ifeq goto L0200fe62
    csync
    r0 = 0
    r1 = -1
    goto L0200fe7c
L0200fe70:
    r2 = r0 + r6
    r2 = r2 + 6644
    rep 26 {
    h[r2++=2] = r1
    }
    r0 += 52
L0200fe7c:
    if (r0 != 260) goto L0200fe70
    r0 = 3296
    r1 = h[r6+r0<<1] (u)
    r1 = r1 & 0x3
    h[r6+r0<<1] = r1
    r0 = r6 + 6904
    r1 = -1
    rep 32 {
    h[r0++=2] = r1
    }
    r0 = 6968
    r5 = 0
    b[r6+r0] = r5
    r0 += 1  ; @add.ri.u5
    b[r6+r0] = r5
    r0 = [r8+24]
    r1 = r6 + 1232
    [r1+0] = r0
    [r1+4] += 1  ; @rmw.add.s12
    r0 = 1532
    b[r6+r0] = r5
    csync
    b[r6+58] = r5
    r3 = 5
    if (r4 != 0) goto L0200fecc
    r3 = 4
L0200fecc:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 32
    r1 = -7
    r2 = r3
    call storage_coordination_notify
    b[r6+61] = r5
    if (r4 == 0) goto L0200fef0
    r0 = h[r6+82] (u)
    call console_helpers_ble_drop
    goto L0200fef6
L0200feec:
    r4 = -1
    goto L0200fef6
L0200fef0:
    call console_helpers_ble_advertise
    r4 = 0
L0200fef6:
    r0 = r4
    {pc, r10-r4} = [sp++]

; bond_records_and_prints_bond_count: 0x0200fefa..0x0200ff2c, module bond-records-and-prints (bond_count)
.type bond_records_and_prints_bond_count,@function
bond_records_and_prints_bond_count:
    [--sp] = {rets, r5, r4}
    r1 = r0
    r0 = 0
    r2 = 90
    r3 = 0
    goto L0200ff26
L0200ff06:
    r4 = h[r1+0] (u)
    r5 = r3 + 2
    r4 = r4 & (1 << r5)
    if (r4 == 0) goto L0200ff22
    r4 = b[r1+r2] (u)
    r5 = r4 & 0xFFFFFF0F
    r4 = 1
    if (r5 != 10) {  ; @if.ne.ri.s12
    r4 = 0
    }
    r0 += r4  ; @add.rr
L0200ff22:
    r2 += 52
    r3 += 1  ; @add.ri.u5
L0200ff26:
    if (r2 != 350) goto L0200ff06
    {pc, r5, r4} = [sp++]

; bond_records_and_prints_bit_count: 0x0200ff2c..0x0200ff48, module bond-records-and-prints (bit_count)
.type bond_records_and_prints_bit_count,@function
bond_records_and_prints_bit_count:
    r1 = r0 + 376
    r0 = 0
    r2 = 0
    goto L0200ff42
L0200ff36:
    r3 = b[r1+0] (u)
    r3 >>= r2
    r3 = r3 & 0x1
    r0 += r3  ; @add.rr
    r2 += 1  ; @add.ri.u5
L0200ff42:
    if (r2 != 4) goto L0200ff36
    rts
