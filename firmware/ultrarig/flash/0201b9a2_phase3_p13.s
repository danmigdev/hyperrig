; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 2 functions, 0x0201b9a2..0x0201b9f6

; phase3_p13_unrequest_irq: 0x0201b9a2..0x0201b9e2, module phase3-p13 (unrequest_irq)
.type phase3_p13_unrequest_irq,@function
phase3_p13_unrequest_irq:
    [--sp] = rets
    r1 = 29883904
    r2 = 0
    [r1+r0<<2] = r2
    r1 = r0 >> 3
    r2 = 32436480
    r2 <= insert(r1, p:2, l:5)
    r0 = r0 << 2
    r0 = r0 & 0x1C
    r3 = 15
    r3 <<= r0
    call storage_platform_gate_disable
    [r2+0] &= ~r3
    r0 = 32436992
    r0 <= insert(r1, p:2, l:5)
    [r0+0] &= ~r3
    call storage_platform_gate_enable
    pc = [sp++]

; phase3_p13_get_device_descriptor: 0x0201b9e2..0x0201b9f6, module phase3-p13 (get_device_descriptor)
.type phase3_p13_get_device_descriptor,@function
phase3_p13_get_device_descriptor:
    r1 = L02035085
    r2 = r0
    rep 18 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = 81
    b[r0+11] = r1
    rts
