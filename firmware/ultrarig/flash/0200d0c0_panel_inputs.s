; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 4 functions, 0x0200d0c0..0x0200d200

; panel_inputs_change_check: 0x0200d0c0..0x0200d0e2, module panel-inputs (change_check)
.type panel_inputs_change_check,@function
panel_inputs_change_check:
    r0 = L01c26890
    r1 = [r0+948]
    r2 = L01c34468
    r2 = [r2+0]
    if (r2 != r1) {
    r1 = 872
    r2 = 1
    b[r0+r1] = r2
    }
    rts

; panel_inputs_event_queue: 0x0200d0e2..0x0200d138, module panel-inputs (event_queue)
.type panel_inputs_event_queue,@function
panel_inputs_event_queue:
    [--sp] = {rets, r7-r4}
    r3 = L01c26890
    r4 = b[r3+50] (u)
    r5 = r3 + 2722
    r6 = 0
    goto L0200d10c
L0200d0f6:
    r7 = b[r5+-2] (u)
    if (r7 != r0) goto L0200d108
    r7 = b[r5+-1] (u)
    if (r7 != r1) goto L0200d108
    r7 = b[r5+0] (u)
    if (r7 == r2) goto L0200d136
L0200d108:
    r5 += 3  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L0200d10c:
    ifs (r6 < r4) goto L0200d0f6
    if (r4 > 15) goto L0200d12c
    r5 = r4 * 0x3
    r5 += r3  ; @add.rr
    r5 = r5 + 2720
    b[r5+0] = r0
    b[r5+1] = r1
    b[r5+2] = r2
    r0 = r4 + 1
    b[r3+50] = r0
    {pc, r7-r4} = [sp++]
L0200d12c:
    r0 = 952
    r1 = 1
    b[r3+r0] = r1
L0200d136:
    {pc, r7-r4} = [sp++]

; panel_inputs_switch_effect: 0x0200d138..0x0200d1ec, module panel-inputs (switch_effect)
.type panel_inputs_switch_effect,@function
panel_inputs_switch_effect:
    [--sp] = {rets, r6-r4}
    r0 = r0 & 0x3
    r2 = L02035810
    r0 += r2  ; @add.rr
    r2 = 1126
    r2 = b[r0+r2] (u)
    r4 = r1
    r1 = L01c26890
    if (r2 == 7) goto L0200d190
    if (r2 != 3) goto L0200d16e
    call preset_application_mode
    if (r0 == 0) goto L0200d16e
    [r4+0] = 0x15
    call slot_commands_requested
    {pc, r6-r4} = [sp++]
L0200d16e:
    r0 = r2 + r1
    r1 = 1590
    r5 = b[r0+r1] (s)
    ifs (r5 <= -1) goto L0200d1e0
    r0 = r5
    call preset_application_effect_type  ; @call.xl
    r0 = r5  #
    [r4+0] = r0
    call preset_application_effect_enabled  ; @call.xl
    {pc, r6-r4} = [sp++]
L0200d190:
    r0 = 1591
    r6 = b[r1+r0] (s)
    r0 += -1
    r5 = b[r1+r0] (s)
    r0 = r5 & r6
    ifs (r0 <= -1) goto L0200d1e0
    r0 = r6
    ifs (r6 <= -1) {  ; @ifs.le.ri.s12
    r0 = r5
    }
    call preset_application_effect_type  ; @call.xl
    [r4+0] = r0
    ifs (r6 < 0) goto L0200d1c8
    r0 = r6
    call preset_application_effect_enabled  ; @call.xl
    r1 = r0
    r0 = 1
    if (r1 != 0) goto L0200d1de
L0200d1c8:
    ifs (r5 < 0) goto L0200d1e8
    r0 = r5
    call preset_application_effect_enabled  ; @call.xl
    r1 = r0
    r0 = 1
    if (r1 != 0) goto L0200d1de
    r0 = r1
    {pc, r6-r4} = [sp++]
L0200d1de:
    {pc, r6-r4} = [sp++]
L0200d1e0:
    [r4+0] = 0x0
    r0 = -1
    {pc, r6-r4} = [sp++]
L0200d1e8:
    r0 = 0
    {pc, r6-r4} = [sp++]

; panel_inputs_change_mark: 0x0200d1ec..0x0200d200, module panel-inputs (change_mark)
.type panel_inputs_change_mark,@function
panel_inputs_change_mark:
    r0 = L01c34468
    r0 = [r0+0]
    r1 = L01c26890
    [r1+948] = r0
    rts
