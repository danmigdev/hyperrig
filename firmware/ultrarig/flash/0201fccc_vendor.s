; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201fccc..0x0201fd16: vendor code (JieLi SDK or library, not reversed), as instructions
L0201fccc:
    [--sp] = {rets, r6-r4}
    sp += -8
    r5 = r2
    r4 = r1
    r6 = r0
    call L0201fb7a
    if (r0 == 0) goto L0201fce8
    r3 = 0
    r0 = r6
    r1 = r4
    r2 = r5
    call phase3_p8_syscfg_bin_group_read
    goto L0201fd12
L0201fce8:
    r0 = 0
    r1 = 0
    d[sp] = r1_r0
    h[sp] = r6
    r0 = sp + 0
    call L0201fc00
    if (r0 != 0) goto L0201fd12
    r6 = h[sp+2] (u)
    r0 = -1022
    if (r6 > r5) goto L0201fd12
    r0 = r4  #
    r1 = [sp+4]
    r2 = r6
    call phase3_p8_bin_buf_read
    r0 = r6
L0201fd12:
    sp += 8
    {pc, r6-r4} = [sp++]
