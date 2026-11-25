; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_enable: 1 function, 0x0201a9dc..0x0201a9ea

; effect_enable_clear: 0x0201a9dc..0x0201a9ea, module effect-enable (clear), effect-parameter-support (clear)
.type effect_enable_clear,@function
effect_enable_clear:
    [--sp] = rets
    r2 = r1
    r1 = 0
    call effect_enable_memset  ; @call.xl
    pc = [sp++]
