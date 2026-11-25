; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 2 functions, 0x020306ee..0x0203076c

; preset_application_services_detach_live: 0x020306ee..0x0203071a, module preset-application-services (detach_live)
.type preset_application_services_detach_live,@function
preset_application_services_detach_live:
    [--sp] = rets
    r2 = r0
    call biquad_coefficients_counter  ; @call.xl
    r0 = -1
    if (r2 > 15) goto L0203070e
    r1 = r2 * 0x1E0
    r3 = L01c2c220
    r1 = r1 + r3
    r1 = b[r1+2] (u)
    if (r1 != 0) goto L02030710
L0203070e:
    pc = [sp++]
L02030710:
    r0 = r2
    call effect_ownership_detach
    r0 = 0
    pc = [sp++]

; preset_application_services_move: 0x0203071a..0x0203076c, module preset-application-services (move)
.type preset_application_services_move,@function
preset_application_services_move:
    [--sp] = {rets, r8-r4}
    r8 = r2
    r6 = r1
    r5 = r0
    call biquad_coefficients_counter  ; @call.xl
    r7 = -1
    if (r5 > 15) goto L02030752
    if (r6 > 1) goto L02030752
    r0 = r5 * 0x1E0
    r1 = L01c2c220
    r4 = r0 + r1
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L02030752
    r0 = L01c32db0
    r0 = r0 + r6
    r0 = b[r0+14] (u)
    r7 = -2
    if (r0 <= 9) goto L02030756
L02030752:
    r0 = r7
    {pc, r8-r4} = [sp++]
L02030756:
    r0 = r5
    call effect_ownership_detach
    r7 = 0
    r0 = r6  #
    b[r4+4] = r7
    r1 = r8
    r2 = r5
    call effect_setup_route_insert
    goto L02030752
