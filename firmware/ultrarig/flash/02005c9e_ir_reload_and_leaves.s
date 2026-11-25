; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_reload_and_leaves: 1 function, 0x02005c9e..0x02005cb8

; ir_reload_and_leaves_buffer_free: 0x02005c9e..0x02005cb8, module ir-reload-and-leaves (buffer_free)
.type ir_reload_and_leaves_buffer_free,@function
ir_reload_and_leaves_buffer_free:
    [--sp] = rets
    r1 = L01c26890
    r0 = [++r1=256]
    r2 = 0
    [r1+0] = r2
    [r1+4] = r2
    call L0203d218  ; @call.xl
    pc = [sp++]
