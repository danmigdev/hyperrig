; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 1 function, 0x02022b12..0x02022bc2

; phase3_p10_sdfile_delete: 0x02022b12..0x02022bc2, module phase3-p10 (sdfile_delete)
.type phase3_p10_sdfile_delete,@function
phase3_p10_sdfile_delete:
    [--sp] = {rets, r11-r4}
    r3 = [r0+12]
    if (r3 == 0) goto L02022bbe
    r0 = [r3+8]
    call L02022376
    r9 = [r3+12]
    r11 = r0
    r10 = L01c26354
    r8 = r10 + 36
    r0 = r8
    call L02040614  ; @call.xl
    r0 = 1
    goto L02022bb2
L02022b3a:
    r2 = [r10+116]
    r7 = r11 / r2 (u)
    r1 = r7 * r2
    r4 = r11 - r1
    r1 = r2 - r4
    r6 = umin(r1, r9)
    if (r4 != 0) goto L02022b76
    if (r6 != r2) goto L02022b76
    if (r0 == 0) goto L02022b64
    r0 = r10 + 636
    r1 = 255
    call effect_enable_memset  ; @call.xl
L02022b64:
    r0 = [r10+32]
    r1 = r10 + 636
    r2 = r7
    call phase3_p10_dev_bulk_write_1
    r0 = 0
    goto L02022ba0
L02022b76:
    r0 = [r10+32]
    r5 = r10 + 636
    r1 = r5
    r2 = r7
    call phase3_p10_dev_bulk_read_1
    r0 = r4 + r5
    r1 = 255
    r2 = r6
    call effect_enable_memset  ; @call.xl
    r0 = [r10+32]
    r1 = r5
    r2 = r7
    call phase3_p10_dev_bulk_write_1
    r0 = 1
L02022ba0:
    r1 = [r10+120]
    if (r1 == r7) {
    [r10+120] = 0xFFFFFFFF
    }
    r11 += r6
    r9 = r9 - r6
L02022bb2:
    if (r9 != 0) goto L02022b3a
    r0 = r8
    call L0204074c  ; @call.xl
L02022bbe:
    r0 = 0
    {pc, r11-r4} = [sp++]
