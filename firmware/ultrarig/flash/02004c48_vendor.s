; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02004c48..0x02004c8a: vendor code (JieLi SDK or library, not reversed), as instructions
L02004c48:
    r2 = r0 & 0xFFFFFFFE
    if (r2 != 148) goto L02004c6e
    r0 = r0 + -142
    r2 = 1
    r2 <<= r0
    r0 = 0x51000
    if (r1 == 0) {  ; @if.eq.ri.s12
    r1 = [r0+0]
    r1 = r1 & ~r2
    } else {
    r1 = [r0+0]
    r1 |= r2
    }
    [r0+0] = r1
    rts
L02004c6e:
    if (r0 != 150) goto L02004c88
    r0 = 92684
    r2 = [r0+0]
    r3 = r2 & 0xFFFFFF9F
    r2 = r2 | 0x60
    if (r1 != 0) goto L02004c86
    r2 = r3
L02004c86:
    [r0+0] = r2
L02004c88:
    rts
