; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sort_and_format: 1 function, 0x02017b1a..0x02017b2a

; sort_and_format_bounded_minimum: 0x02017b1a..0x02017b2a, module sort-and-format (bounded_minimum)
.type sort_and_format_bounded_minimum,@function
sort_and_format_bounded_minimum:
    r2 = -9999
    ifs (r0 >= r2) {
    r2 = smin(r0, r1)
    }
    r0 = r2
    rts
