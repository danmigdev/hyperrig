; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201dfa2..0x0201dfd8: vendor code (JieLi SDK or library, not reversed), as instructions
sdk_dac_idle_query:
    r0 = 77568
    r0 = [r0+0]
    r0 = r0 >> 5
    r1 = 1
    r0 = r1 & ~r0
    rts
sdk_alnk_idle_query:
    r0 = 77316
    r1 = 13107  #
    r2 = h[r0+0] (u)
    r0 = 0
    if ((r2 & r1) != 0) goto L0201dfd6
    r0 = 86276
    r2 = h[r0+0] (u)
    r0 = 1
    if ((r2 & r1) != 0) {
    r0 = 0
    }
L0201dfd6:
    rts
