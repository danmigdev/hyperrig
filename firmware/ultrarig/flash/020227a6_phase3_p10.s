; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 1 function, 0x020227a6..0x02022808

; phase3_p10_sdfile_for_each_dir: 0x020227a6..0x02022808, module phase3-p10 (sdfile_for_each_dir)
.type phase3_p10_sdfile_for_each_dir,@function
phase3_p10_sdfile_for_each_dir:
    [--sp] = {rets, r9-r4}
    sp += -32
    r9_r8 = r1_r0
    r0 = L01c26354
    r5 = sp + 0
    r7 = r5 + 16
    r4 = r5 | 0x2  #
    r6 = [r0+20]
L020227bc:
    r0 = sp + 0
    r2 = 32
    r1 = r6
    call phase3_p10_sdfile_ext_read
    r1 = 30
    r0 = r4
    call L02001776
    r1 = h[sp] (u)
    if (r0 != r1) goto L020227ee
    r0 = r7
    r1 = r9
    call L02022514
    if (r0 == 0) goto L020227f4
    r0 = [r5+8]
    r6 += r0  #  ; @add.rr.p
    r1 = h[r5+14] (u)
    if (r1 == 0) goto L020227bc
    r0 = -255
    goto L02022804
L020227ee:
    r0 = -251
    goto L02022804
L020227f4:
    r0 = sp + 0
    r1 = r8
    rep 32 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    [r8+4] = r6
    r0 = 0
L02022804:
    sp += 32
    {pc, r9-r4} = [sp++]
