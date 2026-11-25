; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_resampling: 1 function, 0x01c07986..0x01c07a4c

; effect_resampling_up: 0x01c07986..0x01c07a4c, module effect-resampling (up)
.type effect_resampling_up,@function
effect_resampling_up:
    [--sp] = {rets, r15-r4}
    sp += -16
    r15 = r2  #
    [sp+12] = r0
    if ((r2 & 0x3) == 0) goto L01c079ca
    ifs (r2 < 1) goto L01c07a48
    r0 = effect_resampling_counts
    r4 = [r0+r3<<2]
    r0 = effect_resampling_pointers
    r0 = [r0+r3<<2]
    r0 = 0x1 - r4  #
    [sp+4] = r0
    r10 = 0  #
    [sp+8] = r4
    r11 = 0  #
    [sp] = r0
    r3 = r0 << 2
    r0 = [sp+12]
    r9 = r0 + r3
    r5 = r9 + -4
    r3 = 0
    goto L01c079f6
L01c079ca:
    if (r3 != 2) goto L01c079da
    r0 = [sp+12]
    call effect_resampling_up4  ; @call.xl
    sp += 16
    {pc, r15-r4} = [sp++]
L01c079da:
    r0 = [sp+12]
    call effect_resampling_up5  ; @call.xl
    goto L01c07a48
L01c079e4:
    r4 = r13 >> 31
    r4 = r4 << 1
    r0 = 2147483647
    r12 = r4 + r0
    goto L01c07a22
L01c079f6:
    r7 = r5  #
    r4 = [sp+4]
    r6 = r9
    r14 = [sp+8]
    r12 = r10
    r13 = 0
L01c07a02:
    r0 = [r4++=4]
    r2 = [r6++=4]
    r8 = [r7++=-4]
    r13_r12 += r2 * r0 (s)
    r13_r12 += r8 * r0 (s)
    if (--r14 != 0) goto L01c07a02
    r13_r12 >>>= 30
    r4 = r12 >>> 31
    if (r13 != r4) goto L01c079e4
L01c07a22:
    r4 = r3 << 3
    [r1+r4] = r12
    r0 = [sp]
    r4 = r0 + r3  #
    r0 = [sp+12]
    r4 = [r0+r4<<2]
    r6 = 4
    r6 <= insert(r3, p:3, l:29)
    [r1+r6] = r4
    r5 = r5 + 4
    r3 = r3 + 1
    r9 = r9 + 4
    if (r3 != r15) goto L01c079f6
L01c07a48:
    sp += 16
    {pc, r15-r4} = [sp++]
