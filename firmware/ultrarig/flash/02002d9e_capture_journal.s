; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_journal: 1 function, 0x02002d9e..0x02002e08

; capture_journal_erase: 0x02002d9e..0x02002e08, module capture-journal (erase)
.type capture_journal_erase,@function
capture_journal_erase:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r5 = -1
    if (r4 < 782336) goto L02002e04
    r0 = 4095
    if ((r4 & r0) != 0) goto L02002e04
    r1 = r1 << 12
    r6 = r1 + r4
    if (r6 > 1044480) goto L02002e04
    r0 = r4
    call capture_journal_invalidate
    call storage_control_ensure
    call storage_control_mode
    r0 = 1
    call storage_coordination_gate
    goto L02002dfa
L02002dd0:
    r0 = 3
    call storage_control_activity
    call storage_platform_clock  ; @call.xl
    r5 = r0
    r0 = 0
    r1 = 200
    r2 = r4
    call storage_control_ioctl
    r0 = 2
    r1 = r4
    r2 = r5
    call storage_coordination_event
    r0 = 0
    call storage_control_activity
    r4 = r4 + 4096
L02002dfa:
    if (r4 < r6) goto L02002dd0
    r0 = 0
    r5 = 0
    call storage_coordination_gate
L02002e04:
    r0 = r5
    {pc, r6-r4} = [sp++]
