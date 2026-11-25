; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020215ca..0x02021d9e: vendor code (JieLi SDK or library, not reversed), as instructions
L020215ca:
    [--sp] = {rets, r6-r4}
    r3 = r0
    r0 = 0
    r4 = 0
    goto L020215f6
L020215d4:
    r6 = b[r3+r4] (u)
    r5 = b[r1+r4] (u)
    if (r6 == 0) goto L020215fc
    if (r5 == 0) goto L020215fe
    if (r6 == 42) goto L020215f4
    if (r6 == 63) goto L020215f4
    if (r5 == 42) goto L020215f4
    if (r6 == r5) goto L020215f4
    if (r5 != 63) goto L020215fe
L020215f4:
    r4 += 1  ; @add.ri.u5
L020215f6:
    if (r2 != r4) goto L020215d4
    {pc, r6-r4} = [sp++]
L020215fc:
    if (r5 == 0) goto L02021602
L020215fe:
    r0 = r4 + 1
    {pc, r6-r4} = [sp++]
L02021602:
    {pc, r6-r4} = [sp++]
L02021604:
    [--sp] = {rets, r6-r4}
    sp += -8
    r6 = r1
    r4 = r0
    r5 = sp + 2
    r2 = 3
    r0 = r5
    call phase3_p8_memcpy_flash
    r1 = 3
    r0 = r5
    call phase3_p9_sdfile_str_to_upper
    r5 = 0
    if (r4 == 0) goto L0202164a
    if (r6 == 0) goto L0202164a
L02021624:
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0202164a
    r6 = sp + 5
    r2 = 3
    r0 = r6
    r1 = r4
    call phase3_p8_memcpy_flash
    r1 = 3
    r0 = r6
    call phase3_p9_sdfile_str_to_upper
    r0 = sp + 2
    r2 = 3
    r1 = r6
    call L020215ca
    r4 += 3  ; @add.ri.u5
    if (r0 != 0) goto L02021624
    r5 = 1
L0202164a:
    r0 = r5
    sp += 8
    {pc, r6-r4} = [sp++]
L02021650:
    [--sp] = {rets, r12-r4}
    sp += -32
    r4 = r3
    r9 = r2
    r8 = r1
    r7 = r0
    r11_r10 = d[sp+72]
    r6 = sp + 0
    r5 = r6 + 16
    r12 = 0
    goto L020216da
L02021668:
    r0 = h[r6+14] (u)
    if (r0 == 0) goto L020216da
L0202166c:
    r0 = 0
    if (r8 == 0) goto L02021722
    r1 = b[r7+4] (u)
    if (r1 != 2) goto L02021722
    r0 = b[r7+3] (u)
    r0 = r0 * 0xC
    r0 += r7  ; @add.rr
    r0 += 64
    call phase3_p9_sdf_opendir
    r0 = b[r7+3] (u)
    if (r0 != 0) goto L020216b4
    r0 = 0
    goto L02021690
L0202168e:
    r0 = b[r7+3] (u)
L02021690:
    r0 = r0.b0 (u)
    r0 = r0 * 0xC
    r0 += r7  ; @add.rr
    r0 += 64
    r1 = sp + 0
    call L020214b6
    if (r0 != 0) goto L020216b0
    r0 = b[r6+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 3) goto L020216ba
    r0 = h[r6+14] (u)
    if (r0 == 0) goto L0202168e
L020216b0:
    r0 = b[r7+3] (u)
    if (r0 == 0) goto L02021720
L020216b4:
    r0 += -1
    b[r7+3] = r0
    goto L02021690
L020216ba:
    h[r7+16] = r12
    r0 = h[r7+8] (u)
    h[r7+18] = r0
    r0 = b[r7+3] (u)
    r0 += 1  ; @add.ri.u5
    r0 = r0.b0 (u)  #
    b[r7+3] = r0
    r0 = r0 * 0xC  #
    r1 = [r6+4]
    r0 += r7  ; @add.rr
    [++r0=64] = r1
    call phase3_p9_sdf_opendir
L020216da:
    r0 = b[r7+3] (u)
    r0 = r0 * 0xC
    r0 += r7  ; @add.rr
    r0 += 64
    r1 = sp + 0
    call L020214b6
    if (r0 != 0) goto L0202166c
    r0 = b[r6+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 2) goto L02021700
    if (r0 != 3) goto L02021668
    if ((r4 & 16) == 0) goto L02021668
    goto L02021716
