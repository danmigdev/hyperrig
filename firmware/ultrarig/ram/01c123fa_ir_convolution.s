; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_convolution: 2 functions, 0x01c123fa..0x01c12446

; ir_convolution_size: 0x01c123fa..0x01c12414, module ir-convolution (size), ir-processing (size)
.type ir_convolution_size,@function
ir_convolution_size:
    r0 += 127
    r1 = r0 >> 7
    r0 = 1
    if (r1 == 0) goto L01c12404
    r0 = r1
L01c12404:
    if (r0 >= 32) {
    r0 = 32
    }
    r0 = r0 * 0x810
    r0 = r0 + 7248
    rts

; ir_convolution_reset: 0x01c12414..0x01c12446, module ir-convolution (reset), ir-processing (reset)
.type ir_convolution_reset,@function
ir_convolution_reset:
    [--sp] = {rets, r5, r4}
    r1 = [r0+4]
    r1 = r1 * 0x81
    if (r1 == 0) goto L01c12430
    r2 = [r0+24]
    r3 = 0
    r4 = 0
    r5 = 0
L01c12426:
    r3 = r3 + 1
    [r2++=4] = r4
    [r2++=4] = r5
    if (r3 < r1) goto L01c12426
L01c12430:
    r3_r2 = 0  #
    r1 = [r0+48]
L01c12434:
    [r1+r3<<2] = r2
    r3 = r3 + 1
    if (r3 != 256) goto L01c12434
    r3 = 0
    [r0+8] = r2
    [r0+12] = r3
    {pc, r5, r4} = [sp++]
