; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_measurement: 3 functions, 0x02028b6c..0x02028bf6

; audio_measurement_control_value: 0x02028b6c..0x02028b80, module audio-measurement (control_value)
.type audio_measurement_control_value,@function
audio_measurement_control_value:
    r1 = r0
    r0 = 0
    if (r1 <= 5) {
    r0 = L01c32e8a
    r0 = h[r0+r1<<1] (s)
    }
    rts

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; audio_measurement_controls_zero: 0x02028b80..0x02028b9a, module audio-measurement (controls_zero)
.type audio_measurement_controls_zero,@function
audio_measurement_controls_zero:
    r0 = 0
    r1 = L01c32e8a
    r2 = 0
L02028b8a:
    r3 = h[r1+r2<<1] (u)
    if (r3 != 0) goto L02028b98
    r2 = r2 + 1
    ifs (r2 <= 5) goto L02028b8a
    r0 = 1
L02028b98:
    rts

; audio_measurement_set_level: 0x02028b9a..0x02028bf6, module audio-measurement (set_level)
.type audio_measurement_set_level,@function
audio_measurement_set_level:
    [--sp] = {rets, r8-r4}
    r3 = r0
    ifs (r3 < 0) goto L02028baa
    ifs (r3 >= 100) {
    r3 = 100
    }
    goto L02028bac
L02028baa:
    r3 = 0
L02028bac:
    r8 = L01c1f7f0
    r0 = b[r8+0] (u)
    r1 = r3.b0 (u)
    if (r1 == r0) goto L02028bf0
    r6 = 0
    r4 = L01c2c220
    r7 = L01c343d8
    r5 = 0
L02028bcc:
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L02028be6
    r0 = b[r4+0] (u)
    if (r0 == 25) goto L02028be2
    r1 = 0
    r0 = r4
    call dsp_stage_capability  ; @call.xl
    if (r0 == 0) goto L02028be6
L02028be2:
    [r7+r5<<2] = r6
L02028be6:
    r5 = r5 + 1
    r4 = r4 + 480
    if (r5 != 16) goto L02028bcc
L02028bf0:
    b[r8+0] = r3
    {pc, r8-r4} = [sp++]
.endif