L02021700:
    r1 = 46
    r0 = r5
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L02021668
    r1 = r0 + 1
    r0 = r9
    call L02021604
    if (r0 == 0) goto L02021668
L02021716:
    r1 = sp + 0
    r0 = r11
    call r10
    if (r0 == 0) goto L02021668
    goto L02021722
L02021720:
    r0 = 0
L02021722:
    sp += 32
    {pc, r12-r4} = [sp++]
L02021726:
    [--sp] = {rets, r9-r4}
    sp += -8
    r7 = r0
    r9 = r1  #
    r0 = b[r7+5] (u)
    if (r0 == 110) goto L02021738
    r4 = -22
    if (r0 != 0) goto L02021794
L02021738:
    r6 = b[r7+3] (u)
    r0 = 88
    call L0203d940  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02021792
    r8 = r7 + 68
    r1 = [r8+20]
    r4 = -14
    if (r1 == 0) goto L02021794
    r6 = r6 & 0xFFFFFF10
    call phase3_p9_sdf_dir_init
    r1 = r9  #
    r0 = b[r7+1] (u)
    b[r5+0] = r0
    r0 = r7 + 6
    r0 = r5 + 64  #
    [r5+28] = r0
    b[r5+2] = r6
    call phase3_p9_sdf_opendir_by_name
    if (r0 != 0) goto L02021788
    r3 = b[r5+2] (u)
    r2 = [r5+28]
    r1 = b[r5+0] (u)
    [sp+4] = r5
    r0 = phase3_p10_sdf_store_number_new
    r0 = r5  #
    [sp] = r0
    call L02021650
    if (r0 == 0) goto L0202179a
L02021788:
    r0 = r5
    call L0203d218  ; @call.xl
    goto L02021794
L02021792:
    r4 = -12
L02021794:
    r0 = r4
    sp += 8
    {pc, r9-r4} = [sp++]
L0202179a:
    r0 = h[r5+8] (u)
    h[r5+12] = r0
    h[r5+14] = r0
    [r8+12] = r5
    h[r8+0] = r0
    r4 = 0
    goto L02021794
L020217ac:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = [++r4=80]
    if (r0 == 0) goto L020217c0
    call L0203d218  ; @call.xl
    [r4+0] = 0x0
L020217c0:
    {pc, r4} = [sp++]
L020217c2:
    [--sp] = rets
    r2 = 0
    r3 = r0 + 32  #
    [r1++=4] = r2
    r2 = 32
    r0 = r1
    r1 = r3
    call phase3_p8_memcpy_flash
    pc = [sp++]
L020217d8:
    [--sp] = {rets, r5, r4}
    sp += -96
    r1 = r0
    r5 = sp + 8
    r2 = 88
    r0 = r5
    call phase3_p8_memcpy_flash
    r4 = 0
    h[sp+16] = r4
    r0 = b[sp+11] (u)
    r0 = r0 * 0xC
    r0 += r5  ; @add.rr
    r0 += 64
    call phase3_p9_sdf_opendir
    r3 = b[sp+10] (u)
    r2 = [sp+36]
    [sp+4] = r5
    r0 = phase3_p10_sdf_seach_total_new
    r1 = 0
    r0 = r5  #
    [sp] = r0
    call L02021650
    if (r0 != 0) goto L0202181c
    r4 = h[sp+16] (u)
L0202181c:
    r0 = r4
    sp += 96
    {pc, r5, r4} = [sp++]
L02021822:
    [--sp] = {rets, r13-r4}
    sp += -8
    r10 = r0
    r7 = [r0+80]
    r4 = r3
    r8 = r2
    r6 = r1
    r0 = 40
    call L0203d940  ; @call.xl
    r9 = r0
    if (r0 == 0) goto L02021868
    r0 = b[r10+4] (u)
    b[r7+1] = r0
    r2 = h[r7+12] (u)
    if (r2 == 0) goto L02021964
    r11 = 1
    if (r0 != 3) goto L0202186c
    r1 = h[r7+16] (u)
    if (r1 == 0) goto L0202186c
    r12 = r2  #
    r3 = h[r7+18] (u)
    r1 += r3  ; @add.rr
    if (r1 <= r2) {
    r11 = r3 + 1
    r12 = r1
    }
    goto L0202186e
