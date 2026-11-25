; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tempo_slot_services: 1 function, 0x02030068..0x02030110

; tempo_slot_services_tempo_fits: 0x02030068..0x02030110, module tempo-slot-services (tempo_fits)
.type tempo_slot_services_tempo_fits,@function
tempo_slot_services_tempo_fits:
    [--sp] = {rets, r10-r4}
    r10 = r1
    r8 = 400
    ifs (r0 >= 400) {
    r1 = 3000
    r8 = smin(r0, r1)
    }
    r0 = 5
    r1 = 0
    r5 = 0
    call preset_application_metadata
    r9 = r0
    r4 = L01c2c220
    r6 = 0
L02030090:
    r0 = b[r4+2] (u)
    if (r0 != 0) goto L020300a0
L02030094:
    r5 = r5 + 1
    r4 = r4 + 480
    ifs (r5 < 16) goto L02030090
    goto L02030104
L020300a0:
    r7 = b[r4+0] (u)
    if (r7 != 5) goto L020300d8
    r2 = h[r4+78] (s)
    r0 = r2
    call effect_parameter_support_tempo_selector
    if (r0 == 0) goto L020300d8
    r0 = r2
    r1 = r8
    call effect_parameter_support_tempo
    if (r9 != 0) {
    r1 = h[r9+2] (s)
    r2 = h[r9+0] (s)
    r0 = smin(r0, r1)
    r0 = smax(r0, r2)
    }
    r1 = [r4+84]
    if (r1 != 0) goto L020300f2
L020300d4:
    r6 = r6 | (1 << r5)
L020300d8:
    r0 = r7
    call effect_construction_tempo_parameter
    ifs (r0 < 0) goto L02030094
    r1 = r4 + 70
    r0 = h[r1+r0<<1] (u)
    if (r0 == 0) goto L02030094
    r6 = r6 | (1 << r5)
    goto L02030094
L020300f2:
    call effect_parameter_support_size_extra
    r2 = [r4+88]
    r1 = r0
    r0 = 0
    if (r1 > r2) goto L0203010e
    goto L020300d4
L02030104:
    r0 = 1
    if (r10 != 0) {
    [r10+0] = r6
    }
L0203010e:
    {pc, r10-r4} = [sp++]
