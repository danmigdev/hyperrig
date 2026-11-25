; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 1 function, 0x02017a62..0x02017ada

; flash_helpers_link_send: 0x02017a62..0x02017ada, module flash-helpers (link_send)
.type flash_helpers_link_send,@function
flash_helpers_link_send:
    [--sp] = {rets, r8-r4}
    r5 = r1
    r6 = r0
    r7 = r5 + -1
    r4 = 0
    if (r7 > 61) goto L02017ad6
    r0 = L01c26890
    r1 = b[r0+136] (u)
    if (r1 == 0) goto L02017a9e
    call state_queries_both_set
    if (r0 == 0) goto L02017ad6
    call link_and_print_other_space
    if (r0 < r5) goto L02017ad6
    r0 = r6
    r1 = r5
    call link_and_print_other_send
    r4 = 1
    if (r0 != r5) {
    r4 = 0
    }
    goto L02017ad6
L02017a9e:
    r8 = L01c1f180
    r1 = [r8+24]
    r1 = r1 * 0xA
    [r0+100] = r1
    r0 = r6
    r1 = r5
    call phase3_p4_cdc_write_data
    if (r0 != r5) goto L02017acc
    r0 = b[r6+r7] (u)
    r1 = 1
    r4 = 1
    if (r0 != 10) {  ; @if.ne.ri.s12
    r4 = 0
    }
    goto L02017ad0
L02017acc:
    r1 = 0
    if (r0 == 0) goto L02017ad6
L02017ad0:
    b[r8+1] = r4
    r4 = r1
L02017ad6:
    r0 = r4
    {pc, r8-r4} = [sp++]
