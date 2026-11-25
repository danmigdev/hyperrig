; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201ff12..0x0201ff7c: vendor code (JieLi SDK or library, not reversed), as instructions
L0201ff12:
    r1 = L02033b40
L0201ff18:
    r2 = h[r1++=4] (u)
    if (r2 == 0) goto L0201ff26
    if (r2 != r0) goto L0201ff18
    r0 = 1
    rts
L0201ff26:
    r0 = 0
    rts
L0201ff2a:
    [--sp] = {rets, r8-r4}
    sp += -8
    r6 = r2
    r8 = r1
    r2 = 0
    r3 = 0
    d[sp] = r3_r2
    h[sp] = r0
    r4 = L01c26040
    r0 = r4
    call L02040614  ; @call.xl
    r0 = sp + 0
    call phase3_p8_btif_item_read
    r7 = r0
    if (r7 != 0) goto L0201ff6e
    r5 = h[sp+2] (u)
    r7 = -761
    if (r5 > r6) goto L0201ff6e
    r0 = r8  #
    r1 = [sp+4]
    r2 = r5
    call phase3_p8_btif_buf_read
    r7 = r5
L0201ff6e:
    r0 = r4
    call L0204074c  ; @call.xl
    r0 = r7
    sp += 8
    {pc, r8-r4} = [sp++]
