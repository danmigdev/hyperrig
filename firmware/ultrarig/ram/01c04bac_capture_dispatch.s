; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_dispatch: 1 function, 0x01c04bac..0x01c04c42

; capture_dispatch_capabilities: 0x01c04bac..0x01c04c42, module capture-dispatch (capabilities), capture-live (capabilities), capture-native (capabilities)
.type capture_dispatch_capabilities,@function
capture_dispatch_capabilities:
    [--sp] = {rets, r6-r4}
    r6 = L01c2bff0
    r5 = r6 + 76
    r3 = r0  #
    r4 = b[r5+14] (u)
    r4 = r6 + 92  #
    b[r3+0] = r4
    r0 = b[r5+15] (u)
    b[r3+1] = r0
    r0 = b[r4+0] (u)
    b[r3+2] = r0
    r0 = b[r4+1] (u)
    b[r3+3] = r0
    r0 = b[r4+2] (u)
    b[r3+4] = r0
    r0 = b[r4+3] (u)
    b[r3+5] = r0
    r0 = b[r4+4] (u)
    b[r3+6] = r0
    r0 = b[r4+5] (u)
    b[r3+7] = r0
    r0 = b[r4+6] (u)
    b[r3+8] = r0
    r0 = b[r4+7] (u)
    b[r3+9] = r0
    r0 = b[r4+8] (u)
    b[r3+10] = r0
    r0 = b[r4+9] (u)
    b[r3+11] = r0
    r0 = b[r4+10] (u)
    b[r3+12] = r0
    r0 = b[r4+11] (u)
    b[r3+13] = r0
    r0 = b[r4+12] (u)
    b[r3+14] = r0
    r0 = b[r4+13] (u)
    b[r3+15] = r0
    r0 = b[r4+14] (u)
    b[r3+16] = r0
    r3 = h[r5+8] (u)
    [r1+0] = r3
    r0 = b[r5+2] (u)
    [r2+0] = r0
    r4 = 0
    if (r0 != 3) goto L01c04c3e
    r0 = b[r6+240] (u)
    if (r0 == 0) goto L01c04c3e
    r0 = b[r5+1] (u)
    if (r0 != 32) goto L01c04c3e
    r4 = 1
    if (r3 == 0) goto L01c04c3e
    r3 = h[r6+84] (u)
    r2 = [r6+168]
    r1 = 0
L01c04c2c:
    r0 = b[r2++=80] (u)
    if (r0 >= 16) goto L01c04c3c
    r1 = r1 + 1
    if (r1 < r3) goto L01c04c2c
    goto L01c04c3e
L01c04c3c:
    r4 = 0
L01c04c3e:
    r0 = r4
    {pc, r6-r4} = [sp++]
