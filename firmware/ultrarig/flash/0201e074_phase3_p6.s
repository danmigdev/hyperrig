; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 1 function, 0x0201e074..0x0201e09a

; phase3_p6_usb_set_die: 0x0201e074..0x0201e09a, module phase3-p6 (usb_set_die)
.type phase3_p6_usb_set_die,@function
phase3_p6_usb_set_die:
    r2 = r0 & 0xFFFFFFFE
    if (r2 != 148) goto L0201e098
    r0 = r0 + -135
    r2 = 1
    r2 <<= r0
    r0 = 0x51000
    if (r1 == 0) {  ; @if.eq.ri.s12
    r1 = [r0+0]
    r1 = r1 & ~r2
    } else {
    r1 = [r0+0]
    r1 |= r2
    }
    [r0+0] = r1
L0201e098:
    rts
