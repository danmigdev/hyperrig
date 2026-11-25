; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; butterworth_table: 2 functions, 0x020021c0..0x020024ec

; butterworth_table_fixed_round: 0x020021c0..0x02002202, module butterworth-table (fixed_round)
.type butterworth_table_fixed_round,@function
butterworth_table_fixed_round:
    [--sp] = {rets, r7-r4}
    r6 = r1
    r7 = r0
    call L02033872  ; @call.xl
    r5_r4 = r1_r0
    r3_r2 = 0
    r0 = r7
    r1 = r6
    call L0203306a  ; @call.xl
    ifs (r0 <= -1) {  ; @ifs.le.ri.s12
    r6 = 0
    r7 = 3219128320
    } else {
    r6 = 0
    r7 = 1071644672
    }
    r2 = 0
    r1_r0 = r5_r4
    r3 = r7
    call L02032cda  ; @call.xl
    call L02033776  ; @call.xl
    {pc, r7-r4} = [sp++]

; butterworth_table_butterworth_table: 0x02002202..0x020024ec, module butterworth-table (butterworth_table)
.type butterworth_table_butterworth_table,@function
butterworth_table_butterworth_table:
    [--sp] = {rets, r15-r4}
    sp += -92
    r2 = r0
    if (r2 == 0) goto L02002258
    r1 = r2 + -20
    r0 = -1
    if (r1 > 100) goto L020024e8
    r1 = 5
    r1 = r2 / r1 (u)
    r1 = r1 * 0x5
    r1 = r2 - r1
    if (r1 != 0) goto L020024e8
    r1 = 2016
    r0 = L01c21cb8
    r1 = b[r0+r1] (u)
    if (r1 == 0) goto L02002262
    r1 = 746
    r0 = h[r0+r1<<1] (u)
    r4 = r2
    call L02033816  ; @call.xl
    r3 = 1068498944
    r2 = 0
    call L02033872  ; @call.xl
    goto L0200226c
L02002258:
    r0 = 0
    r1 = 0
    d[sp+16] = r1_r0
    goto L02002274
L02002262:
    r0 = r2
    r4 = r2
    call L020337ca  ; @call.xl
L0200226c:
    r2 = r4
    d[sp+16] = r1_r0
    r0 = 1
L02002274:
    r3 = L01c26890
    r1 = 12976
    r1 += r3  ; @add.rr
    [r1+0] += 1  ; @rmw.add.s12
    [sp+4] = r2
    [sp] = r1
    [r1+4] = r2
    if (r0 == 0) goto L020024d8
    r0 = [sp+4]
    call L020337ca  ; @call.xl
    d[sp+32] = r1_r0
    r3_r2 = d[sp+16]
    call L020331ce  ; @call.xl
    d[sp+8] = r1_r0
    r0 = sp + 76
    [sp+28] = r0
    r0 = sp + 84
    [sp+24] = r0
    r0 = 0
    goto L020024d2
L020022b6:
    [sp+52] = r0
    r4 = r0 + 1
    r1_r0 = d[sp+32]
    if (r4 == 64) goto L020022f0
    r0 = r4
    call L02033816  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = d[sp+8]
    call L02033872  ; @call.xl
    r2 = 0
    r3 = 1066401792
    call L02033872  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = d[sp+16]
    call L02032cda  ; @call.xl
L020022f0:
    [sp+48] = r4
    d[sp+40] = r1_r0
    r2 = 1413754136
    r3 = 1074340347
    call L02033872  ; @call.xl
    r2 = 0
    r6 = 0
    r3 = 1088911776
    call L02033466  ; @call.xl
    r5_r4 = r1_r0
    r3_r2 = r5_r4
    call L02033872  ; @call.xl
    r9_r8 = r1_r0
    r2 = 2284589306
    r3 = 1066820852
    call L02033872  ; @call.xl
    r2 = 463583772
    r3 = 1068212666
    call L02032cda  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r9_r8
    call L02033872  ; @call.xl
    r2 = 0x11111111
    r3 = 1069617425
    call L02032cda  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r9_r8
    call L02033872  ; @call.xl
    r2 = 0x55555555
    r3 = 1070945621
    call L02032cda  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r9_r8
    call L02033872  ; @call.xl
    r2 = 0
    r7 = 1072693248
    r3 = r7
    call L02032cda  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r5_r4
    call L02033872  ; @call.xl
    r3_r2 = r1_r0
    d[sp+64] = r1_r0
    call L02033872  ; @call.xl
    r11_r10 = r1_r0
    r0 = 0
    r1 = r7
    r3_r2 = r11_r10
    call L020331ce  ; @call.xl
    r3_r2 = r1_r0
    call L02032cda  ; @call.xl
    d[sp+56] = r1_r0
    r8 = 0
    r9 = r7
    r7 = L0203a244
    goto L02002464
L020023d2:
    r3_r2 = d[r7++=8]
    r1_r0 = d[sp+64]
    call L02033466  ; @call.xl
    r5_r4 = r1_r0
    r2 = 0
    r12 = 1072693248
    r3 = r12
    call L02032cda  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r11_r10
    call L02032cda  ; @call.xl
    r3_r2 = r1_r0
    r0 = 0
    r1 = r12
    call L02033466  ; @call.xl
    r15_r14 = r1_r0
    r1_r0 = d[sp+56]
    r3_r2 = r15_r14
    call L02033872  ; @call.xl
    r2 = 0
    r13 = r12 + 0x1E00000
    r3 = r13
    call butterworth_table_fixed_round
    r1 = sp + 84
    [r1+r6<<2] = r0
    r0 = 0
    r1 = r12
    r3_r2 = r5_r4
    call L020331ce  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r11_r10
    call L02032cda  ; @call.xl
    r3_r2 = r15_r14
    call L02033872  ; @call.xl
    r1 ^= 2147483648
    r2 = 0
    r3 = r13
    call butterworth_table_fixed_round
    r1 = sp + 76
    [r1+r6<<2] = r0
    r1_r0 = r9_r8
    r3_r2 = r15_r14
    call L02033872  ; @call.xl
    r9_r8 = r1_r0
    r6 += 1  ; @add.ri.u5
L02002464:
    if (r6 != 2) goto L020023d2
    r7 = 12984  #
    r6 = [sp+52]
    r0 = r6 * 0x14  #
    r1 = [sp+76]
    r5 = L01c26890
    r4 = r0 + r5  #
    r0 = [sp+84]
    r3_r2 = d[sp+24]
    r2 = [r2+4]
    r3 = [r3+4]
    [++r4=r7] = r0
    r1_r0 = r9_r8  #
    [r4+4] = r1
    d[r4+8] = r3_r2
    r2 = 0
    r3 = 1105199104
    call butterworth_table_fixed_round
    [r4+16] = r0
    r2 = 0
    r1_r0 = d[sp+40]
    r3 = 1076887552
    call L02033872  ; @call.xl
    r2 = 0
    r3 = 1071644672
    call L02032cda  ; @call.xl
    call L02033776  ; @call.xl
    r1 = 14264
    r1 += r5  ; @add.rr
    h[r1+r6<<1] = r0
    r0 = [sp+48]
L020024d2:
    if (r0 != 64) goto L020022b6  ; @bne.ri.l
L020024d8:
    r0 = [sp]
    [r0+0] += 1  ; @rmw.add.s12
    r0 = [sp+4]
    call slot_queries_type29_refresh  ; @call.xl
    r0 = 0
L020024e8:
    sp += 92
    {pc, r15-r4} = [sp++]
