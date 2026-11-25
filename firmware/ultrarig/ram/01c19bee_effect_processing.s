; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 2 functions, 0x01c19bee..0x01c19d36

; effect_processing_peak16: 0x01c19bee..0x01c19c98, module effect-processing (peak16)
.type effect_processing_peak16,@function
effect_processing_peak16:
    [--sp] = {r5, r4}
    r5 = 0
    r1 = [r0+0]
    r2 = [r0+4]
    r3 = [r0+8]
    r4 = [r0+12]
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r4 = abs(r4)
    r5 = smax(r5, r1)
    r5 = smax(r5, r2)
    r5 = smax(r5, r3)
    r5 = smax(r5, r4)
    r1 = [r0+16]
    r2 = [r0+20]
    r3 = [r0+24]
    r4 = [r0+28]
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r4 = abs(r4)
    r5 = smax(r5, r1)
    r5 = smax(r5, r2)
    r5 = smax(r5, r3)
    r5 = smax(r5, r4)
    r1 = [r0+32]
    r2 = [r0+36]
    r3 = [r0+40]
    r4 = [r0+44]
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r4 = abs(r4)
    r5 = smax(r5, r1)
    r5 = smax(r5, r2)
    r5 = smax(r5, r3)
    r5 = smax(r5, r4)
    r1 = [r0+48]
    r2 = [r0+52]
    r3 = [r0+56]
    r4 = [r0+60]
    r1 = abs(r1)
    r2 = abs(r2)
    r3 = abs(r3)
    r4 = abs(r4)
    r5 = smax(r5, r1)
    r5 = smax(r5, r2)
    r5 = smax(r5, r3)
    r5 = smax(r5, r4)
    r0 = r5
    {r5, r4} = [sp++]
    rts

; effect_processing_ramp16: 0x01c19c98..0x01c19d36, module effect-processing (ramp16)
.type effect_processing_ramp16,@function
effect_processing_ramp16:
    [--sp] = {r7-r4}
    r7 = 4
L01c19c9c:
    r3 = [r0+0]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r5_r4 >>>= 16
    r6 = r4 >>> 31
    if (r5 != r6) goto L01c19cf6
L01c19cae:
    [r0+0] = r4
    r3 = [r0+4]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r5_r4 >>>= 16
    r6 = r4 >>> 31
    if (r5 != r6) goto L01c19d06
L01c19cc2:
    [r0+4] = r4
    r3 = [r0+8]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r5_r4 >>>= 16
    r6 = r4 >>> 31
    if (r5 != r6) goto L01c19d16
L01c19cd6:
    [r0+8] = r4
    r3 = [r0+12]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r5_r4 >>>= 16
    r6 = r4 >>> 31
    if (r5 != r6) goto L01c19d26
L01c19cea:
    [r0+12] = r4
    r0 = r0 + 16
    if (--r7 != 0) goto L01c19c9c
    {r7-r4} = [sp++]
    rts
L01c19cf6:
    r6 = r5 >> 31
    r6 = r6 + r6
    r5 = 2147483647
    r6 = r6 + r5
    r4 = r6
    goto L01c19cae
L01c19d06:
    r6 = r5 >> 31
    r6 = r6 + r6
    r5 = 2147483647
    r6 = r6 + r5
    r4 = r6
    goto L01c19cc2
L01c19d16:
    r6 = r5 >> 31
    r6 = r6 + r6
    r5 = 2147483647
    r6 = r6 + r5
    r4 = r6
    goto L01c19cd6
L01c19d26:
    r6 = r5 >> 31
    r6 = r6 + r6
    r5 = 2147483647
    r6 = r6 + r5
    r4 = r6
    goto L01c19cea
