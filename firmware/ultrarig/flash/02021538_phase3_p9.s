; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 1 function, 0x02021538..0x020215ca

; phase3_p9_sdf_opendir_by_name: 0x02021538..0x020215ca, module phase3-p9 (sdf_opendir_by_name)
.type phase3_p9_sdf_opendir_by_name,@function
phase3_p9_sdf_opendir_by_name:
    [--sp] = {rets, r9-r4}
    sp += -52
    r4 = r0
    r2 = sp + 3
    r8 = 0
    r0 = r2
    rep 17 {
    b[r0++=1] = r8
    }
    r0 = r1
    r1 = r2
    call L02020e34
    r9 = r0
    r0 = r4
    call phase3_p9_sdf_opendir
    r0 = 1
    r7 = r4 + -60
    b[r7+1] = r0
    r5 = sp + 20
    r6 = r5 + 16
    goto L020215a8
L02021566:
    r1 = sp + 20
    r0 = r4
    call L020214b6
    if (r0 != 0) goto L020215b8
    r0 = b[r5+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 3) goto L0202157e
    r0 = b[r7+0] (u)
    if (r0 == 2) goto L02021588
L0202157e:
    r1 = sp + 3
    r0 = r6
    call L02020e88
    if (r0 == 0) goto L0202158e
L02021588:
    r0 = h[r5+14] (u)
    if (r0 == 0) goto L02021566
    goto L02021596
L0202158e:
    r0 = [r5+4]
    r0 = r4  #
    [r7+60] = r0
    call phase3_p9_sdf_opendir
L02021596:
    r1 = sp + 3
    r0 = r1
    rep 17 {
    b[r0++=1] = r8
    }
    r0 = r9
    call L02020e34
    r9 = r0
L020215a8:
    r0 = b[r9+0] (u)
    r1 = b[sp+3] (u)
    r0 |= r1
    if ((r0 & 0xFF) != 0) goto L02021566
L020215b8:
    r0 = 0
    b[r7+1] = r0
    r0 = b[r9+0] (u)
    if (r0 == 0) goto L020215c6
    r0 = -255
L020215c6:
    sp += 52
    {pc, r9-r4} = [sp++]
