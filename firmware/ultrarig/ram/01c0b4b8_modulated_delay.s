; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; modulated_delay: 1 function, 0x01c0b4b8..0x01c0b524

; modulated_delay_wrapper: 0x01c0b4b8..0x01c0b524, module modulated-delay (wrapper)
.type modulated_delay_wrapper,@function
modulated_delay_wrapper:
    [--sp] = {rets, r4}
    sp += -56
    if (r2 == 0) goto L01c0b520
    r4 = r0 + 288  #
    [sp] = r1
    r1 = [r0+84]
    [sp+4] = r1
    r1 = [r4+0]
    [sp+8] = r1
    r1 = [r4+4]
    [sp+12] = r1
    r1 = [r4+12]
    [sp+16] = r1
    r1 = [r4+8]
    [sp+20] = r1
    r1 = [r4+16]
    [sp+24] = r1
    r1 = [r4+20]
    [sp+28] = r1
    r3 = [r4+24]
    [sp+32] = r3
    r1 = [r4+28]
    r1 = r1 << 3
    [sp+36] = r1
    r1 = [r4+32]
    [sp+40] = r1
    r1 = r2 + 15
    r1 = r1 >> 4
    [sp+44] = r1
    r1 = 2
    if (r3 != 0) goto L01c0b4fc
    r1 = 1
L01c0b4fc:
    [sp+48] = r1
    r0 = [r0+88]
    r0 = r0 << 1
    r0 = r0 & 0xFFFFFFFC
    r0 += -20
    [sp+52] = r0
    r0 = sp + 0
    call modulated_delay_line  ; @call.xl
    r0 = [sp+8]
    [r4+0] = r0
    r0 = [sp+12]
    [r4+4] = r0
    r0 = [sp+16]
    [r4+12] = r0
L01c0b520:
    sp += 56
    {pc, r4} = [sp++]
