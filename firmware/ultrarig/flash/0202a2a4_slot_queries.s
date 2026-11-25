; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 1 function, 0x0202a2a4..0x0202a43c

; slot_queries_type_fits: 0x0202a2a4..0x0202a43c, module slot-queries (type_fits)
.type slot_queries_type_fits,@function
slot_queries_type_fits:
    [--sp] = {rets, r15-r4}
    sp += -128
    r11 = r2
    r5_r4 = r1_r0
    r2 = 0
    if (r4 == 7) goto L0202a2d8
    r0 = r4 + -1
; HyperRig MINI, product option: an effect of HyperRig has no second amount of memory and no parts.
.if MINI_PRODUCT
    if (r0 <= 38) goto Lhr_fits_listed
    ifs (r11 < 1) goto L0202a2d8
    r12 = r11
    ifs (r11 >= 8) {
    r12 = 8
    }
    r6 = 0
    r7 = 0
    r1 = 0
    goto L0202a318
Lhr_fits_listed:
.else
    if (r0 > 38) goto L0202a2d8
.endif
    ifs (r11 < 1) goto L0202a2d8
    r0 = r4 + -27
    if (r0 > 8) goto L0202a2de
    r1 = 497
    r0 = r1 & (1 << r0)
    if (r0 == 0) goto L0202a2de
    call effect_setup_pool_full  ; @call.xl
    if (r0 == 0) goto L0202a2de
L0202a2d8:
    r0 = r2
    sp += 128
    {pc, r15-r4} = [sp++]
L0202a2de:
    r12 = r11
    ifs (r11 >= 8) {
    r12 = 8
    }
    r6 = 2
    r0 = effect_parameter_metadata
    if (r4 == 29) goto L0202a306
    r1 = r4 * 0x54
    r1 = r1 + r0
    r2 = [r1+80]
    r6 = 0
    if (r2 == 0) goto L0202a306
    r6 = h[r1+76] (s)
L0202a306:
    r1 = r4 * 0x54
    r0 = r0 + r1
    r2 = [r0+8]
    r7 = 0
    r1 = 0
    if (r2 == 0) goto L0202a318
    r1 = h[r0+4] (s)
L0202a318:
    r0 = r4
    r2 = r6
    call effect_setup_demand_by_type
    call ram_callbacks_aligned_size  ; @call.xl
    ifs (r11 < 1) goto L0202a340
    r1 = 0
L0202a32c:
    r2 = [r5+r1<<2]
    r3 = sp + 96
    [r3+r1<<2] = r2
    r1 = r1 + 1
    r7 = umax(r2, r7)
    ifs (r1 < r12) goto L0202a32c
L0202a340:
    r2 = 1
    if (r0 <= r7) goto L0202a2d8
    r2 = sp + 12
    r3 = sp + 8
    r0 = r4
    r1 = r6
    call effect_setup_partition_sizes
    r1 = r0
    r2 = 0
    ifs (r1 < 2) goto L0202a2d8
    r3 = 1
    r0 = r3 << r1
    r2 = r0 + -1
    r0 = 0
    r4 = 1
    if (r2 == 0) goto L0202a432
    r0 = [sp+8]
    r8 = r0 + 16  #
    [sp] = r0
    r3 = 0
L0202a374:
    r14 = 0  #
    [sp+4] = r3
    ifs (r12 < 2) goto L0202a39a
    r3 = 0
    r0 = 1
L0202a380:
    r4 = sp + 96
    r5 = [r4+r3<<2]
    r4 = [r4+r0<<2]
    r14 = r0
    if (r4 <= r5) {
    r14 = r3
    }
    r0 = r0 + 1
    r3 = r14
    ifs (r0 < r12) goto L0202a380
L0202a39a:
    r0 = sp + 96
    r15 = [r0+r14<<2]
    r0 = r15 + -16  #
    r3 = [sp]
    r3 = r0 - r3
    r13 = r8
    if (r15 <= r8) {
    r3 = 0
    }
    r0 = sp + 12
    call effect_setup_partition_pack
    if (r0 == 0) goto L0202a42c
    r4 = 0
    r8 = r13
    r3 = r8
L0202a3be:
    r5 = r0 & (1 << r4)
    if (r5 == 0) goto L0202a3cc
    r5 = sp + 12
    r5 = [r5+r4<<2]
    r3 = r3 + r5
L0202a3cc:
    r4 = r4 + 1
    if (r1 != r4) goto L0202a3be
    ifs (r11 < 1) goto L0202a3fc
    r4 = 0
L0202a3d8:
    r6 = sp + 96
    r5 = [r6+r4<<2]
    if (r5 < r3) goto L0202a3f0
    r7 = [r6+r14<<2]
    r6 = r4
    if (r5 >= r7) {
    r6 = r14
    }
    r14 = r6
L0202a3f0:
    r4 = r4 + 1
    ifs (r4 < r12) goto L0202a3d8
    r4 = sp + 96
    r15 = [r4+r14<<2]
L0202a3fc:
    r3 = r3 + 31
    r4 = r3 & 0xFFFFFFF0
    r3 = r15 - r4
    if (r15 <= r4) {
    r3 = 0
    }
    r4 = sp + 96
    [r4+r14<<2] = r3
    r3 = ~r0
    r0 = r2 & ~r0
    if ((r2 & r3) == 0) goto L0202a426
    r2 = r0  #
    r3 = [sp+4]
    r3 = r3 + 1
    if (r3 < 4) goto L0202a374
L0202a426:
    r4 = 1
    r3 = 1
    goto L0202a432
L0202a42c:
    r0 = r2
    r3 = 1
    r4 = 0
L0202a432:
    if (r0 == 0) goto L0202a436
    r3 = 0
L0202a436:
    r2 = r3 & r4
    goto L0202a2d8
