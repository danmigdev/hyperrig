; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; heap_access: 6 functions, 0x02005b84..0x02005c40

; heap_access_heap_free: 0x02005b84..0x02005b8e, module heap-access (heap_free)
.type heap_access_heap_free,@function
heap_access_heap_free:
    [--sp] = rets
    call L0203d862  ; @call.xl
    pc = [sp++]

; heap_access_lock_enter: 0x02005b8e..0x02005bbe, module heap-access (lock_enter)
.type heap_access_lock_enter,@function
heap_access_lock_enter:
    [--sp] = rets
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fa24
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L02005bbc
    csync
    r0 = L01c1fa20
L02005bb4:
    testset b[r0]
    ifeq goto L02005bb4
    csync
L02005bbc:
    pc = [sp++]

; heap_access_heap_allocate: 0x02005bbe..0x02005bc8, module heap-access (heap_allocate)
.type heap_access_heap_allocate,@function
heap_access_heap_allocate:
    [--sp] = rets
    call L0203c15c  ; @call.xl
    pc = [sp++]

; heap_access_heap_release: 0x02005bc8..0x02005bd2, module heap-access (heap_release)
.type heap_access_heap_release,@function
heap_access_heap_release:
    [--sp] = rets
    call L0203d218  ; @call.xl
    pc = [sp++]

; heap_access_lock_leave: 0x02005bd2..0x02005bfe, module heap-access (lock_leave)
.type heap_access_lock_leave,@function
heap_access_lock_leave:
    [--sp] = rets
    r0 = cnum
    r1 = L01c1fa24
    r2 = [r1+r0<<2]
    r2 += -1
    [r1+r0<<2] = r2
    if (r2 != 0) goto L02005bf6
    csync
    r0 = L01c1fa20
    r1 = 0
    b[r0+0] = r1
L02005bf6:
    call storage_coordination_irq_leave  ; @call.xl
    pc = [sp++]

; heap_access_heap_probe: 0x02005bfe..0x02005c40, module heap-access (heap_probe)
.type heap_access_heap_probe,@function
heap_access_heap_probe:
    [--sp] = {rets, r7-r4}
    sp += -4
    call heap_access_heap_free
    r1 = 16449
    r4 = 0
    if (r0 < r1) goto L02005c3a
    r1 = -16447
    r7 = r0 + r1
    goto L02005c34
L02005c16:
    r0 = r0 >> 1
    r5 = r0 + r4
    call heap_access_lock_enter
    r0 = r5
    call heap_access_heap_allocate
    [sp] = r0
    r6 = [sp]
    if (r6 == 0) goto L02005c2a
    r0 = r6
    call heap_access_heap_release
L02005c2a:
    call heap_access_lock_leave
    if (r6 == 0) goto L02005c32
    r4 = r5
    r5 = r7
L02005c32:
    r7 = r5
L02005c34:
    r0 = r7 - r4
    if (r0 >= 257) goto L02005c16
L02005c3a:
    r0 = r4
    sp += 4
    {pc, r7-r4} = [sp++]
