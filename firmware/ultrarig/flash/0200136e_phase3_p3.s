; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 3 functions, 0x0200136e..0x0200152c

; phase3_p3_list_empty: 0x0200136e..0x02001386, module phase3-p3 (list_empty)
.type phase3_p3_list_empty,@function
phase3_p3_list_empty:
    r0 = L01c1f180
    r1 = [r0+164]
    r2 = r0 + 164
    r0 = 1
    if (r1 != r2) {
    r0 = 0
    }
    rts

; phase3_p3_list_del: 0x02001386..0x02001394, module phase3-p3 (list_del)
.type phase3_p3_list_del,@function
phase3_p3_list_del:
    {r2, r1} = [r0+]
    [r1+4] = r2
    [r2+0] = r1
    [r0+0] = r0
    [r0+4] = r0
    rts

; phase3_p3_app_core_msg_handler: 0x02001394..0x0200152c, module phase3-p3 (app_core_msg_handler)
.type phase3_p3_app_core_msg_handler,@function
phase3_p3_app_core_msg_handler:
    [--sp] = {rets, r13-r4}
    r13 = r0  #
    r0 = [r0+4]
    if (r0 != 32) goto L02001478
    r7 = [r13+8]
    r8 = L01c27784
    r0 = r8
    call L02040614  ; @call.xl
    call phase3_p3_list_empty
    r10 = L01c1f180
    r1 = [r10+164]
    r12 = r1 + -16
    if (r0 == 0) goto L020013c4
    r12 = 0
L020013c4:
    r6 = [r7+4]
    r0 = 169552897
    if (r6 == r0) goto L02001414
    r11 = r0 + -1
    if (r6 != r11) goto L0200142c
    if (r12 == 0) goto L0200145a
    r0 = r12 + 16
    call phase3_p3_list_del
    r0 = [r12+28]
    r9 = 0  #
    r3 = [r0+0]
    r1 = 4
    r2 = 0
    r0 = r12
    call r3
    r0 = [r12+28]
    r0 = r12  #
    r3 = [r0+0]
    r1 = 5
    r2 = 0
    r4 = 5
    call r3
    b[r12+0] = r4
    call phase3_p3_list_empty
    if (r0 != 0) goto L0200145e
    r0 = [r10+164]
    r5 = r0 + -16
    goto L0200149a
L02001414:
    r0 = [r12+28]
    r9 = 0  #
    r3 = [r0+0]
    r4 = 4
    r1 = 4
    r2 = 0
    r0 = r12
    call r3
    b[r12+0] = r4
    goto L0200145e
L0200142c:
    r5 = 32669696
    r4 = 32669696
    goto L02001456
L0200143a:
    r1 = [r7+0]
    if (r1 == 0) goto L0200144a
    r0 = [r5+12]
    call L02028308  ; @call.xl
    if (r0 != 0) goto L02001454
    goto L0200147a
L0200144a:
    r0 = [r5+4]
    r0 &= r6
    if (r0 > 4095) goto L0200147a
L02001454:
    r5 += 32
L02001456:
    if (r5 < r4) goto L0200143a
L0200145a:
    r9 = -22
L0200145e:
    r0 = r8
    call L0204074c  ; @call.xl
    r0 = [r13+16]
    [r0+0] = r9
    r0 = [r13+12]
    call L020403ee  ; @call.xl
L02001478:
    {pc, r13-r4} = [sp++]
L0200147a:
    if (r12 == r5) goto L020014b4
    if (r12 == 0) goto L0200149a
    r0 = [r12+28]
    r0 = r12  #
    r3 = [r0+0]
    r1 = 2
    r4 = 2
    r2 = r7
    call r3
    r9 = r0
    if (r0 != 0) goto L0200145e
    b[r12+0] = r4
L0200149a:
    r0 = b[r5+0] (u)
    if (r0 == 2) goto L020014c6
    if (r0 != 5) goto L020014dc
    r0 = [r5+28]
    r0 = r5  #
    r3 = [r0+0]
    r1 = 0
    r2 = 0
    call r3
    r9 = r0
    goto L020014d8
L020014b4:
    r0 = [r12+28]
    r0 = r12  #
    r3 = [r0+0]
    r1 = 1
    r2 = r7
    call r3
    r9 = r0
    goto L0200145e
L020014c6:
    r0 = [r5+28]
    r0 = r5  #
    r3 = [r0+0]
    r1 = 3
    r2 = 0
    call r3
    r9 = r0
    r0 = 1
    b[r5+0] = r0
L020014d8:
    if (r9 != 0) goto L020014f2
L020014dc:
    r0 = [r7+4]
    if (r0 == r11) goto L0200150c
    r2 = r7  #
    r0 = [r5+28]
    r0 = r5  #
    r3 = [r0+0]
    r1 = 1
    call r3
    r9 = r0
    if (r0 == 0) goto L0200150c
L020014f2:
    if (r12 == 0) goto L0200145e
    r0 = [r12+28]
    r0 = r12  #
    r3 = [r0+0]
    r1 = 3
    r2 = 0
    call r3
    r0 = 1
    b[r12+0] = r0
    goto L0200145e
L0200150c:
    r0 = 1
    b[r5+0] = r0
    r0 = r5 + 16
    call phase3_p3_list_del
    r1 = [r10+164]
    r9 = 0  #
    [r1+4] = r0
    r1 = r10 + 164  #
    [r5+16] = r1
    [r5+20] = r1
    [r10+164] = r0
    goto L0200145e
