; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201d1f0..0x0201d20e: vendor code (JieLi SDK or library, not reversed), as instructions
L0201d1f0:
    r1 = r0
    r2 = L01c25cf8
    r0 = 0
    if (r1 < r2) goto L0201d20c
    r2 = r2 + 480
    if (r1 < r2) {
    b[r1+31] = r0
    r0 = 1
    }
L0201d20c:
    rts
