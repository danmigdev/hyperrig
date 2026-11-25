; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_async: 1 function, 0x01c04cda..0x01c05118

; capture_async_run: 0x01c04cda..0x01c05118, module capture-async (run)
.type capture_async_run,@function
capture_async_run:
    [--sp] = {rets, r15-r4}
    sp += -32
    r13 = L01c2bff0
    r2 = h[r13+84] (u)
    r6 = r1
    r5 = r0
    if (r2 == 0) goto L01c05040
    r1 = [r13+168]
    if (r1 == 0) goto L01c05040
    r0 = [r1+76]
    if (r0 == 0) goto L01c05040
    r0 = [r1+68]
    if (r0 == 0) goto L01c05040
    r0 = 67332
    r15 = 0  #
    r0 = [r0+0]
    r12 = r6  #
    [sp+12] = r0
    r0 = L01c1fa1c
    r1 = 1
    [r0+0] = r1
    r0 = L01c344ac
    [r0+0] = r1
    r3 = [r13+164]
    r0 = [r13+52]
    r14 = 4000000
    r7 = 0
    r1 = 0
    [sp+24] = r1
L01c04d44:
    r1 = 1284
    r0 *= r1
    r1 = L01c2b4e0
    r4 = r0 + r1
    r0 = 320
    [r4+r0<<2] = r3
    r2 = r4  #
    r0 = [sp+24]
    r0 = r0 << 8
    r1 = r5 + r0
    r0 = r13 + 76
    [sp+28] = r0
    r0 = [sp+28]
    call capture_live_rechannel
    r0 = 320
    r3 = [r4+r0<<2]
    r2 = [r13+112]
    [sp+8] = r15
    r0 = r4 + 256
    [sp+4] = r0
    r1 = 0
    r3 = r4  #
    [sp] = r3
    r0 = [sp+28]
    call capture_live_iterate
    r0 = 67332
    r2 = [r0+0]
    r1 = 0
L01c04d98:
    r0 = [r13+8]
    if (r0 == 0) goto L01c04da6
    r1 = r1 + 1
    if (r1 <= r14) goto L01c04d98
    goto L01c0505e
L01c04da6:
    r0 = 67332
    r0 = [r0+0]
    [sp+16] = r0
    csync
    r0 = [r13+12]
    r1 = r7 - r2
    [sp+20] = r1
; HyperRig MINI, product option: the second core waits here, so the numbers of the capture may move (mini/product/parametric.c).
.if MINI_PRODUCT
    call hyperrig_capture_turn  ; @call.xl
    r0 = [r13+12]
.endif
    if (r0 == 0) goto L01c04e2e
    r0 = b[r13+60] (u)
    if (r0 == 0) goto L01c04e5e
    call ir_processing_wait
    if (r0 == 0) goto L01c04dda
    r0 = L01c34178
    r0 = [r0+0]
    r0 = r0 + 1
    r1 = L01c34178
    [r1+0] = r0
L01c04dda:
    r10 = [r13+148]
    r11 = [r13+152]
    r3_r2 = r11_r10
    r3_r2 <<= 32
    r3_r2 >>>= 32
    r1 = r11 ^ r3
    r0 = r10 ^ r2
    r0 |= r1
    if (r0 != 0) goto L01c04e7a
    r1 = 0
L01c04dfa:
    r0 = L01c2bee8
    r2 = [r0+r1<<2]
    r3 = r2 + r10
    r4 = r3 ^ r2
    r0 = r3 ^ r10
    r4 &= r0
    r0 = r2 >> 31
    r2 = 2147483647
    r0 = r0 + r2
    ifs (r4 >= 0) {
    r0 = r3
    }
    [r12+r1<<2] = r0
    r1 = r1 + 1
    if (r1 != 64) goto L01c04dfa
    goto L01c04ef2
L01c04e2e:
    r0 = b[r13+56] (u)
    if (r0 == 0) goto L01c04e6c
    r0 = [r13+52]
    r0 ^= 1
    r1 = 1284
    r0 *= r1
    r1 = L01c2b4e0
    r0 = r0 + r1
    r2 = r0 + 1024
    r1 = 0
L01c04e4e:
    r0 = [r2+r1<<2]
    [r12+r1<<2] = r0
    r1 = r1 + 1
    if (r1 != 64) goto L01c04e4e
    goto L01c04fda
L01c04e5e:
    r0 = 64
    r1 = r12
L01c04e62:
    [r1++=4] = r15
    if (--r0 != 0) goto L01c04e62
    goto L01c04f2e
L01c04e6c:
    r0 = 0
L01c04e6e:
    [r12+r0<<2] = r15
    r0 = r0 + 1
    if (r0 != 64) goto L01c04e6e
    goto L01c04fda
L01c04e7a:
    r4 = 0
L01c04e7c:
    r0 = L01c2bee8
    r0 = [r0+r4<<2]
    r1 = r0 >>> 31
    r2 = r0 + r10
    r3 = r1 + r11 + c
    r0 = 2147483647
    r9 = r2 - r0
    r8 = r3 - r15 - !c
    r0 = psr
    r1 = sextra(r0, p:0, l:1)
    r0 = sextra(r0, p:3, l:1)
    r0 ^= r1
    r7 = ~r0
    r1 = r9 | r8
    r0 = 2147483647
    if ((r1 & r7) != 0) goto L01c04ee8
    r8 = r2 - 0x80000000
    r0 = -1
    r7 = r3 - r0 - !c
    r0 = psr
    r1 = sextra(r0, p:0, l:1)
    r0 = sextra(r0, p:3, l:1)
    r0 ^= r1
    r1 = ~r0
    r0 = r8 | r7
    if ((r0 & r1) == 0) {
    r2 = r15 + 0x80000000
    r3 = r15 + -1
    }
    r0 = r2
