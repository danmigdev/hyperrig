; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; block_pool: 3 functions, 0x02008308..0x02008586

; block_pool_contains: 0x02008308..0x02008326, module block-pool (contains)
.type block_pool_contains,@function
block_pool_contains:
    [--sp] = {rets, r4}
    r2 = r0
    r3 = [r2+0]
    r0 = 0
    if (r3 == 0) goto L02008324
    r4 = r3 + 16
    if (r4 > r1) goto L02008324
    r0 = [r2+4]
    r2 = r3 + r0
    r0 = 1
    if (r2 <= r1) {
    r0 = 0
    }
L02008324:
    {pc, r4} = [sp++]

; block_pool_release: 0x02008326..0x020083d6, module block-pool (release)
.type block_pool_release,@function
block_pool_release:
    [--sp] = {rets, r9-r4}
    r8 = r1
    r5 = r0
    call block_pool_contains
    if (r0 == 0) goto L020083d4
    r9 = [r5+0]
    r4 = r1 + -16
    r6 = 0
    r7 = r9
    goto L02008350
L0200833e:
    r0 = r5
    r1 = r7
    call block_pool_block_ok
    if (r0 == 0) goto L02008358
    r6 = r7  #
    r0 = [r7+0]
    r0 += r7  ; @add.rr
    r7 = r0
L02008350:
    if (r7 < r4) goto L0200833e
    if (r7 == r4) goto L0200835e
L02008358:
    [r5+32] += 1  ; @rmw.add.s12
    {pc, r9-r4} = [sp++]
L0200835e:
    r0 = r5
    r1 = r4
    call block_pool_block_ok
    if (r0 == 0) goto L02008358
    r0 = [r8+-12]
    r1 = 4038181086
    if (r0 != r1) goto L02008358
    r8 = [r4+0]
    [r5+8] -= r8
    [r5+12] += -1  ; @rmw.add.s12
    r7 = r4 + r8  #
    r0 = [r5+4]
    r0 += r9
    if (r7 >= r0) goto L020083a8
    r0 = r5
    r1 = r7
    call block_pool_block_ok
    if (r0 == 0) goto L020083a8
    r0 = [r7+4]
    r1 = 4042583552
    if (r0 == r1) {
    r0 = [r7+0]
    r8 += r0
    }
L020083a8:
    if (r6 == 0) goto L020083bc
    r0 = [r6+4]
    r1 = 4042583552
    if (r0 != r1) goto L020083bc
    r0 = [r6+0]
    r8 += r0
    goto L020083be
L020083bc:
    r6 = r4
L020083be:
    [r6+0] = r8
    r0 = 4042583552
    r0 = r0 ^ r8  #
    [r6+4] = r0
    [r6+8] = 0x0
    [r6+12] = r0
L020083d4:
    {pc, r9-r4} = [sp++]

; block_pool_maintain: 0x020083d6..0x02008586, module block-pool (maintain)
.type block_pool_maintain,@function
block_pool_maintain:
    [--sp] = {rets, r15-r4}
    sp += -256
    r6 = L01c26890
    r0 = [r6+416]
    if (r0 == 0) goto L02008508
    r9 = b[r6+20] (u)
    if (r9 == 0) {  ; @if.eq.ri.s12
    call audio_pause_pause_audio
    }
    r0 = 625
    r5 = [r6+r0<<2]
    r13 = 0
    r8 = 0
    if (r5 == 0) goto L02008526
    call block_pool_maintenance_allowed
    if (r0 == 0) goto L0200853c
    r0 = 625
    r11 = 622
    r1 = 623
    r15 = 4038181086
    r5 = 0
    goto L020084fa
L02008422:
    if (r14 == 0) goto L02008514
    r0 = [r6+r1<<2]
    r10 = r12 + r0
    r7 = 0
    r4 = r12
    goto L02008472
