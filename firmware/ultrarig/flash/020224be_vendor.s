; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020224be..0x020225aa: vendor code (JieLi SDK or library, not reversed), as instructions
L020224be:
    [--sp] = {rets, r7-r4}
    r5 = r1  #
    r2 = b[r0+0] (u)
    r4 = r0 + 1
    if (r2 != 47) {  ; @if.ne.ri.s12
    r4 = r0
    }
    r1 = 47
    r0 = r4
    call L020282f4  ; @call.xl
    if (r0 == 0) goto L020224dc
    r6 = r0 - r4
    goto L020224e6
L020224dc:
    r0 = r4
    call L020283a8  ; @call.xl
    r6 = r0
L020224e6:
    r7 = r6
    ifs (r6 >= 15) {  ; @ifs.ge.ri.s12
    r7 = 15
    }
    r0 = r5
    r1 = r4
    r2 = r7
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 0
    b[r5+r7] = r0
    r0 = r5
    r1 = r7
    call phase3_p10_sdfile_str_to_upper
    r1 = r4 + r6
    r2 = b[r1+0] (u)
    r0 = r1 + 1
    if (r2 != 47) {  ; @if.ne.ri.s12
    r0 = r1
    }
    {pc, r7-r4} = [sp++]
L02022514:
    [--sp] = {rets, r6-r4}
    sp += -40
    r4 = 0
    b[sp+36] = r4
    r5 = sp + 20
    r2 = r5 + 8
    r3 = r0 + 8
    rep 8 {
    r6 = b[r3++=1] (u)
    b[r2++=1] = r6
    }
    r2 = r5
    rep 8 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    b[sp+16] = r4
    r6 = sp + 0
    r0 = r6 + 8
    r2 = r1 + 8
    rep 8 {
    r3 = b[r2++=1] (u)
    b[r0++=1] = r3
    }
    r0 = r6
    rep 8 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r1 = 16
    r0 = r5
    call phase3_p10_sdfile_str_to_upper
    r1 = 16
    r0 = r6
    call phase3_p10_sdfile_str_to_upper
    r0 = 240
    r1 = 0
    goto L02022586
L0202255c:
    r2 = b[r5++=1] (u)
    if ((r1 & 0xFF) == 0) goto L02022570
    r3 = 0
    if (r2 != 46) {  ; @if.ne.ri.s12
    r3 = r1
    }
    r1 = r3
    goto L02022582
L02022570:
    r3 = b[r6+0] (u)
    if (r2 != r3) goto L0202257c
    r1 = 0
    if (r2 != 0) goto L02022582
    goto L0202258c
L0202257c:
    r1 = 1
    if (r3 != 42) goto L02022592
L02022582:
    r0 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02022586:
    if ((r0 & 0xFF) != 0) goto L0202255c
L0202258c:
    r0 = r4
    sp += 40
    {pc, r6-r4} = [sp++]
L02022592:
    if (r3 != 63) {  ; @if.ne.ri.s12
    r4 = -1
    }
    goto L0202258c
L0202259a:
    r1 = L01c26354
    r2 = [r1+0]
    r0 = r0 - r2  #
    r1 = [r1+8]
    r0 += r1  ; @add.rr
    rts
