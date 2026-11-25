; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 3 functions, 0x01c05e88..0x01c05eb0

; ram_callbacks_empty_leaf: 0x01c05e88..0x01c05e8a, module ram-callbacks (empty_leaf)
.type ram_callbacks_empty_leaf,@function
ram_callbacks_empty_leaf:
    rts

; ram_callbacks_zero_leaf: 0x01c05e8a..0x01c05e8e, module ram-callbacks (zero_leaf)
.type ram_callbacks_zero_leaf,@function
ram_callbacks_zero_leaf:
    r0 = 0
    rts

; ram_callbacks_halfword_sum: 0x01c05e8e..0x01c05eb0, module ram-callbacks (halfword_sum)
.type ram_callbacks_halfword_sum,@function
ram_callbacks_halfword_sum:
    [--sp] = {rets, r4}
    r1 = b[r0+7] (u)
    if (r1 == 0) goto L01c05eac
    r2 = r0 + 104
    r3 = 0
    r0 = 0
L01c05e9c:
    r4 = h[r2+r3<<1] (u)
    r4 = r4 << 2
    r3 = r3 + 1
    r0 = r0 + r4
    if (r3 < r1) goto L01c05e9c
    {pc, r4} = [sp++]
L01c05eac:
    r0 = 0
    {pc, r4} = [sp++]
