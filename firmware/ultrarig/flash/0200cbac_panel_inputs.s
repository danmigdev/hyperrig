; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 4 functions, 0x0200cbac..0x0200cca0

; panel_inputs_switch_status: 0x0200cbac..0x0200cbfc, module panel-inputs (switch_status)
.type panel_inputs_switch_status,@function
panel_inputs_switch_status:
    [--sp] = {rets, r8-r4}
    r8 = L01c26890
    r7 = r8
    r6 = b[++r7=75] (u)
    r3_r2 = r1_r0
    r1 = 0
    r5 = 1
    r4 = 1
    if (r6 == 1) {  ; @if.eq.ri.s12
    r4 = 0
    }
    r0 = b[r7+2] (u)
    b[r7+0] = r4
    b[r7+2] = r1
    if (r0 != 0) goto L0200cbd2
    r5 = r0
L0200cbd2:
    if (r6 != 1) {  ; @if.ne.ri.s12
    r6 = 0
    }
    r6 |= r5
    ifs (r3 < 0) goto L0200cbe6
    r0 = r3
    call footswitch_events_bank_of
    b[r8+76] = r0
L0200cbe6:
    r0 = 8
    b[r2+0] = r0
    r0 = 16
    if (r6 != 0) goto L0200cbf0
    r0 = r6
L0200cbf0:
    ifs (r3 <= -1) {  ; @ifs.le.ri.s12
    r0 = 0
    }
    r0 |= r4
    b[r2+1] = r0
    {pc, r8-r4} = [sp++]

; panel_inputs_analog_reset: 0x0200cbfc..0x0200cc1a, module panel-inputs (analog_reset)
.type panel_inputs_analog_reset,@function
panel_inputs_analog_reset:
    r1 = 0
    h[r0+8] = r1
    r2 = 0
    r3 = 0
    d[r0+0] = r3_r2
    r2 = 127
    b[r0+10] = r2
    b[r0+11] = r1
    b[r0+12] = r1
    b[r0+13] = r1
    [r0+16] = r1
    b[r0+20] = r1
    rts

; panel_inputs_analog_pins: 0x0200cc1a..0x0200cc40, module panel-inputs (analog_pins)
.type panel_inputs_analog_pins,@function
panel_inputs_analog_pins:
    r0 = L01c246e8
    r1 = b[r0+0] (u)
    if (r1 != 0) goto L0200cc3e
    r1 = 327816
    [r1+8] &= 0xFFFFFDFF
    [r1+12] &= 0xFFFFFDFF
    [r1+4] &= 0xFFFFFDFF
    [r1+0] |= 0x200
    r1 = 1
    b[r0+0] = r1
L0200cc3e:
    rts

; panel_inputs_analog_select: 0x0200cc40..0x0200cca0, module panel-inputs (analog_select)
.type panel_inputs_analog_select,@function
panel_inputs_analog_select:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r3 = [r1+r0<<2]
    r4 = r3 + 1
    [r1+r0<<2] = r4
    r0 = L01c1fa20
    if (r3 != 0) goto L0200cc70
    csync
L0200cc68:
    testset b[r0]
    ifeq goto L0200cc68
    csync
L0200cc70:
    r3 = 327808
    r4 = [r3+0]
    r2 = r2 << 6
    r4 = r4 & 0xFFFFFE3F
    r2 |= r4
    [r3+0] = r2
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L0200cc98
    csync
    r1 = 0
    b[r0+0] = r1
L0200cc98:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]
