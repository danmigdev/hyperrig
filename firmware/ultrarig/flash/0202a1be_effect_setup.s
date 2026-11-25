; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x0202a1be..0x0202a226

; effect_setup_partition_sizes: 0x0202a1be..0x0202a226, module effect-setup (partition_sizes)
.type effect_setup_partition_sizes,@function
effect_setup_partition_sizes:
    [--sp] = {rets, r8-r4}
    r5_r4 = r3_r2
    r6 = r0
    r3 = 0
    r0 = r6 + -27  #
    [r5+0] = r3
    if (r0 > 8) goto L0202a1da
    r2 = 497
    r0 = r2 & (1 << r0)
    if (r0 != 0) goto L0202a1f2
L0202a1da:
    if (r6 != 29) goto L0202a1ee
    if (r1 == 0) goto L0202a1ee
    [r4+0] = 0x2000
    call effect_parameter_lifecycle_resource_extra_size  ; @call.xl
    [r4+4] = r0
    r3 = 2
L0202a1ee:
    r0 = r3
    {pc, r8-r4} = [sp++]
L0202a1f2:
    r0 = r6
    call effect_setup_object_count
    r8 = r0
    ifs (r0 < 1) goto L0202a212
    r7 = 0
L0202a200:
    r1_r0 = r7_r6
    call effect_setup_segment_bytes
    [r4+r7<<2] = r0
    r7 = r7 + 1
    if (r8 != r7) goto L0202a200
    r3 = r8
L0202a212:
    r0 = r6
    call effect_setup_object_extra
    if (r0 == 0) goto L0202a220
    [r4+r3<<2] = r0
    r3 = r3 + 1
L0202a220:
    [r5+0] = 0x8
    goto L0202a1ee
