; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 1 function, 0x02030f6e..0x02030f8e

; slot_queries_type_name: 0x02030f6e..0x02030f8e, module slot-queries (type_name)
.type slot_queries_type_name,@function
slot_queries_type_name:
    r1 = r0
    r2 = r1 + -1
    r0 = L0203b97e  ; "other"
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on.
.if MINI_PRODUCT
    if (r2 > 38) goto Lhr_group
Lhr_group_like:
.else
    if (r2 > 38) goto L02030f8c
.endif
    r2 = L0203b3e0
    r1 = [r2+r1<<2]
    if (r1 == 0) goto L02030f8c
    r0 = r1
L02030f8c:
    rts
.if MINI_PRODUCT
Lhr_group:
    [--sp] = {rets, r3-r1}  ; who calls this counts on r3
    r0 = r1
    call hyperrig_effect_like  ; @call.xl
    {rets, r3-r1} = [sp++]
    r1 = r0
    r0 = L0203b97e  ; "other"
    goto Lhr_group_like
.endif
