; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_helpers: 5 functions, 0x0200e628..0x0200e83a

; console_helpers_pool_check: 0x0200e628..0x0200e69c, module console-helpers (pool_check)
.type console_helpers_pool_check,@function
console_helpers_pool_check:
    [--sp] = {rets, r10-r4}
    r4 = r0
    r5 = [r4+0]
    if (r5 == 0) goto L0200e68c
    r10 = 0  #
    r0 = [r4+4]
    r6 = r5 + r0
    r9 = 4042583552
    r8 = 0
    r7 = 0
    goto L0200e66e
L0200e642:
    r1_r0 = r5_r4
    call block_pool_block_ok
    if (r0 == 0) goto L0200e690
    r0 = [r5+4]
    if (r0 != r9) goto L0200e658
    if (r7 != 0) goto L0200e694
    r0 = [r5+0]
    r7 = 1
    goto L0200e66c
L0200e658:
    r0 = [r5+0]
    r2 = r0 + -16  #
    r1 = [r5+8]
    if (r1 > r2) goto L0200e698
    r10 += r0
    r8 = r8 + 1
    r7 = 0
L0200e66c:
    r5 += r0  ; @add.rr
L0200e66e:
    if (r5 < r6) goto L0200e642
    r0 = -4
    if (r5 != r6) goto L0200e68a
    r1 = [r4+8]
    r0 = -5
    if (r10 != r1) goto L0200e68a
    r1 = [r4+12]
    r0 = 0
    if (r8 != r1) {
    r0 = -5
    }
L0200e68a:
    {pc, r10-r4} = [sp++]
L0200e68c:
    r0 = 0
    {pc, r10-r4} = [sp++]
L0200e690:
    r0 = -1
    {pc, r10-r4} = [sp++]
L0200e694:
    r0 = -2
    {pc, r10-r4} = [sp++]
L0200e698:
    r0 = -3
    {pc, r10-r4} = [sp++]

; console_helpers_top_insert: 0x0200e69c..0x0200e6ca, module console-helpers (top_insert)
.type console_helpers_top_insert,@function
console_helpers_top_insert:
    [--sp] = {rets, r4}
    r3 = [r1+0]
    ifs (r3 >= 8) goto L0200e6aa
    r4 = r3 + 1
    [r1+0] = r4
    goto L0200e6b2
L0200e6aa:
    r1 = [r0+28]
    r3 = 7
    if (r1 >= r2) goto L0200e6c8
L0200e6b2:
    r1 = r3 << 2
    r0 += r1  ; @add.rr
    goto L0200e6c2
L0200e6b8:
    r1 = [r0+-4]
    if (r1 >= r2) goto L0200e6c6
    r3 += -1
    [r0++=-4] = r1
L0200e6c2:
    ifs (r3 >= 1) goto L0200e6b8
L0200e6c6:
    [r0+0] = r2
L0200e6c8:
    {pc, r4} = [sp++]

; console_helpers_free_runs: 0x0200e6ca..0x0200e746, module console-helpers (free_runs)
.type console_helpers_free_runs,@function
console_helpers_free_runs:
    [--sp] = {rets, r10-r4}
    sp += -4
    r5 = r0
    r0 = 0
    r8 = r1  #
    [sp] = r0
    r6 = [r5+0]
    if (r6 == 0) goto L0200e742
    r4 = r6  #
    r0 = [r5+4]
    r10 = r6 + r0
    r9 = 4038181086
    goto L0200e726
L0200e6ea:
    r0 = r5
    r1 = r6
    call block_pool_block_ok
    if (r0 == 0) goto L0200e740
    r0 = [r6+4]
    r7 = [r6+0]
    if (r0 != r9) goto L0200e724
    if (r4 == r6) goto L0200e70e
    r0 = r6 + 16
    r2 = 0
    r1 = r0
    call effect_relocation_relocate  ; @call.xl
    if (r0 == 0) goto L0200e712
L0200e70e:
    r4 += r7  ; @add.rr
    goto L0200e724
