; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_coordination: 5 functions, 0x02002bec..0x02002d9e

; storage_coordination_poll_forward: 0x02002bec..0x02002bf6, module storage-coordination (poll_forward)
.type storage_coordination_poll_forward,@function
storage_coordination_poll_forward:
    [--sp] = rets
    call L0203ea6e  ; @call.xl
    pc = [sp++]

; storage_coordination_gate_core: 0x02002bf6..0x02002d06, module storage-coordination (gate_core)
.type storage_coordination_gate_core,@function
storage_coordination_gate_core:
    [--sp] = {rets, r11-r4}
    r7 = L01c26890
    r2 = b[r7+37] (u)
    r11 = r1
    r5 = r0
    if (r5 == 0) goto L02002c84
    r0 = r2 + 1
    b[r7+37] = r0
    if (r2 != 0) goto L02002c94
    r0 = [r7+336]
    [r7+664] = r0
L02002c18:
    r0 = 1
    if (r5 != 0) goto L02002c1e
    r0 = r5
L02002c1e:
    b[r7+34] = r0
    r0 = [r7+280]
    if (r0 == 0) goto L02002c94
    r0 = b[r7+29] (u)
    if (r0 == 0) goto L02002c94
    call storage_platform_clock  ; @call.xl
    r6 = r0
    call preset_application_rate
    r4 = r0 << 2
    goto L02002c4a
L02002c3c:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r6
    if (r0 >= r4) goto L02002c56
    call storage_coordination_poll_forward
L02002c4a:
    r0 = b[r7+36] (u)
    r1 = b[r7+34] (u)
    if (r0 != r1) goto L02002c3c
L02002c56:
    r6 = 0
    goto L02002c70
L02002c5a:
    r0 = b[r7+36] (u)
    r1 = b[r7+34] (u)
    if (r0 == r1) goto L02002c74
    r0 = 1
    call L0203feb8  ; @call.xl
    r6 += 1  ; @add.ri.u5
L02002c70:
    ifs (r6 <= 3) goto L02002c5a
L02002c74:
    if (r5 == 0) goto L02002c94
    if (r11 != 0) {  ; @if.ne.ri.s12
    r0 = 1
    call L0203feb8  ; @call.xl
    }
    {pc, r11-r4} = [sp++]
L02002c84:
    if (r2 == 0) goto L02002c94
    r0 = r2 + -1
    b[r7+37] = r0
    if ((r0 & 0xFF) == 0) goto L02002c96
L02002c94:
    {pc, r11-r4} = [sp++]
L02002c96:
    r0 = [r7+336]
    r1 = [r7+664]
    if (r0 == r1) goto L02002c18
    r0 = [r7+280]
    if (r0 != 2) goto L02002c18
    r0 = b[r7+29] (u)
    if (r0 == 0) goto L02002c18
    r0 = L01c1f180
    r1 = b[r0+2] (u)
    if (r1 == 0) goto L02002c18
    r0 = b[r0+3] (u)
    if (r0 == 0) goto L02002c18
    r0 = [r7+328]
    if (r0 != 0) goto L02002c18
    r0 = r7 + 668
    [r0+0] += 1  ; @rmw.add.s12
    r8 = 1021
    r9 = [r7+r8<<2]
    call storage_platform_clock  ; @call.xl
    r10 = r0
    call preset_application_rate  ; @call.l
    r6 = r0 * 0xC
    goto L02002cf8
L02002ce6:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r10
    if (r0 >= r6) goto L02002c18
    call storage_coordination_poll_forward  ; @call.l
L02002cf8:
    r0 = [r7+r8<<2]
    r0 = r0 - r9
    if (r0 <= 2) goto L02002ce6
    goto L02002c18

; storage_coordination_gate: 0x02002d06..0x02002d10, module storage-coordination (gate)
.type storage_coordination_gate,@function
storage_coordination_gate:
    [--sp] = rets
    r1 = 1
    call storage_coordination_gate_core
    pc = [sp++]

; storage_coordination_notify: 0x02002d10..0x02002d70, module storage-coordination (notify)
.type storage_coordination_notify,@function
storage_coordination_notify:
    [--sp] = {rets, r8-r4}
    r3 = L01c1f180
    r3 = r1  #
    r5 = [r3+24]
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = L01c26890
    r1 = r0 + 55
L02002d30:
    testset b[r1]
    ifeq goto L02002d30
    csync
    r1 = 299
    r6 = [r0+r1<<2]
    r6 += 1  ; @add.ri.u5
    r7 = r6 & 0x7F
    r7 = r7 << 4
    r8 = L01c2a0d0
    r5 = r5 * 0xA
    [++r7=r8] = r5
    h[r7+4] = r4
    [r7+8] = r3
    [r7+12] = r2
    [r0+r1<<2] = r6
    csync
    r1 = 0
    b[r0+55] = r1
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r8-r4} = [sp++]

; storage_coordination_event: 0x02002d70..0x02002d9e, module storage-coordination (event)
.type storage_coordination_event,@function
storage_coordination_event:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r5 = r1
    r6 = r0
    call storage_platform_clock  ; @call.xl
    r2 = r0 - r4
    call preset_application_rate
    r1 = 1000
    r0 = r0 / r1 (u)
    r2 = r2 / r0 (u)
    r1 = r5 & 0xFFFFFF
    r1 <= insert(r6, p:24, l:8)
    r0 = 24
    call storage_coordination_notify
    {pc, r6-r4} = [sp++]
