; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_live: 1 function, 0x01c127de..0x01c12850

; capture_live_read64: 0x01c127de..0x01c12850, module capture-live (read64), capture-native (read64), capture-parser (read64)
.type capture_live_read64,@function
capture_live_read64:
    [--sp] = {rets, r8-r4}
    r6 = r0
    r1 = [r6+8]
    r3 = [r6+4]
    r2 = r1 + 4
    if (r2 <= r3) goto L01c127f8
    [r6+12] = 0x1
    r4 = 0
    r5 = 0
    r2 = r1
    goto L01c12814
L01c127f8:
    r0 = [r6+0]
    r0 = r0 + r1
    r1 = b[r0+1] (u)
    r4 = b[r0+0] (u)
    r4 <= insert(r1, p:8, l:8)  #
    r7 = b[r0+2] (u)
    r4 <= insert(r7, p:16, l:8)  #
    r0 = b[r0+3] (u)
    r4 <= insert(r0, p:24, l:8)  #
    [r6+8] = r2
    r5 = 0
L01c12814:
    r1 = r2 + 4
    if (r1 <= r3) goto L01c12824
    [r6+12] = 0x1
    r2 = 0
    r3 = 0
    goto L01c12846
L01c12824:
    r0 = [r6+0]
    r0 = r0 + r2
    r7 = b[r0+1] (u)
    r2 = b[r0+0] (u)
    r8 = b[r0+2] (u)
    r2 <= insert(r7, p:8, l:8)  #
    r0 = b[r0+3] (u)
    r2 <= insert(r8, p:16, l:8)  #
    [r6+8] = r1
    r2 <= insert(r0, p:24, l:8)
    r3 = 0
    r3_r2 <<= 32
L01c12846:
    r1 = r3 | r5
    r0 = r2 | r4
    {pc, r8-r4} = [sp++]
