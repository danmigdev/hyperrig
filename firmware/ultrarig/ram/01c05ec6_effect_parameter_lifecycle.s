; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_lifecycle: 1 function, 0x01c05ec6..0x01c05ed6

; effect_parameter_lifecycle_resource_mode_callback: 0x01c05ec6..0x01c05ed6, module effect-parameter-lifecycle (resource_mode_callback), effect-parameter-resources (mode_callback), effect-resource-ownership (resource_mode_callback)
.type effect_parameter_lifecycle_resource_mode_callback,@function
effect_parameter_lifecycle_resource_mode_callback:
    [--sp] = rets
    r1 = L01c34458
    r1 = [r1+0]
    if (r1 == 0) goto L01c05ed4
    call r1
L01c05ed4:
    pc = [sp++]
