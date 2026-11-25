; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 1 function, 0x0202921e..0x02029248

; preset_application_metadata: 0x0202921e..0x02029248, module preset-application (metadata), scene-application (metadata)
.type preset_application_metadata,@function
preset_application_metadata:
    if (r1 > 6) goto L02029244
    r2 = r0 + -1
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on.
.if MINI_PRODUCT
    if (r2 > 38) goto Lhr_metadata
.else
    if (r2 > 38) goto L02029244
.endif
    r1 = r1 * 0xC
    r0 = r0 * 0x54
    r0 = r0 + r1
    r1 = effect_parameter_metadata
    r1 = r1 + r0
.if MINI_PRODUCT
Lhr_metadata_row:
.endif
    r0 = [r1+8]
    if (r0 == 0) goto L02029242
    r0 = r1
L02029242:
    rts
L02029244:
    r0 = 0
    rts
.if MINI_PRODUCT
Lhr_metadata:
    [--sp] = {rets, r3-r1}  ; who calls this counts on r3
    call hyperrig_effect_rows  ; @call.xl
    {rets, r3-r1} = [sp++]
    if (r0 == 0) goto L02029242
    r1 = r1 * 0xC
    r1 = r1 + r0
    goto Lhr_metadata_row
.endif
