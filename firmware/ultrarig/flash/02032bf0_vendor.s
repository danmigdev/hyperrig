; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02032bf0..0x02033172: vendor code (JieLi SDK or library, not reversed), as instructions
L02032bf0:
    [--sp] = {rets, r7-r4}
    r7 = r0
    r4 = r0 & 0x3
    if (r4 == 0) goto L02032c08
    r4 = 0x4 - r4
L02032bfe:
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    if (r2 == 0) goto L02032c5a
    if (--r4 != 0) goto L02032bfe
L02032c08:
    r2 = r1 | r0
    r6 = 4278124287
    if ((r2 & 0x3) != 0) goto L02032c2c
L02032c18:
    r2 = [r1+0]
    r3 = r2 + r6
    r3 = r3 & ~r2
    if ((r3 & 0x80808080) != 0) goto L02032c54
    r1 = r1 + 4
    [r0++=4] = r2
    goto L02032c18
L02032c2c:
    r4 = r1
    r2 = b[r4++=1] (u)
    r5 = b[r4++=1] (u)
    r2 <= insert(r5, p:8, l:8)
    r5 = b[r4++=1] (u)
    r2 <= insert(r5, p:16, l:8)
    r5 = b[r4++=1] (u)
    r2 <= insert(r5, p:24, l:8)
    r5 = r2 + r6
    r5 = r5 & ~r2
    if ((r5 & 0x80808080) != 0) goto L02032c54
    [r0++=4] = r2
    r1 = r4
    goto L02032c2c
L02032c54:
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    if (r2 != 0) goto L02032c54
L02032c5a:
    r0 = r7
    {pc, r7-r4} = [sp++]
L02032c5e:
    [--sp] = {rets, r5, r4}
    r4 = r1
    if (r4 == 0) goto L02032c76
    r1 = 0
L02032c66:
    r5 = r1
    r1 = r4
    call L020282f4
    r1 = r0
    r0 = r1 + 1
    if (r1 != 0) goto L02032c66
    goto L02032c7e
L02032c76:
    r1 = 0
    call L020282f4
    r5 = r0
L02032c7e:
    r0 = r5
    {pc, r5, r4} = [sp++]
    [--sp] = {rets, r4}
    r2 = b[r0+0] (u)
    if (r2 != 0) goto L02032ca6
    r1 = b[r1+0] (u)
    if (r1 == 0) goto L02032caa
L02032c8c:
    r0 = 0
    {pc, r4} = [sp++]
L02032c90:
    r2 = 0
L02032c92:
    r3 = b[r1+r2] (u)
    if (r3 == 0) goto L02032caa
    r4 = b[r0+r2] (u)
    r2 += 1  ; @add.ri.u5
    if (r3 == r4) goto L02032c92
    r2 = b[++r0=1] (u)
L02032ca6:
    if (r2 != 0) goto L02032c90
    goto L02032c8c
L02032caa:
    {pc, r4} = [sp++]
L02032cac:
    if (r1 == 0) {  ; @if.eq.ri.s12
    r0 = clz(r0)
    r0 |= 32
    } else {
    r0 = clz(r1)
    }
    rts
L02032cbc:
    [--sp] = {rets, r5, r4}
    r2 = r0
    r5_r4 = d[r2+0]
    r1_r0 = r5_r4
    call L02032cac
    r1 = r0 + -11
    r5_r4 <<= r1
    r0 = 0xC - r0
    d[r2+0] = r5_r4
    {pc, r5, r4} = [sp++]
L02032cda:
    [--sp] = {rets, r15-r4}
    sp += -28
    r7 = r1 & 0x7FFFFFFF
    d[sp] = r1_r0
    r6 = r0
    r1 = -1
    r8 = r6 + -1
    r9 = r7 + r1 + c
    r4 = -2
    r14 = 2146435071
    r4 = r8 - r4
    r5 = r9 - r14 - !c
    r0 = psr
    r4 |= r5
    r9 = r3 & 0x7FFFFFFF
    r0 = sextra(r0, p:1, l:1)
    r8 = r2
    r12 = r2 + -1
    r13 = r9 + r1 + c
    r11_r10 = r3_r2
    if ((r0 & r4) != 0) goto L02032d88
    r0 = r12 - 0xFFFFFFFF
    r0 = r13 - r14 - !c
    r0 = psr
    if ((r0 & 2) != 0) goto L02032d88
