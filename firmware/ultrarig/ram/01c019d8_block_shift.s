; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; block_shift: 1 function, 0x01c019d8..0x01c01c92

; block_shift_shift_left: 0x01c019d8..0x01c01c92, module block-shift (shift_left)
.type block_shift_shift_left,@function
block_shift_shift_left:
    [--sp] = {rets, r15-r4}
    sp += -52
    r12 = r1  #
    [sp+8] = r0
    r13 = 0
    r2 = 2147483647
    r1_r0 = 0
    d[sp] = r13_r12
    goto L01c01c88
L01c019f0:
    [sp+40] = r0
    r0 = [sp+8]
    r1 += r0  #  ; @add.rr.p
    [sp+44] = r1
    r10 = [r1+12]
    r11 = r10 >>> 31
    r11_r10 <<= r12
    r0 = 0
    r4 = r10 - r2
    r5 = r11 - r0 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r4 |= r5
    r3 = 1
    r6 = ~r6  #
    [sp+48] = r3
    if ((r4 & r6) == 0) {
    r3 = 0
    }
    r8 = [r1+8]
    r9 = r8 >>> 31
    r9_r8 <<= r12
    r4 = r8 - r2
    r5 = r9 - r0 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r4 |= r5
    r5 = 1
    if ((r4 & r6) == 0) {
    r5 = 0
    }
    [sp+32] = r5
    r14 = [r1+4]
    r15 = r14 >>> 31
    r15_r14 <<= r12
    r4 = r14 - r2
    r5 = r15 - r0 - !c
    r6 = psr
    r7 = sextra(r6, p:0, l:1)
    r6 = sextra(r6, p:3, l:1)
    r6 ^= r7
    r6 = ~r6
    r4 |= r5
    r5 = 1
    if ((r4 & r6) == 0) {
    r5 = 0
    }
    [sp+28] = r5
    [sp+36] = r3
    r6 = [r1++=12]
    r7 = r6 >>> 31
    r7_r6 <<= r12
    r4 = r6 - r2
    r5 = r7 - r0 - !c
    r0 = psr
    r2 = sextra(r0, p:0, l:1)
    r0 = sextra(r0, p:3, l:1)
    r0 ^= r2
    r0 = ~r0
    r5 |= r4
    r2 = 1
    if ((r5 & r0) == 0) {
    r2 = 0
    }
    r3 = 2147483649
    r2 = r10 - r3  #
    [sp+24] = r2
    r12 = 0xFFFFFFFF  ; @li.modimm
    r2 = r11 - r12 - !c
    r2 = psr
    r4 = uextra(r2, p:3, l:1)
    r2 ^= r4
    r4 = 1
    if ((r2 & 0x1) == 0) {
    r4 = 0
    }
    r2 = r8 - r3  #
    [sp+20] = r4
    r2 = r9 - r12 - !c
    r2 = psr
    r4 = uextra(r2, p:3, l:1)
    r2 ^= r4
    r4 = 1
    if ((r2 & 0x1) == 0) {
    r4 = 0
    }
    r2 = r14 - r3  #
    [sp+16] = r4
    r2 = r15 - r12 - !c
    r2 = psr
    r4 = uextra(r2, p:3, l:1)
    r4 ^= r2
    r2 = 1
    if ((r4 & 0x1) == 0) {
    r2 = 0
    }
    r4 = r6 - r3  #
    [sp+12] = r2
    r13 = 0xFFFFFFFF  ; @li.modimm
    r4 = r7 - r12 - !c
    r4 = psr
    r2 = uextra(r4, p:3, l:1)
    r2 ^= r4
    if ((r2 & 0x1) == 0) {
    r2 = 0
    [sp+48] = r2
    }
    r3 = r12 + 0x80000000
    r4 = r3
    if ((r5 & r0) != 0) goto L01c01b64
    r0 = r3 + 0x2  ; @add.modimm.rri
    r0 = r6 - r0
    r2 = r7 - r13 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r0 |= r2
    if ((r0 & r4) == 0) {
    r6 = r3 + 2
    r7 = r3 + 0x80000000
    }
    r4 = r6
L01c01b64:
    [++r1=-12] = r4
    r0 = r14 - r3
    r13_r12 = d[sp]
    r2 = r15 - r13 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r2 |= r0
    r0 = r3
    r6 = r3
    r3 = r3 + 0x2  ; @add.modimm.rri
    r7 = -1
    if ((r2 & r4) != 0) goto L01c01bc0
    r0 = r14 - r3
    r2 = r15 - r7 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r0 |= r2
    if ((r0 & r4) == 0) {
    r14 = r3 + 0x0  ; @add.modimm.rri
    r15 = r7 + 0x0  ; @add.modimm.rri
    }
    r0 = r14
    r6 = r7 + 0x80000000
L01c01bc0:
    [++r1=4] = r0
    r0 = r8 - r6
    r2 = r9 - r13 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r2 |= r0
    r0 = r6
    if ((r2 & r4) != 0) goto L01c01c10
    r0 = r8 - r3
    r2 = r9 - r7 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r0 |= r2
    if ((r0 & r4) == 0) {
    r8 = r3 + 0x0  ; @add.modimm.rri
    r9 = r7 + 0x0  ; @add.modimm.rri
    }
    r0 = r8
    r6 = r7 + 0x80000000
L01c01c10:
    [++r1=4] = r0
    r0 = r10 - r6
    r2 = r11 - r13 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r2 |= r0
    r0 = r6
    if ((r2 & r4) != 0) goto L01c01c5c
    r0 = r10 - r3
    r2 = r11 - r7 - !c
    r4 = psr
    r5 = sextra(r4, p:0, l:1)
    r4 = sextra(r4, p:3, l:1)
    r4 ^= r5
    r4 = ~r4
    r0 |= r2
    if ((r0 & r4) == 0) {
    r10 = r3 + 0x0  ; @add.modimm.rri
    r11 = r7 + 0x0  ; @add.modimm.rri
    }
    r0 = r10
L01c01c5c:
    [r1+4] = r0
    r0 = [sp+40]
    r1 = [sp+48]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+24]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+28]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+12]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+32]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+16]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+36]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+20]
    r0 += r1  #  ; @add.rr.p
    r1 = [sp+44]
    r1 += 16  ; @add.ri.u5
    r2 = r7 + 0x80000000
L01c01c88:
    if (r1 != 512) goto L01c019f0
    sp += 52
    {pc, r15-r4} = [sp++]
