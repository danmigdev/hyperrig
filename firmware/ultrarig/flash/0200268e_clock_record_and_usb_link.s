; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; clock_record_and_usb_link: 1 function, 0x0200268e..0x020026ba

; clock_record_and_usb_link_dsp_start: 0x0200268e..0x020026ba, module clock-record-and-usb-link (dsp_start)
.type clock_record_and_usb_link_dsp_start,@function
clock_record_and_usb_link_dsp_start:
    [--sp] = rets
    call dsp_initialization_startup
    r1 = L01c26890
    r2 = [r1+416]
    r0 = -110
    if (r2 != 0) goto L020026b8
    r0 = [r1+436]
    if (r0 == 0) goto L020026b6
    r0 = 500
    r1 = b[r1+r0] (u)
    r0 = 0
    if (r1 != 0) goto L020026b8
L020026b6:
    call capture_dispatch_cleanup
L020026b8:
    pc = [sp++]
