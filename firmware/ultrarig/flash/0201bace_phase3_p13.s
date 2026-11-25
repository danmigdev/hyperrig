; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 4 functions, 0x0201bace..0x0201bafa

; phase3_p13_usb_disable_ep: 0x0201bace..0x0201badc, module phase3-p13 (usb_disable_ep)
.type phase3_p13_usb_disable_ep,@function
phase3_p13_usb_disable_ep:
    if (r0 != 0) goto L0201bada
    r0 = r1 + 19
    r1 = 0x11800
    [r1+0] |= 1 << r0
L0201bada:
    rts

; phase3_p13_usb_ep0_RxPktEnd: 0x0201badc..0x0201bae6, module phase3-p13 (usb_ep0_RxPktEnd)
.type phase3_p13_usb_ep0_RxPktEnd,@function
phase3_p13_usb_ep0_RxPktEnd:
    [--sp] = rets
    r1 = 72
    call L0201b896
    pc = [sp++]

; phase3_p13_usb_ep0_ClrRxPktRdy: 0x0201bae6..0x0201baf0, module phase3-p13 (usb_ep0_ClrRxPktRdy)
.type phase3_p13_usb_ep0_ClrRxPktRdy,@function
phase3_p13_usb_ep0_ClrRxPktRdy:
    [--sp] = rets
    r1 = 64
    call L0201b896
    pc = [sp++]

; phase3_p13_usb_ep0_Set_Stall: 0x0201baf0..0x0201bafa, module phase3-p13 (usb_ep0_Set_Stall)
.type phase3_p13_usb_ep0_Set_Stall,@function
phase3_p13_usb_ep0_Set_Stall:
    [--sp] = rets
    r1 = 96
    call L0201b896
    pc = [sp++]
