; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02026906..0x02026a00: vendor code (JieLi SDK or library, not reversed), as instructions
L02026906:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r0  #
    [sp] = r2
    goto L0202692a
L02026910:
    r0 = [sp]
    r2 = r0 + 4
    [sp] = r2
    r0 = [r0+0]
    r0 |= 4
    b[r4+0] = r0
    goto L02026928
L0202691e:
    r0 = [sp]
    r2 = r0 + 4
    [sp] = r2
    r0 = [r0+0]
    b[r4+2] = r0
L02026928:
    r1 += 1  ; @add.ri.u5
L0202692a:
    r0 = b[r1+0] (u)
    r2 = r0 + -65
    if (r2 <= 6) goto L02026970
    r2 = r0 + -77
    if (r2 > 9) goto L020269a0
    tbb [r2]
L0202693e:
    .byte (L02026964 - L0202693e) / 2, (L020269a8 - L0202693e) / 2, (L020269a8 - L0202693e) / 2, (L0202695c - L0202693e) / 2, (L020269a8 - L0202693e) / 2, (L020269a8 - L0202693e) / 2, (L02026954 - L0202693e) / 2, (L020269a8 - L0202693e) / 2
    .byte (L020269a8 - L0202693e) / 2, (L02026948 - L0202693e) / 2
L02026948:
    r0 = [sp]
    r2 = r0 + 4
    [sp] = r2
    r0 = [r0+0]
    b[r4+3] = r0
    goto L02026928
L02026954:
    r0 = b[r4+5] (u)
    r0 |= 4
    b[r4+5] = r0
    goto L02026928
L0202695c:
    r0 = b[r4+5] (u)
    r0 |= 1
    b[r4+5] = r0
    goto L02026928
L02026964:
    r0 = [sp]
    r2 = r0 + 4
    [sp] = r2
    r0 = [r0+0]
    b[r4+4] = r0
    goto L02026928
L02026970:
    tbb [r2]
L02026972:
    .byte (L02026998 - L02026972) / 2, (L020269a8 - L02026972) / 2, (L020269a8 - L02026972) / 2, (L02026990 - L02026972) / 2, (L02026982 - L02026972) / 2, (L020269a8 - L02026972) / 2, (L0202697a - L02026972) / 2
    .byte 0x00  ; alignment
L0202697a:
    r0 = b[r4+5] (u)
    r0 |= 8
    b[r4+5] = r0
    goto L02026928
L02026982:
    r0 = [sp]
    r2 = r0 + 4
    [sp] = r2
    r0 = [r0+0]
    r0 |= 4
    b[r4+1] = r0
    goto L02026928
L02026990:
    r0 = b[r4+5] (u)
    r0 |= 2
    b[r4+5] = r0
    goto L02026928
L02026998:
    r0 = b[r4+5] (u)
    r0 |= 16
    b[r4+5] = r0
    goto L02026928
L020269a0:
    if (r0 == 118) goto L0202691e
    if (r0 == 101) goto L02026910
L020269a8:
    r0 = 3
    b[r4+6] = r0
    b[r4+7] = r0
    r2 = [sp]
    r0 = r4 + 28
    call L0202520a
    h[r4+10] = r0
    sp += 4
    {pc, r4} = [sp++]
L020269bc:
    [--sp] = rets
    if (r0 == 0) goto L020269f2
    r1 = [r0+-32]
    r2 = 305419896
    if (r1 != r2) goto L020269f4
    r2 = r2 + 0x11111111  #
    r1 = [r0+-8]
    if (r1 != r2) goto L020269f4
    r1 = [r0+-16]
    r0 += -32
    r0 = r0 - r1
    r1 = [r0+0]
    r2 = 2271560481
    if (r1 != r2) goto L020269f4
    r1 = r2 + 0x11111111  #
    r0 = [r0+36]
    if (r0 != r1) goto L020269f4
L020269f2:
    pc = [sp++]
L020269f4:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L020269fe:
    goto L020269fe
