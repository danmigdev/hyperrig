; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c00bb2..0x01c00e2e: vendor code (JieLi SDK or library, not reversed), as instructions
L01c00bb2:
    [--sp] = {rets, r6-r4}
    sp += -12
    r1 = 262656
    r0 = [r1+0]
    [sp+4] = r0
    r0 = 32432136
    r2 = [r0+0]
    [sp] = r2
    csync
L01c00bcc:
    r2 = [r0+0]
    if ((r2 & 16384) == 0) goto L01c00bcc
    [r0+0] &= 0xFFFFFCFF
    csync
L01c00bd8:
    r2 = [r1+0]
    ifs (r2 < 0) goto L01c00bd8
    [r1+0] &= 0xFFFFFFFE
    r2 = 7  ; @li.u32
    r2 = r2.b0 (u)
    r3 = 1
    r3 <= insert(r2, p:8, l:8)
    csync
    ssync
    r3 = 0x1F00000  #
    [sp+8] = r3
    r2 = sp + 8
    r4 = 134213632
    goto L01c00c26
L01c00c04:
    r5 = [sp+8]
    r5 = [r3+r5<<2]
    if ((r5 & 262144) == 0) goto L01c00c22
    r5 = r5 << 12
    r5 &= r4  #
    r6 = [sp+8]
    r6 = r6 << 4
    r6 = r6 & 0xFE0
    r5 |= r6
    csync
    flush [r5]
    csync
L01c00c22:
    [r2+0] += 2  ; @rmw.add.s12
L01c00c26:
    r5 = [sp+8]
    if (r5 <= 2047) goto L01c00c04
    csync
    ssync
    r3 = 0
    [sp+8] = r3
    r3 = 32538624
    r4 = 0  ; @li.u32
    r4 = 0x8 - r4
    r4 = r4.b0 (u)
    r4 = r4 << 7
    goto L01c00c56
L01c00c4c:
    [r3+0] &= 0xFFFF7FFF
    [r2+0] += 1  ; @rmw.add.s12
    r3 += 4  ; @add.ri.u5
L01c00c56:
    r5 = [sp+8]
    if (r5 < r4) goto L01c00c4c
    csync
    ssync
    r2 = [sp+4]
    [r1+0] = r2
    csync
    [r0+0] |= 0x100
    r1 = r1 + 512
    r1 = [r1+0]
    if ((r1 & 2048) != 0) goto L01c00c80
    r1 = 263424
    r1 = [r1+0]
    if ((r1 & 1) == 0) goto L01c00c84
L01c00c80:
    [r0+0] |= 0x200
L01c00c84:
    csync
    ssync
    sp += 12
    {pc, r6-r4} = [sp++]
L01c00c8c:
    [--sp] = {rets, r4}
    r0 = L01c1f0a0  ; "sdram_powerup_ok"
    r2 = 32
    r1 = 32432136
    r3 = r0
    goto L01c00cae
L01c00ca0:
    r4 = [r1+0]
    if ((r4 & 16384) == 0) goto L01c00ca0
    r2 += -32
    csync
    flushinv [r3]
    r3 += 32
L01c00cae:
    ifs (r2 >= 1) goto L01c00ca0
L01c00cb2:
    r2 = [r1+0]
    if ((r2 & 16384) == 0) goto L01c00cb2
    csync
    flushinv [r0]
    csync
    {pc, r4} = [sp++]
L01c00cc0:
    [--sp] = {rets, r7-r4}
    r1 = 0  ; @li.u32
    r2 = 7  ; @li.u32
    r0 = r2 | r1
    if ((r0 & 0xFF) == 0) goto L01c00dce
    r0 = 32432136
L01c00cde:
    r3 = [r0+0]
    if ((r3 & 16384) == 0) goto L01c00cde
    [r0+0] &= 0xFFFFFCFF
    [r0+4] &= 0xFF000000
    r3 = 0
    r4 = 23
    r5 = 1
    goto L01c00d10
L01c00cf4:
    r6 = r4 + -16
    r6 = r5 << r6
    r7 = r4 + -8
    r6 = r6 | (1 << r7)
    r6 = r6 | (1 << r4)
    [r0+4] |= r6
    r4 += -1
    r3 += 1  ; @add.ri.u5
L01c00d10:
    r6 = r2.b0 (u)
    r6 = 0x8 - r6
    ifs (r3 < r6) goto L01c00cf4
    r2 = 4294901760
    [r0+8] &= r2
    r2 = 0
    r3 = 1
    goto L01c00d3a
L01c00d2a:
    r4 = r2 + 8
    r4 = r3 << r4
    r4 = r4 | (1 << r2)
    [r0+8] |= r4
    r2 += 1  ; @add.ri.u5
L01c00d3a:
    r4 = r1.b0 (u)
    r4 = 0x8 - r4
    ifs (r2 < r4) goto L01c00d2a
    r1 = 0x1F00000
    r2 = r1 + 0x4000
    r3 = 0
    goto L01c00d52
L01c00d50:
    [r1++=4] = r3
L01c00d52:
    ifs (r1 < r2) goto L01c00d50
    r2 = r2 + 0x4000
    r1 = r2 + 0x2000
    goto L01c00d62
L01c00d60:
    [r2++=4] = r3
L01c00d62:
    ifs (r2 < r1) goto L01c00d60
    r2 = r1 + 512
    goto L01c00d6e
L01c00d6c:
    [r1++=4] = r3
L01c00d6e:
    ifs (r1 < r2) goto L01c00d6c
    r1 = r2 + 3584
    r2 = r1 + 511
    goto L01c00d7e
L01c00d7c:
    [r1++=4] = r3
L01c00d7e:
    ifs (r1 <= r2) goto L01c00d7c
    [r0+0] |= 0x100
    r1 = 263168
    r1 = [r1+0]
    if ((r1 & 2048) != 0) goto L01c00d9e
    r1 = 263424
    r1 = [r1+0]
    if ((r1 & 1) == 0) goto L01c00da2
L01c00d9e:
    [r0+0] |= 0x200
L01c00da2:
    r0 = 32669696
    r1 = L02076a8c
    r2 = 32  ; @li.u32
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 32669728
    r2 = 0  ; @li.u32
    r1 = 0
    call effect_enable_memset  ; @call.xl
L01c00dce:
    {pc, r7-r4} = [sp++]
L01c00dd0:
    sp += -4
    [--sp] = {r1, r0}
    r0 = icfg
    r0 = r0 & 0xFF
    if (r0 != 0) goto L01c00e02
    r0 = usp
    r0 += -4
    usp = r0
    r1 = reti
    [r0+0] = r1
    r1 = L01c00e16
    reti = r1
    {r1, r0} = [sp++]
    sp += 4
    rti
L01c00e02:
    r1 = reti
    [sp+8] = r1
    r0 = icfg
    r0 |= 256
    icfg = r0
    {r1, r0} = [sp++]
L01c00e16:
    [--sp] = {rets, r2-r0}
    r0 = [sp+16]
    r1 = h[r0+0] (u)
    r2 = h[r0+2] (u)
    r2 = r2 << 16
    r2 |= r1
    r2 = [r2+0]
    [sp+16] = r2
    {rets, r2-r0} = [sp++]
    pc = [sp++]
