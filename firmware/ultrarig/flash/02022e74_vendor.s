; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02022e74..0x02022ed2: vendor code (JieLi SDK or library, not reversed), as instructions
L02022e74:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = [++r4=80]
    if (r0 == 0) goto L02022e88
    call L0203d218  ; @call.xl
    [r4+0] = 0x0
L02022e88:
    {pc, r4} = [sp++]
L02022e8a:
    [--sp] = {rets, r5, r4}
    sp += -96
    r5 = sp + 8
    r1 = r5
    rep 22 {
    r2 = [r0++=4]
    [r1++=4] = r2
    }
    r4 = 0
    h[sp+16] = r4
    r0 = b[sp+11] (u)
    r0 = r0 * 0xC
    r0 += r5  ; @add.rr
    r0 += 64
    call phase3_p10_sdf_opendir
    r3 = b[sp+10] (u)
    r2 = [sp+36]
    [sp+4] = r5
    r0 = L0202345c
    r1 = 0
    r0 = r5  #
    [sp] = r0
    call L02022d14
    if (r0 != 0) goto L02022ecc
    r4 = h[sp+16] (u)
L02022ecc:
    r0 = r4
    sp += 96
    {pc, r5, r4} = [sp++]
