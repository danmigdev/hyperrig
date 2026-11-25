; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x0202def2..0x0202df04

; effect_setup_demand: 0x0202def2..0x0202df04, module effect-setup (demand)
.type effect_setup_demand,@function
effect_setup_demand:
    [--sp] = rets
    r2 = h[r0+82] (s)
    r1 = h[r0+70] (s)
    r0 = b[r0+0] (u)
    call effect_setup_demand_by_type
    pc = [sp++]
