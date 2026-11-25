; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02022808..0x02022910: vendor code (JieLi SDK or library, not reversed), as instructions
L02022808:
    [--sp] = {rets, r6-r4}
    sp += -56
    r4 = r0
    r2 = sp + 39
    r0 = 0
    r3 = r2
    rep 17 {
    b[r3++=1] = r0
    }
    r0 = r1
    r1 = r2
    call L020224be
    r5 = r0
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02022856
    r0 = sp + 0
    r0 += 4  ; @add.ri.u5
    r1 = sp + 39
    call phase3_p10_sdfile_for_each_dir
    if (r0 != 0) goto L02022868
    r0 = b[sp+16] (u)
    r1 = r0 & 0xFFFFFF0F
    r0 = -255
    if (r1 != 3) goto L02022868
    r6 = sp + 39
    r0 = r5
    r1 = r6
    call L020224be
    r1 = sp + 0
    r0 = r4
    r2 = r6
    call L020226bc
    goto L02022868
L02022856:
    r0 = r4 + 4
    r1 = sp + 39
    call phase3_p10_sdfile_for_each_dir
    if (r0 != 0) goto L02022868
    [r4+8] += 32  ; @rmw.add.s12
    [r4+12] += -32
    r0 = 0
L02022868:
    sp += 56
    {pc, r6-r4} = [sp++]
L0202286c:
    [--sp] = {rets, r9-r4}
    sp += -56
    r5 = sp + 39
    r9 = 0
    r2 = r5
    rep 17 {
    b[r2++=1] = r9
    }
    r4 = L01c26354
    r6 = r1  #
    r3 = [r4+16]
    r8 = r0
    r7 = sp + 0
    r0 = r7 + 4
    r2 = 32
    r1 = r3
    call phase3_p10_sdfile_ext_read
    r1 = r5  #
    r0 = [r4+16]
    r0 = r6  #
    [sp+8] = r0
    call L020224be
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L020228ec
    r0 = sp + 0
    r1 = r0
    rep 9 {
    [r1++=4] = r9
    }
    r5 = L02036035  ; "EXT_RESERVED"
    r1 = sp + 39
    r2 = r5
    call phase3_p10_sdfile_open_part_dir
    if (r0 != 0) goto L020228f6
    r1 = sp + 39
    r0 = r6
    call L020224be
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L020228fa
    r0 = sp + 0
    r1 = sp + 39
    r2 = r5
    call phase3_p10_sdfile_open_part_dir
    if (r0 != 0) goto L020228f6
    r5 = sp + 39
    r0 = r6
    r1 = r5
    call L020224be
    r1 = sp + 0
    r0 = r8
    r2 = r5
    goto L020228f2
L020228ec:
    r1 = sp + 0
    r2 = sp + 39
    r0 = r8
L020228f2:
    call L020226bc
L020228f6:
    sp += 56
    {pc, r9-r4} = [sp++]
L020228fa:
    r0 = [r7+8]
    call L0202259a
    r1 = r0 + -32
    r0 = r8  #
    [r7+8] = r1
    r2 = sp + 39
    call L020226ec
    goto L020228f6