L02021868:
    r5 = -12
    goto L02021a16
L0202186c:
    r12 = r2
L0202186e:
    r5 = -22
    if (r6 > 7) goto L02021966
    r3 = 80640
    tbb [r6]
L0202187c:
    .byte (L02021884 - L0202187c) / 2, (L02021892 - L0202187c) / 2, (L0202189c - L0202187c) / 2, (L020218a2 - L0202187c) / 2, (L02021966 - L0202187c) / 2, (L0202198e - L0202187c) / 2, (L020218c8 - L0202187c) / 2, (L02021912 - L0202187c) / 2
L02021884:
    r1 = 0
    r13 = r7 + 10  #
    h[r7+10] = r1
    h[r7+14] = r2
    r4 = 1
    goto L0202199c
L02021892:
    r0 = 0
    r4 = r2  #
    h[r7+10] = r0
    h[r7+14] = r2
    goto L0202198e
L0202189c:
    r4 = h[r7+10] (u)
    if (r4 != 0) goto L02021920
    goto L02021966
L020218a2:
    r1 = h[r7+10] (u)
    if (r1 == 0) goto L02021966
    if (r0 != 4) goto L02021970
    r3 = 0x1 - r11  #
    r0 = [r3+0]
    r3 += r12  #
    h[r7+14] = r2
    r4 = r0 / r3 (u)
    r3 *= r4
    r0 = r0 - r3
    r0 += r11
    r4 = r1 + 1
    if (r0 != r1) {
    r4 = r0
    }
    goto L02021978
L020218c8:
    r0 = 0
    b[r7+3] = r0
    h[r7+10] = r0
    h[r7+8] = r0
    [r7+20] = r4
    r0 = r7 + 64  #
    [r7+16] = r0
    call phase3_p9_sdf_opendir
    r3 = b[r7+2] (u)
    r2 = [r7+28]
    r1 = b[r7+0] (u)
    [sp+4] = r7
    r0 = L02021d5e
    r0 = r7  #
    [sp] = r0
    call L02021650
    if (r0 != 1) goto L02021966
    r0 = r7
    r1 = r9
    call L020217c2
    r4 = h[r7+8] (u)
    h[r7+10] = r4
    r0 = h[r7+16] (u)
    if (r0 != 0) goto L0202198e
    r0 = r7
    call L020217d8
    h[r7+16] = r0
    r4 = h[r7+10] (u)
    goto L0202198e
L02021912:
    r13 = r7
    r4 = h[++r13=10] (u)
    if (r4 == 0) goto L02021966
    r1 = r4
    if (r0 == 2) goto L0202199c
L02021920:
    if (r0 != 4) goto L02021942
    r2 = 0x1 - r11  #
    r1 = [r3+0]
    r2 += r12
    r3 = r1 / r2 (u)
    r2 *= r3
    r1 = r1 - r2
    r2 = r1 + r11
    r1 = r4 + 1
    if (r2 != r4) {
    r1 = r2
    }
    goto L02021944
L02021942:
    r1 = r4 + 1
L02021944:
    r2 = h[r7+14] (u)
    ifs (r1 <= r2) goto L02021954
    if (r0 == 0) goto L02021964
    r1 = r11
    if (r0 != 3) {  ; @if.ne.ri.s12
    r1 = 1
    }
L02021954:
    r4 = r11
    ifs (r1 > r12) goto L02021992
    r4 = r12
    ifs (r1 >= r11) {
    r4 = r1
    }
    goto L0202198e
L02021964:
    r5 = -2
L02021966:
    r0 = r9
    call L0203d218  ; @call.xl
    goto L02021a16
L02021970:
    r4 = r1 + -1  #
    h[r7+14] = r2
    if (r0 == 0) goto L0202198e
L02021978:
    ifs (r4 <= r12) goto L02021984
    r13 = r7 + 10
    r4 = r11
    goto L0202199c
L02021984:
    r0 = r12
    ifs (r4 >= r11) {
    r0 = r4
    }
    r4 = r0
L0202198e:
    r5 = -2
    if (r4 == 0) goto L02021966
L02021992:
    if (r6 == 6) goto L02021a0a
    r13 = r7
    r1 = h[++r13=10] (u)
