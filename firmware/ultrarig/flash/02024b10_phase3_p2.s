; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p2: 2 functions, 0x02024b10..0x02024c28

; phase3_p2_wifi_get_xosc: 0x02024b10..0x02024b8c, module phase3-p2 (wifi_get_xosc)
.type phase3_p2_wifi_get_xosc,@function
phase3_p2_wifi_get_xosc:
    [--sp] = {rets, r5, r4}
    sp += -4
    r1 = 302
    r5 = L01c26890
    r2 = [r5+r1<<2]
    r4 = r0
    if (r2 != 0) goto L02024b34
    r0 = L01c1f180
    r0 = [r0+24]
    r0 |= 1
    [r5+r1<<2] = r0
L02024b34:
    r0 = 71984
    r0 = [r0+0]
    r1 += 1  ; @add.ri.u5
    r2 = [r5+r1<<2]
    if (r2 != 0) goto L02024b4c
    r2 = r0 | 0x80000000
    [r5+r1<<2] = r2
L02024b4c:
    r1 = uextra(r0, p:13, l:4)
    r0 = uextra(r0, p:19, l:4)  #
    b[r4+0] = r1
    b[r4+1] = r0
; HyperRig MINI, product option: the crystal's values of the configuration file, as the SDK takes them (mini/product/crystal.c).
.if MINI_PRODUCT
    r0 = r4
    call hyperrig_crystal  ; @call.xl
.endif
    r0 = b[r5+57] (u)
    r0 |= 8
    b[r5+57] = r0
    r1 = sp + 2
    r0 = 106
    r2 = 2
    call L02024a78
    if (r0 != 2) goto L02024b88
    r0 = b[sp+2] (u)
    b[r4++=1] = r0
    r0 = b[sp+3] (u)
    b[r4+0] = r0
    r0 = b[r5+57] (u)
    r0 = r0 & 0xFFFFFFF6
    r0 |= 1
    b[r5+57] = r0
L02024b88:
    sp += 4
    {pc, r5, r4} = [sp++]

; phase3_p2_set_pll_rn_en: 0x02024b8c..0x02024c28, module phase3-p2 (set_pll_rn_en)
.type phase3_p2_set_pll_rn_en,@function
phase3_p2_set_pll_rn_en:
    [--sp] = {rets, r4}
    r0 = 71988
    [r0+4] &= 0xFFFEFFFF
    [r0+4] &= 0xFFFBFFFF
    [r0+0] &= 0xFEFFFFFF
    r2 = 262656
    r1 = [r2+0]
    if ((r1 & 0x1) != 0) {
    r3 = 8000000
    } else {
    r3 = 4000000
    }
    r1 = L01c373b8
    r4 = [r1+8]
    r3 = r4 / r3 (s)
    r4 = -5
    r3 *= r4
    goto L02024bce
L02024bca:
    nop
    r3 += 1  ; @add.ri.u5
L02024bce:
    if (r3 != 0) goto L02024bca
    [r0+4] |= 0x10000
    r3 = [r2+0]
    if ((r3 & 0x1) != 0) {
    r3 = 8000000
    } else {
    r3 = 4000000
    }
    r4 = [r1+8]
    r3 = r4 / r3 (s)
    r4 = -5
    r3 *= r4
    goto L02024bf6
L02024bf2:
    nop
    r3 += 1  ; @add.ri.u5
L02024bf6:
    if (r3 != 0) goto L02024bf2
    [r0+0] |= 0x1000000
    [r0+4] |= 0x40000
    r0 = [r2+0]
    if ((r0 & 0x1) != 0) {
    r0 = 8000000
    } else {
    r0 = 4000000
    }
    r1 = [r1+8]
    r0 = r1 / r0 (s)
    r1 = -100
    r0 *= r1
    goto L02024c24
L02024c20:
    nop
    r0 += 1  ; @add.ri.u5
L02024c24:
    if (r0 != 0) goto L02024c20
    {pc, r4} = [sp++]
