; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020201dc..0x02020210: vendor code (JieLi SDK or library, not reversed), as instructions
L020201dc:
    [--sp] = {rets, r8-r4}
    sp += -256
    r4 = r2
    r8 = r1
    r6 = r0
    goto L02020200
L020201e8:
    r5 = sp + 0
    r0 = r5
    r1 = r8
    r2 = r7
    call L02020116
    r0 = r5
    r1 = r6
    r2 = r7
    call phase3_p8_sfc_write
    r8 += r7
    r6 += r7  ; @add.rr
    r4 = r4 - r7
L02020200:
    r7 = r4
    if (r4 >= 256) {  ; @if.ge.ri.s12
    r7 = 256
    }
    if (r7 != 0) goto L020201e8
    sp += 256
    {pc, r8-r4} = [sp++]
