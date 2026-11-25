; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_helpers: 12 functions, 0x0200f8ec..0x0200fc48

; console_helpers_id_hash: 0x0200f8ec..0x0200f90e, module console-helpers (id_hash)
.type console_helpers_id_hash,@function
console_helpers_id_hash:
    [--sp] = {rets, r4}
    r1 = 0
    r2 = L01c3743c
    r3 = 16777619
    goto L0200f908
L0200f8fe:
    r4 = b[r1+r2] (u)
    r0 ^= r4
    r0 *= r3
    r1 += 1  ; @add.ri.u5
L0200f908:
    if (r1 != 16) goto L0200f8fe
    {pc, r4} = [sp++]

; console_helpers_ble_address: 0x0200f90e..0x0200f958, module console-helpers (ble_address)
.type console_helpers_ble_address,@function
console_helpers_ble_address:
    [--sp] = {rets, r6-r4}
    r5 = 1204
    r6 = L01c26890
    r0 = b[r6+r5] (u)
    if (r0 != 0) goto L0200f956
    r0 = 2166136261
    call console_helpers_id_hash
    r4 = r0
    r0 = 1540483477
    r0 ^= r4
    call console_helpers_id_hash
    r1 = r4 >> 8
    r2 = r6 + 1584
    b[r2+1] = r1
    r1 = r4 >> 16
    b[r2+2] = r1
    r1 = r4 >> 24
    b[r2+3] = r1
    b[r2+4] = r0
    r0 = r0 >> 8
    r0 = r4 & 0xFC  #
    b[r2+5] = r0
    b[r2+0] = r0
    r0 = 1
    b[r6+r5] = r0
L0200f956:
    {pc, r6-r4} = [sp++]

; console_helpers_ble_name: 0x0200f958..0x0200f992, module console-helpers (ble_name)
.type console_helpers_ble_name,@function
console_helpers_ble_name:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = L01c26890
    r0 = b[r4+56] (u)
    if (r0 != 0) goto L0200f98e
    call console_helpers_ble_address
    r0 = 1588
    r3 = b[r4+r0] (u)
    r0 += 1  ; @add.ri.u5
    r5 = b[r4+r0] (u)
    r0 = r4 + 2072  #
    [sp] = r5
    r2 = L0203a123  ; "UltraRig %02X%02X"
    r1 = 24
    call L0200691e
    b[r4+56] = r0
L0200f98e:
    sp += 4
    {pc, r5, r4} = [sp++]

; console_helpers_ble_advertise: 0x0200f992..0x0200fa58, module console-helpers (ble_advertise)
.type console_helpers_ble_advertise,@function
console_helpers_ble_advertise:
    [--sp] = {rets, r7-r4}
    sp += -4
    r6 = L01c26890
    r0 = b[r6+60] (u)
    if (r0 == 0) goto L0200fa54
    r0 = h[r6+82] (u)
    if (r0 != 0) goto L0200fa54
    r0 = L01c1f180
    r0 = b[r0+17] (u)
    r4 = 0
    if (r0 == 0) goto L0200fa48
    r0 = 1536
    r0 = b[r6+r0] (u)
    if ((r0 & 1) != 0) goto L0200fa48
    r0 = b[r6+61] (u)
    if (r0 != 0) goto L0200fa48
    r5 = r6 + 2260
    r0 = 2
    b[r5+0] = r0
    r4 = 1
    b[r5+1] = r4
    r0 = 6
    b[r5+2] = r0
    r0 = 17
    b[r5+3] = r0
    r7 = 7
    b[r5+4] = r7
    r0 = r5 + 5
    r1 = L0203a254
    rep 16 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = 2
    r1 = 3
    r2 = 160
    r3 = 0
    [sp] = r7
    call L0204c744  ; @call.xl
    r0 = 3
    r1 = 2
    r2 = 21
    r3 = r5
    call L0204c744  ; @call.xl
    call console_helpers_ble_name
    r2 = b[r6+56] (u)
    r5 = r2 + 2
    if (r5 > 31) goto L0200fa38
    r0 = r2 + 1
    r1 = 2291
    b[r6+r1] = r0
    r0 = r1 + 1
    r1 = 9
    b[r6+r0] = r1
    r0 = r6 + 2293
    r1 = r6 + 2072
    call effect_parameter_support_memmove  ; @call.xl
L0200fa38:
    r2 = r5.b0 (u)
    r3 = r6 + 2291
    r0 = 4
    r1 = 2
    call L0204c744  ; @call.xl
L0200fa48:
    r0 = 1
    r1 = 1
    r2 = r4
    call L0204c744  ; @call.xl
L0200fa54:
    sp += 4
    {pc, r7-r4} = [sp++]

; console_helpers_key_ready: 0x0200fa58..0x0200fa74, module console-helpers (key_ready)
.type console_helpers_key_ready,@function
console_helpers_key_ready:
    r0 = L01c26890
    r1 = h[r0+82] (u)
    if (r1 == 0) goto L0200fa70
    r1 = b[r0+59] (u)
    r0 = 1
    if (r1 != 0) goto L0200fa6e
    r0 = r1
L0200fa6e:
    rts
L0200fa70:
    r0 = 0
    rts

; console_helpers_key_window: 0x0200fa74..0x0200fab0, module console-helpers (key_window)
.type console_helpers_key_window,@function
console_helpers_key_window:
    [--sp] = rets
    call console_helpers_key_ready
    r1 = r0
    r0 = 1
    if (r1 == 0) goto L0200fa80
L0200fa7e:
    pc = [sp++]
