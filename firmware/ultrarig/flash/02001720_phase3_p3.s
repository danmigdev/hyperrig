; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 2 functions, 0x02001720..0x02001776

; phase3_p3_app_update_init: 0x02001720..0x0200172c, module phase3-p3 (app_update_init)
.type phase3_p3_app_update_init,@function
phase3_p3_app_update_init:
    [--sp] = rets
    call L0203be90  ; @call.xl
    r0 = 0
    pc = [sp++]

; phase3_p3_update_common_state_cbk: 0x0200172c..0x02001776, module phase3-p3 (update_common_state_cbk)
.type phase3_p3_update_common_state_cbk,@function
phase3_p3_update_common_state_cbk:
    [--sp] = {rets, r7-r4}
    r3 = r0
    r4 = r1  #
    r0 = [r3+0]
    r5 = L01c26890
    if (r4 == 2) goto L02001758
    if (r4 != 1) goto L02001764
    r1 = r5 + 1680
    [r1+8] = 0x0
    r6 = 0
    r7 = 0
    d[r1+0] = r7_r6
    r1 = 1
    b[r5+0] = r1
    goto L02001764
L02001758:
    r1 = r5 + 1680
    r6 = r2
    rep 12 {
    r7 = b[r6++=1] (u)
    b[r1++=1] = r7
    }
L02001764:
    r3 = [r3+4]
    if (r3 == 0) goto L0200176c
    r1 = r4
    call r3
L0200176c:
    if (r4 == 3) {  ; @if.eq.ri.s12
    r0 = 0
    b[r5+0] = r0
    }
    {pc, r7-r4} = [sp++]
