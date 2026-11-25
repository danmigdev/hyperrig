; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tuner_and_control_records: 1 function, 0x0201779c..0x0201792a

; tuner_and_control_records_pitch_estimate: 0x0201779c..0x0201792a, module tuner-and-control-records (pitch_estimate)
.type tuner_and_control_records_pitch_estimate,@function
tuner_and_control_records_pitch_estimate:
    [--sp] = {rets, r15-r4}
    sp += -8
    r12 = r0
    r0 = r1 << 2
    r7 = L01c24790
    r8 = r0 + r7
    r0 = r8 + 1160
    r5 = 1039516303
    r6 = r1
    goto L020177c0
L020177bc:
    r0 += 4  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L020177c0:
    ifs (r6 >= r12) goto L020177e0
    r4 = [r0+-4]
    iff (r4 u>= r5) goto L020177bc
L020177ca:
    r10 = r6
    r6 += 1  ; @add.ri.u5
    r5 = r4
    ifs (r6 >= r12) goto L020177da
    r4 = [r0++=4]
    iff (r4 < r5) goto L020177ca
L020177da:
    ifs (r10 > -1) goto L02017828
    goto L020177e4
L020177e0:
    r10 = -1
L020177e4:
    r9 = r8 + 1156
    r8 = 289
    r0 = r1
    goto L02017808
L020177f0:
    r4 = r0 << 2
    r4 += r7  ; @add.rr
    r5 = [r4+r8<<2]
    r6 = [r9++=4]
    r4 = r1
    iff (r6 u>= r5) {
    r4 = r0
    }
    r1 += 1  ; @add.ri.u5
    r0 = r4
L02017808:
    ifs (r1 < r12) goto L020177f0
    r1 = r0 << 2
    r1 += r7  ; @add.rr
    r4 = r8
    r1 = [r1+r4<<2]
    r4 = 1050253722
    iff (r1 u>= r4) {
    r0 = r10
    }
    r10 = r0
    ifs (r0 < 0) goto L02017924
L02017828:
    d[sp] = r3_r2
    r0 = r10 << 3
    r0 += r7  ; @add.rr
    r14 = r0 + 1144
    r0 = r10
    call sort_and_format_dip_estimate
    r4 = r0
    r0 = r10 << 2
    r13 = r0 + -4
    r6 = 2
    r9 = 289
    r11 = r10
    goto L020178a6
L0201784e:
    r1 = r6 * r10
    r6 += 1  ; @add.ri.u5
    r0 = r1 + r6
    ifs (r0 >= r12) goto L020178aa
    r5 = r1 - r6
    r1 = r14
    r2 = r5
    goto L0201787a
L02017862:
    r3 = r5 << 2
    r3 += r7  ; @add.rr
    r15 = [r3+r9<<2]
    r8 = [r1++=4]
    r3 = r2
    iff (r8 u>= r15) {
    r3 = r5
    }
    r2 += 1  ; @add.ri.u5
    r5 = r3
L0201787a:
    ifs (r2 <= r0) goto L02017862
    r0 = r5
    call sort_and_format_dip_estimate
    r1 = 1028443341
    iff (r4 u<= r1) goto L0201789c
    r1 = 3173242634
    r1 = r4 + r1 (f)
    iff (r0 < r1) goto L020178a0
L0201789c:
    r0 = r4
    r5 = r11
L020178a0:
    r14 += r13
    r4 = r0
    r11 = r5
L020178a6:
    ifs (r6 <= 4) goto L0201784e
L020178aa:
    r6 = L01c26890
    r0 = r11 << 2
    r0 += r7  ; @add.rr
    r2 = r0 + 1152
    r5 = 278  #
    r0 = [r2+4]
    r3 = [r2+8]
    r2 = 0xC0000000  #
    r1 = [r2+0]
    r2 = r0 * r2 (f)
    r2 = r1 + r2 (f)
    r2 = r3 + r2 (f)
    r7 = 814313567
    [r6+r5<<2] = r4
    iff (r2 > r7) {
    r1 = r1 - r3 (f)
    r3 = 0x3F000000
    r1 = r1 * r3 (f)
    r1 = r1 / r2 (f)
    } else {
    r1 = 0
    }
    r2 = 0x3F000000  #
    r3 = [sp+4]
    r4 = [sp]
    iff (r1 u<= r2) {
    r2 = r1
    }
    r1 = 0xBF000000
    iff (r2 u>= r1) {
    r1 = r2
    }
    r2 = itof(r11)
    r1 = r2 + r1 (f)
    r1 = 0x3F800000  #
    [r4+0] = r1
    r0 = r1 - r0 (f)
    [r3+0] = r0
    r0 = 1
    goto L02017926
L02017924:
    r0 = 0
L02017926:
    sp += 8
    {pc, r15-r4} = [sp++]
