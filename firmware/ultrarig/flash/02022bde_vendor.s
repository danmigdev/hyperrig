; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02022bde..0x02022de2: vendor code (JieLi SDK or library, not reversed), as instructions
L02022bde:
    [--sp] = {rets, r5, r4}
    r5 = r0
    r4 = r1  #
    r0 = [r5+8]
    r2 = [r5+4]
    r1 = r2 + r0
    r0 = r4  #
    [r5+4] = r1
    r2 = 32
    call phase3_p10_sdfile_ext_read
    r0 = r4 + 2
    r1 = 30
    call L02001776
    r1 = r0  #
    r2 = h[r4+0] (u)
    r0 = -251
    if (r1 != r2) goto L02022c34
    r0 = [r5+0]
    r1 = L01c26354
    r1 = [r1+20]
    if (r0 <= r1) goto L02022c22
    [r5+8] = 0x20
    r1 = [++r4=4]
    r0 += r1  ; @add.rr
    goto L02022c2e
L02022c22:
    r0 = [r4+8]
    [r5+8] = r0
    r1 = [r5+4]
    r1 += 32
    [r4+4] = r1
    r4 += 8  ; @add.ri.u5
L02022c2e:
    r0 += -32
    [r4+0] = r0
    r0 = 0
L02022c34:
    {pc, r5, r4} = [sp++]
L02022c36:
    [--sp] = {rets, r8-r4}
    sp += -52
    r4 = r0
    r2 = sp + 3
    r8 = 0
    r0 = r2
    rep 17 {
    b[r0++=1] = r8
    }
    r0 = r1
    r1 = r2
    call L020224be
    r5 = r0
    r0 = r4
    call phase3_p10_sdf_opendir
    r7 = sp + 20
    r6 = r7 + 16
    goto L02022c98
L02022c5c:
    r1 = sp + 20
    r0 = r4
    call L02022bde
    if (r0 != 0) goto L02022ca8
    r0 = b[r7+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 != 3) goto L02022c78
    r1 = sp + 3
    r0 = r6
    call L02022514
    if (r0 == 0) goto L02022c7e
L02022c78:
    r0 = h[r7+14] (u)
    if (r0 == 0) goto L02022c5c
    goto L02022c86
L02022c7e:
    r0 = [r7+4]
    r0 = r4  #
    [r4+0] = r0
    call phase3_p10_sdf_opendir
L02022c86:
    r1 = sp + 3
    r0 = r1
    rep 17 {
    b[r0++=1] = r8
    }
    r0 = r5
    call L020224be
    r5 = r0
L02022c98:
    r1 = b[r5+0] (u)
    r0 = b[sp+3] (u)
    r0 |= r1
    if ((r0 & 0xFF) != 0) goto L02022c5c
    goto L02022caa
L02022ca8:
    r1 = b[r5+0] (u)
L02022caa:
    r0 = 0
    if ((r1 & 0xFF) != 0) {
    r0 = -255
    }
    sp += 52
    {pc, r8-r4} = [sp++]
L02022cb8:
    [--sp] = {rets, r6-r4}
    sp += -8
    r5 = r0
    r4 = 0
    if (r5 == 0) goto L02022d0e
    if (r1 == 0) goto L02022d0e
    r0 = b[r1+2] (u)
    b[sp+2] = r0
    r0 = b[r1+1] (u)
    r1 = b[r1+0] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp] = r1
    r0 = sp + 0
    r1 = 3
    call phase3_p10_sdfile_str_to_upper
L02022cde:
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L02022d0e
    r0 = b[r5+2] (u)
    b[sp+6] = r0
    r0 = b[r5+1] (u)
    r1 = b[r5++=3] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+4] = r1
    r6 = sp + 4
    r1 = 3
    r0 = r6
    call phase3_p10_sdfile_str_to_upper
    r0 = sp + 0
    r2 = 3
    r1 = r6
    call L020215ca
    if (r0 != 0) goto L02022cde
    r4 = 1
L02022d0e:
    r0 = r4
    sp += 8
    {pc, r6-r4} = [sp++]
L02022d14:
    [--sp] = {rets, r12-r4}
    sp += -32
    r4 = r3
    r9 = r2
    r8 = r1
    r7 = r0
    r11_r10 = d[sp+72]
    r6 = sp + 0
    r5 = r6 + 16
    r12 = 0
    goto L02022d96
L02022d2c:
    r0 = h[r6+14] (u)
    if (r0 == 0) goto L02022d96
L02022d30:
    if (r8 == 0) goto L02022ddc
    r0 = b[r7+3] (u)
    r0 = r0 * 0xC
    r0 += r7  ; @add.rr
    r0 += 64
    call phase3_p10_sdf_opendir
    r0 = b[r7+3] (u)
    if (r0 != 0) goto L02022d70
    r0 = 0
    goto L02022d4c
L02022d4a:
    r0 = b[r7+3] (u)
L02022d4c:
    r0 = r0.b0 (u)
    r0 = r0 * 0xC
    r0 += r7  ; @add.rr
    r0 += 64
    r1 = sp + 0
    call L02022bde
    if (r0 != 0) goto L02022d6c
    r0 = b[r6+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 3) goto L02022d76
    r0 = h[r6+14] (u)
    if (r0 == 0) goto L02022d4a
L02022d6c:
    r0 = b[r7+3] (u)
    if (r0 == 0) goto L02022ddc
L02022d70:
    r0 += -1
    b[r7+3] = r0
    goto L02022d4c
L02022d76:
    h[r7+16] = r12
    r0 = h[r7+8] (u)
    h[r7+18] = r0
    r0 = b[r7+3] (u)
    r0 += 1  ; @add.ri.u5
    r0 = r0.b0 (u)  #
    b[r7+3] = r0
    r0 = r0 * 0xC  #
    r1 = [r6+4]
    r0 += r7  ; @add.rr
    [++r0=64] = r1
    call phase3_p10_sdf_opendir
L02022d96:
    r0 = b[r7+3] (u)
    r0 = r0 * 0xC
    r0 += r7  ; @add.rr
    r0 += 64
    r1 = sp + 0
    call L02022bde
    if (r0 != 0) goto L02022d30
    r0 = b[r6+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 2) goto L02022dbc
    if (r0 != 3) goto L02022d2c
    if ((r4 & 16) == 0) goto L02022d2c
    goto L02022dd2
L02022dbc:
    r1 = 46
    r0 = r5
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L02022d2c
    r1 = r0 + 1
    r0 = r9
    call L02022cb8
    if (r0 == 0) goto L02022d2c
L02022dd2:
    r1 = sp + 0
    r0 = r11
    call r10
    if (r0 == 0) goto L02022d2c
    goto L02022dde
L02022ddc:
    r0 = 0
L02022dde:
    sp += 32
    {pc, r12-r4} = [sp++]
