; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_live: 1 function, 0x01c12878..0x01c1296c

; capture_live_reset: 0x01c12878..0x01c1296c, module capture-live (reset), capture-native (reset), capture-reset (reset)
.type capture_live_reset,@function
capture_live_reset:
    [--sp] = {rets, r10-r4}
    r10 = r0
    r8 = h[r0+8] (u)
    r9 = r0 + 80
    if (r8 == 0) goto L01c128c2
    r4 = b[r0+2] (u)
    r7 = [r9+12]
    r5 = 0
    r6 = 0
L01c12892:
    r0 = r6 * 0x50
    r1 = r7 + r0
    r3 = r1
    r0 = [++r3=76]
    r0 += 64
    r0 *= r4
    if (r0 == 0) goto L01c128ba
    r2 = [r1+68]
    r1 = 0
L01c128aa:
    [r2+r1<<2] = r5
    r0 = [r3+0]
    r0 += 64
    r0 *= r4
    r1 = r1 + 1
    if (r1 < r0) goto L01c128aa
L01c128ba:
    r6 = r6 + 1
    if (r6 < r8) goto L01c12892
    goto L01c128c4
L01c128c2:
    r4 = b[r0+2] (u)
L01c128c4:
    r0 = [r9+4]
    r0 = r0 + 1
    r1 = r0
    if (r0 >= 64) {
    r1 = 64
    }
    r0 = r0 + r1
    r0 *= r4
    if (r0 == 0) goto L01c128fc
    r3 = [r9+0]
    r5 = 0
    r1 = 0
L01c128e0:
    [r3+r1<<2] = r5
    r0 = [r9+4]
    r0 = r0 + 1
    r2 = r0
    if (r0 >= 64) {
    r2 = 64
    }
    r0 = r0 + r2
    r0 *= r4
    r1 = r1 + 1
    if (r1 < r0) goto L01c128e0
L01c128fc:
    if (r4 != 3) goto L01c12966
    r7 = [r9+60]
    if (r7 == 0) goto L01c12966
    r6 = r10 + 144
    if (r8 == 0) goto L01c12942
    r4 = [r6+0]
    r5 = 0
    r2 = 0
L01c12914:
    r0 = [r4+r2<<2]
    r0 = r0 * 0x3
    if (r0 == -192) goto L01c1293c
    r3 = [r7+r2<<2]
    r1 = 0
L01c12926:
    [r3+r1<<2] = r5
    r0 = [r4+r2<<2]
    r0 = r0 * 0x3
    r0 = r0 + 192
    r1 = r1 + 1
    if (r1 < r0) goto L01c12926
L01c1293c:
    r2 = r2 + 1
    if (r2 < r8) goto L01c12914
L01c12942:
    r0 = [r6+8]
    r0 = r0 * 0x3
    if (r0 == -192) goto L01c12966
    r2 = [r6+4]
    r3 = 0
    r1 = 0
L01c12952:
    [r2+r1<<2] = r3
    r0 = [r6+8]
    r1 = r1 + 1
    r0 = r0 * 0x3
    r0 = r0 + 192
    if (r1 < r0) goto L01c12952
L01c12966:
    [r9+8] = 0x0
    {pc, r10-r4} = [sp++]