L02032d30:
    r0 = r8 - r6
    r1 = r9 - r7 - !c
    r2 = psr
    r0 |= r1
    r1 = sextra(r2, p:1, l:1)
    if ((r1 & r0) == 0) {
    r9 = r11
    r5_r4 = d[sp]
    } else {
    r9_r8 = d[sp]
    r5_r4 = r11_r10
    }
    r2 = 1048575
    r1 = r5 & r2
    r0 = r4
    r13 = r9 & r2
    d[sp+20] = r1_r0
    r12 = r8
    r3_r2 = r9_r8
    r3_r2 >>= 52
    r0 = 2047
    r3 = r2 & r0
    r7_r6 = r5_r4
    r7_r6 >>= 52
    d[sp+12] = r13_r12
    if ((r6 & r0) == 0) goto L02032dc2
    r6 &= r0
    goto L02032dca
L02032d88:
    r0 = r14 + 1
    r1 = r6 - 0x1
    r1 = r7 - r0 - !c
    r1 = psr
    if ((r1 & 2) == 0) goto L02032da6
    r1_r0 = d[sp]
    r1 |= 524288
    r3_r2 = r1_r0
    goto L02032f8e
L02032da6:
    r1 = r2 - 0x1
    r1 = r9 - r0 - !c
    r1 = psr
    r5_r4 = d[sp]
    if ((r1 & 2) == 0) goto L02032f5c
    r11 = r3 | 0x80000
    r3_r2 = r11_r10
    goto L02032f8e
L02032dc2:
    r0 = sp + 20
    call L02032cbc
    r6 = r0
L02032dca:
    if (r3 != 0) goto L02032dd8
    r0 = sp + 12
    call L02032cbc
    r13_r12 = d[sp+12]
    r3 = r0
L02032dd8:
    r1_r0 = d[sp+20]
    r1_r0 <<= 3
    r15 = r1 | 0x800000
    r14 = r0
    d[sp+20] = r15_r14
    r13_r12 <<= 3
    r13 = r13 | 0x800000
    d[sp+12] = r13_r12
    r11 = r5 ^ r9
    r2 = r6 - r3
    r10 = r4 ^ r8
    if (r2 == 0) goto L02032e42
    if (r2 > 63) goto L02032e38
    d[sp] = r5_r4
    r3 = 0x40 - r2
    r5_r4 = r13_r12
    r5_r4 <<= r3
    r3 = r4 | r5
    r8 = 1
    if (r3 != 0) goto L02032e20
    r8 = r3
L02032e20:
    r9 = 0
    r13_r12 >>= r2
    r13 = r13 | r9
    r12 = r12 | r8
    d[sp+12] = r13_r12
    r5_r4 = d[sp]
    goto L02032e42
L02032e38:
    r12 = 1
    r13 = 0
    d[sp+12] = r13_r12
L02032e42:
    ifs (r11 <= -1) goto L02032e80
    r8 = r12 + r0
    r9 = r13 + r15 + c
    r3 = r9 & 0x1000000
    r2 = 0
    d[sp+20] = r9_r8
    if (r3 == 0) goto L02032ec0
    r11_r10 = r5_r4
    r4 = r12 + r0
    r5 = r13 + r1 + c
    r0 = r4 & 0x1
    r5_r4 = r11_r10
    r1 = 0
    r9_r8 >>= 1
    r9 = r9 | r1
    r8 = r8 | r0
    d[sp+20] = r9_r8
    r6 += 1  ; @add.ri.u5
    goto L02032ec0
