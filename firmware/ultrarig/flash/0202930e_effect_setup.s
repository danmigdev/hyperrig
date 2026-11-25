; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x0202930e..0x0202936c

; effect_setup_type_cost: 0x0202930e..0x0202936c, module effect-setup (type_cost)
.type effect_setup_type_cost,@function
effect_setup_type_cost:
    [--sp] = {rets, r4}
    r4 = r0
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on.
.if MINI_PRODUCT
    if (r4 > 39) goto Lhr_type_cost
.endif
    if (r4 == 7) goto L0202933e
    call effect_setup_has_mode  ; @call.xl
    if (r0 == 0) goto L02029332
    r0 = r4
    call effect_setup_default_mode  ; @call.xl
    r1 = r0
    r0 = r4
    call effect_setup_mode_cost  ; @call.xl
    {pc, r4} = [sp++]
L02029332:
    r0 = effect_processing_costs
    r0 = [r0+r4<<2]
    {pc, r4} = [sp++]
L0202933e:
    r0 = L01c1f7d0
    r0 = [r0+0]
    if (r0 != 0) goto L02029356
    r0 = 0
    r1 = 21
    call ir_convolution_installation_effective
    call effect_setup_ir_fallback_cost  ; @call.xl
    {pc, r4} = [sp++]
L02029356:
    r0 = 1
    r1 = 21
    call ir_convolution_installation_effective
    r1 = L01c1fa14
    r1 = [r1+0]
    call effect_setup_ir_partition_cost  ; @call.xl
    {pc, r4} = [sp++]
.if MINI_PRODUCT
Lhr_type_cost:
    call hyperrig_effect_cost  ; @call.xl
    {pc, r4} = [sp++]
.endif
