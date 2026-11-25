; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 1 function, 0x0200e32e..0x0200e34e

; phase3_p13_sprintf: 0x0200e32e..0x0200e34e, module phase3-p13 (sprintf)
.type phase3_p13_sprintf,@function
phase3_p13_sprintf:
    [--sp] = {r3, r2}
    [--sp] = {rets, r4}
    sp += -8
    r4 = r1  #
    [sp+4] = r0
    r3 = sp + 16
    r2 = r4  #
    [sp] = r3
    r0 = sp + 4
    r1 = 0
    call phase3_p15_print
    sp += 8
    {rets, r4} = [sp++]
    sp += 8
    rts
