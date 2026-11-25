; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tap_tempo: 1 function, 0x0200a4b2..0x0200a5b6

; tap_tempo_tap_tempo: 0x0200a4b2..0x0200a5b6, module tap-tempo (tap_tempo)
.type tap_tempo_tap_tempo,@function
tap_tempo_tap_tempo:
    [--sp] = {rets, r6-r4}
    r2 = 720
    r4 = L01c26890
    r5 = b[r4+r2] (u)
    r2 = r1
    r3 = r0
    r1 = 0
    if (r5 == 0) goto L0200a4ea
    r0 = [r4+724]
    r0 = r2 - r0
    if (r0 > 2100) goto L0200a4ea
    r0 = [r4+728]
    r5 = r3 - r0
    call preset_application_rate
    r1 = 10
    r0 = r0 / r1 (u)
    r1 = r5 / r0 (u)
L0200a4ea:
    r0 = r4 + 720
    d[r0+4] = r3_r2
    r2 = 1
    b[r0+0] = r2
    if (r1 < 1500) goto L0200a5a4
    r0 = r1 + -1
    r0 = r0 >> 5
    if (r0 >= 625) goto L0200a5a4
    r0 = 376
    r2 = [r4+r0<<2]
    r0 = 0
    r3 = 0
    if (r2 == 0) goto L0200a54c
    r3 = r2 + -1
    r5 = 3
    r5 = r3 / r5 (s)
    r5 = r5 * 0x3
    r3 = r3 - r5
    r5 = r4 + 1704
    r3 = [r5+r3<<2]
    r5 = r3 * 0x5
    r6 = r1 << 2
    if (r6 > r5) goto L0200a542
    r5 = r3 << 2
    r6 = r1 * 0x5
    r3 = r2
    if (r6 >= r5) goto L0200a54c
L0200a542:
    r2 = 376
    r3 = 0
    [r4+r2<<2] = r3
L0200a54c:
    r2 = 3
    r2 = r3 / r2 (s)
    r2 = r2 * 0x3
    r5 = r3 - r2
    r2 = r4 + 1704
    [r2+r5<<2] = r1
    r1 = 3
    ifs (r3 <= 2) {  ; @ifs.le.ri.s12
    r1 = 0
    }
    r1 += r5  ; @add.rr
    r1 += 1  ; @add.ri.u5
    r3 = 376
    [r4+r3<<2] = r1
    ifs (r1 >= 3) {  ; @ifs.ge.ri.s12
    r1 = 3
    }
    r3 = 0
    goto L0200a586
L0200a57e:
    r4 = [r2+r3<<2]
    r0 += r4  ; @add.rr
    r3 += 1  ; @add.ri.u5
L0200a586:
    if (r3 < r1) goto L0200a57e
    r2 = 6000000
    r1 *= r2
    r2 = r0 >> 1
    r1 += r2  ; @add.rr
    if (r0 > r1) goto L0200a5ae
    r0 = r1 / r0 (u)
    call tempo_slot_services_tempo_command
    {pc, r6-r4} = [sp++]
L0200a5a4:
    r0 = 376
    r1 = 0
    [r4+r0<<2] = r1
L0200a5ae:
    call preset_application_services_tempo  ; @call.xl
    {pc, r6-r4} = [sp++]
