; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020012f2..0x0200136e: vendor code (JieLi SDK or library, not reversed), as instructions
L020012f2:
    [--sp] = {rets, r7-r4}
    r0 = 328
    r4 = L01c1f180
    r1 = b[r4+r0] (u)
    r0 = 0
    if (r1 != 0) goto L02001368
    r5 = 1
    r7 = r4 + 328
    b[r7+0] = r5
    r0 = L01c26890
    r6 = 0
    b[r0+68] = r6
    r0 = r7 + 8
    call L0203fdba  ; @call.xl
    r0 = r7 + 168
    [r4+496] = r0
    [r4+500] = r0
    r0 = 56
    call L0203c15c  ; @call.xl
    r3 = r0
    if (r3 == 0) goto L0200136a
    r7 = 0
    goto L0200134a
L0200133e:
    r0 = r3 + r7
    b[r0+20] = r5
    [r0+12] = r6
    call L0200129c
    r7 += 28  ; @add.ri.u5
L0200134a:
    if (r7 != 56) goto L0200133e
    r0 = [r4+332]
    if (r0 != 0) goto L02001356
    call phase3_p5_event_pool_init
L02001356:
    r0 = phase3_p12_sys_event_task
    r1 = L0203a161  ; "sys_event"
    call phase3_p3_task_create
    r0 = 0
L02001368:
    {pc, r7-r4} = [sp++]
L0200136a:
    r0 = -12
    {pc, r7-r4} = [sp++]