L0200fa80:
    r1 = L01c26890
    r2 = h[r1+82] (u)
    r0 = 0
    if (r2 == 0) goto L0200fa7e
    r2 = 1252
    r2 = b[r1+r2] (u)
    if (r2 == 0) goto L0200fa7e
    r0 = 314
    r2 = [r1+r0<<2]
    r0 += 1  ; @add.ri.u5
    r1 = [r1+r0<<2]
    r0 = 1
    if (r2 != r1) {
    r0 = 0
    }
    pc = [sp++]

; console_helpers_now_ms: 0x0200fab0..0x0200fabe, module console-helpers (now_ms)
.type console_helpers_now_ms,@function
console_helpers_now_ms:
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 * 0xA
    rts

; console_helpers_key_left: 0x0200fabe..0x0200fae4, module console-helpers (key_left)
.type console_helpers_key_left,@function
console_helpers_key_left:
    r2 = 1532
    r1 = L01c26890
    r2 = b[r1+r2] (u)
    if (r2 == 0) goto L0200fae0
    r2 = 382
    r1 = [r1+r2<<2]
    r0 = r1 - r0
    ifs (r0 <= 0) {  ; @ifs.le.ri.s12
    r0 = 0
    }
    rts
L0200fae0:
    r0 = 0
    rts

; console_helpers_key_left_locked: 0x0200fae4..0x0200fb18, module console-helpers (key_left_locked)
.type console_helpers_key_left_locked,@function
console_helpers_key_left_locked:
    [--sp] = {rets, r4}
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r4 = L01c26890
    r0 = r4 + 58
L0200faf8:
    testset b[r0]
    ifeq goto L0200faf8
    csync
    call console_helpers_now_ms
    call console_helpers_key_left
    r3 = r0
    csync
    r0 = 0
    b[r4+58] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r4} = [sp++]

; console_helpers_key_issue: 0x0200fb18..0x0200fc10, module console-helpers (key_issue)
.type console_helpers_key_issue,@function
console_helpers_key_issue:
    [--sp] = {rets, r7-r4}
    sp += -56
    r1 = 1228
    r6 = L01c26890
    r1 = b[r6+r1] (u)
    r4 = L02036158  ; "BLE key %d %s"
    if (r1 == 0) goto L0200fc00
    r5 = 0
    r7 = 0
    if (r0 == 0) goto L0200fb42
    call console_helpers_key_window
    if (r0 != 0) goto L0200fb42
    call console_helpers_key_left_locked
    r7 = 1
    if (r0 == 0) goto L0200fc0a
L0200fb42:
    r0 = sp + 40
    call console_helpers_nonce
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r6 + 58
L0200fb54:
    testset b[r0]
    ifeq goto L0200fb54
    csync
    r0 = 6968
    r0 = b[r6+r0] (u)
    goto L0200fb6e
L0200fb66:
    r1 = r0 & (1 << r5)
    if (r1 == 0) goto L0200fb8c
    r5 += 1  ; @add.ri.u5
L0200fb6e:
    if (r5 <= 3) goto L0200fb66
    if (r5 != 4) goto L0200fb8c
    r0 = 6969
    r1 = b[r6+r0] (u)
    r2 = r1 + 1
    r2 = r2 & 0x3
    b[r6+r0] = r2
    r5 = r1 & 0xFFFFFF03
L0200fb8c:
    r0 = r5 << 4
    r0 += r6  ; @add.rr
    r0 = r0 + 6904
    r1 = sp + 40
    rep 16 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = 6968
    r1 = b[r6+r0] (u)
    r1 = r1 | (1 << r5)
    b[r6+r0] = r1
    r0 = L01c1f180
    r1 = r6 + 1232  #
    r0 = [r0+24]
    [r1+0] = r0
    [r1+4] += 1  ; @rmw.add.s12
    if (r7 == 0) goto L0200fbca
    r0 = 1532
    r1 = 0
    b[r6+r0] = r1
L0200fbca:
    csync
    r0 = 0
    b[r6+58] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = sp + 7
    r1 = sp + 40
    call console_helpers_hex_text
    r6 = r6 + 3668  #
    [sp] = r0
    r1 = 80
    r0 = r6
    r3_r2 = r5_r4
    call L0200691e
    r0 = r7 << 8
    r2 = r5 | r0
    r0 = 32
    r1 = -11
    call storage_coordination_notify
    goto L0200fc04
L0200fc00:
    r6 = r4 + 1977
L0200fc04:
    r0 = r6
    sp += 56
    {pc, r7-r4} = [sp++]
L0200fc0a:
    r6 = r4 + 645
    goto L0200fc04

; console_helpers_key_open: 0x0200fc10..0x0200fc2a, module console-helpers (key_open)
.type console_helpers_key_open,@function
console_helpers_key_open:
    r1 = 1
    r2 = L01c26e88
    b[r2+4] = r1
    r1 = 60000
    r0 += r1  ; @add.rr
    [r2+0] = r0
    r0 = 0
    b[r2+8] = r0
    rts

; console_helpers_ble_drop: 0x0200fc2a..0x0200fc48, module console-helpers (ble_drop)
.type console_helpers_ble_drop,@function
console_helpers_ble_drop:
    [--sp] = {rets, r4}
    r4 = r0
    if (r4 == 0) goto L0200fc46
    r0 = 5
    r1 = 1
    r2 = r4
    call L0204c744  ; @call.xl
    r1 = 19
    r0 = r4
    call L0204a5da  ; @call.xl
L0200fc46:
    {pc, r4} = [sp++]
