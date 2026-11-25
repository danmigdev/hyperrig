; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sort_and_format: 1 function, 0x02017ada..0x02017af8

; sort_and_format_wide_distance: 0x02017ada..0x02017af8, module sort-and-format (wide_distance)
.type sort_and_format_wide_distance,@function
sort_and_format_wide_distance:
    [--sp] = {rets, r7-r4}
    r4 = r0 - r2
    r5 = r1 - r3 - !c
    r3_r2 = r5_r4
    r3_r2 >>>= 63
    r6 = r4 + r2
    r7 = r5 + r3 + c
    r1 = r7 ^ r3
    r0 = r6 ^ r2
    {pc, r7-r4} = [sp++]
