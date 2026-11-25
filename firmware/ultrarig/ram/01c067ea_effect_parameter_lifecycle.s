; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_lifecycle: 6 functions, 0x01c067ea..0x01c06926

; effect_parameter_lifecycle_resource_sum3: 0x01c067ea..0x01c06808, module effect-parameter-lifecycle (resource_sum3), effect-parameter-resources (sum3), effect-resource-ownership (resource_sum3)
.type effect_parameter_lifecycle_resource_sum3,@function
effect_parameter_lifecycle_resource_sum3:
    r1 = 328
    r1 = b[r0+r1] (u)
    r2 = 372
    r2 = b[r0+r2] (u)
    r3 = 416
    r0 = b[r0+r3] (u)
    r1 = r1 + r2
    r0 = r0 + r1
    rts

; effect_parameter_lifecycle_resource_fingerprint36: 0x01c06808..0x01c06846, module effect-parameter-lifecycle (resource_fingerprint36), effect-parameter-resources (fingerprint36), effect-resource-ownership (resource_fingerprint36)
.type effect_parameter_lifecycle_resource_fingerprint36,@function
effect_parameter_lifecycle_resource_fingerprint36:
    [--sp] = {rets, r4}
    r2 = [r0+472]
    r1 = r2 & 0x1
    r3 = uextra(r2, p:1, l:1)
    r1 = r1 + r3
    r3 = uextra(r2, p:2, l:1)
    r1 = r1 + r3
    r3 = uextra(r2, p:3, l:1)
    r4 = uextra(r2, p:4, l:1)
    r3 = r3 + r4
    r4 = [r0+464]
    r0 = uextra(r2, p:5, l:1)
    r0 = r0 + r3
    r0 = r0 + r1
    r2 = 1
    if (r4 == 65536) {
    r2 = 0
    }
    r2 = r2 << 6
    r2 <= insert(r1, p:3, l:3)
    r0 |= r2
    {pc, r4} = [sp++]

; effect_parameter_lifecycle_resource_fingerprint37: 0x01c06846..0x01c0688c, module effect-parameter-lifecycle (resource_fingerprint37), effect-parameter-resources (fingerprint37), effect-resource-ownership (resource_fingerprint37)
.type effect_parameter_lifecycle_resource_fingerprint37,@function
effect_parameter_lifecycle_resource_fingerprint37:
    [--sp] = {rets, r6-r4}
    r0 = r0 + 464
    r3 = [r0+8]
    r2 = uextra(r3, p:2, l:1)  #
    r1 = [r0+12]
    if (r1 == 0) goto L01c06858
    r1 = r2
L01c06858:
    r2 = r3 & 0x1
    r4 = uextra(r3, p:1, l:1)
    r4 = r4 + r2
    r2 = 0
    if (r3 == 0) goto L01c06876
L01c06866:
    r5 = r3
    r6 = r5 + -1
    r3 = r6 & r5
    r2 = r2 + 1
    if ((r6 & r5) != 0) goto L01c06866
L01c06876:
    r0 = r4 + r1  #
    r3 = [r0+0]
    r1 = 1
    if (r3 == 65536) {
    r1 = 0
    }
    r1 = r1 << 6
    r0 = r0 << 3
    r0 |= r2
    r0 |= r1
    {pc, r6-r4} = [sp++]

; effect_parameter_lifecycle_resource_sum4: 0x01c0688c..0x01c068b6, module effect-parameter-lifecycle (resource_sum4), effect-parameter-resources (sum4), effect-resource-ownership (resource_sum4)
.type effect_parameter_lifecycle_resource_sum4,@function
effect_parameter_lifecycle_resource_sum4:
    [--sp] = {rets, r4}
    r1 = 328
    r1 = b[r0+r1] (u)
    r2 = 372
    r2 = b[r0+r2] (u)
    r3 = 416
    r3 = b[r0+r3] (u)
    r4 = 460
    r0 = b[r0+r4] (u)
    r1 = r1 + r2
    r1 = r1 + r3
    r0 = r0 + r1
    {pc, r4} = [sp++]

; effect_parameter_lifecycle_resource_delay_state: 0x01c068b6..0x01c068e0, module effect-parameter-lifecycle (resource_delay_state), effect-parameter-resources (delay_state), effect-resource-ownership (resource_delay_state)
.type effect_parameter_lifecycle_resource_delay_state,@function
effect_parameter_lifecycle_resource_delay_state:
    r2 = b[r0+0] (u)
    r3 = r2 + -17
    r1 = r0 + 312
    if (r3 >= 4) goto L01c068ca
    r1 = r1 + 148
    goto L01c068dc
L01c068ca:
    r0 = r2 + -9
    if (r0 >= 2) goto L01c068d6
    r1 += 32
    goto L01c068dc
L01c068d6:
    r0 = 0
    if (r2 != 3) goto L01c068de
L01c068dc:
    r0 = [r1+0]
L01c068de:
    rts

; effect_parameter_lifecycle_resource_reset: 0x01c068e0..0x01c06926, module effect-parameter-lifecycle (resource_reset), effect-parameter-resources (reset), effect-resource-ownership (resource_reset)
.type effect_parameter_lifecycle_resource_reset,@function
effect_parameter_lifecycle_resource_reset:
    r1 = b[r0+0] (u)
    r2 = r1 + -3
    if (r2 > 20) goto L01c06924
    r1 = 12
    tbb [r2]
resource_reset_branches:
    .byte (L01c06918 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c0691a - resource_reset_branches) / 2, (L01c0691a - resource_reset_branches) / 2
    .byte (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06924 - resource_reset_branches) / 2, (L01c06904 - resource_reset_branches) / 2, (L01c06904 - resource_reset_branches) / 2, (L01c06904 - resource_reset_branches) / 2
    .byte (L01c06904 - resource_reset_branches) / 2, (L01c06904 - resource_reset_branches) / 2, (L01c06908 - resource_reset_branches) / 2, (L01c06908 - resource_reset_branches) / 2, (L01c06908 - resource_reset_branches) / 2
    .byte 0x00  ; alignment
L01c06904:
    r1 = 27
    goto L01c0691a
L01c06908:
    r2 = 0
    r3 = 0
    [r0+404] = r2
    [r0+408] = r3
    r1 = 31
    goto L01c0691a
L01c06918:
    r1 = 5
L01c0691a:
    r0 = r0 + 288
    r2 = 0
    [r0+r1<<2] = r2
L01c06924:
    rts
