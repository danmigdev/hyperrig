; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; bond_records_and_prints: 1 function, 0x0200e03a..0x0200e07a

; bond_records_and_prints_print_b: 0x0200e03a..0x0200e07a, module bond-records-and-prints (print_b)
.type bond_records_and_prints_print_b,@function
bond_records_and_prints_print_b:
    [--sp] = {r3-r1}
    [--sp] = {rets, r5, r4}
    sp += -4
    r3 = sp + 16
    r5 = r0  #
    [sp] = r3
    r4 = L01c25394
    r1 = 160
    r0 = r4
    r2 = r5
    call L02006902
    r1 = r0
    ifs (r1 < 1) goto L0200e06a
    if (r1 >= 160) {  ; @if.ge.ri.s12
    r0 = 10
    b[r4+158] = r0
    r1 = 159
    }
    goto L0200e06c
L0200e06a:
    r1 = 0
L0200e06c:
    r0 = r4
    call link_and_print_send_line
    sp += 4
    {rets, r5, r4} = [sp++]
    sp += 12
    rts
