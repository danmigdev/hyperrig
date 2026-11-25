; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 5 functions, 0x0201c6ec..0x0201c816

; phase3_p13_sys_timeout_del: 0x0201c6ec..0x0201c6f2, module phase3-p13 (sys_timeout_del)
.type phase3_p13_sys_timeout_del,@function
phase3_p13_sys_timeout_del:
    [--sp] = rets
    call L0201c622
    pc = [sp++]

; phase3_p13_get_min_precesion: 0x0201c6f2..0x0201c76a, module phase3-p13 (get_min_precesion)
.type phase3_p13_get_min_precesion,@function
phase3_p13_get_min_precesion:
    [--sp] = {rets, r7-r4}
    r5 = 0
    r4 = 1000
    r6 = L01c26890
    goto L0201c736
L0201c702:
    r0 = r5 << 3
    r0 += r6  ; @add.rr
    r1 = r0 + 1876
    r0 = [r1+0]
    if (r0 != r1) goto L0201c714
    goto L0201c734
L0201c712:
    r0 = [r0+0]
L0201c714:
    if (r0 == r1) goto L0201c734
    r2 = b[r0+27] (u)
    if ((r2 & 1) != 0) goto L0201c712
    r7 = [r0+20]
    call L02041866  ; @call.xl
    r0 = r7 - r0
    ifs (r0 <= 1) {  ; @ifs.le.ri.s12
    r0 = 1
    }
    r4 = umin(r4, r0)
L0201c734:
    r5 += 1  ; @add.ri.u5
L0201c736:
    if (r5 != 2) goto L0201c702
    r5 = L01c1f22c
    r6 = r5
    goto L0201c760
L0201c744:
    r0 = b[r6+27] (u)
    if ((r0 & 1) != 0) goto L0201c760
    r7 = [r6+20]
    call L02041866  ; @call.xl
    r0 = r7 - r0
    ifs (r0 <= 1) {  ; @ifs.le.ri.s12
    r0 = 1
    }
    r4 = umin(r4, r0)
L0201c760:
    r6 = [r6+0]
    if (r6 != r5) goto L0201c744
    r0 = r4
    {pc, r7-r4} = [sp++]

; phase3_p13_list_add_tail: 0x0201c76a..0x0201c776, module phase3-p13 (list_add_tail)
.type phase3_p13_list_add_tail,@function
phase3_p13_list_add_tail:
    r2 = [r1+4]
    [r1+4] = r0
    [r0+] = {r2, r1}
    [r2+0] = r0
    rts

; phase3_p13_timer1_resume: 0x0201c776..0x0201c7e8, module phase3-p13 (timer1_resume)
.type phase3_p13_timer1_resume,@function
phase3_p13_timer1_resume:
    [--sp] = {rets, r12-r4}
    r0 = 1544
    r10 = L01c26890
    r0 = b[r10+r0] (u)
    if (r0 == 0) goto L0201c7e6
    r6 = 0
    r1 = 9
    r8 = 1548
    r12 = L02035912  ; "osc"
    r9 = 1000
    r5 = r12 + 7822
    r11 = 32509
L0201c7a2:
    r7 = r1
    if (r6 > 15) goto L0201c7d2
    r0 = b[r10+r8] (u)
    r4 = 2
    if (r0 != 0) goto L0201c7b2
    r4 = r0
L0201c7b2:
    r0 = r12
    call L020009ee
    r1 = [r5+r6<<2]
    r0 = r0 / r9 (s)
    r0 *= r4
    r0 = r0 / r1 (u)
    r2 = r0 + -257
    r1 = r7 + 16
    r6 += 1  ; @add.ri.u5
    if (r2 > r11) goto L0201c7a2
L0201c7d2:
    r1 = 385
    r1 = [r10+r1<<2]
    r2 = 66816
    [r2+4] = r1
    [r2+8] = r0
    [r2+0] = r7
L0201c7e6:
    {pc, r12-r4} = [sp++]

; phase3_p13_timer1_run: 0x0201c7e8..0x0201c816, module phase3-p13 (timer1_run)
.type phase3_p13_timer1_run,@function
phase3_p13_timer1_run:
    [--sp] = rets
    r1 = 1548
    r0 = L01c26890
    r1 = b[r0+r1] (u)
    if (r1 != 0) goto L0201c814
    r1 = 66816
    [r1+0] = 0x4000
    r1 = 1
    r0 = r0 + 1540
    b[r0+8] = r1
    b[r0+4] = r1
    [r0+0] = 0x0
    call phase3_p13_timer1_resume
L0201c814:
    pc = [sp++]
