; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02001a08..0x02001aee: vendor code (JieLi SDK or library, not reversed), as instructions
L02001a08:
    [--sp] = {rets, r5, r4}
    r4 = r0
    if (r4 == 0) goto L02001a70
    r0 = 90113
    r1 = 0
    r0 = 0x16800  #
    b[r0+0] = r1
    r1 = r0 + 524  #
    [r0+0] = r1
    [r1+0] &= 0xFFFFFFDF
    [r1+0] &= 0xFFFFFCFF
    [r1+0] |= 0x1C
    [r1+0] |= 0x1
    r2 = -1000
    goto L02001a3c
L02001a38:
    nop
    r2 += 1  ; @add.ri.u5
L02001a3c:
    if (r2 != 0) goto L02001a38
    [r1+0] |= 0x2
    [r0+0] |= 0x3
L02001a46:
    r2 = [r0+0]
    if ((r2 & 16) == 0) goto L02001a46
    [r1+0] &= 0xFDFFFFFF
    [r1+0] &= 0xFEFFFFFF
    [r1+0] |= 0x400000
    [r1+0] |= 0x800000
    [r0+0] |= 0x1800
    r0 = 65535
    r1 = r1 + -1740
    h[r1+2] = r0
    h[r1+0] = r0
    {pc, r5, r4} = [sp++]
L02001a70:
    r5 = r4 << 1
    r0 = r5 + 149
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = r5 + 148
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = L02035cb0
    r1 = r0 + 8
    r1 = [r1+r4<<2]
    r0 = [r0+r4<<2]
    [r1+0] &= 0xFFFFF7FF
    [r1+0] |= 0x1000
    r2 = -16437
    [r0+0] &= r2
    [r0+4] = 0x0
    [r0+0] |= 0x1
    [r1+0] &= 0xFFFFFFCF
    [r1+0] &= 0xFFFFFF3F
    [r1+0] |= 0x40
    [r0+0] |= 0x3C
    {pc, r5, r4} = [sp++]
L02001ac0:
    r2 = 0x11800
    r3 = [r2+0]
    if ((r3 & 4) == 0) goto L02001aec
    r0 = r0 << 8
    r3 = 16776960
    r0 &= r3
    r1 = r1.b0 (u)
    r0 |= r1
    [r2+4] = r0
    csync
    r0 = -20001
L02001ae0:
    r1 = [r2+4]
    r1 = r1.l (s)
    ifs (r1 < 0) goto L02001aec
    r0 += 1  ; @add.ri.u5
    if (r0 != 0) goto L02001ae0
L02001aec:
    rts
