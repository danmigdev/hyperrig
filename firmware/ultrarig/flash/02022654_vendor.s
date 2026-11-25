; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02022654..0x020227a6: vendor code (JieLi SDK or library, not reversed), as instructions
L02022654:
    [--sp] = {rets, r10-r4}
    sp += -32
    r9 = r2
    r8 = r1
    r6 = r0
    r5 = sp + 0
    r10 = r5 + 16
    r4 = r5 | 0x2
    r7 = 32
    goto L0202269a
L0202266c:
    r0 = sp + 0
    r2 = 32
    r1 = r6
    call phase3_p10_sdfile_ext_read
    r1 = 30
    r0 = r4
    call L02001776
    r1 = h[sp] (u)
    if (r0 != r1) goto L02022696
    r0 = r10
    r1 = r9
    call L02022514
    if (r0 == 0) goto L020226a4
    r0 = h[r5+14] (u)
    if (r0 == 0) goto L02022698
    goto L020226b6
L02022696:
    r7 += -1
L02022698:
    r6 += 32
L0202269a:
    ifs (r7 >= 1) goto L0202266c
    r0 = -254
    goto L020226b8
L020226a4:
    r0 = 0
    if (r8 == 0) goto L020226b8
    r1 = sp + 0
    rep 32 {
    r2 = b[r1++=1] (u)
    b[r8++=1] = r2
    }
    goto L020226b8
L020226b6:
    r0 = 1
L020226b8:
    sp += 32
    {pc, r10-r4} = [sp++]
L020226bc:
    [--sp] = {rets, r5, r4}
    r5_r4 = r1_r0
    r3 = [++r5=8]
    r1 = r4 + 4
    r0 = r3 + 32
    call L02022654
    r3 = r0
    if (r3 != 0) goto L020226e8
    r0 = b[r4+16] (u)
    if ((r0 & 16) != 0) goto L020226e0
    r0 = [r5+0]
    [r4+8] += r0
    goto L020226e8
L020226e0:
    r0 = [r4+8]
    call L0202259a
    [r4+8] = r0
L020226e8:
    r0 = r3
    {pc, r5, r4} = [sp++]
L020226ec:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = r1 + 32
    r1 = r4 + 4
    call L02022654
    if (r0 != 0) goto L02022704
    r0 = b[r4+16] (u)
    r0 = uextra(r0, p:1, l:1)
    r0 += -1
L02022704:
    {pc, r4} = [sp++]
L02022706:
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
    r3 = [r4+12]
    r8 = r0
    r7 = sp + 0
    r0 = r7 + 4
    r2 = 32
    r1 = r3
    call phase3_p10_sdfile_ext_read
    r1 = r5  #
    r0 = [r4+8]
    r0 = r6  #
    [sp+8] = r0
    call L020224be
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L02022786
    r0 = sp + 0
    r1 = r0
    rep 9 {
    [r1++=4] = r9
    }
    r5 = L02036166  ; "app_area_head"
    r1 = sp + 39
    r2 = r5
    call phase3_p10_sdfile_open_part_dir
    if (r0 != 0) goto L0202278e
    r1 = sp + 39
    r0 = r6
    call L020224be
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L02022792
    r0 = sp + 0
    r1 = sp + 39
    r2 = r5
    call phase3_p10_sdfile_open_part_dir
    if (r0 != 0) goto L0202278e
    r5 = sp + 39
    r0 = r6
    r1 = r5
    call L020224be
    r1 = sp + 0
    r0 = r8
    r2 = r5
    goto L0202278c
L02022786:
    r1 = sp + 0
    r2 = sp + 39
    r0 = r8
L0202278c:
    call L020226bc
L0202278e:
    sp += 56
    {pc, r9-r4} = [sp++]
L02022792:
    r0 = [r7+8]
    call L0202259a
    r1 = r0 + -32
    r0 = r8  #
    [r7+8] = r1
    r2 = sp + 39
    call L020226ec
    goto L0202278e
