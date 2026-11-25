; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201fa72..0x0201fcbe: vendor code (JieLi SDK or library, not reversed), as instructions
L0201fa72:
    [--sp] = {rets, r7, r5, r4}
    r7 = sp
    r4 = r1 >> 20
    r1 = r4 + 3
    r2 = 8188
    r1 &= r2
    r2 = sp
    r5 = r2 - r1
    sp = r5
    r1 = r0 + 4
    r0 = r5
    r2 = r4
    call phase3_p8_bin_buf_read
    r0 = r5
    r1 = r4
    call L02001776
    r0 = r0 & 0xFFFF00FF
    sp = r7
    {pc, r7, r5, r4} = [sp++]
L0201faaa:
    [--sp] = {rets, r9-r4}
    sp += -44
    r6 = 0
    [sp+40] = r6
    r0 = sp + 4
    rep 9 {
    [r0++=4] = r6
    }
    r9 = L0203660c  ; "mnt/sdfile/app/btif"
    r0 = r9 + 1206
    call phase3_p6_syscfg_file_open
    r7 = r0
    r4 = -1024
    if (r7 == 0) goto L0201fb66
    r5 = sp + 4
    r1 = r5
    call phase3_p6_fget_attrs
    r8 = L01c26024
    r0 = [sp+12]
    r1 = 1
    r2 = [sp+8]
    b[r8+0] = r1
    r0 += 4  ; @add.ri.u5
    [r8+4] = r0
    r0 = r2 + -4
    [r8+8] = r0
    r0 = r7
    call phase3_p8_syscfg_file_close
    b[r8+12] = r6
    r0 = r9
    call phase3_p6_syscfg_file_open
    r6 = r0
    if (r6 == 0) goto L0201fb66
    r1 = sp + 4
    call phase3_p6_fget_attrs
    r0 = r6
    call phase3_p8_syscfg_file_close
    r5 = [r5+8]
    r1 = r5 + 512
    [r8+16] = r1
    r0 = sp + 40
    r2 = 4
    call phase3_p8_bin_buf_read
    r7 = [sp+40]
    r0 = r7 + -1
    r4 += 7  ; @add.ri.u5
    if (r0 > 2047) goto L0201fb66
    r0 = 0
    r5 = r5 + 516  #
    [sp] = r0
    r0 = sp + 0
    r2 = 4
    r1 = r5
    call phase3_p8_bin_buf_read
    r6 = [sp]
    r0 = r6 >> 20
    if (r0 > 800) goto L0201fb66
    r0 = r5
    r1 = r6
    call L0201fa72
    r1 = r6.b0 (u)
    if (r0 == r1) {
    r0 = 1
    b[r8+12] = r0
    [r8+16] += 4  ; @rmw.add.s12
    [r8+20] = r7
    }
    r4 = 0
L0201fb66:
    r0 = r4
    sp += 44
    {pc, r9-r4} = [sp++]
L0201fb6c:
    r0 += -100
    r1 = r0.l (u)
    r0 = 1
    if (r1 >= 601) {
    r0 = 0
    }
    rts
L0201fb7a:
    r1 = r0
    r2 = 1
    r0 = L02035398
    goto L0201fb94
L0201fb86:
    r3 = r0
    r2 = h[r3++=6] (u)
    if (r2 == r1) goto L0201fb9a
    r2 = 0
    r0 = r3
L0201fb94:
    if ((r2 & 1) != 0) goto L0201fb86
    r0 = 0
L0201fb9a:
    rts
L0201fb9c:
    [--sp] = {rets, r8-r4}
    sp += -4
    r5 = r0
    r0 = 0
    r8 = r2  #
    [sp] = r0
    r7 = r1 + r5
L0201fbaa:
    r0 = sp + 0
    r2 = 4
    r1 = r5
    call phase3_p8_bin_buf_read
    r6 = [sp]
    r4 = r6 >> 20
    if (r4 > 800) goto L0201fbd6
    r0 = h[r8+0] (u)
    r1 = uextra(r6, p:8, l:12)
    if (r1 == r0) goto L0201fbdc
    r0 = r5 + r4
    r5 = r0 + 4
    if (r5 < r7) goto L0201fbaa
    r0 = -1019
    goto L0201fbfc
L0201fbd6:
    r0 = -1017
    goto L0201fbfc
L0201fbdc:
    r0 = r5
    r1 = r6
    call L0201fa72
    r1 = r0
    r2 = r6.b0 (u)
    r0 = -1021
    if (r1 != r2) goto L0201fbfc
    h[r8+2] = r4
    r0 = r5 + 4
    [r8+4] = r0
    r0 = 0
L0201fbfc:
    sp += 4
    {pc, r8-r4} = [sp++]
L0201fc00:
    [--sp] = {rets, r5, r4}
    r5 = L01c26024
    r4 = r0  #
    r1 = b[r5+12] (u)
    if (r1 != 1) goto L0201fc1a
    r1_r0 = d[r5+16]
    r2 = r4
    call L0201fb9c
    if (r0 == 0) goto L0201fc24
L0201fc1a:
    r1_r0 = d[r5+4]
    r2 = r4
    call L0201fb9c
    {pc, r5, r4} = [sp++]
L0201fc24:
    r0 = 0
    {pc, r5, r4} = [sp++]
L0201fc28:
    [--sp] = {rets, r8-r4}
    sp += -12
    r6 = r3
    r5 = r2
    r4 = r1
    r7 = r0
    call L0201fb7a
    r1 = r0
    if (r1 == 0) goto L0201fcb6
    r0 = -1018  #
    r2 = b[r1+4] (u)
    if (r2 <= r6) goto L0201fcba
    r1 = h[r1+2] (u)
    r0 += -4
    if (r1 > r5) goto L0201fcba
    r0 = 0
    r1 = 0
    d[sp] = r1_r0
    h[sp] = r7
    r0 = sp + 0
    call L0201fc00
    if (r0 != 0) goto L0201fcba
    r8 = [sp+4]  ; @ld.w.sp.l
    r0 = h[sp] (u)
    r1 = 0
    b[sp+11] = r1
    call L0201fb7a
    r7 = r0
    r0 = h[++r7=2] (u)
    r0 += 1  ; @add.ri.u5
    r0 = r0.l (u)
    r0 *= r6
    r6 = r0 + r8
    r0 = sp + 11
    r2 = 1
    r1 = r6
    call phase3_p8_bin_buf_read
    r1 = b[sp+11] (u)
    r0 = sp + 0
    if (r1 == 0) goto L0201fcb6
    r7 = h[r7+0] (u)
    h[sp+2] = r7
    r1 = r6 + 1
    r0 = -1022  #
    [r0+4] = r1
    if (r7 > r5) goto L0201fcba
    r0 = [sp+36]
    if (r0 == 1) {  ; @if.eq.ri.s12
    [r4+0] = r1
    } else {
    r0 = r4
    r2 = r7
    call phase3_p8_bin_buf_read
    }
    r0 = r7
    goto L0201fcba
L0201fcb6:
    r0 = -1019
L0201fcba:
    sp += 12
    {pc, r8-r4} = [sp++]
