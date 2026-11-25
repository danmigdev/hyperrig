; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 1 function, 0x0201e2c6..0x0201e33c

; phase3_p6_usb_otg_sof_check_init: 0x0201e2c6..0x0201e33c, module phase3-p6 (usb_otg_sof_check_init)
.type phase3_p6_usb_otg_sof_check_init,@function
phase3_p6_usb_otg_sof_check_init:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = L01c26ef8
    r0 = [r5+r4<<2]
    if (r0 != 0) goto L0201e2e0
    r1 = 0
    r0 = r4
    call phase3_p6_usb_alloc_ep_dmabuffer
    [r5+r4<<2] = r0
L0201e2e0:
    r0 = r4
    call L02001a08
    r1 = 0
    r0 = r4
    call L02001b40
    r1 = -1
    r0 = r4
    call L02001bca
    r1 = -1
    r0 = r4
    call L02001c58
    if (r4 == 0) goto L0201e312
    r0 = 54
    call phase3_p13_unrequest_irq
    if (r4 == 1) {  ; @if.eq.ri.s12
    r0 = 1
    call phase3_p5_usb_write_power
    }
    goto L0201e318
L0201e312:
    r0 = 9
    call phase3_p13_unrequest_irq
L0201e318:
    r2 = [r5+r4<<2]
    r1 = 0
    r0 = r4
    call sdk_usb_set_dma_raddr
    r2 = 1
    goto L0201e332
L0201e328:
    r0 = r4
    r1 = r2
    call phase3_p13_usb_disable_ep
    r2 += 1  ; @add.ri.u5
L0201e332:
    if (r2 != 5) goto L0201e328
    r0 = r4
    call L0201e274
    {pc, r5, r4} = [sp++]
