; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; status_report: 1 function, 0x0201ab28..0x0201abc8

; status_report_report: 0x0201ab28..0x0201abc8, module status-report (report)
.type status_report_report,@function
status_report_report:
    [--sp] = {rets, r6-r4}
    r6 = L01c26890
    [r6+640] = r0
    r0 = 1023
    r5 = [r6+r0<<2]
    r0 += -1
    r4 = [r6+r0<<2]
    r0 = b[r6+31] (u)
    if (r0 == 0) goto L0201ab6c
    r0 = r6 + 588
    r1 = [r0+0]
    r2 = [r0+4]
    r3 = 0
    b[r6+31] = r3
    [r0+0] = r3
    r0 = L01c1f180
    r0 = [r0+68]
    r1 = r1 / r0 (u)
    r0 = 25
    call storage_coordination_notify
L0201ab6c:
    r0 = [r6+644]
    if (r5 == r0) goto L0201ab82
    r2 = r5 - r0
    r0 = 11
    r1 = r5
    call storage_coordination_notify
    [r6+644] = r5
L0201ab82:
    r0 = [r6+648]
    if (r4 == r0) goto L0201ab98
    r2 = r4 - r0
    r0 = 12
    r1 = r4
    call storage_coordination_notify
    [r6+648] = r4
L0201ab98:
    r0 = L01c340cc
    r4 = [r0+56]
    r0 = L01c341a4
    r1 = [r6+652]
    r5 = [r0+0]
    if (r4 != r1) goto L0201abb8
    r0 = [r6+656]
    if (r5 == r0) goto L0201abc6
L0201abb8:
    r0 = 15
    r1 = r4
    r2 = r5
    call storage_coordination_notify
    d[r6+652] = r5_r4
L0201abc6:
    {pc, r6-r4} = [sp++]
