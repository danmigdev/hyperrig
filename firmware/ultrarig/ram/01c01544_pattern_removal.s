; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; pattern_removal: 2 functions, 0x01c01544..0x01c01690

; pattern_removal_peak: 0x01c01544..0x01c0158a, module pattern-removal (peak)
.type pattern_removal_peak,@function
pattern_removal_peak:
    [--sp] = {rets, r7-r4}
    r1 = 0
    r3_r2 = 0
    goto L01c0157a
L01c0154c:
    r4 = r0
    r5 = [++r4=r1]
    r7_r6 = d[r4+4]
    r2 = smin(r2, r5)  #
    r4 = [r4+12]
    r2 = smin(r2, r6)
    r2 = smin(r2, r7)
    r2 = smin(r2, r4)
    r3 = smax(r3, r5)
    r3 = smax(r3, r6)
    r3 = smax(r3, r7)
    r3 = smax(r3, r4)
    r1 += 16  ; @add.ri.u5
L01c0157a:
    if (r1 != 512) goto L01c0154c
    r0 = 0x0 - r2
    r0 = smax(r3, r0)
    {pc, r7-r4} = [sp++]

; pattern_removal_removal: 0x01c0158a..0x01c01690, module pattern-removal (removal)
.type pattern_removal_removal,@function
pattern_removal_removal:
    [--sp] = {rets, r15-r4}
    r4 = r0
    call pattern_removal_peak
    r1 = 8
    if (r0 < 1048576) goto L01c015b0
    r2 = r0 >> 24
    r1 = 0
    if (r2 != 0) goto L01c015b0
    r0 = clz(r0)
    r0 = 0xB - r0
    r0 = r0 << 1
    r1 = r0 + 12
    ifs (r1 >= 18) {  ; @ifs.ge.ri.s12
    r1 = 18
    }
L01c015b0:
    r0 = r1 + -1
    r2 = 1
    r8 = r2 << r0
    r11 = 0
    ifs (r1 <= 8) {  ; @ifs.le.ri.s12
    r8 = 0
    }
    r10 = L01c26890
    r9 = 9752
    r6 = 2147483647
    r7 = 0
    goto L01c0166c
L01c015d6:
    r2 = r10 + r9
    r12 = [r2+r7<<2]
    if (r1 == 0) goto L01c01606
    r5 = [r4+r7<<2]
    r3 = r8 - r12
    r3 += r5  ; @add.rr
    r3 >>>= r1
    r5 = r3 + r12
    r12 = 0x400000
    ifs (r5 <= 4194304) {
    r0 = 4290772992
    r12 = smax(r5, r0)
    }
    [r2+r7<<2] = r12
L01c01606:
    r2 = [r4+r7<<2]
    r3 = r2 >>> 31
    r13 = r12 >>> 31
    r14 = r2 - r12
    r15 = r3 - r13 - !c
    r2 = r14 - r6
    r3 = r15 - r11 - !c
    r5 = psr
    r0 = sextra(r5, p:0, l:1)
    r5 = sextra(r5, p:3, l:1)
    r0 ^= r5
    r0 = ~r0
    r3 |= r2
    r2 = r6
    if ((r3 & r0) != 0) goto L01c01666
    r0 = r6 + 0x2  ; @add.modimm.rri
    r0 = r14 - r0
    r2 = -1
    r2 = r15 - r2 - !c
    r3 = psr
    r5 = sextra(r3, p:0, l:1)
    r3 = sextra(r3, p:3, l:1)
    r3 ^= r5
    r3 = ~r3
    r0 |= r2
    if ((r0 & r3) == 0) {
    r14 = r6 + 2
    r15 = r6 + 0x80000000
    }
    r2 = r14
L01c01666:
    [r4+r7<<2] = r2
    r7 += 1  ; @add.ri.u5
L01c0166c:
    if (r7 != 128) goto L01c015d6
    if (r1 == 0) goto L01c0168e
    if (r1 != 8) goto L01c01680
    r0 = 10264
    r1 = [++r10=r0]
    goto L01c01688
L01c01680:
    r0 = 10268
    r1 = [++r10=r0]
L01c01688:
    r0 = r1 + 1
    [r10+0] = r0
L01c0168e:
    {pc, r15-r4} = [sp++]
