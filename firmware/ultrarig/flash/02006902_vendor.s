; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02006902..0x02006932: vendor code (JieLi SDK or library, not reversed), as instructions
L02006902:
    [--sp] = rets
    sp += -4
    [sp] = r0
    if (r1 != 0) {  ; @if.ne.ri.s12
    r0 += r1  ; @add.rr
    r1 = r0 + -1
    r0 = sp + 0
    } else {
    r1_r0 = 0
    }
    call phase3_p15_print
    sp += 4
    pc = [sp++]
L0200691e:
    [--sp] = {r3}
    [--sp] = rets
    sp += -4
    r3 = sp + 8
    [sp] = r3
    call L02006902
    sp += 4
    {rets} = [sp++]
    sp += 4
    rts
