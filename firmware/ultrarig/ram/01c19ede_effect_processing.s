; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 1 function, 0x01c19ede..0x01c19efa

; effect_processing_wrap16: 0x01c19ede..0x01c19efa, module effect-processing (wrap16)
.type effect_processing_wrap16,@function
effect_processing_wrap16:
    [--sp] = {r7-r4}
    r3 = r0
    r7 = 16
L01c19ee4:
    rep r7 {
    r6 = [r0++=4]
    r1 = r1 + r2
    r5_r4 = r6 * r1 (s)
    r5_r4 >>>= 16
    [r3++=4] = r4
    }
    if (r7 != 0) goto L01c19ee4
    {r7-r4} = [sp++]
    rts
