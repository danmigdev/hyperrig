; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02021174..0x0202128c: vendor code (JieLi SDK or library, not reversed), as instructions
L02021174:
    [--sp] = {rets, r6-r4}
    sp += -56
    r4 = r0
    r2 = sp + 39
    r0 = 0
    r3 = r2
    rep 17 {
    b[r3++=1] = r0
    }
    r0 = r1
    r1 = r2
    call L02020e34
    r5 = r0
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L020211c2
    r0 = sp + 0
    r0 += 4  ; @add.ri.u5
    r1 = sp + 39
    call phase3_p9_sdfile_for_each_dir
    if (r0 != 0) goto L020211d4
    r0 = b[sp+16] (u)
    r1 = r0 & 0xFFFFFF0F
    r0 = -255
    if (r1 != 3) goto L020211d4
    r6 = sp + 39
    r0 = r5
    r1 = r6
    call L02020e34
    r1 = sp + 0
    r0 = r4
    r2 = r6
    call phase3_p9_sdfile_open_file_in_dir
    goto L020211d4
L020211c2:
    r0 = r4 + 4
    r1 = sp + 39
    call phase3_p9_sdfile_for_each_dir
    if (r0 != 0) goto L020211d4
    [r4+8] += 32  ; @rmw.add.s12
    [r4+12] += -32
    r0 = 0
L020211d4:
    sp += 56
    {pc, r6-r4} = [sp++]
L020211d8:
    [--sp] = {rets, r10-r4}
    sp += -56
    r5 = sp + 39
    r9 = 0
    r2 = r5
    rep 17 {
    b[r2++=1] = r9
    }
    r4 = 561
    r7 = L01c26890
    r3 = [r7+r4<<2]
    r6 = r1
    r8 = r0
    r10 = sp + 0
    r0 = r10 + 4
    r2 = 32
    r1 = r3
    call phase3_p8_memcpy_flash
    r0 = [r7+r4<<2]
    r0 = r6  #
    [sp+8] = r0
    r1 = r5
    call L02020e34
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L02021264
    r0 = sp + 0
    r1 = r0
    rep 9 {
    [r1++=4] = r9
    }
    r5 = L02036035  ; "EXT_RESERVED"
    r1 = sp + 39
    r2 = r5
    call phase3_p9_sdfile_open_part_dir
    if (r0 != 0) goto L0202126e
    r1 = sp + 39
    r0 = r6
    call L02020e34
    r6 = r0
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L02021272
    r0 = sp + 0
    r1 = sp + 39
    r2 = r5
    call phase3_p9_sdfile_open_part_dir
    if (r0 != 0) goto L0202126e
    r5 = sp + 39
    r0 = r6
    r1 = r5
    call L02020e34
    r1 = sp + 0
    r0 = r8
    r2 = r5
    goto L0202126a
L02021264:
    r1 = sp + 0
    r2 = sp + 39
    r0 = r8
L0202126a:
    call phase3_p9_sdfile_open_file_in_dir
L0202126e:
    sp += 56
    {pc, r10-r4} = [sp++]
L02021272:
    r0 = [r10+8]
    call phase3_p8_sdfile_flash_addr2cpu_addr
    r1 = r0 + -32
    [r10+8] = r1
    r2 = sp + 39
    r0 = r8
    call L02021046
    goto L0202126e
