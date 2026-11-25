; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 1 function, 0x02004250..0x02004272

; flash_helpers_record_level: 0x02004250..0x02004272, module flash-helpers (record_level)
.type flash_helpers_record_level,@function
flash_helpers_record_level:
    [--sp] = {rets, r4}
    r4 = r0
    call record_helpers_leading_ones
    if (r0 >= r1) {
    r0 = 4
    {pc, r4} = [sp++]
    }
    r1 = r0 + 1
    r0 = b[r4+r1] (u)
    r2 = r0 + -2
    r0 = 4
    if (r2 >= 5) {  ; @if.ge.ri.s12
    r0 = r1
    }
    {pc, r4} = [sp++]
