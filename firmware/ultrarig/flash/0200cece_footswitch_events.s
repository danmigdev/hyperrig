; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 1 function, 0x0200cece..0x0200cf0a

; footswitch_events_switch_line: 0x0200cece..0x0200cf0a, module footswitch-events (switch_line)
.type footswitch_events_switch_line,@function
footswitch_events_switch_line:
    [--sp] = {rets, r5, r4}
    sp += -4
    r1 = L01c268da
    r0 = b[r1+0] (u)
    r5 = b[r1+1] (u)
    r2 = b[r1+3] (u)
    r4 = L02035a18  ; "live"
    r1 = r4 + 436  #
    r3 = b[r1+2] (u)
    r2 = r4  #
    [sp] = r2
    if (r5 != 1) {  ; @if.ne.ri.s12
    r2 = r1
    }
    r1 = r4 + 1336
    r1 = [r1+r0<<2]
    r0 = r4 + 5884
    r3 += 1  ; @add.ri.u5
    call bond_records_and_prints_print_a
    sp += 4
    {pc, r5, r4} = [sp++]
