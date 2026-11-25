; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02021e68..0x02022008: vendor code (JieLi SDK or library, not reversed), as instructions
L02021e68:
    [--sp] = {rets, r12-r4}
    sp += -88
    r7 = r1
    r5 = r0
    if (r7 == 0) goto L02021ea4
    r0 = 40
    call L0203c15c  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L02021eaa
    r0 = 0
    r1 = r4
    rep 10 {
    [r1++=4] = r0
    }
    r0 = [r5+8]
    r0 += 18  ; @add.ri.u5
    r1 = L0203a54c
    call L02028308  ; @call.xl
    r6 = -19
    if (r0 == 0) goto L02021eb2
L02021e9a:
    r0 = r4
    call L0203d218  ; @call.xl
    goto L02021eac
L02021ea4:
    r6 = -254
    goto L02021eac
L02021eaa:
    r6 = -12
L02021eac:
    r0 = r6
    sp += 88
    {pc, r12-r4} = [sp++]
L02021eb2:
    r1 = sp + 3
    r0 = r7
    call L02020e34
    r7 = r0
    r0 = b[r7+0] (u)
    if (r0 == 0) goto L02021f38
    r0 = sp + 20
    r0 += 4  ; @add.ri.u5
    r1 = sp + 3
    call phase3_p9_nor_sdfile_for_each_dir
    r6 = r0
    if (r6 != 0) goto L02021e9a
    r0 = b[sp+36] (u)
    r0 = r0 & 0xFFFFFF0F
    r6 = -255
    if (r0 != 3) goto L02021e9a
    r1 = sp + 3
    r0 = r7
    call L02020e34
    r10 = [sp+28]  ; @ld.w.sp.l
    [r4+0] = 0x0
    r12 = sp + 56
    r9 = r12 + 16
    r11 = r12 | 0x2
    r8 = r4 + 4
    r6 = 32
    r7 = r10
L02021f00:
    r7 += 32
L02021f02:
    ifs (r6 < 1) goto L02021f56
    r0 = sp + 56
    r2 = 32
    r1 = r7
    call L02021dd8
    r1 = 30
    r0 = r11
    call L02001776
    r1 = h[sp+56] (u)
    if (r0 != r1) goto L02021f34
    r1 = sp + 3
    r0 = r9
    call L02020e88
    if (r0 == 0) goto L02021f5c
    r0 = h[r12+14] (u)
    r7 += 32
    if (r0 == 0) goto L02021f02
    goto L02021f76
L02021f34:
    r6 += -1
    goto L02021f00
L02021f38:
    [r4+0] = 0x0
    r0 = r4 + 4
    r1 = sp + 3
    call phase3_p9_nor_sdfile_for_each_dir
    r6 = r0
    if (r6 != 0) goto L02021e9a
    [r4+8] += 32  ; @rmw.add.s12
    [r4+12] += -32
L02021f50:
    [r5+12] = r4
    r6 = 0
    goto L02021eac
L02021f56:
    r6 = -254
    goto L02021e9a
L02021f5c:
    r1 = sp + 56
    r2 = 32
    r0 = r8
    call phase3_p8_memcpy_flash
    r1 = b[r4+16] (u)
    r0 = [r4+8]
    if ((r1 & 16) != 0) goto L02021f7a
    r0 += r10
    [r4+8] = r0
    goto L02021f50
L02021f76:
    r6 = 1
    goto L02021e9a
L02021f7a:
    call phase3_p8_sdfile_flash_addr2cpu_addr
    [r4+8] = r0
    goto L02021f50
L02021f82:
    [--sp] = {rets, r5, r4}
    r4 = 0
    if (r0 == 0) goto L02021fa8
    r5 = [r0+12]
    if (r5 == 0) goto L02021fa8
    r0 = [r5+0]
    r3 = [r5+8]
    r3 += r0  #  ; @add.rr.p
    r4 = [r5+12]
    r0 = r4 - r0
    r4 = umin(r0, r2)
    r0 = r1
    r1 = r3
    r2 = r4
    call L02021dd8
    [r5+0] += r4
L02021fa8:
    r0 = r4
    {pc, r5, r4} = [sp++]
L02021fac:
    [--sp] = {rets, r9-r4}
    sp += -32
    r1 = 559
    r2 = L01c26890
    r5 = [r2+r1<<2]
    r6 = r0
    r8 = 0
    if (r5 == 0) goto L02022002
    r4 = sp + 0
    r7 = r4 + 16
    r9 = L02036035  ; "EXT_RESERVED"
L02021fce:
    r0 = sp + 0
    r2 = 32
    r1 = r5
    call phase3_p8_memcpy_flash
    r1 = r9 + 305
    r0 = r7
    call L02020e88
    if (r0 == 0) goto L02021fee
    r0 = r7
    r1 = r9
    call L02020e88
    if (r0 != 0) goto L02022000
L02021fee:
    r1_r0 = r7_r6
    call L02020e88
    if (r0 == 0) goto L02022000
    r0 = [r4+8]
    r5 += r0  #  ; @add.rr.p
    r1 = h[r4+14] (u)
    if (r1 == 0) goto L02021fce
    goto L02022002
L02022000:
    r8 = r5
L02022002:
    r0 = r8
    sp += 32
    {pc, r9-r4} = [sp++]
