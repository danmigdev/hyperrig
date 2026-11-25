; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c0344c..0x01c03524: vendor code (JieLi SDK or library, not reversed), as instructions
L01c0344c:
    sp += -8
    r0 = 65548
    r1 = [r0+0]
    [sp] = r1
    r1 = [sp]
    if ((r1 & 256) == 0) goto L01c0349c
    r1 = sp + 0
    [r1+0] |= 0x2
    [r1+0] &= 0xFFFFFEFF
    csync
    r1 = 32432136
L01c03470:
    r2 = [r1+0]
    if ((r2 & 16384) == 0) goto L01c03470
    csync
    r1 = 262656
L01c0347e:
    r2 = [r1+0]
    ifs (r2 < 0) goto L01c0347e
    r1 = [sp]
    [r0+0] = r1
    csync
    r0 = 300
    [sp+4] = r0
    goto L01c03494
L01c03492:
    nop
L01c03494:
    r0 = [sp+4]
    r0 += -1
    [sp+4] = r0
    if (r0 != 0) goto L01c03492
L01c0349c:
    sp += 8
    rts
sdk_RC16M_udelay:
    sp += -4
    r1 = L01c373e4
    r1 = b[r1+3] (u)
    r0 = r0 << 1
    if (r1 == 0) goto L01c034c2
    r1 = L01c373b8
    r1 = [r1+8]
    r2 = 16000000
    r1 = r1 / r2 (u)
    r0 *= r1
L01c034c2:
    [sp] = r0
    goto L01c034c8
L01c034c6:
    nop
L01c034c8:
    r0 = [sp]
    r0 += -1
    [sp] = r0
    if (r0 != 0) goto L01c034c6
    sp += 4
    rts
sdk_sys_clk_source_rc_clk_off:
    sp += -8
    r0 = 65548
    r1 = [r0+0]
    [sp] = r1
    r1 = [sp]
    if ((r1 & 256) != 0) goto L01c03520
    r1 = sp + 0
    [r1+0] |= 0x100
    csync
    r1 = 32432136
L01c034f4:
    r2 = [r1+0]
    if ((r2 & 16384) == 0) goto L01c034f4
    csync
    r1 = 262656
L01c03502:
    r2 = [r1+0]
    ifs (r2 < 0) goto L01c03502
    r1 = [sp]
    [r0+0] = r1
    csync
    r0 = 300
    [sp+4] = r0
    goto L01c03518
L01c03516:
    nop
L01c03518:
    r0 = [sp+4]
    r0 += -1
    [sp+4] = r0
    if (r0 != 0) goto L01c03516
L01c03520:
    sp += 8
    rts
