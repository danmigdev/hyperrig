; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_command: 1 function, 0x0200a7de..0x0200a868

; capture_command_tenths: 0x0200a7de..0x0200a868, module capture-command (tenths)
.type capture_command_tenths,@function
capture_command_tenths:
    [--sp] = {rets, r6-r4}
    r4 = b[r0+0] (u)
    if (r4 == 45) goto L0200a7ec
    r3 = 0
    if (r4 != 43) goto L0200a7f8
L0200a7ec:
    r3 = 1
    if (r4 != 45) {  ; @if.ne.ri.s12
    r3 = 0
    }
    r4 = b[++r0=1] (u)
L0200a7f8:
    r2 = r4 + -48
    r5 = r2.b0 (u)
    r2 = 0
    if (r5 > 9) goto L0200a864
    r0 += 2  ; @add.ri.u5
    r5 = 0
    r2 = 100000
    goto L0200a820
L0200a810:
    r4 = r4.b0 (s)
    r4 += r5  ; @add.rr
    r5 = r4 + -48
    ifs (r5 > r2) goto L0200a862
    r4 = b[r0+-1] (u)
    r0 += 1  ; @add.ri.u5
L0200a820:
    r6 = r4 + -48
    r6 = r6.b0 (u)
    r5 = r5 * 0xA
    if (r6 <= 9) goto L0200a810
    if (r4 != 46) goto L0200a84a
    r6 = b[r0+-1] (s)
    r2 = r6 + -48
    r4 = r2.b0 (u)
    r2 = 0
    if (r4 > 9) goto L0200a864
    r0 = r5 + r6  #
    r4 = b[r0+0] (u)
    r5 = r0 + -48
L0200a84a:
    r0 = r4 | 0x20
    r0 = r0.b0 (u)
    if (r0 != 32) goto L0200a862
    r0 = 0x0 - r5
    if (r3 != 0) goto L0200a85c
    r0 = r5
L0200a85c:
    [r1+0] = r0
    r2 = 1
    goto L0200a864
L0200a862:
    r2 = 0
L0200a864:
    r0 = r2
    {pc, r6-r4} = [sp++]
