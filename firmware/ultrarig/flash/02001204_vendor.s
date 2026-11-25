; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02001204..0x020012c8: vendor code (JieLi SDK or library, not reversed), as instructions
sdk_timer1_init:
    [--sp] = rets
    r0 = 66816
    [r0+0] = 0x4000
    r2 = phase3_p6_timer1_isr
    r0 = 5
    r1 = 1
    r3 = 0
    call storage_platform_register
    r0 = 0
    pc = [sp++]
L02001224:
    [--sp] = {rets, r4}
    r4 = L01c26fe4
    r0 = r4 + 2032
    call L0203fdba  ; @call.xl
    [r4+0] = r4
    [r4+4] = r4
    r0 = r4 + 8
    [r4+8] = r0
    [r4+12] = r0
    call sdk_timer1_init
    r0 = L0201ef6c
    r1 = L0203a176  ; "systimer"
    call phase3_p3_task_create
    {pc, r4} = [sp++]
L02001254:
    [--sp] = rets
    r0 = L0201f2ae
    r1 = L0203a1b7  ; "sys_timer"
    call phase3_p3_task_create
    pc = [sp++]
L02001268:
    [--sp] = {rets, r5, r4}
    r4 = L02055948
    r5 = L02055954
    goto L0200128a
L02001278:
    r0 = [r4+4]
    if (r0 == 0) goto L02001288
    r2 = [r0+4]
    if (r2 == 0) goto L02001288
    r0 = r4  #
    r1 = [r4+8]
    call r2
    if (r0 != 0) goto L02001290
L02001288:
    r4 += 12  ; @add.ri.u5
L0200128a:
    if (r4 < r5) goto L02001278
    {pc, r5, r4} = [sp++]
L02001290:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0200129a:
    goto L0200129a
L0200129c:
    r1 = L01c1f370
sdk_list_add_tail_020012a2:
    r2 = [r1+4]
    [r1+4] = r0
    [r0+] = {r2, r1}
    [r2+0] = r0
    rts
L020012ae:
    r3 = 0
    [r0+24] = r3
    [r0+20] = r3
    [r0+0] = r1
    [r0+8] = r1
    [r0+12] = r1
    r1 += r2  #  ; @add.rr.p
    [r0+16] = r1
    [r0+4] = r1
    [r0+28] = r2
    b[r0+32] = r3
    rts
