; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; delay_line: 1 function, 0x01c06c58..0x01c06cb8

; delay_line_delay_tap: 0x01c06c58..0x01c06cb8, module delay-line (delay_tap)
.type delay_line_delay_tap,@function
delay_line_delay_tap:
    [--sp] = {rets, r5, r4}
    sp += -56
    r4 = r0 + 288  #
    [sp] = r1
    r1 = [r0+84]
    [sp+4] = r1
    r1 = [r4+0]
    r5 = [sp+68]
    [sp+8] = r1
    [sp+12] = r3
    r1 = [r5+0]
    [sp+16] = r1
    r1 = [r4+8]
    r3 = [sp+72]
    [sp+20] = r1
    r3 = 0x80000  #
    [sp+24] = r3
    r1 = [r4+20]
    [sp+28] = r1
    r1 = 0
    [sp+32] = r1
    [sp+36] = r3
    [sp+40] = r1
    r1 = r2 + 15
    r1 = r1 >> 4
    [sp+44] = r1
    r1 = 1
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
    r0 = [sp+16]
    [r5+0] = r0
    sp += 56
    {pc, r5, r4} = [sp++]
