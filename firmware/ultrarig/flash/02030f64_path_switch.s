; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; path_switch: 1 function, 0x02030f64..0x02030f6e

; path_switch_count_request: 0x02030f64..0x02030f6e, module path-switch (count_request)
.type path_switch_count_request,@function
path_switch_count_request:
    [--sp] = rets
    call biquad_coefficients_counter  ; @call.xl
    pc = [sp++]
