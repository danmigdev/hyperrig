; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_journal: 1 function, 0x02002f16..0x02002fae

; capture_journal_write: 0x02002f16..0x02002fae, module capture-journal (write)
.type capture_journal_write,@function
capture_journal_write:
    [--sp] = {rets, r11-r4}
    r5 = r2
    r9 = r1
    r11 = r0
    r7 = -1
    if (r0 < 782336) goto L02002faa
    r0 += r5  ; @add.rr
    if (r0 > 1044480) goto L02002faa
    r0 = r11
    r1 = r5
    call capture_journal_invalidate
    call storage_control_ensure
    call storage_control_mode
    r0 = 2
    call storage_control_activity
    call storage_platform_clock  ; @call.xl
    r8 = r0
    r6 = 0
    r4 = 1
    r10 = L01c26890
    goto L02002f92
L02002f58:
    if (r6 >= r5) goto L02002f94
    r0 = r5 - r6
    r3 = r6 + r11
    r1 = r3.b0 (u)
    r2 = 0x100 - r1
    r1 = r9 + r6
    r7 = umin(r2, r0)
    r0 = 0
    r2 = r7
    call storage_control_program
    r4 = 1
    if (r0 != r7) {
    r4 = 0
    }
    r6 += r7  ; @add.rr
    if (r6 >= r5) goto L02002f92
    r0 = [r10+280]
    if (r0 == 0) goto L02002f92
    r0 = 1
    call L0203feb8  ; @call.xl
L02002f92:
    if (r4 != 0) goto L02002f58
L02002f94:
    r0 = 1
    r1 = r11
    r2 = r8
    call storage_coordination_event
    r0 = 0
    r7 = 0
    call storage_control_activity
    if (r4 != 0) goto L02002faa
    r7 = -3
L02002faa:
    r0 = r7
    {pc, r11-r4} = [sp++]
