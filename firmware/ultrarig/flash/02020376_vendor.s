; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02020376..0x02020450: vendor code (JieLi SDK or library, not reversed), as instructions
L02020376:
    [--sp] = {rets, r9-r4}
    r8 = r0
    r0 = 623
    r6 = L01c26090
    r1 = b[r6+r0] (u)
    r0 = [r8+4]
    r5 = [r8+0]
    if ((r1 & 4) != 0) goto L020203c6
    r7 = uextra(r0, p:12, l:16)
    r4 = 0
    r9 = 622
    goto L020203be
L020203a0:
    r0 = 2
    r1 = r5
    call phase3_p8_sfc_erase
    if (r0 == 0) goto L020203fc
    r0 = b[r6+r9] (u)
    if (r0 == 0) goto L020203b8
    r0 = r0 << 1
    call L0203feb8  ; @call.xl
L020203b8:
    r4 += 1  ; @add.ri.u5
    r5 = r5 + 4096
L020203be:
    r0 = r4.l (u)
    if (r0 < r7) goto L020203a0
    goto L020203f6
L020203c6:
    r7 = uextra(r0, p:8, l:16)
    r4 = 0
    r9 = 622
    goto L020203f0
L020203d2:
    r0 = 3
    r1 = r5
    call phase3_p8_sfc_erase
    if (r0 == 0) goto L020203fc
    r0 = b[r6+r9] (u)
    if (r0 == 0) goto L020203ea
    r0 = r0 << 1
    call L0203feb8  ; @call.xl
L020203ea:
    r4 += 1  ; @add.ri.u5
    r5 = r5 + 256
L020203f0:
    r0 = r4.l (u)
    if (r0 < r7) goto L020203d2
L020203f6:
    r0 = 0
    h[r8+8] = r0
L020203fc:
    {pc, r9-r4} = [sp++]
L020203fe:
    [--sp] = {rets, r5, r4}
    sp += -4
    r0 = 1437248085
    r4 = L01c26090
    r0 = r4  #
    [sp] = r0
    call L02020376
    r0 = r4 + 12
    call L02020376
    r5 = r4 + 616
    r0 = b[r5+7] (u)
    r0 &= 4294967293
    b[r5+7] = r0
    r1 = [r4+0]
    r0 = sp + 0
    r2 = 4
    call phase3_p8_sfc_write
    r2 = 512  #
    r0 = b[r5+7] (u)
    r0 = uextra(r0, p:1, l:1)
    r0 = r0 * 0xC
    r0 = [r0+r4]
    r0 += 4  ; @add.ri.u5
    [r5+0] = r0
    r0 = r4 + 24
    r1 = 0
    call effect_enable_memset  ; @call.xl
    sp += 4
    {pc, r5, r4} = [sp++]