L0202199c:
    ifs (r4 >= r11) {
    r11 = smin(r4, r12)
    }
    if (r1 != r11) goto L020219b2
    r0 = r7
    r1 = r9
    call L020217c2
    goto L02021a0a
L020219b2:
    if (r1 == 0) goto L020219bc
    ifs (r1 >= r11) goto L020219bc
    h[r7+8] = r1
    goto L020219ce
L020219bc:
    r0 = 0
    b[r7+3] = r0
    h[r7+8] = r0
    h[r7+16] = r0
    r0 = r7 + 64  #
    h[r7+18] = r0
    call phase3_p9_sdf_opendir
L020219ce:
    h[r13+0] = r11
    r3 = b[r7+2] (u)
    r2 = [r7+28]
    r1 = b[r7+0] (u)
    [sp+4] = r7
    r0 = L02021d7e
    r0 = r7  #
    [sp] = r0
    call L02021650
    r5 = -254
    if (r0 != 1) goto L02021966
    r0 = r7
    r1 = r9
    call L020217c2
    r0 = h[r7+8] (u)
    h[r13+0] = r0
    r0 = h[r7+16] (u)
    if (r0 != 0) goto L02021a0a
    r0 = r7
    call L020217d8
    h[r7+16] = r0
L02021a0a:
    r0 = h[r7+10] (u)
    h[r10+70] = r0
    [r8+12] = r9
    r5 = 0
L02021a16:
    r0 = r5
    sp += 8
    {pc, r13-r4} = [sp++]
L02021a1c:
    r0 = [r0+12]
    r0 = b[r0+16] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 3) {  ; @if.eq.ri.s12
    [r1+0] |= 0x10
    }
    r0 = 0
    rts
L02021a32:
    if (r0 == 0) goto L02021a52
    r0 = [r0+12]
    if (r0 == 0) goto L02021a52
    r2 = b[r0+16] (u)
    r2 = r2 & 0xFFFFFF0F
    if (r2 == 3) {  ; @if.eq.ri.s12
    r2 = b[r1+0] (u)
    r2 |= 16
    b[r1+0] = r2
    }
    r2 = [r0+12]
    [r1+4] = r2
    r0 = [r0+8]
    [r1+8] = r0
L02021a52:
    r0 = 0
    rts
L02021a56:
    [--sp] = {rets, r15-r4}
    sp += -100
    r8 = r2
    r6 = r0
    r0 = r1 + -5
    r5 = -1
    if (r0 > 7) goto L02021d46
    r1 = r0 << 1
    tbh [r1]
L02021a6e:
    .short (L02021a7e - L02021a6e) / 2, (L02021d46 - L02021a6e) / 2, (L02021d46 - L02021a6e) / 2, (L02021a96 - L02021a6e) / 2, (L02021a9a - L02021a6e) / 2, (L02021d46 - L02021a6e) / 2, (L02021afe - L02021a6e) / 2, (L02021b94 - L02021a6e) / 2
L02021a7e:
    r0 = [r6+80]
    r5 = 0
    if (r0 == 0) goto L02021d46
    r1 = h[r0+18] (u)
    r1 += 1  ; @add.ri.u5
    h[r2+0] = r1
    r0 = h[r0+16] (u)
    h[r2+2] = r0
    goto L02021d46
L02021a96:
    [r6+36] = r2
    goto L02021d44
L02021a9a:
    r7 = [r6+12]
    r4 = [r6+8]
    if (r7 != 0) goto L02021abc
    r0 = 128
    call L0203d940  ; @call.xl
    r7 = r0
    if (r7 == 0) goto L02021c6a
    r0 = r7 + 40
    r1 = r4  #
    [r7+36] = r0
    call phase3_p9_sdf_dir_init
    [r6+12] = r7
L02021abc:
    r6 = [r7+36]
    if (r6 == 0) goto L02021d46
    r0 = [r8+4]
    r9 = [r4+36]
    if (r0 == 0) goto L02021bea
    r2 = h[r0+4] (u)
    r1 = 0
    if (r2 != 0) goto L02021c64
    r1 = b[r6+3] (u)
    r2 = r1 * 0xC
    r2 += r6  ; @add.rr
    r7 = r2 + 64
    if (r1 != 0) goto L02021c04
    r0 = [r0+0]
    if (r0 == 0) goto L02021d4c
    r1 = 1
    b[r6+3] = r1
    r1 = 0
    h[r6+16] = r1
    [++r7=12] = r0
    goto L02021c04
