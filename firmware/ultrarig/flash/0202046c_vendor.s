; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0202046c..0x020204b4: vendor code (JieLi SDK or library, not reversed), as instructions
L0202046c:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r6 = r0
    r0 = r4
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L020204a4
    r0 = r6
    call phase3_p8_sdfile_flash_addr2cpu_addr
    r1 = r0
    r0 = r5
    r2 = r4
    call phase3_p8_memcpy_flash
    r0 = 0
L0202048e:
    if (r4 == r0) goto L020204a8
    r1 = b[r5+r0] (u)
    r0 += 1  ; @add.ri.u5
    if (r1 == 255) goto L0202048e
    r0 = r5
    call L0203d218  ; @call.xl
L020204a4:
    r0 = 0
    {pc, r6-r4} = [sp++]
L020204a8:
    r0 = r5
    call L0203d218  ; @call.xl
    r0 = 1
    {pc, r6-r4} = [sp++]
