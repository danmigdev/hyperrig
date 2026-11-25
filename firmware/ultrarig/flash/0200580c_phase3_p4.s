; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 1 function, 0x0200580c..0x02005834

; phase3_p4_usb_sie_close: 0x0200580c..0x02005834, module phase3-p4 (usb_sie_close)
.type phase3_p4_usb_sie_close,@function
phase3_p4_usb_sie_close:
    if (r0 == 0) goto L02005818
    r0 = 0x16800
    [r0+0] = 0x0
    rts
L02005818:
    r1 = L02035cb0
    r2 = [r1+r0<<2]
    r1 += 8  ; @add.ri.u5
    r0 = [r1+r0<<2]
    r1 = 0
    [r2+0] = r1
    [r2+4] = r1
    [r0+0] = 0xC
    rts
