; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; heap_access: 2 functions, 0x02008296..0x02008308

; heap_access_vendor_allocate: 0x02008296..0x02008302, module heap-access (vendor_allocate)
.type heap_access_vendor_allocate,@function
heap_access_vendor_allocate:
    [--sp] = {rets, r6-r4}
    sp += -8
    r4 = r0
    r5 = 0
    if (r4 == 0) goto L020082fc
    r0 = 16448
    r6 = r4 + r0
    call heap_access_heap_free
    if (r0 < r6) goto L020082fc
    call heap_access_lock_enter
    r0 = r4
    call heap_access_heap_allocate
    [sp+4] = r0
    call heap_access_lock_leave
    r4 = [sp+4]
    if (r4 == 0) goto L020082fc
    call heap_access_heap_free
    r0 = r0 >> 14
    if (r0 != 0) goto L020082d2
    r0 = r4
    call heap_access_heap_release
    goto L020082fc
L020082d2:
    call heap_access_lock_enter
    r0 = 8192
    call heap_access_heap_allocate
    [sp] = r0
    r0 = [sp]
    if (r0 == 0) goto L020082ee
    call heap_access_heap_release
    call heap_access_lock_leave
    goto L020082fa
L020082ee:
    call heap_access_lock_leave
    r0 = r4
    call heap_access_heap_release
    r4 = 0
L020082fa:
    r5 = r4
L020082fc:
    r0 = r5
    sp += 8
    {pc, r6-r4} = [sp++]

; heap_access_vendor_allocate_wrapper: 0x02008302..0x02008308, module heap-access (vendor_allocate_wrapper)
.type heap_access_vendor_allocate_wrapper,@function
heap_access_vendor_allocate_wrapper:
    [--sp] = rets
    call heap_access_vendor_allocate
    pc = [sp++]
