; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_async: 1 function, 0x01c04588..0x01c04774

; capture_async_worker: 0x01c04588..0x01c04774, module capture-async (worker)
.type capture_async_worker,@function
capture_async_worker:
    [--sp] = {rets, r15-r4}
    sp += -16
    r6 = L01c2bff0
    r10 = r0  #
    r1 = [r6+16]
    [r6+20] = r1
    [r6+24] = r1
    csync
    r12 = 1
    [r6+28] = r12
    csync
    r0 = [r0+0]
    if (r0 == 0) goto L01c0476a
    r14 = L01c2a8e0
    r13 = 1524
    r15 = L01c340cc
    r0 = 0
    r11 = 0  #
    [sp+12] = r0
    goto L01c04666
L01c045c4:
    r1 = 1023  #
    r0 = [sp+12]
    r0 = r0 + 1
    [sp+12] = r0
    r0 = [sp+12]
    if ((r0 & r1) != 0) goto L01c045e0
    r0 = L01c340c0
    r0 = [r0+0]
    if (r0 == 0) goto L01c045e0
    call r0
L01c045e0:
    r4 = [r6+16]
    r0 = [r6+24]
    if (r4 == r0) goto L01c04762
    cli
    r0 = 67332
    r5 = [r0+0]
    [r6+24] = r4
    csync
    r0 = [r6+32]
    if (r0 != r4) goto L01c04610
    r0 = L01c34190
    r0 = [r0+0]
    r0 = r0 + 1
    r1 = L01c34190
    [r1+0] = r0
    goto L01c0465e
L01c04610:
    r1 = [r6+36]
    r0 = [r6+40]
    csync
    call r1
    csync
    r2 = [r6+44]
    r0 = 67332
    r3 = [r0+0]
    r0 = L01c34184
    r0 = [r0+0]
    r0 = r0 + 1
    r1 = L01c34174
    r1 = [r1+0]
    r7 = L01c34184
    r0 = r5 - r2  #
    [r7+0] = r0
    r2 = L01c34188
    r2 = r3 - r5  #
    [r2+0] = r0
    if (r0 > r1) {
    r1 = L01c34174
    [r1+0] = r0
    }
    r0 = L01c340c8
    [r0+0] = r2
L01c0465e:
    [r6+20] = r4
    csync
    sti
    goto L01c04762
L01c04666:
    r0 = [r6+8]
    if (r0 == 0) goto L01c045c4
    csync
    r1 = r0.b0 (u)
    if (r1 == 251) goto L01c04680
    if (r1 == 252) goto L01c04696
    if (r1 != 255) goto L01c0472a
    [r6+48] = r12
    goto L01c0475a
L01c04680:
    cli
    [r6+0] = r12
    csync
L01c04688:
    r0 = [r6+4]
    if (r0 != 0) goto L01c04688
    [r6+0] = r11
    csync
    sti
    goto L01c0475a
L01c04696:
    r9 = uextra(r0, p:8, l:1)
    r0 = 1284
    r0 *= r9
    r1 = L01c2b4e0
    r4 = r0 + r1
    r8 = r4 + 1280
    cli
    r0 = [r8+0]
    r2 = h[r6+84] (u)
    r1 = [r6+112]
    [sp+8] = r12
    r5 = r4 + 256
    r7 = r6 + 76  #
    [sp+4] = r5
    r0 = r7  #
    [sp] = r0
    r3 = r4
    call capture_live_iterate
    r0 = [r6+12]
    if (r0 == 0) goto L01c04748
    r1 = b[r6+79] (u)
    r0 = r1 * 0x3
    if (r0 == 3) goto L01c0470c
    r0 = r9 ^ 0x1
    r2 = -3
    r1 *= r2
    r0 *= r13
    r4 = r0 + r14
    r0 = r9 * r13
    r3 = r0 + r14
L01c046f6:
    r0 = r4 + 1536
    r2 = [r0+r1<<2]
    r0 = r3 + 768
    [r0+r1<<2] = r2
    r1 = r1 + 1
    if (r1 != -3) goto L01c046f6
L01c0470c:
    r0 = r9 * r13
    r0 += r14
    r2 = r0 + 756
    r1 = 0
L01c04718:
    r0 = [r5+r1<<2]
    [r2+r1<<2] = r0
    r1 = r1 + 1
    if (r1 != 192) goto L01c04718
    sti
    goto L01c0475a
L01c0472a:
    r5 = r0 >> 24
    r2 = r6 + 76  #
    [sp] = r5
    r4 = uextra(r0, p:8, l:1)
    r3 = uextra(r0, p:16, l:8)
    r0 = r2
    r2 = r4
    call capture_async_command_noop
    [r15+60] += 0x1
    goto L01c0475a
L01c04748:
    r2 = [r8+0]
    r3 = r4 + 1024
    r0 = r7
    r1 = r5
    call capture_live_head
    sti
L01c0475a:
    csync
    [r6+8] = r11
    csync
L01c04762:
    r0 = [r10+0]
    if (r0 != 0) goto L01c04666
L01c0476a:
    [r6+28] = 0x0
    csync
    sp += 16
    {pc, r15-r4} = [sp++]