L02032e80:
    r8 = r0 - r12
    r9 = r15 - r13 - !c
    r0 = r8 | r9
    d[sp+20] = r9_r8
    if (r0 == 0) goto L02032f80
    r0 = 8388607
    r1 = r8 - 0xFFFFFFFF
    r0 = r9 - r0 - !c
    r2 = psr
    r0 |= r1
    r1 = sextra(r2, p:1, l:1)
    if ((r1 & r0) != 0) goto L02032ec0
    r1_r0 = r9_r8
    call L02032cac
    r0 += -8
    r9_r8 <<= r0
    d[sp+20] = r9_r8
    r6 = r6 - r0
L02032ec0:
    r3 = r5 & 0x80000000
    r2 = 0
    ifs (r6 < 2047) goto L02032ed6
    r0 = 2146435072
    r3 |= r0
    goto L02032f8e
L02032ed6:
    ifs (r6 > 0) goto L02032f06
    r4 = 0x1 - r6
    r0 = 0x40 - r4
    r7_r6 = r9_r8
    r7_r6 <<= r0
    r5 = r6 | r7
    r0 = 1
    if (r5 != 0) goto L02032ef2
    r0 = r5
L02032ef2:
    r1 = 0
    r9_r8 >>= r4
    r9 = r9 | r1
    r8 = r8 | r0
    d[sp+20] = r9_r8
    r6 = 0
L02032f06:
    r1_r0 = r9_r8
    r1_r0 >>= 3
    r4 = 1048575
    r1 &= r4
    r5 = r1 | r3
    r7 = 0
    r4 = r0 | r2
    r2 = r6
    r3 = 0
    r3_r2 <<= 52
    r1 = r5 | r3
    r0 = r4 | r2
    r2 = r8 & 0x7
    r8 = 1
    if (r2 <= 4) {  ; @if.le.ri.s12
    r8 = 0
    }
    r9 = 0
    r4 = r0 + r8
    r5 = r1 + r7 + c
    r0 = r4 & 0x1
    if (r2 != 4) {  ; @if.ne.ri.s12
    r0 = 0
    r1 = 0
    } else {
    r1 = 0
    }
    r2 = r0 + r4
    r3 = r1 + r5 + c
    goto L02032f8e
L02032f5c:
    r1 = r7 ^ r0
    r1 |= r6
    if (r1 != 0) goto L02032f86
    r1 = r3 ^ r5
    r0 = r2 ^ r4
    r2 = r1 ^ 0x80000000
    r0 |= r2
    if (r0 != 0) goto L02032f7c
    r4 = 0
    r5 = 2146959360
L02032f7c:
    r3_r2 = r5_r4
    goto L02032f8e
L02032f80:
    r2 = 0
    r3 = 0
    goto L02032f8e
L02032f86:
    r0 = r0 ^ r9
    r0 |= r2
    if (r0 != 0) goto L02032f94
L02032f8e:
    r1_r0 = r3_r2
    sp += 28
    {pc, r15-r4} = [sp++]
L02032f94:
    r0 = r6 | r7
    if (r0 == 0) goto L02032fa8
    r0 = r2 | r9
    r3_r2 = r5_r4
    if (r0 != 0) goto L02032d30
    goto L02032f8e
L02032fa8:
    r0 = r2 | r9
    if (r0 != 0) goto L02032f8e
    r1_r0 = d[sp]
    r3 &= r1
    r2 = r8 & r0
    goto L02032f8e
