; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_lifecycle: 1 function, 0x0202df04..0x0202df38

; effect_parameter_lifecycle_resource_allocate: 0x0202df04..0x0202df38, module effect-parameter-lifecycle (resource_allocate), effect-parameter-resources (allocate), effect-resource-ownership (resource_allocate)
.type effect_parameter_lifecycle_resource_allocate,@function
effect_parameter_lifecycle_resource_allocate:
    [--sp] = {rets, r5, r4}
    r1 = L01c32db0
    r5 = r0  #
    r1 = [r1+52]
    r4 = 0
    if (r1 == 0) goto L0202df34
    r0 = r5 + 16
    call r1
    if (r0 == 0) goto L0202df34
    r1 = r0 + r5
    r2 = 0
    r3 = 3235798765
L0202df24:
    r4 = r2 ^ r3
    [r1+r2<<2] = r4
    r2 = r2 + 1
    if (r2 != 4) goto L0202df24
    r4 = r0
L0202df34:
    r0 = r4
    {pc, r5, r4} = [sp++]
