; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; pool_callbacks: 3 functions, 0x0201a864..0x0201a9dc

; pool_callbacks_pool_take: 0x0201a864..0x0201a96a, module pool-callbacks (pool_take)
.type pool_callbacks_pool_take,@function
pool_callbacks_pool_take:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r7 = L01c26890
    r0 = r7 + 2452
    r1 = r4
    call block_pool_allocate_compacting
    r5 = r0
    if (r5 == 0) goto L0201a888
L0201a87c:
    if (r5 == 0) goto L0201a880
    r4 = 0
L0201a880:
    [r7+468] = r4
    r0 = r5
    {pc, r8-r4} = [sp++]
L0201a888:
    r0 = [r7+416]
    if (r0 == 0) goto L0201a89c
    r0 = r7 + 2488
    r1 = r4
    call block_pool_allocate_compacting
    r5 = r0
    if (r5 != 0) goto L0201a87c
L0201a89c:
    r0 = r4
    call heap_access_vendor_allocate_wrapper
    r5 = r0
    if (r5 == 0) goto L0201a8b0
    r0 = r7 + 432
    [r0+0] += 1  ; @rmw.add.s12
    goto L0201a87c
L0201a8b0:
    r0 = [r7+416]
    r5 = 0
    if (r0 != 0) goto L0201a87c
    r0 = [r7+436]
    if (r0 == 0) goto L0201a87c
    r0 = L01c1f180
    r0 = b[r0+3] (u)
    r1 = b[r7+24] (u)
    r0 |= r1
    if ((r0 & 0xFF) != 0) goto L0201a87c
    call block_pool_maintenance_allowed
    if (r0 == 0) goto L0201a87c
    r0 = [r7+280]
    if (r0 != 2) goto L0201a906
    [r7+332] = r5
    r0 = 1
    [r7+328] = r0
    goto L0201a8f6
L0201a8ec:
    r0 = 1
    call L0203feb8  ; @call.xl
    r5 += 1  ; @add.ri.u5
L0201a8f6:
    ifs (r5 > 19) goto L0201a900
    r0 = [r7+332]
    if (r0 == 0) goto L0201a8ec
L0201a900:
    r0 = [r7+332]
    if (r0 == 0) goto L0201a95e
L0201a906:
    r0 = r7 + 1924
    r6 = r7 + 416
    r1 = r6 + 72
    r2 = r6 + 76
    call dispatch_helpers_capabilities
    [r7+496] = r0
    r0 = 500  #
    r0 = [r6+0]
    r5 = 0
    b[r7+r0] = r5
    [r6+0] = 0x1
    r8 = r7 + 2488  #
    r2 = [r6+24]
    r0 = r8  #
    r1 = [r6+20]
    call ir_reload_and_leaves_pool_setup
    [r6+28] += 1  ; @rmw.add.s12
    r2 = [r8+4]
    r0 = 29
    r1 = 10
    call storage_coordination_notify
    r0 = [r8+0]
    if (r0 == 0) goto L0201a87c
    r0 = r8
    r1 = r4
    call block_pool_allocate_compacting
    r5 = r0
    goto L0201a87c
L0201a95e:
    r0 = r7 + 348
    [r0+0] += 1  ; @rmw.add.s12
    r5 = 0
    goto L0201a87c

; pool_callbacks_pool_give: 0x0201a96a..0x0201a9ac, module pool-callbacks (pool_give)
.type pool_callbacks_pool_give,@function
pool_callbacks_pool_give:
    [--sp] = {rets, r5, r4}
    r1 = r0
    if (r1 == 0) goto L0201a9aa
    r5 = L01c26890
    r4 = r5 + 2452
    r0 = r4
    call block_pool_contains
    if (r0 != 0) goto L0201a98e
    r4 = r5 + 2488
    r0 = r4
    call block_pool_contains
    if (r0 == 0) goto L0201a996
L0201a98e:
    r0 = r4
    call block_pool_release
    {pc, r5, r4} = [sp++]
L0201a996:
    r0 = [r5+432]
    if (r0 == 0) goto L0201a9a2
    r0 += -1
    [r5+432] = r0
L0201a9a2:
    r0 = r1
    call L0203d218  ; @call.xl
L0201a9aa:
    {pc, r5, r4} = [sp++]

; pool_callbacks_event_report: 0x0201a9ac..0x0201a9dc, module pool-callbacks (event_report)
.type pool_callbacks_event_report,@function
pool_callbacks_event_report:
    [--sp] = {rets, r5, r4}
    r3 = r2
    r4 = r1
    r5 = r0
    if (r5 != 0) goto L0201a9cc
    r1 = uextra(r4, p:16, l:8)
    r0 = 0
    if (r1 != 9) {  ; @if.ne.ri.s12
    r0 = r1
    }
    r1 = r4.b0 (u)
    r2 = uextra(r4, p:8, l:8)
    call audio_pause_breadcrumb
L0201a9cc:
    r0 = 28
    if (r5 != 0) goto L0201a9d2
    r0 = 27
L0201a9d2:
    r1 = r4
    r2 = r3
    call storage_coordination_notify
    {pc, r5, r4} = [sp++]
