; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02026b52..0x02026ba4: vendor code (JieLi SDK or library, not reversed), as instructions
L02026b52:
    [--sp] = {r3, r2}
    [--sp] = {rets, r6-r4}
    sp += -4
    r6 = r1
    r4 = r0
    r0 = 17
    call L0204bc90  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02026b98
    r2 = sp + 20
    r1 = r6  #
    [sp] = r2
    call L02026906
    r0 = b[r4+154] (u)
    if (r0 == 1) {  ; @if.eq.ri.s12
    r0 = b[r5+28] (u)
    r0 |= 1
    b[r5+28] = r0
    }
    r0 = [r4+236]
    r1 = r5
    call L0204ba62  ; @call.xl
    sp += 4
    {rets, r6-r4} = [sp++]
    sp += 8
    rts
L02026b98:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02026ba2:
    goto L02026ba2
