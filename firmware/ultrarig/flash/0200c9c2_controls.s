; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; controls: 1 function, 0x0200c9c2..0x0200c9f4

; controls_immediate: 0x0200c9c2..0x0200c9f4, module controls (immediate)
.type controls_immediate,@function
controls_immediate:
    [--sp] = {rets, r4}
    r1 = r0 * 0x9
    r2 = L01c1f180
    r3 = r1 + r2
    r4 = b[r3+242] (u)
    r1 = 0
    if (r4 != 0) goto L0200c9f0
    r1 = b[r3+239] (u)
    if (r1 == 0) goto L0200c9ee
    r1 = 1
    r0 = r1 << r0  #
    r2 = b[r2+11] (u)
    if ((r2 & r0) == 0) {
    r1 = 0
    }
    goto L0200c9f0
L0200c9ee:
    r1 = 1
L0200c9f0:
    r0 = r1
    {pc, r4} = [sp++]
