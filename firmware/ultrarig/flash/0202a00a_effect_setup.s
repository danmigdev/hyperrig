; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x0202a00a..0x0202a076

; effect_setup_demand_by_type: 0x0202a00a..0x0202a076, module effect-setup (demand_by_type)
.type effect_setup_demand_by_type,@function
effect_setup_demand_by_type:
    [--sp] = rets
; HyperRig MINI, product option: the memory of the acoustic block, of the harmonizer and of the effects of HyperRig, in halfwords.
.if MINI_PRODUCT
    if (r0 > 39) goto Lhr_demand_own
    if (r0 == 24) goto Lhr_demand_harmonizer
    if (r0 != 6) goto Lhr_demand_others
    r3 = hyperrig_acoustic_memory
    r3 = [r3+0]
    goto L0202a05a
Lhr_demand_harmonizer:
    r3 = hyperrig_harmonizer_memory
    r3 = [r3+0]
    goto L0202a05a
Lhr_demand_others:
.endif
    if (r0 == 30) goto L0202a056
    r3 = 1032
    if (r0 == 39) goto L0202a05a
    r3 = r0 + -31
    if (r3 < 5) goto L0202a05e
    r3 = r0 + -11
    if (r3 < 2) goto L0202a064
    if (r0 == 5) goto L0202a06c
    if (r0 == 15) goto L0202a064
    if (r0 == 27) goto L0202a05e
    r1 = r0 | 0x4
    r3 = 0
    if (r1 != 29) goto L0202a05a
    r3 = 4096
    if (r0 != 29) goto L0202a05a
    if (r2 == 0) goto L0202a05a
    call effect_parameter_lifecycle_resource_extra_size  ; @call.xl
    r0 = r0 >> 1
    r3 = r0 + 4096
    goto L0202a05a
L0202a056:
    r3 = 10204
L0202a05a:
    r0 = r3
    pc = [sp++]
.if MINI_PRODUCT
Lhr_demand_own:
    call hyperrig_effect_memory  ; @call.xl
    pc = [sp++]
.endif
L0202a05e:
    call effect_setup_object_total
    r3 = r0
    goto L0202a05a
L0202a064:
    call effect_construction_size
    r0 = r0 << 1
    r3 = r0 + 8
    goto L0202a05a
L0202a06c:
    r0 = r1
    call effect_parameter_support_size_extra
    r3 = r0
    goto L0202a05a
