; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 1 function, 0x020204b4..0x02020616

; phase3_p8_vm_defrag: 0x020204b4..0x02020616, module phase3-p8 (vm_defrag)
.type phase3_p8_vm_defrag,@function
phase3_p8_vm_defrag:
    [--sp] = {rets, r12-r4}
    sp += -8
    r8 = 623
    r12 = L01c26090
    r0 = b[r12+r8] (u)
    r0 = r0 >> 1
    r9 = 1
    r0 = r9 & ~r0
    r0 = r0 * 0xC
    r1 = r0 + r12
    r1 = h[r1+8] (u)
    if (r1 != 0) goto L02020612
    r1 = [r0+r12]
    r1 += 4  ; @add.ri.u5
    [r12+616] = r1
    r1 = [r0+r12]
    r0 = 3723410295
    [sp] = r0
    r0 = sp + 0
    r2 = 4
    call phase3_p8_sfc_write
    r11 = sp + 4
    r7 = 0
    r10 = 622
    goto L020205aa
L02020508:
    r0 = r12 + 24
    r0 = h[r0+r7<<1] (u)
    if (r0 == 0) goto L020205a8
    r6 = r12 + 616
    r1 = b[r6+7] (u)
    r1 = uextra(r1, p:1, l:1)
    r1 = r1 * 0xC
    r1 = [r1+r12]
    r1 += r0  ; @add.rr
    r0 = sp + 4
    r2 = 4
    call L02020116
    r2 = b[r6+7] (u)
    r0 = r2 >> 1
    r0 = r9 & ~r0
    r0 = r0 * 0xC
    r1 = [++r0=r12]
    r3 = [r0+4]
    r4 = b[r11+3] (u)
    r5 = b[r11+2] (u)
    r1 += r3  #  ; @add.rr.p
    r0 = [r6+0]
    r5 <= insert(r4, p:8, l:8)
    r4 = r5 >> 4
    r3 = r0 + r4
    r3 += 4  ; @add.ri.u5
    if (r3 > r1) goto L0202060e
    r1 = b[r12+r10] (u)
    if (r1 == 0) goto L02020570
    r0 = r1
    call L0203feb8  ; @call.xl
    r2 = b[r12+r8] (u)
    r0 = [r12+616]
L02020570:
    r1 = uextra(r2, p:1, l:1)
    r1 = r1 * 0xC
    r1 = [r1+r12]
    r2 = r7 << 1
    r5 = r2 + r12
    r2 = h[r5+24] (u)
    r1 += r2  ; @add.rr
    r4 += 4  ; @add.ri.u5
    r2 = r4
    call L020201dc
    r0 = b[r6+7] (u)
    r0 = r0 >> 1
    r0 = r9 & ~r0  #
    r1 = [r6+0]
    r0 = r0 * 0xC
    r0 = [r0+r12]
    r0 = r1 - r0
    h[r5+24] = r0
    [r6+0] += r4
L020205a8:
    r7 += 1  ; @add.ri.u5
L020205aa:
    if (r7 <= 255) goto L02020508
    r6 = r12 + 623
    r0 = b[r6+0] (u)
    r0 = r0 >> 1
    r5 = 1
    r0 = r5 & ~r0
    r0 = r0 * 0xC
    r1 = [r0+r12]
    r0 = 3723405909
    r4 = sp + 0
    r2 = 4
    r0 = r4  #
    [sp] = r0
    call phase3_p8_sfc_write
    r0 = b[r6+0] (u)
    r0 = r0 >> 1
    r0 = r5 & ~r0
    r0 = r0 * 0xC
    r1 = [r0+r12]
    r0 = 1437248085
    r0 = r4  #
    [sp] = r0
    r2 = 4
    call phase3_p8_sfc_write
    r0 = b[r6+0] (u)
    r0 = uextra(r0, p:1, l:1)
    r0 = r0 * 0xC
    r0 += r12
    call L02020376
    r0 = b[r6+0] (u)
    r0 ^= 2
    b[r6+0] = r0
    goto L02020612
L0202060e:
    call L020203fe
L02020612:
    sp += 8
    {pc, r12-r4} = [sp++]
