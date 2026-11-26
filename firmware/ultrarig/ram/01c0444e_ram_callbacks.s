; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 2 functions, 0x01c0444e..0x01c04588

; ram_callbacks_pll_set: 0x01c0444e..0x01c0457e, module ram-callbacks (pll_set)
.type ram_callbacks_pll_set,@function
ram_callbacks_pll_set:
    [--sp] = {rets, r10-r4}
    sp += -12
    r3 = L01c2bff0
    r1 = 0
    [r3+0] = r1
    [r3+4] = 0x1
    csync
    r7 = r0
    r4 = 3999999
L01c0446a:
    r0 = [r3+8]
    if (r1 > r4) goto L01c04474
    r1 = r1 + 1
    if (r0 != 0) goto L01c0446a
L01c04474:
    [r3+8] = 0xFB
    csync
    r1 = 0
    r2 = r4 + 1
L01c0447e:
    r0 = [r3+0]
    if (r0 != 0) goto L01c04488
    r1 = r1 + 1
    if (r1 < r2) goto L01c0447e
L01c04488:
    r0 = [r3+0]
    if (r0 == 0) goto L01c044b4
    cli
    r8 = 72108
    r9 = [r8+0]
    r1 = 0
    r5 = 32432136
    r2 = 2000000
L01c044a6:
    r0 = [r5+0]
    if ((r0 & 16384) != 0) goto L01c044ba
    r1 = r1 + 1
    if (r1 <= r2) goto L01c044a6
    goto L01c044d2
L01c044b4:
    [r3+4] = 0x0
    goto L01c04578
L01c044ba:
    [r5+0] &= 0xFFFFFCFF
    r1 = 0
    r6 = 262656
L01c044c6:
    r0 = [r6+0]
    ifs (r0 > -1) goto L01c044da
    r1 = r1 + 1
    if (r1 <= r2) goto L01c044c6
L01c044d2:
    [r5+0] |= 0x100
    r2 = 0
    goto L01c0455c
L01c044da:
    r10 = [r6+0]
    r0 = r10 & 0xFFFFFFFE
    [r6+0] = r0
    csync
    r0 = 20000
    [sp] = r0
    r0 = [sp]
    if (r0 == 0) goto L01c044fa
    r1 = sp + 0
L01c044f2:
    [r1+0] += 0xFFFFFFFF
    r0 = [sp]
    if (r0 != 0) goto L01c044f2
L01c044fa:
    r0 = r9 >> 12
    r7 <= insert(r0, p:12, l:20)
    [r8+0] = r7
    csync
    r0 = 400000
    [sp+4] = r0
    r0 = [sp+4]
    if (r0 == 0) goto L01c0451e
    r1 = sp + 4
L01c04516:
    [r1+0] += 0xFFFFFFFF
    r0 = [sp+4]
    if (r0 != 0) goto L01c04516
L01c0451e:
    r1 = 0
L01c04520:
    r0 = [r5+0]
    if ((r0 & 16384) != 0) goto L01c0452c
    r1 = r1 + 1
    if (r1 < r2) goto L01c04520
L01c0452c:
    r1 = 0
L01c0452e:
    r0 = [r6+0]
    ifs (r0 > -1) goto L01c0453a
    r1 = r1 + 1
    if (r1 < r2) goto L01c0452e
L01c0453a:
    [r6+0] = r10
    csync
    r0 = 20000
    [sp+8] = r0
    r0 = [sp+8]
    if (r0 == 0) goto L01c04554
    r1 = sp + 8
L01c0454c:
    [r1+0] += 0xFFFFFFFF
    r0 = [sp+8]
    if (r0 != 0) goto L01c0454c
L01c04554:
    [r5+0] |= 0x100
    csync
    r2 = 1
L01c0455c:
    sti
    r0 = 0
    [r3+4] = r0
    csync
L01c04564:
    r1 = [r3+8]
    if (r0 > r4) goto L01c0456e
    r0 = r0 + 1
    if (r1 != 0) goto L01c04564
L01c0456e:
    r0 = 4095
    r0 = r0 & r9
    if (r2 != 0) goto L01c0457a
L01c04578:
    r0 = -1
L01c0457a:
    sp += 12
    {pc, r10-r4} = [sp++]

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; ram_callbacks_idle_word: 0x01c0457e..0x01c04588, module ram-callbacks (idle_word)
.type ram_callbacks_idle_word,@function
ram_callbacks_idle_word:
    r0 = L01c2bff0
    r0 = [r0+12]
    rts
.endif
