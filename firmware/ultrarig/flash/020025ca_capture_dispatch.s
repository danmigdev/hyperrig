; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_dispatch: 2 functions, 0x020025ca..0x0200268e

; capture_dispatch_prepare: 0x020025ca..0x02002634, module capture-dispatch (prepare), capture-live (prepare), capture-native (prepare)
.type capture_dispatch_prepare,@function
capture_dispatch_prepare:
    [--sp] = {rets, r5, r4}
    r5 = L01c26890
    r1 = [r5+416]
    r4 = r0
    r0 = -110
    if (r1 != 0) goto L02002624
    r1 = [r5+436]
    if (r1 == 0) goto L020025ee
    r2 = [r5+440]
    r0 = 0
    if (r2 >= r4) goto L02002624
L020025ee:
    r0 = 500
    r2 = 0
    b[r5+r0] = r2
    r0 = r1
    call L0203d218  ; @call.xl
    r4 = r4 + 256
    r0 = r4
    call L0203c15c  ; @call.xl
    [r5+436] = r0
    if (r0 != 0) goto L02002614
    r4 = r0
L02002614:
    [r5+440] = r4
    if (r0 == 0) goto L02002626
    r1 = 1032
    [r5+r1<<2] = r0
    r0 = 0
L02002624:
    {pc, r5, r4} = [sp++]
L02002626:
    r1 = 1035
    r0 = -100
    [r5+r1<<2] = r0
    {pc, r5, r4} = [sp++]

; capture_dispatch_cleanup: 0x02002634..0x0200268e, module capture-dispatch (cleanup), capture-live (cleanup), capture-native (cleanup)
.type capture_dispatch_cleanup,@function
capture_dispatch_cleanup:
    [--sp] = {rets, r6-r4}
    r2 = 500
    r6 = L01c1f180
    r1_r0 = d[r6+60]
    r5 = L01c26890
    r3 = 0
    b[r5+r2] = r3
    call capture_dispatch_probe  ; @call.xl
    r1 = [r6+64]
    r4 = r0
    if (r1 == 0) goto L0200268a
    call capture_dispatch_prepare
    if (r0 != 0) goto L02002688
    r0 = 1030
    [r5+r0<<2] = r4
    r3_r2 = d[r6+60]
    r0 = [r5+436]
    r1 = r4
    call capture_dispatch_load  ; @call.xl
    if (r0 != 0) goto L02002688
    r0 = 500
    r1 = 1
    b[r5+r0] = r1
    r0 = 0
L02002688:
    {pc, r6-r4} = [sp++]
L0200268a:
    r0 = -2
    {pc, r6-r4} = [sp++]
