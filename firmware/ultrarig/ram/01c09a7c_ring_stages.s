; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ring_stages: 1 function, 0x01c09a7c..0x01c09cda

; ring_stages_rate_state: 0x01c09a7c..0x01c09cda, module ring-stages (rate_state)
.type ring_stages_rate_state,@function
ring_stages_rate_state:
    [--sp] = {rets, r15-r4}
    sp += -68
    r13_r12 = r1_r0  #
    [sp+36] = r2
    if (r1 == 0) goto L01c09a9a
    r0 = L01c30e84
    r0 = r0 + 256
    r1 = 0
    r2 = r13
L01c09a94:
    [r0++=4] = r1
    if (--r2 != 0) goto L01c09a94
L01c09a9a:
    r14 = r12 + 632
    r0 = [r12+884]
    r1 = b[r14+2] (u)
    r2 = r12 + 576
    r2 = r12 + 276  #
    [sp+44] = r2
    [sp+40] = r2
    if (r0 != r1) goto L01c09ad0
    r4 = -12
L01c09ab8:
    r0 = r12 + r4
    r6 = r0 + 872
    r1 = [r6+12]
    r0 = [r6+0]
    call rate_leaves_approach
    r4 = r4 + 4
    [r6+0] = r0
    if (r4 != 0) goto L01c09ab8
    goto L01c09b34
L01c09ad0:
    r6 = r14 + 228
    r4 = 0
    r7 = 0
L01c09ad8:
    r0 = [r6+r7<<2]
    r1 = 0
    call rate_leaves_approach
    [r6+r7<<2] = r0
    r7 = r7 + 1
    r4 |= r0
    if (r7 != 3) goto L01c09ad8
    if (r4 != 0) goto L01c09b34
    r0 = 0
    r1 = [sp+40]
    r1 = r1 + 164
    r2 = 0
L01c09afa:
    r3 = r2 << 2
    r3 += r12
    r4 = [r3++=80]
    r6 = 0
L01c09b04:
    [r4+r6<<2] = r0
    r7 = [r3+0]
    r6 = r6 + 1
    if (r6 <= r7) goto L01c09b04
    [r1+r2<<2] = r0
    r2 = r2 + 1
    if (r2 != 3) goto L01c09afa
    r0 = [r14+44]
    r1 = 0
    r2 = 0
L01c09b22:
    [r0+r2<<2] = r1
    r2 = r2 + 1
    if (r2 != 240) goto L01c09b22
    r0 = [r14+252]
    b[r14+2] = r0
L01c09b34:
    r4 = r12 + 820
    r0 = [r4+0]
    r1 = [r4+4]
    call rate_leaves_approach
    [sp+32] = r4
    [r4+0] = r0
    r0 = b[r14+2] (u)
    if (r0 == 0) goto L01c09cd6
    r1 = read_only_tables_0203be28
    r0 = b[r0+r1] (u)
    r0 = r0 >> 1
    [sp+28] = r0
    r9 = sp + 48
    r7 = 0
    r0 = [sp+44]
    r5 = r0 + 100
    r0 = r5 + 172
    [sp+20] = r0
    [sp+24] = r14
L01c09b6e:
    r4 = r7 << 2
    r6 = r12 + r4
    r14 = r6 + 312
    r0 = [r14+0]
    r1 = [r6+376]
    r1 = r1 - r0
    r2 = 4
    r1 = r1 / r2 (s)
    r0 = r0 + r1
    [r14+0] = r0
    r0 = [r14+32]
    r1 = [r6+408]
    r1 = r1 - r0
    r1 = r1 / r2 (s)
    r0 = r0 + r1
    [r14+32] = r0
    r15 = r5 + r4  #
    r0 = [sp+20]
    r1 = [r0+r7<<2]
    r0 = [++r15=160]
    call rate_leaves_approach
    [r15+0] = r0
    r2 = [sp+44]
    r0 = [r2+0]
    r1 = 1664525
    r0 *= r1
    r1 = 1013904223
    r0 = r0 + r1
    [r2+0] = r0
    r1 = [r6+544]
    r0 = r0 >>> 1
    r0 = r0 - r1
    r0 = r0 >>> 4
    r0 = r0 + r1
    [r6+544] = r0
    r1 = [r2+4]
    r11_r10 = r0 * r1 (s)  #
    r0 = [sp+36]
    r11_r10 >>= 30
    if (r0 == 0) goto L01c09bf6
    r0 = r12
    r1 = r7
    r2 = r10
    call rate_leaves_wrap_position
L01c09bf6:
    r6 = 1024  #
    r3 = [sp+40]
    r0 = [r3+r7<<2]
    r1 = [r14+0]
    r2 = [r14+32]
    r0 += r10  #
    [sp+16] = r6
    r0 = r3 + 164  #
    [sp+12] = r0
    r0 = r0 + r4
    r3 = r13  #
    [sp+8] = r0
    r0 = L01c30e84
    r4 = r0 + 512  #
    [sp+4] = r2
    r0 = r12  #
    [sp] = r1
    r1 = r7
    r2 = r4
    call ring_stages_ring_read
    r8 = r5
    r0 = r5 + 184
    r10 = [r0+r7<<2]
    if (r13 == 0) goto L01c09c68
    r0 = [r15+0]
    r1 = r0 >>> 31
    r2 = r13
    r3 = L01c30e84
L01c09c4c:
    r6 = [r3+512]
    r5 = [r3+0]
    r15_r14 = r5 * r0 (s)
    r15_r14 >>= 31
    r5 = r14 + r6
    [r3+512] = r5
    r3 = r3 + 4
    if (--r2 != 0) goto L01c09c4c
L01c09c68:
    r1 = r7 * 0x140  #
    [sp+48] = r4
    r14 = [sp+24]
    r0 = [r14+44]
    r0 = r0 + r1
    [r9+4] = r0
    [r9+8] = r13
    r0 = [sp+28]
    [r9+12] = r0
    r0 = [sp+32]
    r0 = [r0+0]
    [r9+16] = r0
    r0 = sp + 48
    call filter_kernels_section_cascade  ; @call.xl
    r0 = r12
    r1 = r7
    r2 = r4
    r3 = r13
    call rate_leaves_ring_write
    if (r13 == 0) goto L01c09cca
    r11 = r10 >>> 31
    r0 = L01c30e84
    r0 = r0 + 256
    r1 = r13
L01c09cb4:
    r2 = [r0+0]
    r3 = [r0+256]
    r5_r4 = r3 * r10 (s)
    r5_r4 >>= 15
    r2 = r2 + r4
    [r0++=4] = r2
    if (--r1 != 0) goto L01c09cb4
L01c09cca:
    r0 = b[r14+2] (u)
    r7 = r7 + 1
    r5 = r8
    ifs (r7 < r0) goto L01c09b6e
L01c09cd6:
    sp += 68
    {pc, r15-r4} = [sp++]
