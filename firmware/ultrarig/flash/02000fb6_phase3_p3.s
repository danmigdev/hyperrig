; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 3 functions, 0x02000fb6..0x02001204

; phase3_p3_get_task_priority: 0x02000fb6..0x02000ff8, module phase3-p3 (get_task_priority)
.type phase3_p3_get_task_priority,@function
phase3_p3_get_task_priority:
    [--sp] = {rets, r6-r4}
    r5 = r0
    r0 = 12248
    r1 = L02035810
    r4 = r1 + r0
    goto L02000fee
L02000fc8:
    r0 = r6
    r1 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000ff4
    r0 = b[r6+0] (u)
    if (r0 != 35) goto L02000fec
    r0 = b[r6+1] (u)
    if (r0 != 67) goto L02000fec
    r0 = r6 + 3
    r1 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000ff4
L02000fec:
    r4 += 20  ; @add.ri.u5
L02000fee:
    r6 = [r4+0]
    if (r6 != 0) goto L02000fc8
    r4 = 0
L02000ff4:
    r0 = r4
    {pc, r6-r4} = [sp++]

; phase3_p3_task_create: 0x02000ff8..0x02001042, module phase3-p3 (task_create)
.type phase3_p3_task_create,@function
phase3_p3_task_create:
    [--sp] = {rets, r6-r4}
    sp += -8
    r4 = r0
    r0 = r1
    call phase3_p3_get_task_priority
    if (r0 == 0) goto L0200101e
    r5 = [r0+0]
    r3 = h[r0+12] (u)
    r2 = [r0+8]
    r6 = [r0+16]
    r1 = b[r0+4] (u)
    if (r6 == 0) goto L02001022
    r0 = r4  #
    [sp+4] = r6
    [sp] = r5
    call L0203fc70  ; @call.xl
    goto L0200102c
L0200101e:
    r1 = -14
    goto L02001030
L02001022:
    r0 = r4  #
    [sp] = r5
    call L0203fd12  ; @call.xl
L0200102c:
    r1 = 0
    if (r0 != 0) goto L02001036
L02001030:
    r0 = r1
    sp += 8
    {pc, r6-r4} = [sp++]
L02001036:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02001040:
    goto L02001040

; phase3_p3_main: 0x02001042..0x02001204, module phase3-p3 (main)
.type phase3_p3_main,@function
phase3_p3_main:
    [--sp] = {rets, r6-r4}
    sp += -12
    call storage_coordination_irq_enter  ; @call.xl
    r0 = 65728
    r0 = [r0+0]
    r6 = L01c26890
    [r6+108] = r0
    r0 = 18
    call storage_fault_read_register  ; @call.xl
    [r6+112] = r0
    r4 = 29883888
    r0 = [r4+0]
    r2 = 2057046784
    r5 = 1
    if (r0 != r2) goto L0200108c
    r0 = [r4+8]
    r1 = [r4+4]
    r1 = ~r1
    if (r0 == r1) {
    r0 = [r4+4]
    r5 = r0 + 1
    }
L0200108c:
    [r6+116] = r5
    r0 = [r4+12]
    [r6+120] = r0
    r3 = [r4+12]
    r0 = r3 & 0xFF000000
    r1 = 0
    if (r0 != 3238002688) goto L020010b6
    r0 = r3.l (u)
    r3 = uextra(r3, p:16, l:8)
    call boundary_hooks_record_check
    r1 = 1
    if (r3 != r0) {
    r1 = 0
    }
L020010b6:
    b[r6+5] = r1
    [r4+0] = r2
    r0 = ~r5  #
    [r4+4] = r5
    [r4+8] = r0
    r0 = 1
    r1 = 0
    r2 = 0
    r6 = 0
    call boundary_hooks_record_pack
    call boundary_hooks_record_store
    if (r5 >= 3) goto L020011f8
    call phase3_p3_wdt_init
    call phase3_p3_clk_early_init
    r0 = 6
    r1 = 0
    r2 = 3
    r3 = 7
    call storage_fault_masked_register  ; @call.xl
    r0 = 0
    call storage_fault_read_register  ; @call.xl
    if ((r0 & 8) != 0) goto L0200116a
    r0 = 0
    r1 = 2
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
    r0 = 1000
    [sp+8] = r0
    goto L02001112
L0200110c:
    r0 = sp + 8
    [r0+0] += -1  ; @rmw.add.s12
L02001112:
    r0 = [sp+8]
    if (r0 != 0) goto L0200110c
    r0 = 0
    r1 = 3
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
    r0 = 1000
    [sp+4] = r0
    goto L02001132
L0200112c:
    r0 = sp + 4
    [r0+0] += -1  ; @rmw.add.s12
L02001132:
    r0 = [sp+4]
    if (r0 != 0) goto L0200112c
    r0 = 0
    r1 = 2
    r2 = 1
    r3 = 0
    call storage_fault_masked_register  ; @call.xl
    r0 = 1000
    [sp] = r0
    goto L02001152
L0200114c:
    r0 = sp + 0
    [r0+0] += -1  ; @rmw.add.s12
L02001152:
    r0 = [sp]
    if (r0 != 0) goto L0200114c
    r0 = 7
    r1 = 165
    call storage_fault_write_register  ; @call.xl
    r0 = 8
    r1 = 150
    call storage_fault_write_register  ; @call.xl
L0200116a:
    r0 = 9
    r1 = 0
    r2 = 4
    r3 = 15
    call storage_fault_masked_register  ; @call.xl
    r0 = 131328
    call interrupt_and_stack_calls_clock_word_set  ; @call.xl
    call phase3_p14_interrupt_init
    call phase3_p3_system_reset_reason_get
    r0 = 0x10200
    r0 = [r0+0]
    r4 = L020358f2  ; "hsb"
    r0 = r4 + 16
    call L020009ee
    r0 = r4 + 619
    call L020009ee
    r0 = r4
    call L020009ee
    r0 = r4 + 613
    call L020009ee
    r0 = r4
    call L020009ee
    r0 = 262660
    r0 = [r0+0]
    call L02000ebc
    call phase3_p3_debug_init
    call phase3_p3_crc16_mutex_init
    call L02000ee0
    call L0203fbbe  ; @call.xl
    r1 = r4 + 1108
    r0 = phase3_p4_app_task_handler
    call phase3_p3_task_create
    call L0203ed8e  ; @call.xl
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 0
    sp += 12
    {pc, r6-r4} = [sp++]
L020011f8:
    [r4+0] = r6
    [r4+12] = r6
    call phase3_p7_go_mask_usb_updata  ; @call.xl
L02001202:
    goto L02001202
