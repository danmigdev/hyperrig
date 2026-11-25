; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 2 functions, 0x02017988..0x02017a18

; flash_helpers_record_tick: 0x02017988..0x020179c0, module flash-helpers (record_tick)
.type flash_helpers_record_tick,@function
flash_helpers_record_tick:
    [--sp] = rets
    sp += -12
    r0 = sp + 0
    call storage_fault_decode
    if (r0 == 0) goto L020179bc
    r1 = b[sp+8] (u)
    r0 = sp + 0
    r1 += 1  ; @add.ri.u5
    r2 = r1.b0 (u)
    b[sp+8] = r1
    if (r2 < 6) goto L020179b6
    r1 = 0
    b[r0+8] = r1
    r0 = h[sp+2] (u)
    call record_helpers_next_serial
    h[sp+2] = r0
L020179b6:
    r0 = sp + 0
    call storage_fault_encode
L020179bc:
    sp += 12
    pc = [sp++]

; flash_helpers_link_ready: 0x020179c0..0x02017a18, module flash-helpers (link_ready)
.type flash_helpers_link_ready,@function
flash_helpers_link_ready:
    [--sp] = {rets, r5, r4}
    r5 = L01c26890
    r0 = b[r5+136] (u)
    if (r0 == 0) goto L020179d6
    call state_queries_both_set
    r4 = r0
    goto L02017a14
L020179d6:
    call phase3_p4_cdc_ready
    r4 = 0
    if (r0 == 0) goto L02017a14
    r0 = L01c1f180
    r0 = b[r0+1] (u)
    if (r0 == 0) goto L02017a14
    r0 = L01c26844
    r0 = b[r0+0] (u)
    if (r0 != 0) goto L02017a14
    call L02006a9e
    if ((r0 & 1) != 0) goto L02017a14
    r0 = b[r5+148] (u)
    r4 = 1
    if (r0 == 0) goto L02017a14
    r0 = 0
    b[r5+148] = r0
    r2 = [r5+144]
    r0 = 14
    r1 = 3
    call storage_coordination_notify
L02017a14:
    r0 = r4
    {pc, r5, r4} = [sp++]