L02021afe:
    r0 = [r6+12]
    if (r0 == 0) goto L02021d46
    r7 = [r0+36]
    if (r7 == 0) goto L02021d46
    r0 = b[r7+3] (u)
    r5 = 0
    r1 = 0
    if (r0 == 0) goto L02021b8e
    r1 = [r6+8]
    r9 = [r1+36]
    r0 += -1
    r0 = r0.b0 (u)  #
    b[r7+3] = r0
    r1 = 0
    r0 = r0 * 0xC  #
    h[r7+6] = r1
    r0 += r7  #  ; @add.rr.p
    h[r7+8] = r1
    r4 = r0 + 64  #
    h[r7+10] = r1
    r0 = r4
    call phase3_p9_sdf_opendir
    r6 = sp + 36
    r10 = r6 + 16
    goto L02021b7a
L02021b42:
    r0 = b[r6+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 2) goto L02021b5c
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = h[r7+6] (u)
    r0 += 1  ; @add.ri.u5
    h[r7+6] = r0
    }
L02021b56:
    r0 = h[r6+14] (u)
    if (r0 == 0) goto L02021b7a
    goto L02021b84
L02021b5c:
    r1 = 46
    r0 = r10
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L02021b56
    r1 = r0 + 1
    r0 = r9
    call L02021604
    if (r0 == 0) goto L02021b56
    r0 = h[r7+8] (u)
    r0 += 1  ; @add.ri.u5
    h[r7+8] = r0
    goto L02021b56
L02021b7a:
    r1 = sp + 36
    r0 = r4
    call L020214b6
    if (r0 == 0) goto L02021b42
L02021b84:
    r0 = h[r7+8] (u)
    r1 = h[r7+6] (u)
    r0 += r1  ; @add.rr
    r1 = r0.l (u)  #
    h[r7+16] = r0
L02021b8e:
    [r8+0] = r1
    goto L02021d46
L02021b94:
    r0 = [r6+12]
    if (r0 == 0) goto L02021d46
    r9 = [r0+36]
    if (r9 == 0) goto L02021d46
    r0 = [r6+8]
    r12 = [r0+36]
    r6 = [r2+12]
    r0 = b[r9+3] (u)
    r0 = r0 * 0xC  #
    r1 = [r2+8]
    r0 += r9  #
    [sp] = r1
    r4 = h[r9+10] (u)
    r13 = [r2+4]
    r11 = r0 + 64
    if (r4 == 0) goto L02021c72
    r0 = h[r9+6] (u)
    if (r0 >= r13) goto L02021c6e
    r5 = 0
    r1 = 1
    if (r4 >= r13) {
    r1 = 0
    }
    if (r4 <= r0) goto L02021bde
    if (r1 != 0) goto L02021cd6
L02021bde:
    r0 = r11
    call phase3_p9_sdf_opendir
    r4 = h[r9+6] (u)
    goto L02021cd6
L02021bea:
    r0 = 0
    b[r6+3] = r0
    [r6+72] = r0
    r1 = 0
    d[r6+64] = r1_r0
    r0 = r6
    r1 = r4
    call phase3_p9_sdf_dir_init
    r7 = r6 + 64
L02021c04:
    r0 = 0
    h[r6+6] = r0
    h[r6+8] = r0
    r0 = r7  #
    h[r6+10] = r0
    call phase3_p9_sdf_opendir
    r5 = sp + 4
    r4 = r5 + 16
    goto L02021c50
L02021c18:
    r0 = b[r5+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 2) goto L02021c32
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = h[r6+6] (u)
    r0 += 1  ; @add.ri.u5
    h[r6+6] = r0
    }
L02021c2c:
    r0 = h[r5+14] (u)
    if (r0 == 0) goto L02021c50
    goto L02021c5a
L02021c32:
    r1 = 46
    r0 = r4
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L02021c2c
    r1 = r0 + 1
    r0 = r9
    call L02021604
    if (r0 == 0) goto L02021c2c
    r0 = h[r6+8] (u)
    r0 += 1  ; @add.ri.u5
    h[r6+8] = r0
    goto L02021c2c
