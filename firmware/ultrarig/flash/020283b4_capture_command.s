; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_command: 3 functions, 0x020283b4..0x020284d6

; capture_command_prefix: 0x020283b4..0x020283ce, module capture-command (prefix)
.type capture_command_prefix,@function
capture_command_prefix:
    [--sp] = {rets, r4}
    if (r2 == 0) goto L020283ca
L020283b8:
    r2 += -1
    r3 = b[r1++=1] (u)
    r4 = b[r0++=1] (u)
    if (r4 == 0) goto L020283c6
    if (r2 == 0) goto L020283c6
    if (r4 == r3) goto L020283b8
L020283c6:
    r0 = r4 - r3
    {pc, r4} = [sp++]
L020283ca:
    r0 = 0
    {pc, r4} = [sp++]

; capture_command_decimal_core: 0x020283ce..0x020284be, module capture-command (decimal_core)
.type capture_command_decimal_core,@function
capture_command_decimal_core:
    [--sp] = {rets, r14-r4}
    r8 = L01c1f39c
    r4 = [r8+0]
    r4 += 1  ; @add.ri.u5
    r5 = r1
L020283de:
    r7 = b[r5++=1] (u)
    r6 = b[r4+r7] (u)
    if ((r6 & 8) != 0) goto L020283de
    if (r7 == 43) goto L020283f6
    if (r7 != 45) goto L020283fc
    r9 = 1
    goto L020283f8
L020283f6:
    r9 = 0
L020283f8:
    r7 = b[r5++=1] (u)
    goto L020283fe
L020283fc:
    r9 = 0
L020283fe:
    r4 = -17
    if ((r3 & r4) != 0) goto L02028418
    if (r7 != 48) goto L02028418
    r4 = b[r5+0] (u)
    r4 |= 32
    if (r4 == 120) {  ; @if.eq.ri.s12
    r7 = b[r5+1] (u)
    r5 += 2  ; @add.ri.u5
    r3 = 16
    } else {
    r7 = 48
    }
L02028418:
    r10 = 0x80000000
    if (r9 == 0) {  ; @if.eq.ri.s12
    r10 = r10 + 0xFFFFFFFF  ; @add.modimm.rri
    }
    r12 = 8
    if (r7 != 48) {  ; @if.ne.ri.s12
    r12 = 10
    }
    if (r3 == 0) goto L02028434
    r12 = r3
L02028434:
    r3 = [r8+0]
    r13 = r10 / r12 (u)
    r4 = r13 * r12
    r8 = r10 - r4
    r11 = r3 + 1
    r4 = 0
    r14 = 0
    goto L02028474
L0202844e:
    r6 = -1
    if (r4 > r13) goto L0202846c
    ifs (r14 < 0) goto L0202846c
    if (r4 != r13) goto L02028462
    r3 = r13
    ifs (r7 > r8) goto L0202846e
L02028462:
    r3 = r4 * r12
    r3 += r7  ; @add.rr
    r6 = 1
    goto L0202846e
L0202846c:
    r3 = r4
L0202846e:
    r4 = r3  #
    r7 = b[r5++=1] (u)
    r14 = r6
L02028474:
    r6 = b[r11+r7] (s)
    if ((r6 & 4) != 0) goto L02028492
    if ((r6 & 0x3) == 0) goto L02028498
    r3 = r6 & 0x3
    r6 = 55
    if (r3 != 1) {  ; @if.ne.ri.s12
    r6 = 87
    }
    r7 = r7 - r6
    goto L02028494
L02028492:
    r7 += -48
L02028494:
    ifs (r7 < r12) goto L0202844e
L02028498:
    ifs (r14 <= -1) goto L020284a8
    r10 = 0x0 - r4
    if (r9 == 0) {  ; @if.eq.ri.s12
    r10 = r4
    }
    goto L020284ac
L020284a8:
    [r0+0] = 0x22
L020284ac:
    if (r2 == 0) goto L020284ba
    r0 = r5 + -1
    if (r14 == 0) {  ; @if.eq.ri.s12
    r0 = r1
    }
    [r2+0] = r0
L020284ba:
    r0 = r10
    {pc, r14-r4} = [sp++]

; capture_command_decimal: 0x020284be..0x020284d6, module capture-command (decimal)
.type capture_command_decimal,@function
capture_command_decimal:
    [--sp] = {rets, r4}
    r3 = L01c1f3a0
    r4 = r2  #
    r3 = [r3+0]
    r2 = r1
    r1 = r0
    r0 = r3
    r3 = r4
    {rets, r4} = [sp++]
    goto capture_command_decimal_core
