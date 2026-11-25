; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201b2ce..0x0201b4bc: vendor code (JieLi SDK or library, not reversed), as instructions
L0201b2ce:
    [--sp] = {rets, r4}
    r1 = L01c1f180
    r2 = [r1+24]
    r2 += 20  ; @add.ri.u5
L0201b2da:
    r3 = [r1+24]
    ifs (r3 >= r2) goto L0201b2f4
    r3 = [r0+20]
    r4 = h[r3+0] (s)
    ifs (r4 > -1) goto L0201b2da
    r0 = h[r3+0] (u)
    r0 |= 16384
    h[r3+0] = r0
    r0 = 0
    {pc, r4} = [sp++]
L0201b2f4:
    r0 = -14
    {pc, r4} = [sp++]
L0201b2f8:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = [r4+20]
    r2 = h[r0+0] (u)
    r2 |= 8
    h[r0+0] = r2
    r2 = h[r0+0] (u)
    r2 |= 32
    h[r0+0] = r2
    r2 = h[r0+0] (u)
    r2 &= 4294967231
    h[r0+0] = r2
    r2 = 255
    b[r0+4] = r2
    csync
    nop
    r0 = [r4+20]
    r5 = r1  #
    r2 = h[r0+0] (u)
    r1 = r2 | 0x4
    r0 = r4  #
    h[r0+0] = r1
    call L0201b2ce
    [r5+0] = r0
    r0 = [r4+20]
    r0 = b[r0+4] (u)
    {pc, r5, r4} = [sp++]
L0201b330:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = [r4+20]
    r2 = h[r0+0] (u)
    r2 |= 8
    h[r0+0] = r2
    r2 = h[r0+0] (u)
    r2 &= 4294967231
    h[r0+0] = r2
    r2 = 255
    b[r0+4] = r2
    csync
    nop
    r0 = [r4+20]
    r5 = r1  #
    r2 = h[r0+0] (u)
    r1 = r2 | 0x4
    r0 = r4  #
    h[r0+0] = r1
    call L0201b2ce
    [r5+0] = r0
    r0 = [r4+20]
    r0 = b[r0+4] (u)
    {pc, r5, r4} = [sp++]
L0201b362:
    r1 = [r0+20]
    r2 = h[r1+0] (u)
    r2 |= 16
    h[r1+0] = r2
    csync
    nop
    r0 = [r0+20]
    r1 = h[r0+0] (u)
    r1 |= 4
    h[r0+0] = r1
L0201b376:
    r1 = h[r0+0] (u)
    if ((r1 & 8192) == 0) goto L0201b376
    r1 = h[r0+0] (u)
    r1 |= 4096
    h[r0+0] = r1
    rts
L0201b384:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = [r4+20]
    r2 = h[r0+0] (u)
    r2 |= 8
    h[r0+0] = r2
    r2 = h[r0+0] (u)
    r2 |= 64
    h[r0+0] = r2
    r2 = 255
    b[r0+4] = r2
    csync
    nop
    r0 = [r4+20]
    r5 = r1  #
    r2 = h[r0+0] (u)
    r1 = r2 | 0x4
    r0 = r4  #
    h[r0+0] = r1
    call L0201b2ce
    [r5+0] = r0
    r0 = [r4+20]
    r0 = r4  #
    r3 = b[r0+4] (u)
    call L0201b362
    r0 = r3
    {pc, r5, r4} = [sp++]
L0201b3bc:
    [--sp] = {rets, r9-r4}
    sp += -4
    r9 = r1
    r6 = r0
    r4 = 0
    r8 = r2  #
    [sp] = r4
    if (r2 == 0) goto L0201b402
    r0 = [r6+12]
    r1 = sp + 0
    call L0201b2f8
    r5 = r8 + -1
    r4 = 2
    goto L0201b3e2
L0201b3da:
    r0 = [r6+12]
    r1 = sp + 0
    call L0201b330
    r4 += 1  ; @add.ri.u5
L0201b3e2:
    r7 = r9 + r4
    r3 = r4 + -1  #
    b[r7+-2] = r0
    if (r3 < r5) goto L0201b3da
    r0 = [r6+12]
    if (r8 != r4) goto L0201b3fe
    r1 = sp + 0
    call L0201b384
    b[r7+-1] = r0
    goto L0201b402
L0201b3fe:
    call L0201b362
    r4 = r3
L0201b402:
    r0 = r4
    sp += 4
    {pc, r9-r4} = [sp++]
L0201b408:
    [--sp] = rets
    r2 = [r0+20]
    r3 = h[r2+0] (u)
    r3 &= 4294967287
    h[r2+0] = r3
    r3 = h[r2+0] (u)
    r3 |= 32
    h[r2+0] = r3
    b[r2+4] = r1
    csync
    nop
    r1 = [r0+20]
    r2 = h[r1+0] (u)
    r2 |= 4
    h[r1+0] = r2
    call L0201b2ce
    pc = [sp++]
L0201b42c:
    [--sp] = rets
    r2 = [r0+20]
    r3 = h[r2+0] (u)
    r3 &= 4294967287
    h[r2+0] = r3
    b[r2+4] = r1
    csync
    nop
    r1 = [r0+20]
    r2 = h[r1+0] (u)
    r2 |= 4
    h[r1+0] = r2
    call L0201b2ce
    pc = [sp++]
L0201b44a:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = [r4+20]
    r2 = h[r0+0] (u)
    r2 &= 4294967287
    h[r0+0] = r2
    b[r0+4] = r1
    csync
    nop
    r0 = [r4+20]
    r1 = h[r0+0] (u)
    r1 |= 4
    r0 = r4  #
    h[r0+0] = r1
    call L0201b2ce
    r3 = r0
    r0 = r4
    call L0201b362
    r0 = r3
    {pc, r4} = [sp++]
L0201b476:
    [--sp] = {rets, r8-r4}
    r8 = r2
    r5 = r1
    r7 = r0
    if (r2 == 0) goto L0201b4ae
    r1 = b[r5+0] (u)
    r0 = [r7+12]
    call L0201b408
    r6 = r8 + -1
    r4 = 2
    goto L0201b498
L0201b48e:
    r0 = r5 + r4
    r1 = b[r0+-1] (u)
    r0 = [r7+12]
    call L0201b42c
    r4 += 1  ; @add.ri.u5
L0201b498:
    r3 = r4 + -1
    if (r3 < r6) goto L0201b48e
    r0 = [r7+12]
    if (r8 != r4) goto L0201b4b2
    r1 = r5 + r4
    r1 = b[r1+-1] (u)
    call L0201b44a
    goto L0201b4b8
L0201b4ae:
    r4 = 0
    goto L0201b4b8
L0201b4b2:
    call L0201b362
    r4 = r3
L0201b4b8:
    r0 = r4
    {pc, r8-r4} = [sp++]
