; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201df12..0x0201df9e: vendor code (JieLi SDK or library, not reversed), as instructions
L0201df12:
    r0 = rets
    r0 = reti
    r0 = sp
    r0 = usp
    r0 = ssp
L0201df26:
    goto L0201df26
L0201df28:
    [--sp] = {rets, r5, r4}
    sp += -4
    r1 = cnum
    r5 = L01c3748d
    r2 = r0  #
    r4 = b[r5+0] (u)
    r0 = 1
    r3 = 1
    if (r4 == 0) goto L0201df42
    r3 = 0
L0201df42:
    b[sp+3] = r3
    if (r1 == 0) goto L0201df4a
    r0 = 0
L0201df4a:
    r1 = L01c3740c
    r4 = r0 + r1
    goto L0201df5c
L0201df54:
    r0 = b[sp+3] (u)
    if (r0 != 0) goto L0201df60
    csync
L0201df5c:
    r0 = b[r4+2] (u)
    if (r0 != 0) goto L0201df54
L0201df60:
    r0 = b[++r4=4] (u)
    if (r0 == 0) goto L0201df94
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201df7a
    r1 = cnum
    r0 = 1
    if (r1 == 0) goto L0201df74
    r0 = 0
L0201df74:
    call storage_platform_peer_stop  ; @call.xl
L0201df7a:
    r0 = [r2+0]
    call phase3_p4_low_power_process
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0201df94
    r1 = cnum
    r0 = 1
    if (r1 == 0) goto L0201df8e
    r0 = 0
L0201df8e:
    call storage_platform_peer_resume  ; @call.xl
L0201df94:
    r0 = 0
    b[r4+0] = r0
    csync
    sp += 4
    {pc, r5, r4} = [sp++]
