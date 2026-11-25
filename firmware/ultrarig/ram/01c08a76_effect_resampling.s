; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_resampling: 1 function, 0x01c08a76..0x01c08b34

; effect_resampling_down: 0x01c08a76..0x01c08b34, module effect-resampling (down)
.type effect_resampling_down,@function
effect_resampling_down:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r1
    if ((r2 & 0x3) == 0) goto L01c08ab0
    ifs (r2 < 1) goto L01c08b30
    r4 = effect_resampling_counts
    r12 = [r4+r3<<2]
    r4 = effect_resampling_pointers
    r1 = [r4+r3<<2]
    r3 = r12 << 1
    r3 = 0x2 - r3
    r3 = r3 << 2
    r13 = r0 + r3
    r14 = r13 + -8
    r15 = 0
    goto L01c08adc
L01c08ab0:
    if (r3 != 2) goto L01c08ac0
    r1 = [sp]
    call effect_resampling_down4  ; @call.xl
    sp += 4
    {pc, r15-r4} = [sp++]
L01c08ac0:
    r1 = [sp]
    call effect_resampling_down5  ; @call.xl
    goto L01c08b30
L01c08aca:
    r3 = r11 >> 31
    r3 = r3 << 1
    r4 = 2147483647
    r10 = r3 + r4
    goto L01c08b1a
L01c08adc:
    r3 = r15 - r12
    r4 = 4
    r4 <= insert(r3, p:3, l:29)
    r10 = [r0+r4]
    r11 = r10 >>> 31
    r11_r10 <<= 30
    r3 = r1
    r6 = r14
    r5_r4 = r13_r12
L01c08af8:
    r7 = [r3++=4]
    r8 = [r5++=8]
    r9 = [r6++=-8]
    r11_r10 += r8 * r7 (s)
    r11_r10 += r9 * r7 (s)
    if (--r4 != 0) goto L01c08af8
    r11_r10 >>>= 31
    r3 = r10 >>> 31
    if (r11 != r3) goto L01c08aca
L01c08b1a:
    r14 = r14 + 8  #
    r3 = [sp]
    [r3+r15<<2] = r10
    r15 = r15 + 1
    r13 = r13 + 8
    if (r15 != r2) goto L01c08adc
L01c08b30:
    sp += 4
    {pc, r15-r4} = [sp++]
