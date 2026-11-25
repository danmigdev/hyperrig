; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 1 function, 0x0200152c..0x020016ec

; phase3_p4_app_task_handler: 0x0200152c..0x020016ec, module phase3-p4 (app_task_handler)
.type phase3_p4_app_task_handler,@function
phase3_p4_app_task_handler:
    sp += -128
    call L02001224
    call L02001254
    call L02001268
    r4 = L020558c0
    r5 = L020558d0
    goto L0200154c
L02001548:
    r0 = [r4++=4]
    call r0
L0200154c:
    if (r4 < r5) goto L02001548
    r4 = L020558d4
    r5 = L020558d8
    goto L02001562
L0200155e:
    r0 = [r4++=4]
    call r0
L02001562:
    if (r4 < r5) goto L0200155e
    r4 = L020558bc
    r5 = L020558c0
    goto L02001578
L02001574:
    r0 = [r4++=4]
    call r0
L02001578:
    if (r4 < r5) goto L02001574
    r4 = L020558d8
    r5 = L020558dc
    goto L0200158e
L0200158a:
    r0 = [r4++=4]
    call r0
L0200158e:
    if (r4 < r5) goto L0200158a
    r6 = L01c1f180
    r0 = r6 + 164
    [r6+164] = r0
    [r6+168] = r0
    r5 = L01c26890
    r0 = r5 + 3828
    call L0203fb92  ; @call.xl
    r0 = 32669696
    r1 = 32669696
    goto L020015ca
L020015c2:
    r2 = r0 + 16
    [r0+16] = r2
    [r0+20] = r2
    r0 += 32
L020015ca:
    if (r0 < r1) goto L020015c2
    r0 = 328
    r0 = b[r6+r0] (u)
    if (r0 == 0) goto L02001688
L020015d8:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r7 = r5 + 68
L020015e4:
    testset b[r7]
    ifeq goto L020015e4
    r0 = r6 + 496
    csync
    r4 = r0
L020015f2:
    r4 = [r4+0]
    if (r4 == r0) goto L02001616
    r1 = b[r4+20] (u)
    if (r1 == 0) goto L020015f2
    r1_r0 = d[r4+0]
    [r0+4] = r1
    [r1+0] = r0
    csync
    r0 = 0
    b[r5+68] = r0
    call storage_coordination_irq_leave  ; @call.xl
    goto L02001630
L02001616:
    csync
    r0 = 0
    b[r5+68] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 28
    call L0203c15c  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L0200168e
L02001630:
    r0 = 0
    b[r4+20] = r0
    [r4+24] = r0
    r1 = phase3_p4_app_core_event_handler
    [r4+12] = r1
    r1 = 65535
    h[r4+22] = r1
    b[r4+21] = r0
    call L0204178c  ; @call.xl
    [r4+16] = r0
    if (r0 == 0) goto L020016e0
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0200165e:
    testset b[r7]
    ifeq goto L0200165e
    r0 = r6 + 496
    csync
    r1 = r0
L0200166c:
    r1 = [r1+0]
    if (r1 != r0) goto L0200166c
    r0 = r4
    call L0200129c
    csync
    r0 = 0
    b[r5+68] = r0
    call storage_coordination_irq_leave  ; @call.xl
    goto L0200168e
L02001688:
    call L020012f2
    if (r0 == 0) goto L020015d8
L0200168e:
    r4 = L020558d0
    r5 = L020558d4
    goto L020016a0
L0200169c:
    r0 = [r4++=4]
    call r0
L020016a0:
    if (r4 < r5) goto L0200169c
    r4 = L0203c018
    r5 = L0203c018
    goto L020016b8
L020016b2:
    r0 = [++r4=-4]
    call r0
L020016b8:
    if (r4 > r5) goto L020016b2
    r0 = main_task_main_task
    r1 = L02039f84  ; "#C0tankg_ctl"
    call phase3_p3_task_create
L020016cc:
    r0 = sp + 0
    call L020405d6  ; @call.xl
    if (r0 != 13) goto L020016cc
    r0 = sp + 0
    call phase3_p3_app_core_msg_handler
    goto L020016cc
L020016e0:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L020016ea:
    goto L020016ea
