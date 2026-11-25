; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; switched_high_pass: 1 function, 0x01c012d8..0x01c01544

; switched_high_pass_switch: 0x01c012d8..0x01c01544, module switched-high-pass (switch)
.type switched_high_pass_switch,@function
switched_high_pass_switch:
    [--sp] = {rets, r11-r4}
    r2 = 3244
    r9 = L01c26890
    r8 = [r9+r2<<2]
    r3 = [r9+660]
    r5 = r0
    r10 = L01c21cb8
    if (r8 == r3) goto L01c01362
    if ((r8 & 1) != 0) goto L01c01362
    r0 = r2 + 1
    r0 = [r9+r0<<2]
    r3 = 1
    if (r0 != 0) goto L01c01308
    r3 = r0
L01c01308:
    r6 = 2017
    b[r10+r6] = r3
    if (r0 == 0) goto L01c01348
    r0 = 0
    r3 = -1280
    r11 = 14264
    goto L01c0133c
L01c0131e:
    r7 = r10 + 1364
    r2 = r3 + r7
    r1 = r9 + r11
    r4 = r3 + r1
    rep 5 {
    r6 = [r4++=4]
    [r2++=4] = r6
    }
    r1 = h[r0+r1] (u)
    h[r0+r7] = r1
    r3 += 20  ; @add.ri.u5
    r0 += 2  ; @add.ri.u5
L01c0133c:
    if (r3 != 0) goto L01c0131e
    r0 = 503
    r3 = 64
    [r10+r0<<2] = r3
L01c01348:
    r0 = 3244
    r0 = [r9+r0<<2]
    if (r0 != r8) {
    r0 = 503
    r1 = 0
    [r10+r0<<2] = r1
    } else {
    [r9+660] = r8
    }
L01c01362:
    r1 = 2017
    r0 = 2016
    r0 = b[r10+r0] (u)
    r1 = b[r10+r1] (u)
    if (r0 == 0) goto L01c01406
    r2 = 1
    if ((r1 & 0xFF) != 0) {
    r2 = 0
    }
    r3 = r0 + -1
    r3 = r3.b0 (u)
    if (r3 > 1) goto L01c0138a
    r3 = 3
    if (r2 != 0) goto L01c01392
L01c0138a:
    if (r0 != 3) goto L01c0139c
    r3 = 2
    if (r1 == 0) goto L01c0139c
L01c01392:
    r0 = 2016
    b[r10+r0] = r3
    r0 = r3
L01c0139c:
    r1 = 503
    r2 = [r10+r1<<2]
    if (r2 == 0) goto L01c013f4
    r3 = 0x40 - r2
    r4 = r3 * 0x14
    r4 += r10
    r4 += 84
    r6 = r10 + 64
    rep 5 {
    r7 = [r4++=4]
    [r6++=4] = r7
    }
    r4 = r10 + 1364
    r3 = h[r4+r3<<1] (u)
    r4 = 746
    h[r10+r4<<1] = r3
    r2 += -1
    [r10+r1<<2] = r2
    r1 = r10 + 64
    r2 = [r1+0]
    [r10+0] = r2
    r2 = [r1+4]
    [r10+4] = r2
    r2 = [r1+16]
    [r10+8] = r2
    r2 = [r1+8]
    [r10+32] = r2
    r1 = [r1+12]
    [r10+36] = r1
L01c013f4:
    if (r0 != 1) goto L01c01476
    r1 = 128
    r0 = r5
    r2 = r10
    call switched_high_pass_cascade  ; @call.xl
    {pc, r11-r4} = [sp++]
L01c01406:
    if (r1 == 0) goto L01c01542
    r0 = r10 + 64
    r1 = r10 + 1344
    rep 5 {
    r2 = [r1++=4]
    [r0++=4] = r2
    }
    r0 = 745
    r0 = h[r10+r0<<1] (u)
    r1 = 746
    h[r10+r1<<1] = r0
    r0 = 0
    r1 = r10 + 2008
    r2 = r10 + 64  #
    [r1+4] = r0
    r3 = [r2+0]
    [r10+0] = r3
    r3 = [r2+4]
    [r10+4] = r3
    r3 = [r2+16]
    [r10+8] = r3
    r4 = [r2+8]
    [r10+32] = r4
    r2 = [r2+12]
    [r10+36] = r2
    r2 = [r5+0]
    r3_r2 = r2 * r3 (s)
    [r10+12] = r3
    r2 = 0
    r3 = 0
    d[r10+24] = r3_r2
    d[r10+16] = r3_r2
    r2 = r10 + 44
    rep 5 {
    [r2++=4] = r0
    }
    r2 = 2
    b[r1+8] = r2
    [r1+0] = r0
L01c01476:
    r0 = 0
    goto L01c01488
L01c0147a:
    r1 = [r5+r0<<2]
    r2 = r10 + 1496
    [r2+r0<<2] = r1
    r0 += 1  ; @add.ri.u5
L01c01488:
    if (r0 != 128) goto L01c0147a
    r1 = 128
    r0 = r5
    r2 = r10
    call switched_high_pass_cascade  ; @call.xl
    r0 = 2016
    r0 = b[r10+r0] (u)
    if (r0 != 2) goto L01c014fc
    r0 = 0
    r1 = 502
    goto L01c014d4
L01c014ac:
    r2 = [r10+r1<<2]
    r3 = [r5+r0<<2]
    r4 = r10 + 1496
    r4 = [r4+r0<<2]
    r2 += r0  ; @add.rr
    r2 += 1  ; @add.ri.u5
    r7_r6 = r3 * r2 (s)
    r7_r6 -= r4 * r2 (s)
    r7_r6 >>= 11
    r2 = r6 + r4
    [r5+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
L01c014d4:
    if (r0 != 128) goto L01c014ac
    r0 = r1
    r1 = [r10+r0<<2]
    r1 = r1 + 128
    [r10+r0<<2] = r1
    if (r1 <= 2047) goto L01c01542
    r1 = 2048
    [r10+r0<<2] = r1
    r0 = 2016
    r1 = 1
    goto L01c0153e
L01c014fc:
    r0 = r10 + 1496
    r1 = -1
    r2 = 502
    goto L01c01526
L01c01508:
    r3 = [r10+r2<<2]
    r3 += r1  #  ; @add.rr.p
    r4 = [r5+0]
    r9_r8 = r4 * r3 (s)  #
    r6 = [r0++=4]
    r9_r8 -= r6 * r3 (s)
    r9_r8 >>= 11
    r3 = r8 + r6
    [r5++=4] = r3
    r1 += -1
L01c01526:
    if (r1 != -129) goto L01c01508
    r0 = r2
    r1 = [r10+r0<<2]
    r1 += -128
    [r10+r0<<2] = r1
    if (r1 != 0) goto L01c01542
    r0 = 2016
    r1 = 0
L01c0153e:
    b[r10+r0] = r1
L01c01542:
    {pc, r11-r4} = [sp++]
