; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tuner_and_control_records: 7 functions, 0x02014d44..0x02015076

; tuner_and_control_records_mode_bits: 0x02014d44..0x02014d58, module tuner-and-control-records (mode_bits)
.type tuner_and_control_records_mode_bits,@function
tuner_and_control_records_mode_bits:
    r0 = 5468
    r1 = L01c26890
    r0 = b[r1+r0] (u)
    r0 = r0 & 0xFFFFFF0F
    rts

; tuner_and_control_records_event_reset: 0x02014d58..0x02014d8a, module tuner-and-control-records (event_reset)
.type tuner_and_control_records_event_reset,@function
tuner_and_control_records_event_reset:
    [--sp] = {rets, r5, r4}
    r2 = L01c1f180
    r3 = r2 + 316
    r4 = b[r3+8] (u)
    r1 = 0
    h[r3+4] = r1
    [r3+0] = r1
    r5 = 4
    b[r3+6] = r5
    b[r3+7] = r1
    b[r3+8] = r1
    if (r4 == 0) goto L02014d86
    r1 = 325
    r3 = 3
    b[r2+r1] = r3
    [r2+312] = r0
    r1 = 1
L02014d86:
    r0 = r1
    {pc, r5, r4} = [sp++]

; tuner_and_control_records_event_notify: 0x02014d8a..0x02014dbc, module tuner-and-control-records (event_notify)
.type tuner_and_control_records_event_notify,@function
tuner_and_control_records_event_notify:
    [--sp] = rets
    if (r0 == 0) goto L02014dba
    r0 = L01c246e4
    r1 = [r0+0]
    if (r1 > 39) goto L02014dba
    r1 += 1  ; @add.ri.u5
    r2 = L01c1f2b8
    r3 = b[r2+13] (u)
    [r0+0] = r1
    r0 = b[r2+12] (u)
    r1 = b[r2+11] (u)
    r3 = r3 << 4
    r0 |= r3  #
    r2 = [r2+0]
    r1 = r1 << 8
    r1 |= r0
    r0 = 33
    call storage_coordination_notify
L02014dba:
    pc = [sp++]

; tuner_and_control_records_bus_read: 0x02014dbc..0x02014dcc, module tuner-and-control-records (bus_read)
.type tuner_and_control_records_bus_read,@function
tuner_and_control_records_bus_read:
    [--sp] = rets
    r3 = r2
    r2 = 80000
    call footswitch_events_adc_read
    pc = [sp++]

; tuner_and_control_records_range_kind: 0x02014dcc..0x02014df4, module tuner-and-control-records (range_kind)
.type tuner_and_control_records_range_kind,@function
tuner_and_control_records_range_kind:
    if (r1 == 0) goto L02014de2
    r1 = 1
    r2 = 1
    if (r0 == 30) {  ; @if.eq.ri.s12
    r2 = 0
    }
    if (r0 == 6) {  ; @if.eq.ri.s12
    r1 = 0
    }
    r1 &= r2
    goto L02014df0
L02014de2:
    r1 = 2
    if (r0 == 6) goto L02014df0
    r1 = 3
    if (r0 != 30) {  ; @if.ne.ri.s12
    r1 = 4
    }
L02014df0:
    r0 = r1
    rts

; tuner_and_control_records_control_record: 0x02014df4..0x02014ff6, module tuner-and-control-records (control_record)
.type tuner_and_control_records_control_record,@function
tuner_and_control_records_control_record:
    [--sp] = {rets, r9-r4}
    r4 = r1
    r1 = r0 + -1
    r8 = 0
    r2 = L02035810
    r7 = 0
    if (r1 <= 13) {  ; @if.le.ri.s12
    r0 += r2  ; @add.rr
    r1 = 4931
    r7 = b[r0+r1] (u)
    }
    r1 = r4
    r0 = r7 + -1
    rep 5 {
    b[r1++=1] = r8
    }
    if (r0 > 17) goto L02014ff2
    r1 = L01c26890
    tbb [r0]
