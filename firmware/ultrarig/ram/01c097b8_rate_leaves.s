; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; rate_leaves: 4 functions, 0x01c097b8..0x01c09932

; rate_leaves_approach: 0x01c097b8..0x01c097ce, module rate-leaves (approach)
.type rate_leaves_approach,@function
rate_leaves_approach:
    r2 = r1 - r0
    r3 = r2 + 63
    if (r3 >= 127) {
    r1 = 4
    r1 = r2 / r1 (s)
    r1 = r1 + r0
    }
    r0 = r1
    rts

; rate_leaves_soft_clip: 0x01c097ce..0x01c0989c, module rate-leaves (soft_clip)
.type rate_leaves_soft_clip,@function
rate_leaves_soft_clip:
    [--sp] = {rets, r15-r4}
    sp += -12
    r12 = r1
    if (r0 == 0) goto L01c09898
    r13 = r1 >>> 31
    r1 = L01c30e84
    r2 = 0xC00000
    r3 = 0
    [sp] = r2
    [sp+4] = r3
L01c097ea:
    r4 = [r1+0]
    r15_r14 = r4 * r12 (s)
    r15_r14 >>>= 19
    r4 = r14 - 0xC00000
    r2 = 0
    r4 = r15 - r2 - !c
    r4 = psr
    r5 = r4 >> 3
    r4 ^= r5
    r11_r10 = r15_r14
    if ((r4 & 0x1) == 0) {
    r10 = [sp]
    r11 = [sp+4]
    }
    r2 = 4282384384
    r6 = r10 - r2
    r2 = -1
    r7 = r11 - r2 - !c
    r5 = psr
    r2 = sextra(r5, p:0, l:1)
    r3 = sextra(r5, p:3, l:1)
    r2 ^= r3
    r5 = ~r2
    r6 |= r7
    if ((r6 & r5) == 0) {
    r10 = 4282384384
    r11 = -1
    }
    r2 = r14 * r15
    r15_r14 = r14 * r14 (u)
    r3 = r15 + r2
    r15 = r3 + r2
    r15_r14 >>>= 23
    r8 = 0x1200000
    r9 = 0
    if ((r6 & r5) == 0) {
    r14 = r8
    r15 = 0
    }
    if ((r4 & 0x1) == 0) {
    r14 = r8
    r15 = 0
    }
    r2 = r14 * r11
    r9_r8 = r14 * r10 (u)
    r2 += r9
    r3 = r15 * r10
    r9 = r2 + r3
    r9_r8 >>>= 23
    r9_r8 <<= 2
    r2 = 27
    r3_r2 = r9_r8 / r2 (s)
    r4 = r10 - r2
    r5 = r11 - r3 - !c
    [r1++=4] = r4
    if (--r0 != 0) goto L01c097ea
L01c09898:
    sp += 12
    {pc, r15-r4} = [sp++]

; rate_leaves_wrap_position: 0x01c0989c..0x01c098c6, module rate-leaves (wrap_position)
.type rate_leaves_wrap_position,@function
rate_leaves_wrap_position:
    [--sp] = {rets, r4}
    r3 = r1 << 2
    r3 = r3 + r0
    r4 = [++r3=240]
    r0 += 80
    r1 = [r0+r1<<2]
    r0 = r4 - r2
    r1 = r1 << 16
    ifs (r0 <= 4294967295) {
    r0 = r0 + r1
    [r3+0] = r0
    {pc, r4} = [sp++]
    }
    ifs (r0 < r1) {
    r1 = 0
    }
    r0 = r0 - r1
    [r3+0] = r0
    {pc, r4} = [sp++]

; rate_leaves_read_rate: 0x01c098c6..0x01c09932, module rate-leaves (read_rate)
.type rate_leaves_read_rate,@function
rate_leaves_read_rate:
    [--sp] = {rets, r6-r4}
    r4 = r0 + 240  #
    r6 = [sp+16]
    r5 = r0 + 160
    r5 = [r5+r1<<2]
    r4 = [r4+r1<<2]
    r5 = r5 << 16
    r5 = r5 - r4
    ifs (r5 > -1) goto L01c098ec
    r0 += 80
    r0 = [r0+r1<<2]
    r0 = r0 << 16
    r5 = r5 + r0
L01c098ec:
    r0 = r6 * r2
    r1 = r3 - r5
    ifs (r1 <= r0) {
    r0 = 0x0 - r0
    r0 = smax(r1, r0)
    }
    if (r2 == 32) goto L01c0990e
    if (r2 != 64) {
    r0 = r0 / r2 (s)
    } else {
    r0 = r0 >>> 6
    }
    goto L01c09910
L01c0990e:
    r0 = r0 >>> 5
L01c09910:
    r1 = 1
    r3 = 65535
    r2 = 1
    if ((r4 & r3) == 0) {
    r2 = 0
    }
    r0 = 0x10000 - r0  #
    r3 = [sp+20]
    if (r0 == 65536) {
    r1 = 0
    }
    r1 |= r2
    [r3+0] = r1
    {pc, r6-r4} = [sp++]