L0200e712:
    r0 = r6 - r4
    if (r0 >= 17) {  ; @if.ge.ri.s12
    r2 = r0 + -16
    r1 = sp + 0
    r0 = r8
    call console_helpers_top_insert
    }
    r4 = r6 + r7
L0200e724:
    r6 += r7  ; @add.rr
L0200e726:
    if (r6 < r10) goto L0200e6ea
    r0 = r10 - r4
    if (r0 >= 17) {  ; @if.ge.ri.s12
    r2 = r0 + -16
    r1 = sp + 0
    r0 = r8
    call console_helpers_top_insert
    }
    r0 = [sp]
    goto L0200e742
L0200e740:
    r0 = 0
L0200e742:
    sp += 4
    {pc, r10-r4} = [sp++]

; console_helpers_heap_largest: 0x0200e746..0x0200e77e, module console-helpers (heap_largest)
.type console_helpers_heap_largest,@function
console_helpers_heap_largest:
    [--sp] = {rets, r6-r4}
    call heap_access_heap_free
    r1 = 16449
    r4 = 0
    if (r0 < r1) goto L0200e77a
    r1 = -16447
    r6 = r0 + r1
L0200e75c:
    r5 = r6
L0200e75e:
    r6 = r5
    r0 = r6 - r4
    if (r0 < 257) goto L0200e77a
    r0 = r0 >> 1
    r5 = r0 + r4
    r0 = r5
    call heap_access_vendor_allocate
    if (r0 == 0) goto L0200e75e
    call heap_access_heap_release
    r4 = r5
    goto L0200e75c
L0200e77a:
    r0 = r4
    {pc, r6-r4} = [sp++]

; console_helpers_memory_buckets: 0x0200e77e..0x0200e83a, module console-helpers (memory_buckets)
.type console_helpers_memory_buckets,@function
console_helpers_memory_buckets:
    [--sp] = {rets, r6-r4}
    sp += -48
    r4 = r0
    r5 = L01c26890
    r0 = r5 + 2452
    r1 = r4
    call console_helpers_free_runs
    [sp+12] = r0
    r0 = [r5+416]
    if (r0 == 0) goto L0200e808
    r0 = r5 + 2488
    r1 = sp + 16
    call console_helpers_free_runs
    r5 = r0
    r6 = 0
    goto L0200e7b8
L0200e7a8:
    r0 = sp + 16
    r2 = [r0+r6<<2]
    r1 = sp + 12
    r0 = r4
    call console_helpers_top_insert
    r6 += 1  ; @add.ri.u5
L0200e7b8:
    ifs (r6 < r5) goto L0200e7a8
L0200e7bc:
    r5 = 0
L0200e7be:
    call console_helpers_heap_largest
    r2 = r0
    if (r2 < 1024) goto L0200e7ea
    r1 = sp + 12
    r0 = r4
    call console_helpers_top_insert
    r0 = r2
    call heap_access_vendor_allocate_wrapper
    r1 = sp + 0
    [r1+r5<<2] = r0
    r1 = 1
    if (r0 != 0) goto L0200e7e2
    r1 = r0
L0200e7e2:
    r5 += r1  ; @add.rr
    ifs (r5 > 2) goto L0200e7ea
    if (r0 != 0) goto L0200e7be
L0200e7ea:
    r0 = sp + 0
    r4 = r0 + -4
    goto L0200e7fe
L0200e7f2:
    r0 = [r4+r5<<2]
    call L0203d218  ; @call.xl
    r5 += -1
L0200e7fe:
    ifs (r5 >= 1) goto L0200e7f2
    r0 = [sp+12]
    sp += 48
    {pc, r6-r4} = [sp++]
L0200e808:
    r0 = [r5+436]
    if (r0 == 0) goto L0200e7bc
    r0 = L01c1f180
    r0 = b[r0+3] (u)
    r1 = b[r5+24] (u)
    r0 |= r1
    if ((r0 & 0xFF) != 0) goto L0200e7bc
    r0 = [r5+440]
    if (r0 < 65) goto L0200e7bc
    r0 += -31
    r2 = r0 & 0xFFFFFFF0
    r1 = sp + 12
    r0 = r4
    call console_helpers_top_insert
    goto L0200e7bc
