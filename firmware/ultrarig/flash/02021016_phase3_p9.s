; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 1 function, 0x02021016..0x02021046

; phase3_p9_sdfile_open_file_in_dir: 0x02021016..0x02021046, module phase3-p9 (sdfile_open_file_in_dir)
.type phase3_p9_sdfile_open_file_in_dir,@function
phase3_p9_sdfile_open_file_in_dir:
    [--sp] = {rets, r6-r4}
    r5_r4 = r1_r0
    r3 = [++r5=8]
    r1 = r4 + 4
    r0 = r3 + 32
    call L02020fac
    r6 = r0
    if (r6 != 0) goto L02021042
    r0 = b[r4+16] (u)
    if ((r0 & 16) != 0) goto L0202103a
    r0 = [r5+0]
    [r4+8] += r0
    goto L02021042
L0202103a:
    r0 = [r4+8]
    call phase3_p8_sdfile_flash_addr2cpu_addr
    [r4+8] = r0
L02021042:
    r0 = r6
    {pc, r6-r4} = [sp++]
