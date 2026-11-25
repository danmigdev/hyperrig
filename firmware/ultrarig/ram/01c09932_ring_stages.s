; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ring_stages: 2 functions, 0x01c09932..0x01c09a2e

; ring_stages_ring_chunks: 0x01c09932..0x01c099f2, module ring-stages (ring_chunks)
.type ring_stages_ring_chunks,@function
ring_stages_ring_chunks:
    [--sp] = {rets, r15-r4}
    sp += -48
    r11 = r0  #
    [sp+8] = r1
    r0 = r1 << 2
    r1 = r11 + r0
    r0 = [r1+240]
    r15 = r3  #
    [sp+4] = r2
    if (r3 == 0) goto L01c099ea
    r8 = 0  #
    [sp] = r1
    r1 = [r1+80]
    r14 = [sp+116]
    r4 = [sp+112]
    r5 = [sp+108]
    r12 = [sp+104]
    r13 = [sp+100]
    r7 = r1 << 16
    r6 = sp + 12
L01c09960:
    r1 = r15 - r8
    r2 = r7 - r0
    r2 = r2 >> 16
    r2 = umin(r1, r2)
    r1 = 1
    if (r2 == 0) goto L01c09972
    r1 = r2
L01c09972:
    r2 = r4 * r1
    r2 = r2 + r0
L01c09978:
    r10 = r1
    r9 = r2
    if (r1 < 2) goto L01c09988
    r2 = r2 - r4
    r1 += -1
    if (r2 >= r7) goto L01c09978
L01c09988:
    r1 = [sp+8]
    r1 = [r11+r1<<2]
    r2 = r0 >> 16
    r2 = r2 << 2
    r1 = r1 + r2
    r1 = r8 << 2  #
    [sp+12] = r1
    r2 = [sp+4]
    r1 = r1 + r2
    r0 = r0.l (u)  #
    [r6+4] = r1
    [r6+8] = r10
    [r6+12] = r0
    [r6+16] = r4
    [r6+20] = r13
    [r6+24] = r12
    r0 = [r5+0]
    [r6+28] = r0
    [r6+32] = r14
    r0 = sp + 12
    if (r14 == 0) goto L01c099c8
    call resampling_kernels_resample  ; @call.xl
    goto L01c099ce
L01c099c8:
    call rate_leaves_one_pole  ; @call.xl
L01c099ce:
    r0 = [r6+28]
    [r5+0] = r0
    r1 = 0
    if (r9 >= r7) {
    r1 = r7
    }
    r8 += r10
    r0 = r9 - r1
    if (r8 < r15) goto L01c09960
    r0 = r9 - r1  #
    r1 = [sp]
L01c099ea:
    [r1+240] = r0
    sp += 48
    {pc, r15-r4} = [sp++]

; ring_stages_ring_read: 0x01c099f2..0x01c09a2e, module ring-stages (ring_read)
.type ring_stages_ring_read,@function
ring_stages_ring_read:
    [--sp] = {rets, r10-r4}
    sp += -24
    r7 = r0
    r9_r8 = r3_r2  #
    r0 = [sp+72]
    r10 = r1  #
    r3 = [sp+68]
    r1 = sp + 20
    [sp] = r0
    [sp+4] = r1
    r0 = r7
    r1 = r10
    r2 = r9
    call rate_leaves_read_rate
    r1 = [sp+20]
    [sp+16] = r1
    r1 = [sp+64]
    r2 = [sp+60]
    r3 = [sp+56]
    r0 = r7  #
    [sp+12] = r0
    r1 = r10  #
    [sp+8] = r1
    [sp+4] = r2
    r3_r2 = r9_r8  #
    [sp] = r3
    call ring_stages_ring_chunks
    sp += 24
    {pc, r10-r4} = [sp++]
