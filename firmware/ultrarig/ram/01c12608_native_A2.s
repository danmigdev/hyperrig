; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; native_A2: 2 functions, 0x01c12608..0x01c127de

; native_A2_dot_i16: 0x01c12608..0x01c126f4, module native-A2 (dot_i16)
.type native_A2_dot_i16,@function
native_A2_dot_i16:
    [--sp] = {rets, r15-r4}
    sp += -28
    r15 = [sp+88]
    r8 = r2  #
    [sp+20] = r1
    [sp+24] = r0
    ifs (r15 < 1) goto L01c126f0
    r10 = [sp+92]
    r9 = [sp+84]
    r11 = 0  #
    r0 = [sp+80]
    r2 = r10 + -1  #
    [sp+16] = r0
    r12 = 1
    r13 = 0
    r0 = 0x0 - r10
    [sp+8] = r0
    [sp+12] = r1
    r13_r12 <<= r2
    r0 = [sp+8]
    r1 = [sp+12]
    r1 = 0
    [sp+8] = r0
    [sp+12] = r1
    r0 = r10 + 32
    r14 = r3 << 2  #
    [sp+4] = r0
    r5 = 0
L01c1264e:
    ifs (r9 < 1) goto L01c1266c
    r6 = 0
    r7 = 0
    r0 = r9  #
    r1 = [sp+16]
    r2 = r8
L01c1265c:
    r4 = h[r1++=2] (s)
    r3 = [r2++=4]
    r7_r6 += r3 * r4 (s)
    if (--r0 != 0) goto L01c1265c
    goto L01c12670
L01c1266c:
    r6 = 0
    r7 = 0
L01c12670:
    ifs (r10 <= 0) goto L01c12686
    ifs (r7 < 0) goto L01c126ae
    r6 += r12
    r7 = r7 + r13 + c
    r0 = r7 >> 31
    r7_r6 >>>= r10
    goto L01c126ce
L01c12686:
    ifs (r10 > -1) goto L01c126cc
    r0 = [sp+8]
    r1 = [sp+12]
    ifs (r0 > 31) goto L01c126c4
    r0 = [sp+4]
    r1 = r6 >> r0
    r2 = [sp+8]
    r3 = [sp+12]
    r0 = r7 << r2
    r7 = r0 | r1
    r0 = r7 >> 31
    r2 = [sp+8]
    r3 = [sp+12]
    r6 <<= r2
    goto L01c126ce
L01c126ae:
    r0 = r12 - r6
    r1 = r13 - r7 - !c
    r1_r0 >>>= r10
    r6 = 0x0 - r0
    r7 = r11 - r1 - !c
    goto L01c126cc
L01c126c4:
    r0 = [sp+8]
    r1 = [sp+12]
    r7_r6 <<= r0
L01c126cc:
    r0 = r7 >> 31
L01c126ce:
    r1 = 2147483647
    r1 = r1 + r0
    r0 = r6 >>> 31
    if (r7 != r0) {
    r6 = r1
    }
    r0 = [sp+20]
    r1 = [sp+24]
    r0 *= r5
    [r1+r0<<2] = r6
    r5 = r5 + 1
    r8 += r14
    if (r5 != r15) goto L01c1264e
L01c126f0:
    sp += 28
    {pc, r15-r4} = [sp++]

; native_A2_dot_i32: 0x01c126f4..0x01c127de, module native-A2 (dot_i32)
.type native_A2_dot_i32,@function
native_A2_dot_i32:
    [--sp] = {rets, r15-r4}
    sp += -28
    r15 = [sp+88]
    r8 = r2  #
    [sp+20] = r1
    [sp+24] = r0
    ifs (r15 < 1) goto L01c127da
    r10 = [sp+92]
    r9 = [sp+84]
    r11 = 0  #
    r0 = [sp+80]
    r2 = r10 + -1  #
    [sp+16] = r0
    r12 = 1
    r13 = 0
    r0 = 0x0 - r10
    [sp+8] = r0
    [sp+12] = r1
    r13_r12 <<= r2
    r0 = [sp+8]
    r1 = [sp+12]
    r1 = 0
    [sp+8] = r0
    [sp+12] = r1
    r0 = r10 + 32
    r14 = r3 << 2  #
    [sp+4] = r0
    r5 = 0
L01c1273a:
    ifs (r9 < 1) goto L01c12756
    r6 = 0
    r7 = 0
    r0 = r9  #
    r1 = [sp+16]
    r2 = r8
L01c12748:
    r4 = [r1++=4]
    r3 = [r2++=4]
    r7_r6 += r3 * r4 (s)
    if (--r0 != 0) goto L01c12748
    goto L01c1275a
L01c12756:
    r6 = 0
    r7 = 0
L01c1275a:
    ifs (r10 <= 0) goto L01c12770
    ifs (r7 < 0) goto L01c12798
    r6 += r12
    r7 = r7 + r13 + c
    r0 = r7 >> 31
    r7_r6 >>>= r10
    goto L01c127b8
L01c12770:
    ifs (r10 > -1) goto L01c127b6
    r0 = [sp+8]
    r1 = [sp+12]
    ifs (r0 > 31) goto L01c127ae
    r0 = [sp+4]
    r1 = r6 >> r0
    r2 = [sp+8]
    r3 = [sp+12]
    r0 = r7 << r2
    r7 = r0 | r1
    r0 = r7 >> 31
    r2 = [sp+8]
    r3 = [sp+12]
    r6 <<= r2
    goto L01c127b8
L01c12798:
    r0 = r12 - r6
    r1 = r13 - r7 - !c
    r1_r0 >>>= r10
    r6 = 0x0 - r0
    r7 = r11 - r1 - !c
    goto L01c127b6
L01c127ae:
    r0 = [sp+8]
    r1 = [sp+12]
    r7_r6 <<= r0
L01c127b6:
    r0 = r7 >> 31
L01c127b8:
    r1 = 2147483647
    r1 = r1 + r0
    r0 = r6 >>> 31
    if (r7 != r0) {
    r6 = r1
    }
    r0 = [sp+20]
    r1 = [sp+24]
    r0 *= r5
    [r1+r0<<2] = r6
    r5 = r5 + 1
    r8 += r14
    if (r5 != r15) goto L01c1273a
L01c127da:
    sp += 28
    {pc, r15-r4} = [sp++]
