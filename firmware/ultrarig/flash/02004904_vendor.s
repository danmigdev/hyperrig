; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02004904..0x02004988: vendor code (JieLi SDK or library, not reversed), as instructions
L02004904:
    r2 = r0 & 0xFFFFFFFE
    if (r2 != 148) goto L02004928
    r0 = r0 + -146
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
L02004928:
    rts
L0200492a:
    r2 = r0 & 0xFFFFFFFE
    if (r2 == 150) goto L02004954
    if (r2 != 148) goto L02004986
    r0 = r0 + -148
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
L02004954:
    r3 = 65551
    r2 = 92684
    [r2+0] |= r3
    if (r0 == 151) goto L02004978
    if (r0 != 150) goto L02004986
    r0 = [r2+0]
    r3 = r0 & 0xFFFDFFFF
    r0 |= 131072
    if (r1 == 0) goto L02004982
    goto L02004984
L02004978:
    r0 = [r2+0]
    r3 = r0 & 0xFFFBFFFF
    r0 |= 262144
    if (r1 != 0) goto L02004984
L02004982:
    r0 = r3
L02004984:
    [r2+0] = r0
L02004986:
    rts
