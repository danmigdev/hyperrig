; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 1 function, 0x02021e02..0x02021e68

; phase3_p9_nor_sdfile_for_each_dir: 0x02021e02..0x02021e68, module phase3-p9 (nor_sdfile_for_each_dir)
.type phase3_p9_nor_sdfile_for_each_dir,@function
phase3_p9_nor_sdfile_for_each_dir:
    [--sp] = {rets, r9-r4}
    sp += -32
    r9_r8 = r1_r0
    r0 = 563
    r1 = L01c26890
    r5 = [r1+r0<<2]
    r6 = sp + 0
    r7 = r6 + 16
    r4 = r6 | 0x2
L02021e1e:
    r0 = sp + 0
    r2 = 32
    r1 = r5
    call L02021dd8
    r1 = 30
    r0 = r4
    call L02001776
    r1 = h[sp] (u)
    if (r0 != r1) goto L02021e4e
    r0 = r7
    r1 = r9
    call L02020e88
    if (r0 == 0) goto L02021e54
    r0 = [r6+8]
    r5 += r0  #  ; @add.rr.p
    r1 = h[r6+14] (u)
    if (r1 == 0) goto L02021e1e
    r0 = -255
    goto L02021e64
L02021e4e:
    r0 = -251
    goto L02021e64
L02021e54:
    r1 = sp + 0
    r2 = 32
    r0 = r8
    call phase3_p8_memcpy_flash
    [r8+4] = r5
    r0 = 0
L02021e64:
    sp += 32
    {pc, r9-r4} = [sp++]
