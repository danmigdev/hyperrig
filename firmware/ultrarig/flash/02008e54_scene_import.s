; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; scene_import: 2 functions, 0x02008e54..0x0200907a

; scene_import_clean_name: 0x02008e54..0x02008eac, module scene-import (clean_name)
.type scene_import_clean_name,@function
scene_import_clean_name:
    [--sp] = {rets, r7-r4}
    r2 = 0
    r3 = r0
    rep 16 {
    b[r3++=1] = r2
    }
L02008e5e:
    r3 = b[r1++=1] (u)
    if (r3 == 32) goto L02008e5e
    goto L02008e8c
L02008e66:
    if (r3 == 0) goto L02008e90
    r4 = 95
    r5 = 95
    if (r3 != 127) {  ; @if.ne.ri.s12
    r5 = r3
    }
    r7 = r3.b0 (s)
    r6 = 95
    ifs (r7 >= 32) {  ; @ifs.ge.ri.s12
    r6 = r5
    }
    if (r3 != 39) {  ; @if.ne.ri.s12
    r4 = r6
    }
    b[r0+r2] = r4
    r3 = b[r1+r2] (u)
    r2 += 1  ; @add.ri.u5
L02008e8c:
    if (r2 <= 14) goto L02008e66
L02008e90:
    r1 = r2 + -1
    r2 = 0
    goto L02008ea6
L02008e98:
    r3 = b[r0+r1] (u)
    if (r3 != 32) goto L02008eaa
    b[r0+r1] = r2
    r1 += -1
L02008ea6:
    if (r1 != -1) goto L02008e98
L02008eaa:
    {pc, r7-r4} = [sp++]

; scene_import_import_scenes: 0x02008eac..0x0200907a, module scene-import (import_scenes)
; HyperRig MINI, product option: eight scenes (mini/product/scenes.c); the first four from the working preset as ever.
.type scene_import_import_scenes,@function
scene_import_import_scenes:
    [--sp] = {rets, r15-r4}
    sp += -36
    r15 = r0
    r0 = 11936
.if MINI_PRODUCT
    r9 = hyperrig_scene_base  ; @li.u32
.else
    r9 = L01c26890
.endif
    r0 += r9
    r1 = 0
.if MINI_PRODUCT
    r2 = 2080
.else
    r2 = 1040
.endif
    r7 = 0
    call effect_enable_memset  ; @call.xl
    r0 = L01c1f180
    r11 = L01c24790
    r1 = b[r11+0] (u)
    [r0+88] = 0xFFFFFFFF
    [sp] = r1
    if (r1 < 2) goto L02009034
    r0 = 12182
    r3 = b[r11+1] (u)
    r0 += r9
    r0 = 11958  #
    [sp+12] = r0
    r14 = r9 + r0
    if (r3 >= 16) {  ; @if.ge.ri.s12
    r3 = 16
    }
    r0 = r11 + 1436
    r0 = r11 + 306  #
    [sp+8] = r0
    r10 = 0  #
    [sp+4] = r0
    goto L0200901c
L02008f10:
    r0 = b[r11+7] (u)
    r1 = 1
    r12 = r1 << r10
    if ((r0 & r12) == 0) goto L02008ffe
    r8 = r10 * 0x104
    r4 = r9
    r9 = r8 + r4
    r13 = r8 + r11
    r0 = 302
    r0 = b[r13+r0] (u)
    r1 = 303
    r1 = b[r13+r1] (u)
    r2 = r9
    r5 = 1
    r6 = 11936
    b[++r2=r6] = r5
    b[r2+4] = r0
    b[r2+5] = r1
    r0 = 0
    r1 = [sp]
    if (r1 < 5) goto L02008f64
    r0 = 1347
    r1 = b[r11+r0] (u)
    r0 = 1
    if ((r1 & r12) == 0) {
    r0 = 0
    }
L02008f64:
    r1 = 12194
    b[r9+r1] = r0
    r1 = 6
    r5 = [sp+8]
    r6 = [sp+12]
    goto L02008f7a
L02008f74:
    r0 = h[r5++=2] (u)
    h[r6++=2] = r0
    r1 += -1
L02008f7a:
    if (r1 != 0) goto L02008f74
    r0 = 1
    r1 = [sp]
    if (r1 == 2) goto L02008f94
    r0 = 1345
    r1 = b[r11+r0] (u)
    r0 = 1
    if ((r1 & r12) != 0) {
    r0 = 0
    }
L02008f94:
    r1 = 11936
    r6 = r9 + r1
    r9 = r4  #
    b[r6+1] = r0
    r1 = 0
    r0 = [sp+4]
    goto L02008ffa
L02008fa6:
    r7 = b[r15+r1] (s)
    ifs (r7 < 0) goto L02008ff6
    r2 = h[r13+300] (u)
    r2 = r2 & (1 << r1)
    if (r2 == 0) goto L02008ff6
    r4 = 304  #
    r2 = h[r6+2] (u)
    r2 = r2 | (1 << r7)
    r5 = r1 << 4
    r5 += r8
    r5 += r11
    r5 = b[r5+r4] (u)
    r2 = r8 + r7  #
    h[r6+2] = r2
    r2 += r9
    r4 = 11942
    b[r2+r4] = r5
    r2 = r7 * 0xE
    r7 = r14 + r2
    r2 = 0
    r5 = r0
    goto L02008ff2
L02008fea:
    r4 = h[r5++=2] (u)
    h[r7+r2<<1] = r4
    r2 += 1  ; @add.ri.u5
L02008ff2:
    if (r2 != 7) goto L02008fea
L02008ff6:
    r0 += 16  ; @add.ri.u5
    r1 += 1  ; @add.ri.u5
L02008ffa:
    ifs (r1 < r3) goto L02008fa6
L02008ffe:
    r0 = [sp+4]
    r0 = r0 + 260
    r14 = r14 + 260  #
    [sp+4] = r0
    r0 = [sp+8]
    r0 += 12  ; @add.ri.u5
    [sp+8] = r0
    r0 = [sp+12]
    r0 = r0 + 260
    r10 = r10 + 1  #
    [sp+12] = r0
L0200901c:
    if (r10 != 4) goto L02008f10
    r0 = b[r11+6] (u)
    r7 = 0
    r1 = L01c1f180
.if MINI_PRODUCT
    if (r0 < 8) {  ; @if.lt.ri.s12
.else
    if (r0 < 4) {  ; @if.lt.ri.s12
.endif
    [r1+88] = r0
    }
.if MINI_PRODUCT
L02009034:
    r9 = hyperrig_name_base  ; @li.u32
    r4 = sp + 16
.else
L02009034:
    r4 = sp + 16
.endif
    r5 = 0
    goto L0200906a
L0200903a:
    r0 = r5 + r11
    r2 = r0 + 1368
    r1 = sp + 16
    r3 = r1 + 8
    rep 8 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r0 = r0 + 1360
    r2 = r1
    rep 8 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    b[r4+16] = r7
    r0 = r5 + r9
    r0 = r0 + 3248
    call scene_import_clean_name
    r5 += 16  ; @add.ri.u5
L0200906a:
    if (r5 != 64) goto L0200903a
    r0 = h[r11+10] (u)
.if MINI_PRODUCT
    r1 = L01c26890
    h[r1+78] = r0
    r0 = r15
    call hyperrig_import_more  ; @call.xl
.else
    h[r9+78] = r0
.endif
    sp += 36
    {pc, r15-r4} = [sp++]
