; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; interrupt_and_stack_calls: 2 functions, 0x01c04928..0x01c049f0

; interrupt_and_stack_calls_clock_word_set: 0x01c04928..0x01c0498e, module interrupt-and-stack-calls (clock_word_set)
.type interrupt_and_stack_calls_clock_word_set,@function
interrupt_and_stack_calls_clock_word_set:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r0
    cli
    r1 = 0
    r2 = 262656
    r3 = 1000000
L01c0493e:
    r0 = [r2+0]
    ifs (r0 > -1) goto L01c0494a
    r1 = r1 + 1
    if (r1 < r3) goto L01c0493e
L01c0494a:
    r2 = 32432136
    r3 = 2000000
L01c04956:
    r0 = [r2+0]
    if ((r0 & 16384) != 0) goto L01c04962
    r1 = r1 + 1
    if (r1 < r3) goto L01c04956
L01c04962:
    r0 = 262143
    r1 = r4 & r0
    r0 = 65544
    [r0+0] = r1
    csync
    r0 = 2000
    [sp] = r0
    r0 = [sp]
    if (r0 == 0) goto L01c0498a
    r1 = sp + 0
L01c04982:
    [r1+0] += 0xFFFFFFFF
    r0 = [sp]
    if (r0 != 0) goto L01c04982
L01c0498a:
    sp += 4
    {pc, r4} = [sp++]

; interrupt_and_stack_calls_clock_mode_set: 0x01c0498e..0x01c049f0, module interrupt-and-stack-calls (clock_mode_set)
.type interrupt_and_stack_calls_clock_mode_set,@function
interrupt_and_stack_calls_clock_mode_set:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r0
    r1 = 0
    r2 = 262656
    r3 = 1000000
L01c049a2:
    r0 = [r2+0]
    ifs (r0 > -1) goto L01c049ae
    r1 = r1 + 1
    if (r1 < r3) goto L01c049a2
L01c049ae:
    r2 = 32432136
    r3 = 2000000
L01c049ba:
    r0 = [r2+0]
    if ((r0 & 16384) != 0) goto L01c049c6
    r1 = r1 + 1
    if (r1 < r3) goto L01c049ba
L01c049c6:
    r1 = 65556
    r0 = [r1+0]
    r0 = r0 >> 2
    r4 <= insert(r0, p:2, l:30)
    [r1+0] = r4
    csync
    r0 = 20000
    [sp] = r0
    r0 = [sp]
    if (r0 == 0) goto L01c049ec
    r1 = sp + 0
L01c049e4:
    [r1+0] += 0xFFFFFFFF
    r0 = [sp]
    if (r0 != 0) goto L01c049e4
L01c049ec:
    sp += 4
    {pc, r4} = [sp++]
