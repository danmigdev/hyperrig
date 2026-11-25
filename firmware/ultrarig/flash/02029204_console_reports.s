; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_reports: 1 function, 0x02029204..0x0202921e

; console_reports_type_name: 0x02029204..0x0202921e, module console-reports (type_name)
.type console_reports_type_name,@function
console_reports_type_name:
    r1 = r0 + -1
; HyperRig MINI, product option: the effects of HyperRig (mini/product/effects.c) have the ids from 40 on.
.if MINI_PRODUCT
    if (r1 > 38) goto Lhr_type_name
.endif
    if (r1 <= 38) {
    r1 = L0203a574
    r0 = [r1+r0<<2]
    } else {
    r0 = L0203b97c
    }
    rts
.if MINI_PRODUCT
Lhr_type_name:
    [--sp] = {rets, r3-r1}  ; who calls this counts on r2 and r3
    call hyperrig_effect_name  ; @call.xl
    {pc, r3-r1} = [sp++]
.endif
