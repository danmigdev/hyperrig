; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 1 function, 0x020225aa..0x02022654

; phase3_p10_sdfile_open_part_dir: 0x020225aa..0x02022654, module phase3-p10 (sdfile_open_part_dir)
.type phase3_p10_sdfile_open_part_dir,@function
phase3_p10_sdfile_open_part_dir:
    [--sp] = {rets, r11-r4}
    sp += -32
    r4 = r2
    r11 = r1
    r8 = r0
    r6 = L0203590a  ; "res"
    r1 = r6 + 2140
    r0 = r4
    call L02022514
    r7 = L01c26360
    if (r0 == 0) goto L020225e8
    r1 = r6 + 1835
    r0 = r4
    call L02022514
    if (r0 == 0) goto L020225e6
    r0 = r4
    r1 = r6
    call L02022514
    r1 = r0
    r0 = -255
    if (r1 != 0) goto L02022650
    r7 += 8  ; @add.ri.u5
    goto L020225e8
L020225e6:
    r7 += 4  ; @add.ri.u5
L020225e8:
    r0 = [r8+8]
    if (r0 == 0) goto L020225f8
    call L0202259a
    r6 = r0
    r9 = 1
    goto L020225fc
L020225f8:
    r9 = 0  #
    r6 = [r7+0]
L020225fc:
    r10 = r8 + 4
    r5 = sp + 0
    r7 = r5 + 16
    r4 = r5 | 0x2
L02022608:
    r0 = sp + 0
    r2 = 32
    r1 = r6
    call phase3_p10_sdfile_ext_read
    r1 = 30
    r0 = r4
    call L02001776
    r1 = h[sp] (u)
    if (r0 != r1) goto L02022634
    r0 = r7
    r1 = r11
    call L02022514
    if (r0 == 0) goto L0202263a
    r1 = h[r5+14] (u)
    r6 += 32
    if (r1 == 0) goto L02022608
    goto L02022650
L02022634:
    r0 = -251
    goto L02022650
L0202263a:
    r0 = sp + 0
    rep 8 {
    r1 = [r0++=4]
    [r10++=4] = r1
    }
    if (r9 == 0) {  ; @if.eq.ri.s12
    r6 = [sp+4]
    }
    [r8+8] = r6
    r0 = 0
L02022650:
    sp += 32
    {pc, r11-r4} = [sp++]
