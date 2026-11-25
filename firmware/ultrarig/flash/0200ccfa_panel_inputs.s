; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 4 functions, 0x0200ccfa..0x0200cece

; panel_inputs_analog_start: 0x0200ccfa..0x0200cd14, module panel-inputs (analog_start)
.type panel_inputs_analog_start,@function
panel_inputs_analog_start:
    r2 = 1023
    r1 &= r2
    h[r0+2] = r1
    h[r0+0] = r1
    r2 = 0
    b[r0+8] = r2
    r3 = 1
    b[r0+9] = r3
    b[r0+11] = r2
    r1 = r1 >> 3
    b[r0+10] = r1
    rts

; panel_inputs_analog_filter: 0x0200cd14..0x0200cde0, module panel-inputs (analog_filter)
.type panel_inputs_analog_filter,@function
panel_inputs_analog_filter:
    [--sp] = {rets, r6-r4}
    r0 = r0 * 0x28
    r4 = L01c26890
    r4 += r0  ; @add.rr
    r0 = 10272
    r0 += r4  ; @add.rr
    if (r1 == 0) goto L0200cd32
    if (r3 == 0) goto L0200cd32
    r1 = r2
L0200cd2e:
    call panel_inputs_analog_start
    {pc, r6-r4} = [sp++]
L0200cd32:
    r3 = 10283
    r3 += r4  ; @add.rr
    if (r1 == 0) goto L0200cd94
    r1 = 0
    r1 = 1023  #
    b[r3+0] = r1
    r1 &= r2
    r2 = 10281  #
    h[r0+0] = r1
    r2 = b[r4+r2] (u)
    if (r2 == 0) goto L0200cd2e
    r2 = 10274
    r0 = r4
    r3 = h[++r0=r2] (u)
    if (r1 < 1016) goto L0200cdaa
    if (r3 >= 1016) goto L0200cdaa
L0200cd62:
    r2 = 10280
    r2 += r4  ; @add.rr
    r3 = b[r2+12] (u)
    if (r3 != 0) goto L0200cd78
    r3 = b[r2+0] (u)
    r3 += 1  ; @add.ri.u5
    r5 = r3.b0 (u)  #
    b[r2+0] = r3
    if (r5 < 2) goto L0200cd92
L0200cd78:
    r3 = 0
    b[r2+0] = r3
    r3 = 3
    b[r2+12] = r3
    r0 = 10282  #
    h[r0+0] = r1
    r2 = b[++r4=r0] (u)
    r0 = r1 >> 3
    if (r0 != r2) {
    b[r4+0] = r0
    }
L0200cd92:
    {pc, r6-r4} = [sp++]
L0200cd94:
    r0 = b[r3+0] (u)
    if (r0 != 255) {  ; @if.ne.ri.s12
    r0 += 1  ; @add.ri.u5
    b[r3+0] = r0
    }
    r0 = 10288
    r0 += r4  ; @add.rr
    [r0+0] += 1  ; @rmw.add.s12
    {pc, r6-r4} = [sp++]
L0200cdaa:
    r5 = r3 - r1
    r2 = r1 - r3
    if (r1 <= r3) {
    r2 = r5
    }
    r5 = 1
    r6 = 1
    if (r3 <= 7) {  ; @if.le.ri.s12
    r6 = 0
    }
    if (r1 >= 8) {  ; @if.ge.ri.s12
    r5 = 0
    }
    if ((r5 & r6) != 0) goto L0200cd62
    if (r2 > 6) goto L0200cd62
    r0 = 0
    r1 = 10280
    b[++r4=r1] = r0
    r0 = b[r4+12] (u)
    if (r0 == 0) goto L0200cd92
    r0 += -1
    b[r4+12] = r0
    {pc, r6-r4} = [sp++]

; panel_inputs_analog_scan: 0x0200cde0..0x0200ce8e, module panel-inputs (analog_scan)
.type panel_inputs_analog_scan,@function
panel_inputs_analog_scan:
    [--sp] = {rets, r9-r4}
    sp += -4
    r2 = 868
    r9 = L01c26890
    r2 = b[r9+r2] (u)
    r8 = r1
    r4 = r0
    if (r2 != 0) goto L0200ce24
    r0 = 10306
    r7 = r9 + r0
    r5 = 16
    r6 = 255
    goto L0200ce18
L0200ce06:
    r0 = r7 + -34
    call panel_inputs_analog_reset
    b[r7+-1] = r6
    b[r7+0] = r6
    b[r7+-4] = r6
    r5 += -1
    r7 += 40
L0200ce18:
    if (r5 != 0) goto L0200ce06
    r0 = 868
    r1 = 1
    b[r9+r0] = r1
L0200ce24:
    call panel_inputs_analog_pins
    r0 = 0
    [sp] = r0
    if (r4 == 0) goto L0200ce50
    r0 = r4
    call panel_inputs_analog_select
    r2 = 80000
    r3 = sp + 0
    r0 = 3
    r1 = 15
    call footswitch_events_adc_read
    r1 = r0  #
    r2 = [sp]
    r0 = r4
    r3 = r8
    call panel_inputs_analog_filter
L0200ce50:
    r0 = 852
    r0 = b[r9+r0] (u)
    if (r0 == 0) goto L0200ce66
    r0 = 72960
    r0 = [r0+0]
    if ((r0 & 32768) == 0) goto L0200ce82
L0200ce66:
    r2 = 80000
    r3 = sp + 0
    r0 = 8
    r1 = 2
    call footswitch_events_adc_read
    r1 = r0  #
    r2 = [sp]
    r0 = r4 + 8
    r3 = r8
    call panel_inputs_analog_filter
L0200ce82:
    if (r4 == 0) goto L0200ce8a
    r0 = 0
    call panel_inputs_analog_select
L0200ce8a:
    sp += 4
    {pc, r9-r4} = [sp++]

; panel_inputs_analog_command: 0x0200ce8e..0x0200cece, module panel-inputs (analog_command)
.type panel_inputs_analog_command,@function
panel_inputs_analog_command:
    [--sp] = {rets, r5, r4}
    r4 = r0
    if ((r4 & 0x10) != 0) {
    call footswitch_events_reload_preset
    }
    r0 = r4 & 0xF
    if (r0 != 1) goto L0200cecc
    r0 = 832
    r5 = L01c26890
    r0 = b[r5+r0] (u)
    if (r0 == 0) goto L0200cec2
    r4 = 0
    goto L0200cebe
L0200ceb6:
    r1 = 1
    r0 = r4
    call panel_inputs_analog_scan
    r4 += 1  ; @add.ri.u5
L0200cebe:
    if (r4 != 8) goto L0200ceb6
L0200cec2:
    r0 = 836
    r1 = 1
    b[r5+r0] = r1
L0200cecc:
    {pc, r5, r4} = [sp++]
