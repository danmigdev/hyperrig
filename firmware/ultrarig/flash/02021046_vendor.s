; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02021046..0x0202110c: vendor code (JieLi SDK or library, not reversed), as instructions
L02021046:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = r1 + 32
    r1 = r4 + 4
    call L02020fac
    if (r0 != 0) goto L0202105e
    r0 = b[r4+16] (u)
    r0 = uextra(r0, p:1, l:1)
    r0 += -1
L0202105e:
    {pc, r4} = [sp++]
L02021060:
    [--sp] = {rets, r9-r4}
    sp += -56
    r5 = sp + 39
    r9 = 0
    r2 = r5
    rep 17 {
    b[r2++=1] = r9
    }
    r2 = 560
    r4 = L01c26890
    r3 = [r4+r2<<2]
    r6 = r1
    r8 = r0
    r7 = sp + 0
    r0 = r7 + 4
    r2 = 32
    r1 = r3
    call phase3_p8_memcpy_flash
    r0 = 559
    r0 = [r4+r0<<2]
    r0 = r6  #
    [sp+8] = r0
    r1 = r5
    call L02020e34
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L020210ec
    r0 = sp + 0
    r1 = r0
    rep 9 {
    [r1++=4] = r9
    }
    r5 = L02036166  ; "app_area_head"
    r1 = sp + 39
    r2 = r5
    call phase3_p9_sdfile_open_part_dir
    if (r0 != 0) goto L020210f4
    r1 = sp + 39
    r0 = r6
    call L02020e34
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L020210f8
    r0 = sp + 0
    r1 = sp + 39
    r2 = r5
    call phase3_p9_sdfile_open_part_dir
    if (r0 != 0) goto L020210f4
    r5 = sp + 39
    r0 = r6
    r1 = r5
    call L02020e34
    r1 = sp + 0
    r0 = r8
    r2 = r5
    goto L020210f2
L020210ec:
    r1 = sp + 0
    r2 = sp + 39
    r0 = r8
L020210f2:
    call phase3_p9_sdfile_open_file_in_dir
L020210f4:
    sp += 56
    {pc, r9-r4} = [sp++]
L020210f8:
    r0 = [r7+8]
    call phase3_p8_sdfile_flash_addr2cpu_addr
    r1 = r0 + -32
    r0 = r8  #
    [r7+8] = r1
    r2 = sp + 39
    call L02021046
    goto L020210f4
