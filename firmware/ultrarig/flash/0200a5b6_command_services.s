; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; command_services: 1 function, 0x0200a5b6..0x0200a5e2

; command_services_count_matches: 0x0200a5b6..0x0200a5e2, module command-services (count_matches)
.type command_services_count_matches,@function
command_services_count_matches:
    [--sp] = {rets, r6-r4}
    r1 = r0
    r0 = 0
    r2 = L01c26890
    r3 = 3440
    r4 = 0
    goto L0200a5dc
L0200a5ca:
    r5 = r4 + r2
    r6 = b[r5+r3] (u)
    r5 = 1
    if (r6 != r1) {
    r5 = 0
    }
    r0 += r5  ; @add.rr
    r4 += 1  ; @add.ri.u5
L0200a5dc:
    if (r4 != 18) goto L0200a5ca
    {pc, r6-r4} = [sp++]