L02032fba:
    [--sp] = {rets, r12-r4}
    r7 = r1 & 0x7FFFFFFF
    r6 = r0
    r10 = 2146435072
    r8 = r6 - 0x0
    r5 = r7 - r10 - !c
    r4 = psr
    r5 = r5 | r8
    r4 = sextra(r4, p:1, l:1)
    r11 = 1
    if ((r4 & r5) != 0) goto L02033066
    r9 = r3 & 0x7FFFFFFF
    r8 = r2
    r12 = r2 - 0x0
    r5 = r9 - r10 - !c
    r4 = psr
    r5 = r5 | r12
    r4 = sextra(r4, p:1, l:1)
    if ((r4 & r5) != 0) goto L02033066
    r5 = r9 | r7
    r4 = r2 | r6
    r4 |= r5
    if (r4 == 0) goto L02033032
    r5 = r3 & r1
    r4 = r2 & r0
    ifs (r5 < 0) goto L02033036
    r4 = r0 - r2
    r4 = r1 - r3 - !c
    r4 = psr
    r5 = r4 >> 3
    r4 ^= r5
    r11 = -1
    if ((r4 & 1) == 0) goto L02033056
    goto L02033066
L02033032:
    r11 = 0
    goto L02033066
L02033036:
    r4 = r0 - r2
    r5 = r1 - r3 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r4 |= r5
    r11 = -1
    if ((r4 & r6) != 0) goto L02033066
L02033056:
    r4 = r1 ^ r3
    r0 ^= r2
    r0 |= r4
    r11 = 1
    if (r0 != 0) goto L02033066
    r11 = r0
L02033066:
    r0 = r11
    {pc, r12-r4} = [sp++]
L0203306a:
    [--sp] = {rets, r12-r4}
    r7 = r1 & 0x7FFFFFFF
    r6 = r0
    r10 = 2146435072
    r8 = r6 - 0x0
    r5 = r7 - r10 - !c
    r4 = psr
    r5 = r5 | r8
    r4 = sextra(r4, p:1, l:1)
    r11 = -1
    if ((r4 & r5) != 0) goto L0203310e
    r9 = r3 & 0x7FFFFFFF
    r8 = r2
    r12 = r2 - 0x0
    r5 = r9 - r10 - !c
    r4 = psr
    r5 = r5 | r12
    r4 = sextra(r4, p:1, l:1)
    if ((r4 & r5) != 0) goto L0203310e
    r5 = r9 | r7
    r4 = r2 | r6
    r4 |= r5
    if (r4 == 0) goto L020330de
    r5 = r3 & r1
    r4 = r2 & r0
    ifs (r5 < 0) goto L020330e2
    r4 = r0 - r2
    r4 = r1 - r3 - !c
    r4 = psr
    r5 = r4 >> 3
    r4 ^= r5
    if ((r4 & 1) == 0) goto L020330fe
    goto L0203310e
L020330de:
    r11 = 0
    goto L0203310e
L020330e2:
    r4 = r0 - r2
    r5 = r1 - r3 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r4 |= r5
    if ((r4 & r6) != 0) goto L0203310e
L020330fe:
    r4 = r1 ^ r3
    r0 ^= r2
    r0 |= r4
    r11 = 1
    if (r0 != 0) goto L0203310e
    r11 = r0
L0203310e:
    r0 = r11
    {pc, r12-r4} = [sp++]
    [--sp] = {rets, r5, r4}
    r3 &= 2147483647
    r4 = 2146435072
    r5 = r2 - 0x0  ; @sub.modimm.rri
    r2 = r3 - r4 - !c
    r3 = psr
    r2 |= r5
    r3 = sextra(r3, p:1, l:1)
    r2 &= r3
    r1 &= 2147483647
    r3 = r0 - 0x0  ; @sub.modimm.rri
    r0 = r1 - r4 - !c
    r1 = psr
    r0 |= r3
    r1 = sextra(r1, p:1, l:1)
    r0 &= r1
    r1 = r0 | r2
    r0 = 1
    if (r1 != 0) goto L02033150
    r0 = r1
L02033150:
    {pc, r5, r4} = [sp++]
L02033152:
    [--sp] = rets
    call L02032fba
    pc = [sp++]
L0203315a:
    [--sp] = rets
    call L02032fba
    pc = [sp++]
L02033162:
    [--sp] = rets
    call L02032fba
    pc = [sp++]
L0203316a:
    [--sp] = rets
    call L0203306a  ; @call.l
    pc = [sp++]
