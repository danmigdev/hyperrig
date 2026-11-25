; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_enable: 1 function, 0x01c11f76..0x01c11faa

; effect_enable_ir_reset: 0x01c11f76..0x01c11faa, module effect-enable (ir_reset)
.type effect_enable_ir_reset,@function
effect_enable_ir_reset:
    [--sp] = {rets, r5, r4}
    if (r0 == 0) goto L01c11fa8
    r1 = [r0+0]
    if (r1 == 0) goto L01c11fa8
    r1 = [r0+4]
    r1 = r1 * 0x81
    if (r1 == 0) goto L01c11f94
    r2 = [r0+24]
    r4 = 0
    r5 = 0
L01c11f8c:
    [r2++=4] = r4
    [r2++=4] = r5
    if (--r1 != 0) goto L01c11f8c
L01c11f94:
    r3_r2 = 0  #
    r1 = [r0+48]
L01c11f98:
    [r1+r3<<2] = r2
    r3 = r3 + 1
    if (r3 != 256) goto L01c11f98
    r3 = 0
    [r0+8] = r2
    [r0+12] = r3
L01c11fa8:
    {pc, r5, r4} = [sp++]
