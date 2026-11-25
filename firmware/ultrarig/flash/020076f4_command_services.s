; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; command_services: 1 function, 0x020076f4..0x0200777a

; command_services_record_header: 0x020076f4..0x0200777a, module command-services (record_header)
; HyperRig MINI, product option: a preset that uses more than four scenes is stored packed (mini/product/scenes.c).
.type command_services_record_header,@function
command_services_record_header:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r0 = 1363626836
    [r4+0] = r0
.if MINI_PRODUCT
    call hyperrig_pack  ; @call.xl
    r1 = r0
    r0 = hyperrig_packed  ; @li.u32
    if (r1 != 0) goto L02007742
    r0 = L01c24790
    r1 = r0 + 1484
.else
    r0 = L01c24790
    r1 = r0 + 1484
.endif
    r2 = 0
    goto L02007722
L0200770e:
    r3 = 0
    r5 = r1
L02007712:
    ifs (r3 > 2) goto L0200771e
    r6 = b[r5++=1] (u)
    r3 += 1  ; @add.ri.u5
    if (r6 == 0) goto L02007712
    goto L0200773e
L0200771e:
    r1 += 3  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L02007722:
    ifs (r2 <= 1) goto L0200770e
    r2 = 0
L02007728:
    ifs (r2 >= 6) goto L02007750
    r1 = r0 + 1424
    r3 = h[r1+r2<<1] (u)
    r2 += 1  ; @add.ri.u5
    r1 = 1484
    if (r3 == 0) goto L02007728
    goto L02007742
L0200773e:
    r1 = 1490
L02007742:
    [r4+4] = r1
    call preset_storage_checksum
    [r4+8] = r0
    [r4+12] = 0x0
    {pc, r7-r4} = [sp++]
L02007750:
    r2 = r0 + 1436
    r3 = 0
    goto L02007770
L02007758:
    r5 = 0
    r6 = r2
L0200775c:
    ifs (r5 > 5) goto L0200776c
    r1 = 1484  #
    r7 = h[r6++=2] (u)
    r5 += 1  ; @add.ri.u5
    if (r7 == 0) goto L0200775c
    goto L02007742
L0200776c:
    r2 += 12  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L02007770:
    ifs (r3 <= 3) goto L02007758
    r1 = 1424
    goto L02007742
