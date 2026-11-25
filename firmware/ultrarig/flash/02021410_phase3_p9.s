; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 3 functions, 0x02021410..0x020214b6

; phase3_p9_sdfile_delete: 0x02021410..0x0202145e, module phase3-p9 (sdfile_delete)
.type phase3_p9_sdfile_delete,@function
phase3_p9_sdfile_delete:
    [--sp] = {rets, r8-r4}
    r8 = 0  #
    r6 = [r0+12]
    if (r6 == 0) goto L0202145a
    r0 = [r6+8]
    call phase3_p8_sdfile_cpu_addr2flash_addr
    r1 = 623
    r2 = L01c26090
    r1 = b[r2+r1] (u)
    r5 = r0
    r7 = 4096
    if ((r1 & 0x4) != 0) {
    r7 = 256
    }
    r0 = [r6+12]
    r4 = r0 + r5
    r0 = uextra(r1, p:2, l:1)
    r6 = r0 | 0x2
L02021446:
    if (r5 >= r4) goto L0202145a
    r0 = r6
    r1 = r5
    call phase3_p8_sfc_erase
    r5 += r7  ; @add.rr
    if (r0 != 0) goto L02021446
    r8 = -1
L0202145a:
    r0 = r8
    {pc, r8-r4} = [sp++]

; phase3_p9_sdf_dir_init: 0x0202145e..0x020214ac, module phase3-p9 (sdf_dir_init)
.type phase3_p9_sdf_dir_init,@function
phase3_p9_sdf_dir_init:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = 0
    b[r4+3] = r0
    r2 = [r1+4]
    [r4+24] = r2
    [r4+64] = r2
    r5 = r1 + 18
    r6 = L0203590a  ; "res"
    r1 = r6 + 4
    r0 = r5  #
    h[r4+4] = r0
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020214a2
    r0 = r5
    r1 = r6
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020214a6
    r1 = r6 + 1835
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 != 0) goto L020214aa
    r0 = 3
    goto L020214a8
L020214a2:
    r0 = 1
    goto L020214a8
L020214a6:
    r0 = 2
L020214a8:
    b[r4+4] = r0
L020214aa:
    {pc, r6-r4} = [sp++]

; phase3_p9_sdf_opendir: 0x020214ac..0x020214b6, module phase3-p9 (sdf_opendir)
.type phase3_p9_sdf_opendir,@function
phase3_p9_sdf_opendir:
    r1 = [r0+0]
    [r0+4] = r1
    [r0+8] = 0x0
    rts
