; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02020e34..0x02020f02: vendor code (JieLi SDK or library, not reversed), as instructions
L02020e34:
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
    if (r0 == 0) goto L02020e52
    r6 = r0 - r4
    goto L02020e5c
L02020e52:
    r0 = r4
    call L020283a8  ; @call.xl
    r6 = r0
L02020e5c:
    r7 = r6
    ifs (r6 >= 15) {  ; @ifs.ge.ri.s12
    r7 = 15
    }
    r0 = r5
    r1 = r4
    r2 = r7
    call phase3_p8_memcpy_flash
    r0 = 0
    b[r5+r7] = r0
    r0 = r5
    r1 = r7
    call phase3_p9_sdfile_str_to_upper
    r1 = r4 + r6
    r2 = b[r1+0] (u)
    r0 = r1 + 1
    if (r2 != 47) {  ; @if.ne.ri.s12
    r0 = r1
    }
    {pc, r7-r4} = [sp++]
L02020e88:
    [--sp] = {rets, r7-r4}
    sp += -36
    r7 = r1
    r1 = r0
    r5 = sp + 19
    r4 = 0
    r0 = r5
    r6 = sp + 2
    rep 17 {
    b[r0++=1] = r4
    }
    r0 = r6
    rep 17 {
    b[r0++=1] = r4
    }
    r2 = 16
    r0 = r5
    call phase3_p8_memcpy_flash
    r2 = 16
    r1_r0 = r7_r6
    call phase3_p8_memcpy_flash
    r1 = 16
    r0 = r5
    call phase3_p9_sdfile_str_to_upper
    r1 = 16
    r0 = r6
    call phase3_p9_sdfile_str_to_upper
    r0 = 240
    r1 = 0
    goto L02020eee
L02020ec4:
    r2 = b[r5++=1] (u)
    if ((r1 & 0xFF) == 0) goto L02020ed8
    r3 = 0
    if (r2 != 46) {  ; @if.ne.ri.s12
    r3 = r1
    }
    r1 = r3
    goto L02020eea
L02020ed8:
    r3 = b[r6+0] (u)
    if (r2 != r3) goto L02020ee4
    r1 = 0
    if (r2 != 0) goto L02020eea
    goto L02020ef4
L02020ee4:
    r1 = 1
    if (r3 != 42) goto L02020efa
L02020eea:
    r0 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02020eee:
    if ((r0 & 0xFF) != 0) goto L02020ec4
L02020ef4:
    r0 = r4
    sp += 36
    {pc, r7-r4} = [sp++]
L02020efa:
    if (r3 != 63) {  ; @if.ne.ri.s12
    r4 = -1
    }
    goto L02020ef4
