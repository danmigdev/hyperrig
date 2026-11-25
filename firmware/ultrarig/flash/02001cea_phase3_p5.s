; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 1 function, 0x02001cea..0x02001d0a

; phase3_p5_usb_slave_init: 0x02001cea..0x02001d0a, module phase3-p5 (usb_slave_init)
.type phase3_p5_usb_slave_init,@function
phase3_p5_usb_slave_init:
    [--sp] = rets
    r1_r0 = 0
    call L02001b40
    r0 = 0
    r1 = -1
    call L02001bca
    r0 = 0
    r1 = -1
    call L02001c58
    r0 = 0x11800
    [r0+0] |= 0x800
    pc = [sp++]
