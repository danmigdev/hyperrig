; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 1 function, 0x0201dc74..0x0201df12

; phase3_p4_low_power_process: 0x0201dc74..0x0201df12, module phase3-p4 (low_power_process)
.type phase3_p4_low_power_process,@function
phase3_p4_low_power_process:
    [--sp] = {rets, r10-r4}
    r8 = L01c3740c
    r1 = 0
    b[r8+7] = r1
    [r8+24] = r1
    r5 = L01c1fa30
    r1 = b[r5+95] (u)
    r2 = h[r8+0] (u)
    r4 = r0
    r0 = r1 & 0xFFFFFF04
    r2 = r2 & 0xFFFFFF3B
    r0 |= r2
    r1 = r1 << 1
    r2 = r1 & 0x40
    r0 |= r2
    r1 = r1 & 0x80
    r0 |= r1
    h[r8+0] = r0
    r0 = 9
    call storage_fault_read_register  ; @call.xl
    r0 = r0 & 0xFFFFFF0F
    b[r8+17] = r0
    r0 = 128
    call storage_fault_read_register  ; @call.xl
    b[r8+10] = r0
    r6 = 263168
    r0 = [r6+0]
    r1 = h[r8+0] (u)
    r1 &= 4294967294
    r0 = r0 >> 11
    r2 = r0 & 0x1
    r1 |= r2
    h[r8+0] = r1
    if ((r0 & 1) == 0) goto L0201dd64
    r0 = 5
    call storage_fault_read_register  ; @call.xl
    r1 = h[r8+0] (u)
    r2 = r0 >> 4
    r1 <= insert(r2, p:3, l:2)
    r0 = r0 >> 1
    r0 = r0 & 0x18
    h[r8+0] = r1
    if (r0 == 24) goto L0201dd1e
    r0 = 5
    r1 = 4
    r2 = 2
    r3 = 3
    call storage_fault_masked_register  ; @call.xl
    r1 = h[r8+0] (u)
L0201dd1e:
    r2 = 65534
    r1 &= r2  #
    r0 = [r6+0]
    r0 = uextra(r0, p:11, l:1)
    r1 |= r0
    h[r8+0] = r1
    r1 = [r8+36]
    if (r1 != 0) goto L0201dd64
    if (r0 == 0) goto L0201dd64
    r0 = L02035b5d  ; "sdram"
    call L020009ee
    r1 = 1000000
    r0 = r0 / r1 (s)
    r0 = r0 * 0x3E8
    r1 = 24
    r0 = r0 / r1 (s)
    r1 = 6000
    r0 = umax(r0, r1)
    [r8+36] = r0
L0201dd64:
    r0 = b[r5+95] (u)
    if ((r0 & 16) != 0) goto L0201dd76
    call phase3_p7_sys_clk_source_set  ; @call.xl
    [r8+28] = r0
L0201dd76:
    r0 = r4
    call phase3_p7_low_power_enter_and_exit  ; @call.xl
    r0 = b[r8+0] (u)
    if ((r0 & 1) == 0) goto L0201ddac
    r0 = 5
    call storage_fault_read_register  ; @call.xl
    r1 = h[r8+0] (u)
    r1 = uextra(r1, p:3, l:2)
    r0 = uextra(r0, p:4, l:2)
    if (r0 == r1) goto L0201ddac
    r3 = r1.b0 (u)
    r0 = 5
    r1 = 4
    r2 = 2
    call storage_fault_masked_register  ; @call.xl
L0201ddac:
    r0 = b[r5+90] (u)
    if (r0 == 0) goto L0201ddb8
    r0 = 0
    b[r5+90] = r0
L0201ddb8:
    r0 = b[r5+95] (u)
    if ((r0 & 0x10) == 0) {
    r0 = [r8+28]
    call L01c040a8  ; @call.xl
    }
    r0 = 1
    call sdk___hw_nv_timer_is_runnig  ; @call.xl
    if (r0 == 0) goto L0201dde2
    r0 = 4
    call L0201dbe2
    r4 = r0
    call L01c0374a  ; @call.xl
L0201dde2:
    r0 = 0
    call sdk___hw_nv_timer_is_runnig  ; @call.xl
    if (r0 == 0) goto L0201de0c
    r0 = [r5+84]
    if (r0 == 0) goto L0201de0c
    r0 = 2
    call L0201dbe2
    r2 = [r5+84]
    r1 = [r5+76]
    r0 = r0 - r2
    if (r0 <= r1) {
    r1 = 0
    }
    r4 = r0 - r1
    goto L0201de2e
L0201de0c:
    r1 = b[r8+0] (u)
    r0 = [r5+76]
    if ((r1 & 0x1) != 0) {
    r1 = [r8+36]
    r0 += r1  ; @add.rr
    r0 = r0 + 6000
    } else {
    r0 = r0 + 4000
    }
    r0 += r4  ; @add.rr
    r1 = 20000
    r4 = r0 + r1
L0201de2e:
    r9 = 0  #
    [r5+32] = r4
    r6 = [r5+24]
    goto L0201de4e
L0201de36:
    r0 = [r7+16]
    r6 = [r7+0]
    if (r0 == 0) goto L0201de4e
    r2 = [r0+20]
    if (r2 == 0) goto L0201de4e
    r0 = b[r7+12] (u)
    if (r0 == 0) goto L0201de4e
    r1 = r4  #
    r0 = [r7+8]
    call r2
    b[r7+12] = r9
L0201de4e:
    r0 = r5 + 24
    r7 = r6
    if (r7 != r0) goto L0201de36
    [r5+84] = 0x0
    r0 = 168
    call storage_fault_read_register  ; @call.xl
    r10 = r0
    r0 = 32936
    call storage_fault_read_register  ; @call.xl
    r0 = 147
    call storage_fault_read_register  ; @call.xl
    r9 = r0
    if ((r10 & 2) != 0) goto L0201de84
    if (r0 == 0) goto L0201dec6
    if (r0 == 255) goto L0201dec6
L0201de84:
    r0 = 147
    call storage_fault_read_register  ; @call.xl
    r6 = r0
    r0 = 148
    call storage_fault_read_register  ; @call.xl
    r7 = r0 & 0xFFFFFF01
    r0 = r6 >> r7
    if ((r0 & 0xFF) == 0) goto L0201dec6
    r6 = r0.b0 (u)
    r4 = 0
    r5 = 255
    goto L0201dec2
L0201deac:
    r0 = r6 & (1 << r4)
    if (r0 == 0) goto L0201dec0
    r0 = r7 + r4
    r1 = r5 & (1 << r0)
    r0 = 146
    call L01c00f72  ; @call.xl
L0201dec0:
    r4 += 1  ; @add.ri.u5
L0201dec2:
    if (r4 != 8) goto L0201deac
L0201dec6:
    r6 = sextra(r10, p:0, l:8)
    if ((r10 & 64) == 0) goto L0201def8
    r0 = 24
    r1 = 6
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
    r0 = 24
    r1 = 1
    r2 = 1
    r3 = 0
    call storage_fault_masked_register  ; @call.xl
    r0 = 24
    r1 = 0
    r2 = 1
    r3 = 0
    call storage_fault_masked_register  ; @call.xl
L0201def8:
    ifs (r6 <= -1) goto L0201df12
    if (r9 != 0) {  ; @if.ne.ri.s12
    r0 = 146
    r1 = r9
    call L01c00f72  ; @call.xl
    }
    r0 = 0
    b[r8+8] = r0
    {pc, r10-r4} = [sp++]