L01c04ee8:
    [r12+r4<<2] = r0
    r4 = r4 + 1
    if (r4 != 64) goto L01c04e7c
L01c04ef2:
    r0 = [r13+72]
    if (r0 != 2) goto L01c04f2e
    r1_r0 = 0
L01c04efc:
    r2 = L01c2c120
    r4 = [r2+r0<<2]
    r3 = [r12+r0<<2]
    r2 = 1
    if (r3 == r4) {
    r2 = 0
    }
    r0 = r0 + 1
    r1 = r1 + r2
    if (r0 != 64) goto L01c04efc
    r0 = L01c34170
    [r0+0] += 0x1
    r0 = L01c34180
    [r0+0] += r1
L01c04f2e:
    b[r13+60] = r15
    r0 = b[r13+56] (u)
    if (r0 == 0) goto L01c04fda
    r7 = [r13+144]
    r2 = [r13+52]
    r0 = b[r13+79] (u)
    r1 = b[r13+133] (s)
    r3 = r0 * 0x3  #
    [sp+8] = r1
    r1 = 64
    [sp+4] = r1
    r1 = -12
    r1 *= r0  #
    [sp] = r3
    r0 = r2 ^ 0x1
    r2 = 1284
    r4 = r0 * r2
    r0 = r2
    r0 = r4 / r0 (s)
    r2 = 1524
    r0 *= r2
    r0 = r0 + r1
    r1 = L01c2a8e0
    r0 = r0 + r1
    r1 = r0 + 768
    r2 = 12
    r0 = L01c2bee8
    r3 = r7
    call capture_async_submit
    r0 = L01c3417c
    r0 = [r0+0]
    if (r0 == 0) goto L01c04fd0
    r0 = L01c2b4e0
    r0 = r0 + r4
    r1 = 320
    r2 = [r0+r1<<2]
    r1 = r0 + 256  #
    r0 = [sp+28]
    r3 = L01c2c120
    call capture_live_head
    r1 = [r13+72]
    r0 = 2
    if (r1 != 0) goto L01c04fc0
    r0 = 1
L01c04fc0:
    [r13+72] = r0
    r0 = L01c3417c
    [r0+0] += 0xFFFFFFFF
    goto L01c04fd4
L01c04fd0:
    [r13+72] = r15
L01c04fd4:
    r0 = 1
    b[r13+60] = r0
L01c04fda:
    r1 = [r13+52]
    r0 = 252
    r0 <= insert(r1, p:8, l:24)
    [r13+8] = r0
    csync
    r0 = 1
    b[r13+56] = r0
    r0 = [r13+52]
    r0 ^= 1
    [r13+52] = r0
    r1 = [r13+164]
    r2 = [sp+20]
    r3 = [sp+16]
    r7 = r3 + r2
    r3 = r1 + 64
    [r13+164] = r3
    r1 = [sp+24]
    r1 = r1 + 1
    r12 = r12 + 256  #
    [sp+24] = r1
    r1 = [sp+24]
    if (r1 < 2) goto L01c04d44
    r0 = L01c340cc
    [r0+60] += 0x2
    [r0+136] = r7
    r0 = [r0+140]
    if (r7 > r0) {
    r0 = L01c340cc
    [r0+140] = r7
    }
    goto L01c05074
L01c05040:
    r1 = 0
L01c05042:
    r0 = [r5+r1<<2]
    [r6+r1<<2] = r0
    r1 = r1 + 1
    if (r1 != 128) goto L01c05042
    r0 = L01c344b0
    [r0+0] += 0x1
    sp += 32
    {pc, r15-r4} = [sp++]
L01c0505e:
    r0 = L01c340cc
    [r0+56] += 0x1
    r3 = 128
    r1 = r5  #
    r0 = [sp+28]
    r2 = r6
    call capture_live_process
L01c05074:
    r0 = 67332
    r1 = [r0+0]
    r0 = L01c340cc
    r0 += 72
    [r0+0] += 0x1
    r2 = [sp+12]
    r3 = r1 - r2
    [r0+4] = r3
    r2 = [r0+12]
    r1 = r2 + r3
    [r0+12] = r1
    r0 = 1
    if (r1 >= r2) {
    r0 = 0
    }
    if (r0 == 1) {
    r0 = L01c340cc
    r0 = r0 + 160
    [r0+0] += 0x1
    }
    r0 = L01c340cc
    r0 = [r0+80]
    if (r3 > r0) {
    r0 = L01c340cc
    [r0+80] = r3
    }
    r0 = [r13+272]
    if (r0 != 0) goto L01c05114
    r0 = [r13+68]
    if (r0 == 0) goto L01c05114
    r1 = 0
    r3_r2 = 0  #
    r0 = [sp+28]
    r4 = 0
    call capture_dispatch_noop_a
    r1 = 0
    r2 = 0
    r0 = [sp+28]
    call capture_dispatch_noop_b
    r1 = 0
    r3_r2 = 0  #
    r0 = [sp+28]
    call capture_dispatch_noop_c
    r1 = 0
    r3_r2 = 0  #
    [sp] = r4
    r0 = [sp+28]
    call capture_dispatch_noop_d
    [r13+64] = r4
    [r13+68] = r4
    r0 = L01c340cc
    [r0+64] = r4
    [r0+68] = r4
L01c05114:
    sp += 32
    {pc, r15-r4} = [sp++]
