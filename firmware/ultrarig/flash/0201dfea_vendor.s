; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201dfea..0x0201e074: vendor code (JieLi SDK or library, not reversed), as instructions
L0201dfea:
    [--sp] = {rets, r4}
    r0 = 341
    r2 = L01c26890
    r1 = [r2+r0<<2]
    r2 = r2 + 5468
    r3 = 0
    goto L0201e022
L0201e002:
    if (r1 == 0) goto L0201e01e
    r0 = b[r1+0] (u)
    r0 = r0 & (1 << r3)
    if (r0 == 0) goto L0201e01e
    r4 = b[r2+16] (u)
    r0 = 0
    if (r4 != 0) goto L0201e028
    r4 = b[r2+0] (u)
    r4 = r4 & 0xFFFFFF0F
    if (r4 > 2) goto L0201e028
L0201e01e:
    r2 += 100
    r3 += 1  ; @add.ri.u5
L0201e022:
    if (r3 <= 1) goto L0201e002
    r0 = 1
L0201e028:
    {pc, r4} = [sp++]
sdk_usb_phy_status:
    r1 = 0x11800
    if (r0 == 0) goto L0201e036
    r1 = 92684
L0201e036:
    r0 = [r1+0]
    r0 = r0 & 0x1
    rts
L0201e03e:
    if (r0 == 0) goto L0201e058
    r0 = 92684
    [r0+0] &= 0xFFFFFFDF
    [r0+0] &= 0xFFFFFCFF
    [r0+0] &= 0x8FFFFFFF
    [r0+0] &= 0xFFFFFFE1
    rts
L0201e058:
    r1 = L02035cb0
    r2 = [r1+r0<<2]
    r1 += 8  ; @add.ri.u5
    r0 = [r1+r0<<2]
    r1 = 4097
    [r2+0] = r1
    [r0+0] = 0xC
    rts
