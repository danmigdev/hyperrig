; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tempo_slot_services: 1 function, 0x0202fbd6..0x0202fcd4

; tempo_slot_services_set_tempo: 0x0202fbd6..0x0202fcd4, module tempo-slot-services (set_tempo)
.type tempo_slot_services_set_tempo,@function
tempo_slot_services_set_tempo:
    [--sp] = {rets, r9-r4}
    sp += -64
    r1 = 400
    ifs (r0 >= 400) {
    r1 = 3000
    r1 = smin(r0, r1)
    }
    r8 = L01c1f7f0
    [r8+12] = r1
    r0 = 5
    r1 = 0
    r7 = 0
    call preset_application_metadata
    r9 = r0
    r5 = L01c2c220
    r4 = -1
    r6 = r5
L0202fc0a:
    r0 = b[r6+2] (u)
    r1 = sp + 0
    [r1+r7<<2] = r4
    if (r0 == 0) goto L0202fc1a
    r0 = b[r6+0] (u)
    if (r0 == 5) goto L0202fc26
L0202fc1a:
    r7 = r7 + 1
    r6 = r6 + 480
    ifs (r7 < 16) goto L0202fc0a
    goto L0202fc6c
L0202fc26:
    r2 = h[r6+78] (s)
    r0 = r2
    call effect_parameter_support_tempo_selector
    if (r0 == 0) goto L0202fc1a
    r0 = r2
    call effect_parameter_support_tempo_global
    r2 = r0
    if (r9 != 0) {
    r0 = h[r9+2] (s)
    r1 = h[r9+0] (s)
    r0 = smin(r2, r0)
    r2 = smax(r0, r1)
    }
    r0 = [r6+84]
    if (r0 != 0) goto L0202fc5c
L0202fc54:
    r0 = sp + 0
    [r0+r7<<2] = r2
    goto L0202fc1a
L0202fc5c:
    r0 = r2
    call effect_parameter_support_size_extra
    r1 = [r6+88]
    if (r0 <= r1) goto L0202fc54
    goto L0202fc8c
L0202fc6c:
    r4 = 0
L0202fc6e:
    r0 = sp + 0
    r2 = [r0+r4<<2]
    ifs (r2 >= 0) goto L0202fc80
L0202fc78:
    r4 = r4 + 1
    ifs (r4 < 16) goto L0202fc6e
    goto L0202fc90
L0202fc80:
    r1 = 0
    r3 = 1
    r0 = r4
    call effect_parameter_lifecycle_parameter_fast_wrapper
    if (r0 != -6) goto L0202fc78
L0202fc8c:
    r0 = -6
    goto L0202fcd0
L0202fc90:
    r4 = 0
    r6 = L01c1f7e0
L0202fc98:
    r0 = b[r5+2] (u)
    if (r0 != 0) goto L0202fca8
L0202fc9c:
    r4 = r4 + 1
    r5 = r5 + 480
    ifs (r4 < 16) goto L0202fc98
    goto L0202fccc
L0202fca8:
    r2 = r5
    r0 = b[r2++=70] (u)
    call effect_construction_tempo_parameter
    r1 = r0
    ifs (r1 < 0) goto L0202fc9c
    r2 = h[r2+r1<<1] (s)
    if (r2 == 0) goto L0202fc9c
    r0 = r4  #
    r3 = b[r6+0] (u)
    call effect_parameter_lifecycle_parameter_fast_wrapper
    if (r0 != -6) goto L0202fc9c
    goto L0202fc8c
L0202fccc:
    r0 = [r8+12]
L0202fcd0:
    sp += 64
    {pc, r9-r4} = [sp++]
