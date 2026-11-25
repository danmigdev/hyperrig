; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02020616..0x02020648: vendor code (JieLi SDK or library, not reversed), as instructions
L02020616:
    r0 = L01c26090
    r1 = r0 + 616
    r2 = b[r1+7] (u)
    r2 = uextra(r2, p:1, l:1)  #
    r3 = b[r1+4] (u)
    r2 = r2 * 0xC  #
    r1 = [r1+0]
    r0 += r2  ; @add.rr
    {r2, r0} = [r0+]
    r2 *= r3
    r3 = 100
    r2 = r2 / r3 (u)
    r2 += r0  ; @add.rr
    r0 = 1
    if (r1 <= r2) {
    r0 = 0
    }
    rts
