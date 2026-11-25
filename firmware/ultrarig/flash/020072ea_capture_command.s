; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_command: 1 function, 0x020072ea..0x02007324

; capture_command_slot_parse: 0x020072ea..0x02007324, module capture-command (slot_parse)
.type capture_command_slot_parse,@function
capture_command_slot_parse:
    [--sp] = {rets, r5, r4}
    sp += -4
    r5_r4 = r1_r0
    r0 = [r4+0]
    r1 = sp + 0
    r2 = 10
    call capture_command_decimal  ; @call.xl
    r1 = -1
    ifs (r0 >= r5) goto L0200731e
    ifs (r0 < 0) goto L0200731e
    r3 = [r4+0]
    r2 = [sp]
    if (r2 == r3) goto L0200731e
L0200730e:
    r1 = b[r2++=1] (u)
    if (r1 == 32) goto L0200730e
    r1 = r2 + -1
    [sp] = r1
    r1 = r0  #
    [r4+0] = r1
L0200731e:
    r0 = r1
    sp += 4
    {pc, r5, r4} = [sp++]
