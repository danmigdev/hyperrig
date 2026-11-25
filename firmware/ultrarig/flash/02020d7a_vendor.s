; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02020d7a..0x02020e1a: vendor code (JieLi SDK or library, not reversed), as instructions
L02020d7a:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = 40
    call L0203d940  ; @call.xl
    if (r0 == 0) goto L02020d8a
    [r4+0] = r0
L02020d8a:
    {pc, r4} = [sp++]
L02020d8c:
    [--sp] = {rets, r8-r4}
    r6 = 561
    r8 = L01c26890
    r7 = [r8+r6<<2]
    r4 = r0
    r0 = r4 + 32
    call L02020d7a
    r5 = r0
    if (r7 == 0) goto L02020dd6
    call L02020d7a
    r1 = [r8+r6<<2]
    r6 = r0  #
    [r5+4] = r1
    r5 += 18  ; @add.ri.u5
    r1 = L02036035  ; "EXT_RESERVED"
    r2 = 16
    r0 = r5
    call phase3_p8_memcpy_flash
    r0 = r5
    call L020283a8  ; @call.xl
    r1 = 0
    b[r5+r0] = r1
    r0 = 3
    r5 = r6
    goto L02020dd8
L02020dd6:
    r0 = 2
L02020dd8:
    b[r4+165] = r0
    r0 = 560
    r0 = [r8+r0<<2]
    r1 = r4 + 48  #
    [r4+36] = r0
    r0 = 97
    b[r1+2] = r0
    r0 = 112
    b[r1+3] = r0
    r0 = 562  #
    b[r1+4] = r0
    r2 = 0
    b[r1+5] = r2
    r0 = [r8+r0<<2]
    r1 = r5 + 4
    [r1+0] = r0
    r0 = 114
    b[r1+14] = r0
    r0 = 101
    b[r1+15] = r0
    r0 = 115
    b[r5+20] = r0
    r0 = 0
    b[r5+21] = r2
    {pc, r8-r4} = [sp++]
