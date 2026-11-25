; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tempo_slot_services: 1 function, 0x0203076c..0x020307ea

; tempo_slot_services_retire_slot: 0x0203076c..0x020307ea, module tempo-slot-services (retire_slot)
.type tempo_slot_services_retire_slot,@function
tempo_slot_services_retire_slot:
    [--sp] = {rets, r8-r4}
    r5 = r0
    r4 = 0
    if (r5 > 15) goto L02030788
    r7 = r5 * 0x1E0
    r8 = L01c2c220
    r6 = r7 + r8
    r0 = b[r6+2] (u)
    if (r0 != 0) goto L0203078c
L02030788:
    r0 = r4
    {pc, r8-r4} = [sp++]
L0203078c:
    r0 = r5
    call effect_ownership_detach
    r0 = L01c1f7e4
    r0 = [r0+0]
    if (r0 == 0) goto L020307e2
    r0 = b[r7+r8] (u)
    call effect_enable_tail_type  ; @call.xl
    if (r0 == 0) goto L020307e2
    r1 = r6
    r2 = b[++r1=1] (u)
    r0 = L01c32db0
    if (r2 == 0) goto L020307c4
    r2 = b[r0+8] (u)
    if (r2 > 3) goto L020307e2
    r3 = 1500
    h[r6+8] = r3
    goto L020307ce
L020307c4:
    r2 = h[r6+8] (u)
    if (r2 == 0) goto L020307e2
    r2 = b[r0+8] (u)
    if (r2 >= 4) goto L020307e2
L020307ce:
    r3 = 0
    b[r1+0] = r3
    r4 = 1
    b[r6+3] = r4
    r1 = r2 + 1
    r0 = r0 + r2  #
    b[r0+8] = r1
    b[r0+88] = r5
    goto L02030788
L020307e2:
    r0 = r5
    call effect_ownership_remove
    goto L02030788
