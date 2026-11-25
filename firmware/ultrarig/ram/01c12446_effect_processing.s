; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 1 function, 0x01c12446..0x01c1245c

; effect_processing_ir_accelerated: 0x01c12446..0x01c1245c, module effect-processing (ir_accelerated)
.type effect_processing_ir_accelerated,@function
effect_processing_ir_accelerated:
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L01c1245a
    r2 = [r1+0]
    if (r2 == 0) goto L01c1245a
    r1 = [r1+548]
    r0 = 1
    if (r1 != 0) goto L01c1245a
    r0 = r1
L01c1245a:
    rts
