; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x01c05f1c..0x01c05ff2

; effect_setup_layout29: 0x01c05f1c..0x01c05ff2, module effect-setup (layout29)
.type effect_setup_layout29,@function
effect_setup_layout29:
    [--sp] = {rets, r8-r4}
    r2 = 1024
    if (r1 != 0) goto L01c05f28
    r2 = 512
L01c05f28:
    r3 = r2 >> 1
    r4 = r3 | 0x1
    if (r0 == 0) goto L01c05fb8
    r3 = 12312
    r3 = r3 + r0
    r6 = r3 + 64
    r5 = 12376  #
    [r3+0] = r6
    r6 = r2 << 2
    r5 = r5 + r6
    r7 = r0 + r5
    r7 = 8192  #
    [r3+4] = r7
    if (r1 != 0) goto L01c05f52
    r7 = 4096
L01c05f52:
    r7 = r7 + r5
    r5 = r0 + r7
    r8 = 3080  #
    [r3+8] = r5
    r5 = r7 + r6
    r6 = r0 + r5
    [r3+12] = r6
    r6 = r4 << 3
    r5 = r5 + r6
    r7 = r0 + r5
    r5 = r5 + r6  #
    [r3+16] = r7
    r7 = r0 + r5
    r5 = r5 + r6  #
    [r3+20] = r7
    r7 = r0 + r5
    r4 = r4 << 2
    r4 = r4 + 7
    r4 = r4 & r8  #
    [r3+24] = r7
    r5 = r5 + r4
    r7 = r0 + r5
    r4 = r4 + r5  #
    [r3+28] = r7
    r5 = r0 + r4
    r5 = r2 | 0x8  #
    [r3+32] = r5
    r4 = r4 + r5
    r7 = r0 + r4
    r4 = r4 + r5  #
    [r3+36] = r7
    r5 = r0 + r4
    r4 = r4 + r2  #
    [r3+40] = r5
    r5 = r0 + r4
    r4 = r4 + r6  #
    [r3+44] = r5
    r5 = r0 + r4
    r2 = r2 << 1
    r2 |= 4
    r2 = r2 + 7
    r2 = r2 & r8  #
    [r3+48] = r5
    r2 = r2 + r4
    r0 = r0 + r2
    [r3+52] = r0
    goto L01c05fe6
L01c05fb8:
    r0 = 21592
    if (r1 != 0) goto L01c05fc2
    r0 = 16984
L01c05fc2:
    r3 = r2 << 1
    r3 |= 4
    r3 = r3 + 7
    r5 = 3080
    r3 &= r5
    r0 = r0 + r3
    r3 = r4 << 5
    r0 = r0 + r3
    r3 = r4 << 2
    r3 = r3 + 7
    r3 &= r5
    r4 = r2 << 2
    r2 |= r4
    r2 |= 8
    r2 = r2 + r3
    r2 = r2 << 1
    r2 = r2 + r0
L01c05fe6:
    r0 = 1
    if (r1 != 0) goto L01c05fec
    r0 = r1
L01c05fec:
    r0 = r0 << 11
    r0 = r0 + r2
    {pc, r8-r4} = [sp++]