control_record_cases:
    .byte (L02014e70 - control_record_cases) / 2, (L02014e70 - control_record_cases) / 2, (L02014e8e - control_record_cases) / 2, (L02014e8e - control_record_cases) / 2, (L02014ed6 - control_record_cases) / 2, (L02014ed6 - control_record_cases) / 2, (L02014eee - control_record_cases) / 2, (L02014eee - control_record_cases) / 2
    .byte (L02014f30 - control_record_cases) / 2, (L02014f46 - control_record_cases) / 2, (L02014f72 - control_record_cases) / 2, (L02014e3e - control_record_cases) / 2, (L02014e3e - control_record_cases) / 2, (L02014e3e - control_record_cases) / 2, (L02014e3e - control_record_cases) / 2, (L02014e3e - control_record_cases) / 2
    .byte (L02014f08 - control_record_cases) / 2, (L02014f08 - control_record_cases) / 2
L02014e3e:
    call preset_application_mode
    if (r0 == 0) goto L02014f1c
    r0 = r7 + r2
    r1 = 2970
    r0 = b[r0+r1] (u)
    r1 = 2
    b[r4+0] = r1
    b[r4+2] = r0
    call status_helpers_flags_set
    r0 = -240  #
    b[r4+4] = r0
    if (r7 != 12) {  ; @if.ne.ri.s12
    r0 += 120
    }
    r8 = 1  #
    h[r4+6] = r0
    r0 = 120
    h[r4+8] = r0
    goto L02014ff2
L02014e70:
    r0 = 1590
    r6 = b[r1+r0] (s)
    ifs (r6 < 0) goto L02014fb8
    r0 = r6
    call preset_application_effect_type  ; @call.xl
    if (r7 != 1) {  ; @if.ne.ri.s12
    r7 = 0
    }
    r1 = r7
    goto L02014fb0
L02014e8e:
    r0 = 1592
    r6 = b[r1+r0] (s)
    ifs (r6 < 0) goto L02014f88
    r0 = r6
    call preset_application_effect_type  ; @call.xl
    r1 = r0 + -11
    r5 = 2
    r0 = 1
    if (r1 >= 5) {  ; @if.ge.ri.s12
    r0 = 2
    }
    r9 = -1
    if (r1 <= 4) {  ; @if.le.ri.s12
    r9 = 0
    }
    if (r7 != 3) {  ; @if.ne.ri.s12
    r9 = r0
    }
    if (r7 != 3) {  ; @if.ne.ri.s12
    r5 = 5
    }
    r0 = r6
    call preset_application_effect_type  ; @call.xl
    if (r0 != 39) {  ; @if.ne.ri.s12
    r5 = r9
    }
    goto L02014f8a
L02014ed6:
    r0 = 1
    if (r7 != 6) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r2 = 1591
    r6 = b[r1+r2] (s)
    r5 = r0 << 1
    if (r7 == 5) goto L02014f8e
    goto L02014fba
L02014eee:
    r0 = 1591
    r6 = b[r1+r0] (s)
    ifs (r6 < 0) goto L02014f94
    r5 = 2
    if (r7 == 7) {  ; @if.eq.ri.s12
    r0 = 1
    b[r4+3] = r0
    r5 = 0
    }
    goto L02014fba
L02014f08:
    r0 = 1596
    r6 = b[r1+r0] (s)
    r5 = 1
    b[r4+3] = r5
    if (r7 != 17) {  ; @if.ne.ri.s12
    r5 = 2
    }
    goto L02014fba
L02014f1c:
    r0 = 1593
    r6 = b[r1+r0] (s)
    r0 = r7 + r2
    r1 = 2987
    r5 = b[r0+r1] (u)
    goto L02014fba
L02014f30:
    r0 = 1594
    r0 = b[r1+r0] (u)
    r1 = r0.b0 (s)
    ifs (r1 < 0) goto L02014ff2
    r2 = 5
    b[r4+0] = r2
    b[r4+1] = r1
    goto L02014f6a
L02014f46:
    r0 = 1595
    r0 = b[r1+r0] (u)
    r1 = r0.b0 (s)
    ifs (r1 < 0) goto L02014ff2
    r2 = 3
    b[r4+0] = r2
    b[r4+1] = r1
    r1 = 65456
    h[r4+6] = r1
    r1 += 60
    h[r4+8] = r1
    r1 = 2
    b[r4+3] = r1
