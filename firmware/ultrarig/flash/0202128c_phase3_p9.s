; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 6 functions, 0x0202128c..0x020213d6

; phase3_p9_sdfile_open: 0x0202128c..0x02021314, module phase3-p9 (sdfile_open)
.type phase3_p9_sdfile_open,@function
phase3_p9_sdfile_open:
    [--sp] = {rets, r8-r4}
    r6 = r1
    r4 = r0
    if (r6 == 0) goto L020212e6
    r0 = 40
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L0202130e
    r0 = 0
    r1 = r5
    rep 10 {
    [r1++=4] = r0
    }
    r8 = L0203590a  ; "res"
    r1 = r8 + 4  #
    r0 = [r4+8]
    r7 = r0 + 18
    r0 = r7
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020212ec
    r0 = r7
    r1 = r8
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020212f6
    r1 = r8 + 1835
    r0 = r7
    call L02028308  ; @call.xl
    r7 = 0
    if (r0 != 0) goto L02021302
    r0 = r5
    r1 = r6
    call L020211d8
    goto L020212fe
L020212e6:
    r7 = -254
    goto L02021310
L020212ec:
    r0 = r5
    r1 = r6
    call L02021060
    goto L020212fe
L020212f6:
    r0 = r5
    r1 = r6
    call L02021174
L020212fe:
    r7 = r0
    if (r7 == 0) goto L0202130c
L02021302:
    r0 = r5
    call L0203d218  ; @call.xl
    goto L02021310
L0202130c:
    [r4+12] = r5
L0202130e:
    r7 = 0
L02021310:
    r0 = r7
    {pc, r8-r4} = [sp++]

; phase3_p9_sdfile_read: 0x02021314..0x0202133e, module phase3-p9 (sdfile_read)
.type phase3_p9_sdfile_read,@function
phase3_p9_sdfile_read:
    [--sp] = {rets, r5, r4}
    r4 = 0
    if (r0 == 0) goto L0202133a
    r5 = [r0+12]
    if (r5 == 0) goto L0202133a
    r0 = [r5+0]
    r3 = [r5+8]
    r3 += r0  #  ; @add.rr.p
    r4 = [r5+12]
    r0 = r4 - r0
    r4 = umin(r0, r2)
    r0 = r1
    r1 = r3
    r2 = r4
    call phase3_p8_memcpy_flash
    [r5+0] += r4
L0202133a:
    r0 = r4
    {pc, r5, r4} = [sp++]

; phase3_p9_sdfile_write: 0x0202133e..0x02021398, module phase3-p9 (sdfile_write)
.type phase3_p9_sdfile_write,@function
phase3_p9_sdfile_write:
    [--sp] = {rets, r7-r4}
    r4 = r1
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L02021396
    r7 = [r1+12]
    if (r7 == 0) goto L02021396
    r0 = [r7+0]
    r1 = [r7+12]
    r1 = r1 - r0  #
    r3 = [r7+8]
    r5 = umin(r1, r2)
    r0 += r3  ; @add.rr
    call phase3_p8_sdfile_cpu_addr2flash_addr
    r6 = r0
    call phase3_p8_sdfile_flash_addr2cpu_addr
    r1 = 0
L02021366:
    if (r1 >= r5) goto L02021380
    r2 = b[r4+r1] (u)
    r3 = b[r0+r1] (u)
    r3 &= r2
    r1 += 1  ; @add.ri.u5
    if (r3 == r2) goto L02021366
    r0 = -250
    {pc, r7-r4} = [sp++]
L02021380:
    r0 = 0
    r1 = r4
    r2 = r5
    r3 = r6
    call storage_control_program
    if (r0 == r5) {
    [r7+0] += r5
    r0 = r5
    }
L02021396:
    {pc, r7-r4} = [sp++]

; phase3_p9_sdfile_seek: 0x02021398..0x020213ba, module phase3-p9 (sdfile_seek)
.type phase3_p9_sdfile_seek,@function
phase3_p9_sdfile_seek:
    if (r0 == 0) goto L020213b6
    r0 = [r0+12]
    if (r0 == 0) goto L020213b6
    if (r2 == 2) goto L020213aa
    if (r2 == 1) goto L020213b2
    if (r2 == 0) goto L020213ae
    goto L020213b6
L020213aa:
    r2 = [r0+12]
    r1 = r2 - r1
L020213ae:
    [r0+0] = r1
    goto L020213b6
L020213b2:
    [r0+0] += r1
L020213b6:
    r0 = 0
    rts

; phase3_p9_sdfile_len: 0x020213ba..0x020213c8, module phase3-p9 (sdfile_len)
.type phase3_p9_sdfile_len,@function
phase3_p9_sdfile_len:
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L020213c6
    r1 = [r1+12]
    if (r1 == 0) goto L020213c6
    r0 = [r1+12]
L020213c6:
    rts

; phase3_p9_sdfile_pos: 0x020213c8..0x020213d6, module phase3-p9 (sdfile_pos)
.type phase3_p9_sdfile_pos,@function
phase3_p9_sdfile_pos:
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L020213d4
    r1 = [r1+12]
    if (r1 == 0) goto L020213d4
    r0 = [r1+0]
L020213d4:
    rts
