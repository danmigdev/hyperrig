; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 6 functions, 0x0201c474..0x0201c606

; phase3_p4_usb_enable_ep: 0x0201c474..0x0201c480, module phase3-p4 (usb_enable_ep)
.type phase3_p4_usb_enable_ep,@function
phase3_p4_usb_enable_ep:
    if (r0 != 0) goto L0201c47e
    r0 = 0x11800
    [r0+0] &= 0xFFDFFFFF
L0201c47e:
    rts

; phase3_p4_cdc_endpoint_init: 0x0201c480..0x0201c4d2, module phase3-p4 (cdc_endpoint_init)
.type phase3_p4_cdc_endpoint_init,@function
phase3_p4_cdc_endpoint_init:
    [--sp] = {rets, r5, r4}
    r0 = b[r0+25] (u)
    call phase3_p4_usb_device2id
    r4 = r0
    r5 = L01c26f00
    r0 = [r5+r4<<2]
    if (r0 == 0) goto L0201c4c6
    r0 = r4  #
    r3 = [r0+8]
    r1 = 130
    r2 = 0
    call phase3_p4_usb_g_ep_config
    r0 = [r5+r4<<2]
    r0 = r4  #
    r3 = [r0+4]
    r1 = 2
    r2 = 1
    call phase3_p4_usb_g_ep_config
    r2 = phase3_p4_cdc_wakeup_handler
    r1 = 2
    r0 = r4
    call L0201c442
    r0 = r4
    call phase3_p4_usb_enable_ep
    {pc, r5, r4} = [sp++]
L0201c4c6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0201c4d0:
    goto L0201c4d0

; phase3_p4_cdc_setup: 0x0201c4d2..0x0201c588, module phase3-p4 (cdc_setup)
.type phase3_p4_cdc_setup,@function
phase3_p4_cdc_setup:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = b[r4+25] (u)
    call phase3_p4_usb_device2id
    r2 = b[r1+0] (u)
    r2 = r2 & 0xFFFFFF60
    if (r2 != 32) goto L0201c56a
    r3 = b[r1+1] (u)
    r2 = L01c26f00
    if (r3 == 34) goto L0201c50a
    if (r3 == 33) goto L0201c546
    if (r3 != 32) goto L0201c56a
    r1 = phase3_p4_cdc_setup_rx
    r0 = r4
    call L0201c2d8
    goto L0201c572
L0201c50a:
    r0 = [r2+r0<<2]
    if (r0 == 0) goto L0201c53c
    r3 = b[r1+3] (u)
    r1 = b[r1+2] (u)
    r2 = b[r0+104] (u)
    r1 <= insert(r3, p:8, l:8)
    r3 = r2 | 0x3
    r5 = r2 & 0xFFFFFFEC
    r5 |= 1
    if ((r1 & 0x1) != 0) {
    r5 = r3
    }
    r3 = r5 | 0x10
    b[r0+104] = r3
    if ((r2 & 2) != 0) goto L0201c576
    if ((r1 & 1) == 0) goto L0201c576
L0201c53c:
    r1 = 0
    r0 = r4
    call phase3_p4_usb_set_setup_phase
    goto L0201c582
L0201c546:
    r0 = [r2+r0<<2]
    if (r0 == 0) goto L0201c56a
    r3 = b[r1+7] (u)
    r2 = b[r1+6] (u)
    r2 <= insert(r3, p:8, l:24)
    r3 = r2.l (u)
    if (r3 >= 7) {  ; @if.ge.ri.s12
    r2 = 7
    }
    r3 = r2.l (u)
    r2 = r0 + 105
    r0 = r4
    call L0201ba8a
    goto L0201c572
L0201c56a:
    r1 = 3
    r0 = r4
    call phase3_p4_usb_set_setup_phase
L0201c572:
    r0 = 0
    {pc, r5, r4} = [sp++]
L0201c576:
    r1 = 0
    r0 = r4
    call phase3_p4_usb_set_setup_phase
    if ((r2 & 16) != 0) goto L0201c572
L0201c582:
    call phase3_p4_cdc_endpoint_init
    goto L0201c572

; phase3_p4_cdc_reset: 0x0201c588..0x0201c590, module phase3-p4 (cdc_reset)
.type phase3_p4_cdc_reset,@function
phase3_p4_cdc_reset:
    [--sp] = rets
    call phase3_p4_cdc_endpoint_init
    pc = [sp++]

; phase3_p4_cdc_wakeup_handler: 0x0201c590..0x0201c5b2, module phase3-p4 (cdc_wakeup_handler)
.type phase3_p4_cdc_wakeup_handler,@function
phase3_p4_cdc_wakeup_handler:
    [--sp] = rets
    r1 = r0
    r0 = b[r1+25] (u)
    call phase3_p4_usb_device2id
    r2 = L01c26f00
    r0 = [r2+r0<<2]
    if (r0 == 0) goto L0201c5b0
    r2 = [r0+20]
    if (r2 == 0) goto L0201c5b0
    r0 = r1
    call r2
L0201c5b0:
    pc = [sp++]

; phase3_p4_cdc_setup_rx: 0x0201c5b2..0x0201c606, module phase3-p4 (cdc_setup_rx)
.type phase3_p4_cdc_setup_rx,@function
phase3_p4_cdc_setup_rx:
    [--sp] = {rets, r6-r4}
    sp += -8
    r0 = b[r0+25] (u)
    r5 = r1
    call phase3_p4_usb_device2id
    r6 = r0  #
    r1 = b[r5+7] (u)
    r4 = b[r5+6] (u)
    r4 <= insert(r1, p:8, l:8)
    r1 = sp + 0
    r2 = r4
    call L0201b8f2
    r0 = b[r5+0] (u)
    r0 = r0 & 0xFFFFFF60
    if (r0 != 32) goto L0201c600
    r0 = b[r5+1] (u)
    if (r0 != 32) goto L0201c600
    r0 = L01c26f00
    r0 = [r0+r6<<2]
    if (r0 == 0) goto L0201c600
    if (r4 >= 7) {  ; @if.ge.ri.s12
    r4 = 7
    }
    r0 += 105
    r1 = sp + 0
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
L0201c600:
    r0 = 0
    sp += 8
    {pc, r6-r4} = [sp++]
