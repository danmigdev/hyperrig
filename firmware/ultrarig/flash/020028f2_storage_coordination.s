; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_coordination: 2 functions, 0x020028f2..0x0200294e

; storage_coordination_ready_threshold: 0x020028f2..0x02002920, module storage-coordination (ready_threshold)
.type storage_coordination_ready_threshold,@function
storage_coordination_ready_threshold:
    r1 = 1019
    r2 = L01c26890
    r3 = [r2+r1<<2]
    r2 = [r2+404]
    r1 = r0
    r0 = r3 - r2
    r2 = 1331
    r0 *= r2
    r2 = 1000
    r2 = r0 / r2 (u)
    r0 = 1
    if (r2 < r1) {
    r0 = 0
    }
    rts

; storage_coordination_wait_ready: 0x02002920..0x0200294e, module storage-coordination (wait_ready)
.type storage_coordination_wait_ready,@function
storage_coordination_wait_ready:
    [--sp] = {rets, r6-r4}
    r4 = 0
    r5 = L01c1f180
    r6 = L01c26890
    goto L02002948
L02002932:
    r0 = 150
    call storage_coordination_ready_threshold
    if (r0 != 0) goto L0200294c
    r0 = [r5+24]
    [r6+204] = r0
    r0 = 1
    call L0203feb8  ; @call.xl
    r4 += 1  ; @add.ri.u5
L02002948:
    ifs (r4 <= 29) goto L02002932
L0200294c:
    {pc, r6-r4} = [sp++]
