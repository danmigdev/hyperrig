; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; rate_leaves: 1 function, 0x01c09cda..0x01c09cfe

; rate_leaves_quantize: 0x01c09cda..0x01c09cfe, module rate-leaves (quantize)
.type rate_leaves_quantize,@function
rate_leaves_quantize:
    [--sp] = {rets, r6-r4}
    r4 = r1 - r0
    r5 = r4 / r2 (s)
    r4 = r5 * r2  #
    [r3+0] = r5
    r4 = r4 + r0
    r6 = r4 - r1
    r0 = r1
    ifs (r6 >= r2) {
    r0 = r4
    }
    r1 = r1 - r4
    ifs (r1 >= r2) {
    r0 = r4
    }
    {pc, r6-r4} = [sp++]
