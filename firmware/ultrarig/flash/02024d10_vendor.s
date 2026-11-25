; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02024d10..0x02024d34: vendor code (JieLi SDK or library, not reversed), as instructions
L02024d10:
    [--sp] = {rets, r4}
    r4 = r0
    if (r4 >= 3) {  ; @if.ge.ri.s12
    r4 = 3
    }
    r0 = 81
    call L02055e38  ; @call.xl
    r0 = r0 & 0xFFFFFFFC
    r1 = r0 | r4
    r0 = 81
    call L02055a4e  ; @call.xl
    {pc, r4} = [sp++]
