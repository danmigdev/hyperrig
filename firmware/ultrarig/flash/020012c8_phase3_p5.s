; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 1 function, 0x020012c8..0x020012f2

; phase3_p5_event_pool_init: 0x020012c8..0x020012f2, module phase3-p5 (event_pool_init)
.type phase3_p5_event_pool_init,@function
phase3_p5_event_pool_init:
    [--sp] = rets
    r0 = 292
    call L0203c15c  ; @call.xl
    r1 = L01c1f180
    [r1+332] = r0
    if (r0 == 0) goto L020012ee
    r1 = r0 + 36
    r2 = 256
    call L020012ae
    r0 = 0
    pc = [sp++]
L020012ee:
    r0 = -12
    pc = [sp++]