L02014f6a:
    call preset_application_effect_enabled  ; @call.xl
    goto L02014f80
L02014f72:
    call preset_application_mode
    if (r0 == 0) goto L02014ff2
    r0 = 4
    b[r4+0] = r0
    call status_helpers_flags_set
L02014f80:
    r8 = 1  #
    b[r4+4] = r0
    goto L02014ff2
L02014f88:
    r5 = -1
L02014f8a:
    if (r7 != 3) goto L02014fba
L02014f8e:
    r0 = 1
    b[r4+3] = r0
    goto L02014fba
L02014f94:
    r0 += -1
    r6 = b[r1+r0] (s)
    ifs (r6 < 0) goto L02014fb8
    r5 = 1
    if (r7 != 7) {  ; @if.ne.ri.s12
    r5 = 0
    }
    r0 = r6
    call preset_application_effect_type  ; @call.xl
    r1 = r5
L02014fb0:
    call tuner_and_control_records_range_kind
    r5 = r0
    goto L02014fba
L02014fb8:
    r5 = -1
L02014fba:
    r0 = r6 | r5
    ifs (r0 < 0) goto L02014ff2
    r0 = r6
    call preset_application_effect_type  ; @call.xl
    r1 = r5
    call preset_application_metadata  ; @call.xl
    if (r0 == 0) goto L02014ff2
    r8 = 1
    b[r4+0] = r8
    b[r4+1] = r6
    b[r4+2] = r5
    r1 = h[r0+0] (u)
    h[r4+6] = r1
    r0 = h[r0+2] (u)
    r0 = r6  #
    h[r4+8] = r0
    call preset_application_effect_enabled  ; @call.xl
    b[r4+4] = r0
L02014ff2:
    r0 = r8
    {pc, r9-r4} = [sp++]

; tuner_and_control_records_record_value: 0x02014ff6..0x02015076, module tuner-and-control-records (record_value)
.type tuner_and_control_records_record_value,@function
tuner_and_control_records_record_value:
    [--sp] = {rets, r4}
    r2 = r0
    r0 = b[r2+0] (u)
    r1 = r0 + -1
    r0 = 0
    if (r1 > 4) goto L0201506e
    r4 = L01c1f180
    tbb [r1]
record_value_cases:
    .byte (L02015014 - record_value_cases) / 2, (L02015020 - record_value_cases) / 2, (L0201502a - record_value_cases) / 2, (L0201503a - record_value_cases) / 2, (L0201504a - record_value_cases) / 2
    .byte 0x00  ; alignment
L02015014:
    r1 = b[r2+2] (u)
    r0 = b[r2+1] (u)
    call preset_application_parameter  ; @call.xl
    {pc, r4} = [sp++]
L02015020:
    r0 = b[r2+2] (u)
    call audio_measurement_control_value  ; @call.xl
    {pc, r4} = [sp++]
L0201502a:
    r0 = b[r2+4] (u)
    if (r0 == 0) goto L02015070
    r0 = b[r2+1] (u)
    r1 = 0
    call preset_application_parameter  ; @call.xl
    {pc, r4} = [sp++]
L0201503a:
    r1 = b[r4+9] (u)
    r0 = -1
    if (r1 != 255) {  ; @if.ne.ri.s12
    r0 = r1
    }
    if (r0 >= 9) goto L0201506c
    {pc, r4} = [sp++]
L0201504a:
    r1 = b[r2+4] (u)
    if (r1 == 0) goto L0201506e
    r0 = b[r2+1] (u)
    r1 = 2
    call preset_application_parameter  ; @call.xl
    ifs (r0 > 0) goto L0201506e
    r0 = b[r4+10] (u)
    r1 = -1
    if (r0 != 255) {  ; @if.ne.ri.s12
    r1 = r0
    }
    r0 = r1 + 1
    ifs (r1 > -1) goto L0201506e
L0201506c:
    r0 = -1
L0201506e:
    {pc, r4} = [sp++]
L02015070:
    r0 = -32768
    {pc, r4} = [sp++]
