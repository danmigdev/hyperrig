; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 2 functions, 0x02007008..0x0200704e

; link_and_print_send_line: 0x02007008..0x02007010, module link-and-print (send_line)
.type link_and_print_send_line,@function
link_and_print_send_line:
    [--sp] = rets
    call command_services_console_send
    pc = [sp++]

; link_and_print_print: 0x02007010..0x0200704e, module link-and-print (print)
.type link_and_print_print,@function
link_and_print_print:
    [--sp] = {r3-r1}
    [--sp] = {rets, r5, r4}
    sp += -4
    r3 = sp + 16
    r5 = r0  #
    [sp] = r3
    r4 = L01c24358
    r1 = 200
    r0 = r4
    r2 = r5
    call L02006902
    r1 = r0
    ifs (r1 < 1) goto L02007040
    if (r1 >= 200) {  ; @if.ge.ri.s12
    r0 = 10
    b[r4+198] = r0
    r1 = 199
    }
    goto L02007042
L02007040:
    r1 = 0
L02007042:
    r0 = r4
    call link_and_print_send_line
    sp += 4
    {rets, r5, r4} = [sp++]
    sp += 12
    rts
