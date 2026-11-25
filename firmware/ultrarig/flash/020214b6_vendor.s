; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020214b6..0x02021538: vendor code (JieLi SDK or library, not reversed), as instructions
L020214b6:
    [--sp] = {rets, r5, r4}
    r5 = r0
    r4 = r1  #
    r0 = [r5+8]
    r2 = [r5+4]
    r1 = r2 + r0
    r0 = r4  #
    [r5+4] = r1
    r2 = 32
    call phase3_p8_memcpy_flash
    r0 = r4 + 2
    r1 = 30
    call L02001776
    r1 = r0  #
    r2 = h[r4+0] (u)
    r0 = -251
    if (r1 != r2) goto L02021514
    r0 = [r5+0]
    r1 = [r5+-40]
    if (r0 <= r1) goto L02021516
    r1 = r5 + -64
    r2 = b[r1+5] (u)
    if (r2 != 1) goto L020214f8
    r3 = b[r1+4] (u)
    if (r3 != 2) goto L02021528
L020214f8:
    [r5+8] = 0x20
    r3 = [r4+4]
    r3 += r0  ; @add.rr
    r0 = r3 + -32
    [++r4=4] = r0
    r0 = 0
    if (r2 != 0) goto L02021514
    r1 = b[r1+4] (u)
    if (r1 != 2) {  ; @if.ne.ri.s12
    [r4+0] = r3
    }
L02021514:
    {pc, r5, r4} = [sp++]
L02021516:
    r0 = [r4+8]
    [r5+8] = r0
    r1 = [r5+4]
    r1 += 32
    [r4+4] = r1
    r0 += -32
    [r4+8] = r0
    r0 = 0
    {pc, r5, r4} = [sp++]
L02021528:
    r0 = [r4+4]
    call phase3_p8_sdfile_flash_addr2cpu_addr
    [r4+4] = r0
    [r5+8] = 0x20
    r0 = 0
    {pc, r5, r4} = [sp++]
