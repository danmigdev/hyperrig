; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02001916..0x02001968: vendor code (JieLi SDK or library, not reversed), as instructions
L02001916:
    [--sp] = {rets, r5, r4}
    r4 = r0
    if (r4 == 0) goto L0200192c
    r0 = 0x16800
    [r0+0] &= 0xFFFFFFFC
    r1 = -4
    r0 = r0 + 524
    goto L02001962
L0200192c:
    r5 = r4 << 1
    r0 = r5 + 149
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = r5 + 148
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = L02035cb0
    r1 = r0 + 8
    r1 = [r1+r4<<2]
    r0 = [r0+r4<<2]
    [r1+0] &= 0xFFFFFFDF
    [r1+0] &= 0xFFFFFF3F
    r1 = 513
    [r0+0] |= r1
    r1 = -2049
L02001962:
    [r0+0] &= r1
    {pc, r5, r4} = [sp++]
