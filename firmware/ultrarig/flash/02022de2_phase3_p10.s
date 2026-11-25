; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 1 function, 0x02022de2..0x02022e74

; phase3_p10_sdfile_scan: 0x02022de2..0x02022e74, module phase3-p10 (sdfile_scan)
.type phase3_p10_sdfile_scan,@function
phase3_p10_sdfile_scan:
    [--sp] = {rets, r8-r4}
    sp += -8
    r6 = r0
    r5 = r1  #
    r0 = b[r6+5] (u)
    r4 = -22
    if (r0 == 110) goto L02022df4
    if (r0 != 0) goto L02022e6e
L02022df4:
    r7 = r6 + 68
    r0 = [r7+20]
    r1 = L0203590a  ; "res"
    r0 += 18  ; @add.ri.u5
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02022e6e
    r8 = b[r6+3] (u)
    r0 = 88
    call L0203d940  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L02022e5e
    r0 = b[r6+1] (u)
    b[r4+0] = r0
    r0 = r6 + 6
    r0 = r8 & 0xFFFFFF10  #
    [r4+28] = r0
    r0 = r4  #
    b[r4+2] = r0
    call L02022bc2
    r0 = r4 + 64
    r1 = r5
    call L02022c36
    if (r0 != 0) goto L02022e52
    r3 = b[r4+2] (u)
    r2 = [r4+28]
    r1 = b[r4+0] (u)
    [sp+4] = r4
    r0 = L02023468
    r0 = r4  #
    [sp] = r0
    call L02022d14
    if (r0 == 0) goto L02022e62
L02022e52:
    r0 = r4
    call L0203d218  ; @call.xl
    r4 = -14
    goto L02022e6e
L02022e5e:
    r4 = -12
    goto L02022e6e
L02022e62:
    r0 = h[r4+8] (u)
    h[r4+12] = r0
    h[r4+14] = r0
    [r7+12] = r4
    h[r7+0] = r0
    r4 = 0
L02022e6e:
    r0 = r4
    sp += 8
    {pc, r8-r4} = [sp++]