L02021c50:
    r1 = sp + 4
    r0 = r7
    call L020214b6
    if (r0 == 0) goto L02021c18
L02021c5a:
    r0 = h[r6+8] (u)
    r1 = h[r6+6] (u)
    r0 += r1  ; @add.rr
    r1 = r0.l (u)  #
    h[r6+16] = r0
L02021c64:
    [r8+0] = r1
    goto L02021d44
L02021c6a:
    r5 = -12
    goto L02021d46
L02021c6e:
    if (r4 < r13) goto L02021c7a
L02021c72:
    r0 = r11
    call phase3_p9_sdf_opendir
    r4 = 0
L02021c7a:
    r7 = sp + 68
    r14 = r7 + 16
    r15 = 0
    r5 = 0
L02021c84:
    r1 = sp + 68
    r0 = r11
    call L020214b6
    if (r0 != 0) goto L02021ccc
    r0 = b[r7+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 != 3) goto L02021cc8
    r4 += 1  ; @add.ri.u5
    if (r4 < r13) goto L02021cc8
    r0 = r5 * 0x20C
    r10 = r6 + r0
    h[r10+6] = r15
    r0 = r10 + 10
    r2 = 16
    r1 = r14
    call phase3_p8_memcpy_flash
    r0 = [r7+4]
    [r10+0] = r0
    r5 += 1  ; @add.ri.u5
    h[r10+4] = r15
    r0 = [sp]
    if (r5 >= r0) goto L02021d3c
L02021cc8:
    r0 = h[r7+14] (u)
    if (r0 == 0) goto L02021c84
L02021ccc:
    h[r9+10] = r4
    r0 = r11
    call phase3_p9_sdf_opendir
L02021cd6:
    r7 = sp + 68
    r14 = r7 + 16
    r15 = 1
L02021ce0:
    r1 = sp + 68
    r0 = r11
    call L020214b6
    if (r0 != 0) goto L02021d3c
    r0 = b[r7+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 != 2) goto L02021d38
    r1 = 46
    r0 = r14
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L02021d38
    r1 = r0 + 1
    r0 = r12
    call L02021604
    if (r0 == 0) goto L02021d38
    r4 += 1  ; @add.ri.u5
    if (r4 < r13) goto L02021d38
    r0 = r5 * 0x20C
    r10 = r6
    r6 += r0  ; @add.rr
    r0 = 0
    r1 = r14  #
    h[r6+6] = r0
    r0 = r6 + 10
    r2 = 16
    call phase3_p8_memcpy_flash
    r0 = [r7+4]
    [r6+0] = r0
    r5 += 1  ; @add.ri.u5
    h[r6+4] = r15
    r6 = r10  #
    r0 = [sp]
    if (r5 >= r0) goto L02021d3c
L02021d38:
    r0 = h[r7+14] (u)
    if (r0 == 0) goto L02021ce0
L02021d3c:
    h[r9+10] = r4
    [r8+0] = r5
L02021d44:
    r5 = 0
L02021d46:
    r0 = r5
    sp += 100
    {pc, r15-r4} = [sp++]
L02021d4c:
    r0 = 0
    r1 = r7
    rep 6 {
    [r1++=4] = r0
    }
    r0 = r6
    r1 = r4
    call phase3_p9_sdf_dir_init
    goto L02021c04
L02021d5e:
    [--sp] = {rets, r4}
    r2 = h[r0+8] (u)
    r2 += 1  ; @add.ri.u5
    h[r0+8] = r2
    r3 = [r0+20]
    r4 = [r1+4]
    r2 = 0
    if (r4 != r3) goto L02021d7a
    r0 += 32
    r2 = 32
    call phase3_p8_memcpy_flash
    r2 = 1
L02021d7a:
    r0 = r2
    {pc, r4} = [sp++]
L02021d7e:
    [--sp] = {rets, r4}
    r2 = h[r0+8] (u)
    r2 += 1  ; @add.ri.u5
    r4 = r2.l (u)  #
    h[r0+8] = r2
    r3 = h[r0+10] (u)
    r2 = 0
    if (r4 != r3) goto L02021d9a
    r0 += 32
    r2 = 32
    call phase3_p8_memcpy_flash
    r2 = 1
L02021d9a:
    r0 = r2
    {pc, r4} = [sp++]
