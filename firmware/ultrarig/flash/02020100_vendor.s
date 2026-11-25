; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02020100..0x02020124: vendor code (JieLi SDK or library, not reversed), as instructions
L02020100:
    r0 = L01c21cb4
    r2 = 23042  #
    r1 = h[r0+0] (u)
    r0 = 1
    if (r1 != r2) {
    r0 = 0
    }
    rts
L02020116:
    [--sp] = rets
    r3 = r1
    r1 = r2
    r2 = r3
    call phase3_p8_norflash_read
    pc = [sp++]
