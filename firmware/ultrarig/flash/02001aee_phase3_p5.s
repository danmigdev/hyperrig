; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 1 function, 0x02001aee..0x02001b40

; phase3_p5_usb_write_power: 0x02001aee..0x02001b40, module phase3-p5 (usb_write_power)
.type phase3_p5_usb_write_power,@function
phase3_p5_usb_write_power:
    [--sp] = {rets, r4}
    if (r0 == 0) goto L02001afe
    r0 = 90113
    r1 = 96
    b[r0+0] = r1
    {pc, r4} = [sp++]
L02001afe:
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fc4c
    r0 = cnum
    r1 = [r4+r0<<2]
    r2 = r1 + 1
    [r4+r0<<2] = r2
    if (r1 != 0) goto L02001b1c
    lockset
L02001b1c:
    csync
    r0 = 1
    r1 = 96
    call L02001ac0
    csync
    r0 = cnum
    r1 = [r4+r0<<2]
    r1 += -1
    [r4+r0<<2] = r1
    if (r1 != 0) goto L02001b38
    lockclr
L02001b38:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]
