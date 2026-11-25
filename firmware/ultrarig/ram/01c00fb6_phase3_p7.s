; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p7: 1 function, 0x01c00fb6..0x01c00fdc

; phase3_p7_go_mask_usb_updata: 0x01c00fb6..0x01c00fdc, module phase3-p7 (go_mask_usb_updata)
.type phase3_p7_go_mask_usb_updata,@function
phase3_p7_go_mask_usb_updata:
    call storage_coordination_irq_enter
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L01c00fd2
    lockset
L01c00fd2:
    csync
    call phase3_p3_nvram_set_boot_state  ; @call.xl
L01c00fda:
    goto L01c00fda
