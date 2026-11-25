; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 3 functions, 0x020059fc..0x02005b84

; link_and_print_start_complete: 0x020059fc..0x02005a84, module link-and-print (start_complete)
.type link_and_print_start_complete,@function
link_and_print_start_complete:
    [--sp] = {rets, r9-r4}
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r7 = L01c26890
    r0 = r7 + 2
L02005a10:
    testset b[r0]
    ifeq goto L02005a10
    csync
    r0 = 1440
    r6 = b[r7+r0] (u)
    r0 = 362
    r8 = [r7+r0<<2]
    r9 = 0
    r5 = 0
    if (r6 != 0) goto L02005a48
    r0 = r7 + 1440
    r1 = b[r0+4] (u)
    r2 = 1
    b[r0+0] = r2
    r2 = 0
    b[r0+4] = r2
    if (r1 == 0) goto L02005a42
    call clock_record_and_usb_link_usb_note
L02005a42:
    call state_queries_toggle_update
    r5 = r0
L02005a48:
    csync
    b[r7+2] = r9
    call storage_coordination_irq_leave  ; @call.xl
    if (r6 != 0) goto L02005a82
    r0 = r5
    call link_and_print_usb_restart
    r0 = 0
    if ((r5 & 0x2) != 0) {
    r0 = 65535
    r0 = umin(r8, r0)
    r0 |= 65536
    }
    r1 = 1
    if (r4 != 0) goto L02005a74
    r1 = r4
L02005a74:
    r1 = r1 << 17
    r2 = r0 | r1
    r0 = 14
    r1 = 15
    call storage_coordination_notify
L02005a82:
    {pc, r9-r4} = [sp++]

; link_and_print_link_toggle: 0x02005a84..0x02005ad4, module link-and-print (link_toggle)
.type link_and_print_link_toggle,@function
link_and_print_link_toggle:
    [--sp] = {rets, r6-r4}
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r5 = L01c26890
    r0 = r5 + 2
L02005a96:
    testset b[r0]
    ifeq goto L02005a96
    csync
    r0 = 1440
    r0 = b[r5+r0] (u)
    r6 = 0
    r4 = 0
    if (r0 == 0) goto L02005ab2
    call state_queries_toggle_update
    r4 = r0
L02005ab2:
    csync
    b[r5+2] = r6
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 == 0) goto L02005ad2
    r0 = r4
    call link_and_print_usb_restart
    if ((r4 & 0x1) != 0) {
    r0 = 14
    r1 = 19
    r2 = r4
    call storage_coordination_notify
    }
L02005ad2:
    {pc, r6-r4} = [sp++]

; link_and_print_link_report: 0x02005ad4..0x02005b84, module link-and-print (link_report)
.type link_and_print_link_report,@function
link_and_print_link_report:
    [--sp] = {rets, r7-r4}
    sp += -4
    r0 = 1456
    r5 = L01c26890
    r0 = b[r5+r0] (u)
    if (r0 == 0) goto L02005b80
    r0 = sp + 0
    call state_queries_ready_word
    if (r0 == 0) goto L02005b80
    r0 = 1456  #
    r4 = [sp]
    r1 = 0
    b[r5+r0] = r1
    call L0203d862  ; @call.xl
    r3 = [r5+280]
    r2 = r0
    call state_queries_state_byte
    r1 = 1460
    r1 = b[r5+r1] (u)
    if (r1 == 0) goto L02005b1e
    r2 = 65535
    goto L02005b3e
L02005b1e:
    r6 = 368
    r7 = [r5+r6<<2]
    r6 = r7 - r2
    if (r7 <= r2) {
    r6 = 0
    }
    r7 = 1023
    r2 = 1
    if ((r6 & r7) == 0) {
    r2 = 0
    }
    r6 = r6 >> 10
    r2 += r6  ; @add.rr
L02005b3e:
    r7 = 1
    r6 = 1
    if (r0 != 0) goto L02005b46
    r6 = r0
L02005b46:
    if (r3 != 0) goto L02005b4a
    r7 = r3
L02005b4a:
    r0 = r7 << 17
    r0 <= insert(r6, p:18, l:1)
    r3 = 0x10000
    if (r1 != 0) goto L02005b58
    r3 = r1
L02005b58:
    r0 |= r3
    r1 = 1464
    r1 = b[r5+r1] (u)
    r3 = 65535
    r2 = umin(r2, r3)
    r0 |= r2
    r2 = 0x80000
    if (r1 != 0) goto L02005b76
    r2 = r1
L02005b76:
    r2 |= r0
    r0 = 32
    r1 = r4
    call storage_coordination_notify
L02005b80:
    sp += 4
    {pc, r7-r4} = [sp++]