L02008434:
    r0 = r6 + 2488
    r1 = r4
    call block_pool_block_ok
    if (r0 == 0) goto L0200850c
    r0 = [r4+4]
    if (r0 != r15) goto L0200846e
    if (r7 == 0) goto L02008450
    r0 = [r7+0]
    r1 = [r4+0]
    if (r1 <= r0) goto L0200846e
L02008450:
    r0 = 0
    goto L02008456
L02008454:
    r0 += 1  ; @add.ri.u5
L02008456:
    if (r0 >= r5) goto L02008464
    r1 = sp + 0
    r1 = [r1+r0<<2]
    if (r1 != r4) goto L02008454
L02008464:
    r1 = r4
    if (r5 != r0) {
    r1 = r7
    }
    r7 = r1
L0200846e:
    r0 = [r4+0]
    r4 += r0  ; @add.rr
L02008472:
    if (r4 < r10) goto L02008434
    if (r7 == 0) goto L02008514
    r0 = [r7+8]
    r1 = r0 + 15
    r14 = r1 & 0xFFFFFFF0
    if (r0 != 0) goto L02008486
    r14 = 16
L02008486:
    r4 = r7 + 16
    r2 = 0
    r0 = r4
    r1 = r4
    call effect_relocation_relocate  ; @call.xl
    if (r0 == 0) goto L020084ae
    r0 = r6 + 2452
    r1 = r14
    call block_pool_allocate_compacting
    r1 = r0
    if (r1 != 0) goto L020084cc
    r0 = r14
    call heap_access_vendor_allocate_wrapper
    r1 = r0
    if (r1 != 0) goto L020084c4
L020084ae:
    if (r5 >= 64) goto L02008576
    r0 = sp + 0
    [r0+r5<<2] = r7
    r5 += 1  ; @add.ri.u5
L020084ba:
    r0 = 625
    r1 = 623
    goto L020084fa
L020084c4:
    r0 = r6 + 432
    [r0+0] += 1  ; @rmw.add.s12
L020084cc:
    r0 = r14 >> 2
    r2 = 0
    goto L020084de
L020084d4:
    r3 = [r4+r2<<2]
    [r1+r2<<2] = r3
    r2 += 1  ; @add.ri.u5
L020084de:
    if (r0 != r2) goto L020084d4
    r2 = 1
    r0 = r4
    call effect_relocation_relocate  ; @call.xl
    r0 = r6 + 2488
    r1 = r4
    call block_pool_release
    r8 += r14
    goto L020084ba
L020084fa:
    r12 = [r6+r11<<2]
    r14 = [r6+r0<<2]
    if (r12 != 0) goto L02008422
    goto L02008514
L02008508:
    r0 = 0
    goto L02008572
L0200850c:
    r0 = r6 + 2520
    [r0+0] += 1  ; @rmw.add.s12
L02008514:
    if (r12 == 0) goto L02008526
    if (r14 == 0) goto L02008526
    r0 = r6 + 452
    r4 = 1
    r13 = r14
    goto L0200854a
L02008526:
    r0 = r6 + 2488
    rep 9 {
    [r0++=4] = r13
    }
    [r6+416] = r13
    r0 = r6 + 448
    r4 = 0
    goto L0200854a
L0200853c:
    r0 = r6 + 428
    [r0+0] += 1  ; @rmw.add.s12
    r0 += 24  ; @add.ri.u5
    r4 = 1
    r13 = r5
L0200854a:
    [r0+0] += 1  ; @rmw.add.s12
    if (r9 == 0) {  ; @if.eq.ri.s12
    call audio_pause_resume_audio
    }
    r0 = r8 >> 10
    r2 = 0x0 - r13
    if (r4 != 0) goto L02008562
    r2 = r0
L02008562:
    r0 = 29
    r1 = 11
    call storage_coordination_notify
    r0 = -110
    if (r4 != 0) goto L02008572
    r0 = r4
L02008572:
    sp += 256
    {pc, r15-r4} = [sp++]
L02008576:
    r0 = 625
    r14 = [r6+r0<<2]
    r0 = r11
    r12 = [r6+r0<<2]
    goto L02008514
