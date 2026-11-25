; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 1 function, 0x0200a72e..0x0200a768

; link_and_print_tenths: 0x0200a72e..0x0200a768, module link-and-print (tenths)
.type link_and_print_tenths,@function
link_and_print_tenths:
    [--sp] = {rets, r5, r4}
    sp += -8
    r3 = abs(r1)
    r4 = 10
    r4 = r3 / r4 (s)
    r4 = r4 * 0xA  #
    [sp] = r4
    r3 = r3 - r4
    r4 = L02035810
    r5 = r4 + 5
    [sp+4] = r3
    if (r2 != 0) goto L0200a752
    r5 = r4
L0200a752:
    r3 = r4 + 15
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r3 = r5
    }
    r2 = r4 + 1158
    r1 = 12
    call L0200691e
    sp += 8
    {pc, r5, r4} = [sp++]
