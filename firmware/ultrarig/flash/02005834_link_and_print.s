; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 2 functions, 0x02005834..0x020058ec

; link_and_print_usb_restart: 0x02005834..0x0200587e, module link-and-print (usb_restart)
.type link_and_print_usb_restart,@function
link_and_print_usb_restart:
    [--sp] = {rets, r5, r4}
    r4 = r0
    if ((r4 & 1) == 0) goto L02005846
    r0 = 0
    call phase3_p5_usb_device_mode
    r0 = 0
    call phase3_p4_usb_sie_close
L02005846:
    r5 = L01c26890
    if ((r4 & 0x3) != 0) {
    r0 = 0
    b[r5+4] = r0
    b[r5+3] = r0
    }
    if ((r4 & 2) == 0) goto L0200587c
    r0 = 16
    call phase3_p5_usb_device_mode
    r1 = clock_record_and_usb_link_usb_ready
    r0 = 0
    call phase3_p5_cdc_set_wakeup_handler
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 * 0xA
    [r5+100] = r0
L0200587c:
    {pc, r5, r4} = [sp++]

; link_and_print_link_pause: 0x0200587e..0x020058ec, module link-and-print (link_pause)
.type link_and_print_link_pause,@function
link_and_print_link_pause:
    [--sp] = {rets, r6-r4}
    r5 = L01c26890
    r0 = b[r5+1] (u)
    r4 = 0
    if (r0 == 0) goto L020058e8
    r0 = 1440
    r0 = b[r5+r0] (u)
    if ((r0 & 1) == 0) goto L020058e8
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r5 + 2
L020058a2:
    testset b[r0]
    ifeq goto L020058a2
    csync
    r0 = 1718
    r4 = 1
    b[r5+r0] = r4
    r0 += -2
    r0 = b[r5+r0] (u)
    r6 = 0
    r3 = 0
    if (r0 == 0) goto L020058ce
    r0 = 0
    r1 = r5 + 1716
    b[r1+0] = r0
    [r1+12] += 1  ; @rmw.add.s12
    r3 = 1
L020058ce:
    csync
    b[r5+2] = r6
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    call link_and_print_usb_restart
    b[r5+4] = r6
    b[r5+3] = r6
    r0 = 5
    call L0203feb8  ; @call.xl
L020058e8:
    r0 = r4
    {pc, r6-r4} = [sp++]
