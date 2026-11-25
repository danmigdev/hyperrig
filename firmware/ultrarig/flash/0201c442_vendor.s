; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201c442..0x0201c474: vendor code (JieLi SDK or library, not reversed), as instructions
L0201c442:
    [--sp] = {rets, r5, r4}
    r3 = r1 << 2
    r4 = r0 * 0x14
    r0 = r4 + r3
    r3 = L01c26890
    r0 += r3  ; @add.rr
    r0 = r0 + 2560
    r5 = r1 & 0xF
    r5 = r5 << 2
    r4 += r5  ; @add.rr
    r3 += r4  ; @add.rr
    r3 = r3 + 2600
    r1 = r1.b0 (s)
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r3 = r0
    }
    r0 = 0
    [r3+0] = r2
    {pc, r5, r4} = [sp++]
