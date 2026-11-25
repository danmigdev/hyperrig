; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0203291c..0x02032b2e: vendor code (JieLi SDK or library, not reversed), as instructions
L0203291c:
    cli
    lockset
    csync
    csync
    csync
    csync
    csync
    [--sp] = {r15-r0}
    [--sp] = {psr, rets, reti}
    call L0201b13c  ; @call.xl
    {psr, rets, reti} = [sp++]
    {r15-r0} = [sp++]
    sp = usp
    [--sp] = {r15-r0}
    [--sp] = {psr, rets, reti}
    r1 = L01c1fc64
    r0 = cnum
    r1 = [r1+r0<<2]
    r0 = sp
    [r1+0] = r0
    call L02040eee  ; @call.xl
    r0 = L01c1fc78
    r1 = cnum
    r0 = [r0+r1<<2]
    r0 = [r0+0]
    sp = r0
    {psr, rets, reti} = [sp++]
    {r15-r0} = [sp++]
    usp = sp
    sp = ssp
    [--sp] = {r15-r0}
    [--sp] = {psr, rets, reti}
    call L0201b150  ; @call.xl
    {psr, rets, reti} = [sp++]
    {r15-r0} = [sp++]
    lockclr
    sti
    rti
    [--sp] = {rets, r8-r4}
    r5_r4 = r1_r0
    r1_r0 >>= 52
    r2 = 2047
    r7 = r0 & r2
    r6 = r7 + -1023
    ifs (r6 > 19) goto L020329f4
    ifs (r6 <= -1) goto L02032a40
    r0 = 1048575
    r7 = r0 >> r6
    r0 = r7 & r5
    r0 |= r4
    if (r0 == 0) goto L02032a9c
    r2 = 2281731484
    r3 = 2117592124
    r1_r0 = r5_r4
    call L02032cda
    r3_r2 = 0
    call L0203316a
    ifs (r0 < 1) goto L02032a9c
    r0 = 0x100000
    r0 >>= r6
    ifs (r5 <= 0) {  ; @ifs.le.ri.s12
    r0 = 0
    }
    r0 += r5  ; @add.rr
    r5 = r0 & ~r7
    r4 = 0
    goto L02032a9c
L020329f4:
    ifs (r6 < 52) goto L02032a08
    r1_r0 = r5_r4
    r3_r2 = r5_r4
    call L02032cda
    if (r6 != 1024) {  ; @if.ne.ri.s12
    r1_r0 = r5_r4
    }
    {pc, r8-r4} = [sp++]
L02032a08:
    r0 = r7 + -1043
    r1 = -1
    r8 = r1 >> r0
    if ((r8 & r4) == 0) goto L02032a9c
    r2 = 2281731484
    r3 = 2117592124
    r1_r0 = r5_r4
    call L02032cda
    r3_r2 = 0
    call L0203316a
    ifs (r0 < 1) goto L02032a9c
    ifs (r5 < 1) goto L02032a3c
    if (r6 != 20) goto L02032a82
    r5 += 1  ; @add.ri.u5
L02032a3c:
    r0 = r4
    goto L02032a98
L02032a40:
    r2 = 2281731484
    r3 = 2117592124
    r1_r0 = r5_r4
    call L02032cda
    r3_r2 = 0
    call L0203316a
    ifs (r0 < 1) goto L02032a9c
    ifs (r5 < 0) goto L02032a7a
    r1_r0 = r5_r4
    r1_r0 >>= 32
    r3 = r1 | r5
    r2 = r0 | r4
    if (r2 == 0) goto L02032a9c
    r5 = 1072693248
    r4 = 0
    goto L02032a9c
L02032a7a:
    r5 = 0x80000000
    r4 = 0
    goto L02032a9c
L02032a82:
    r0 = 1075
    r0 = r0 - r7
    r1 = 1
    r2 = r1 << r0
    r0 = r2 + r4
    if (r0 >= r2) {
    r1 = 0
    }
    r5 += r1  ; @add.rr
L02032a98:
    r4 = r0 & ~r8
L02032a9c:
    r1_r0 = r5_r4
    {pc, r8-r4} = [sp++]
L02032aa0:
    [--sp] = {rets, r9-r4}
    r5_r4 = r1_r0
    r5_r4 >>= 52
    r3 = 2047
    r4 &= r3
    r3 = r4 + -1023
    ifs (r3 > 19) goto L02032ae4
    ifs (r3 <= -1) goto L02032b22
    r4 = 1048575
    r3 = r4 >> r3
    r4 = r3 & r1
    r4 |= r0
    if (r4 == 0) goto L02032b16
    r4 = r1 & ~r3
    r5 = 0
    r6 = r4
    r7 = 0
    r7_r6 <<= 32
    d[r2+0] = r7_r6
    r2 = 0
    r3 = r4
    goto L02032b10
L02032ae4:
    ifs (r3 >= 52) goto L02032b16
    r3 = r4 + -1043
    r4 = -1
    r3 = r4 >> r3
    if ((r3 & r0) == 0) goto L02032b16
    r4 = 0
    r6 = r0 & ~r3
    r5 = r1
    r7 = r4
    r9 = r7 | r5
    r8 = r6 | r4
    d[r2+0] = r9_r8
    r2 = r6
    r3 = r5
L02032b10:
    {rets, r9-r4} = [sp++]
    goto L020331ce  ; @goto.l
L02032b16:
    d[r2+0] = r1_r0
    r1 = r1 & 0x80000000
    r0 = 0
    {pc, r9-r4} = [sp++]
L02032b22:
    r5 = r1 & 0x80000000
    r4 = 0
    d[r2+0] = r5_r4
    {pc, r9-r4} = [sp++]
