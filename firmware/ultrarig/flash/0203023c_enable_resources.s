; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; enable_resources: 3 functions, 0x0203023c..0x020303f4

; enable_resources_enable_cost: 0x0203023c..0x020302c6, module enable-resources (enable_cost)
.type enable_resources_enable_cost,@function
enable_resources_enable_cost:
    [--sp] = {rets, r6-r4}
    sp += -12
    r5 = r0
    r1 = 1
    call effect_setup_slot_cost
    r4 = r0
    r1 = sp + 8
    r0 = r5
    call effect_ownership_lookup
    ifs (r0 < 0) goto L0203026a
    r1 = r5 * 0x1E0
    r2 = L01c2c220
    r1 = r1 + r2
    r2 = b[r1+46] (u)
    if (r2 != 2) goto L02030270
L0203026a:
    r0 = r4
    sp += 12
    {pc, r6-r4} = [sp++]
L02030270:
    r3 = b[r1+4] (u)
    r6 = b[r1+0] (u)
    r1 = b[r1+6] (u)
    r2 = [sp+8]
    r1 = r2 + -1  #
    [sp+4] = r1
    r2 = r2 + 1
    [sp] = r6
    call effect_setup_neighbor_group
    if (r0 == 0) goto L0203026a
    r0 = L01c343d8
    r0 = [r0+r5<<2]
    if (r0 == 0) goto L020302aa
    r0 = L01c32db0
    r0 = [r0+124]
    if (r0 != 0) goto L020302a4
    r0 = 1875
L020302a4:
    r1 = r0 >> 4
    r0 = r0 + r1
    goto L020302ae
L020302aa:
    r0 = 1875
L020302ae:
    r1 = effect_processing_costs
    r2 = [r1+r6<<2]
    r1 = r4 - r0
    r0 = r0 + r2
    if (r4 <= r0) {
    r1 = r2
    }
    r4 = r1
    goto L0203026a

; enable_resources_release_idle: 0x020302c6..0x0203033c, module enable-resources (release_idle)
.type enable_resources_release_idle,@function
enable_resources_release_idle:
    [--sp] = {rets, r10-r4}
    r2 = L01c32db0
    r8 = r1  #
    r2 = [r2+56]
    if (r2 == 0) goto L020302e4
    r7 = L01c2c220
    r4 = r0 - r7
    r9 = 0
    r5 = 0
    r10 = 0
    goto L020302fe
L020302e4:
    r10 = 0
    goto L02030338
L020302e8:
    h[r0+0] = r9
    r0 = r6
    call effect_ownership_release
    r0 = r6
    call effect_ownership_capture
    r10 = r10 + 1
    goto L0203032e
L020302fe:
    if (r4 == r5) goto L0203032e
    r6 = r5 + r7
    r0 = b[r6+2] (u)
    if (r0 == 0) goto L0203032e
    r0 = b[r6+1] (u)
    if (r0 != 0) goto L0203032e
    r0 = b[r6+10] (u)
    if (r0 != 0) goto L0203032e
    r0 = b[r6+3] (u)
    if (r0 != 0) goto L0203032e
    r0 = b[r5+r7] (u)
    if (r0 == 7) goto L0203032e
    r0 = [r6+84]
    if (r0 == 0) goto L0203032e
    r0 = r6
    r1 = h[++r0=8] (u)
    if (r8 != 0) goto L020302e8
    if (r1 == 0) goto L020302e8
L0203032e:
    r5 = r5 + 480
    if (r5 != 7680) goto L020302fe
L02030338:
    r0 = r10
    {pc, r10-r4} = [sp++]

; enable_resources_make_resource: 0x0203033c..0x020303f4, module enable-resources (make_resource)
.type enable_resources_make_resource,@function
enable_resources_make_resource:
    [--sp] = {rets, r10-r4}
    r4 = r0
    r7 = r4 + 288  #
    r0 = b[r4+0] (u)
    if (r0 != 7) goto L02030352
    r1 = [r7+0]
    r0 = 0
    if (r1 == 0) goto L020303ba
L02030350:
    {pc, r10-r4} = [sp++]
L02030352:
    r0 = r4
    call effect_setup_demand
    r10 = r0
    r0 = 0
    if (r10 == 0) goto L02030350
    r1 = [r4+84]
    if (r1 != 0) goto L02030350
    r8 = 0
    r9 = L01c3448b
    r1 = 0
L02030370:
    if (r1 == 2) goto L02030384
    r5 = r1
    if (r1 != 1) goto L02030390
    r1 = 0
    r0 = r4
    call enable_resources_release_idle
    r5 = 1
    if (r0 != 0) goto L02030390
L02030384:
    call effect_parameter_lifecycle_resource_flush
    r1 = 1
    r0 = r4
    call enable_resources_release_idle
    r5 = 2
L02030390:
    b[r9+0] = r8
    r0 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r0 = r4
    r1 = r10
    call effect_setup_allocate
    r6 = r0
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    if (r6 == 0) goto L020303c2
    r1 = r5 + 1
    r0 = -3
    ifs (r5 < 2) goto L02030370
    {pc, r10-r4} = [sp++]
L020303ba:
    r0 = r4
    call ir_effect_lifecycle_select_source
    {pc, r10-r4} = [sp++]
L020303c2:
    r0 = b[r4+0] (u)
    if (r0 != 5) goto L020303ea
    r0 = 0
    r1 = r4 + 392  #
    [r7+0] = r0
    [r7+32] = r0
    [r1+0] = r0
    [r1+4] = r0
    r1 = r4 + 328  #
    [r1+8] = r0
    [r7+20] = r0
    r2 = 0
L020303e0:
    [r1+r2<<2] = r0
    r2 = r2 + 1
    if (r2 != 16) goto L020303e0
L020303ea:
    r0 = r4
    call effect_construction_construct
    r0 = 0
    {pc, r10-r4} = [sp++]
