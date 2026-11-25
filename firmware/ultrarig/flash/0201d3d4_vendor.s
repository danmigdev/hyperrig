; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201d3d4..0x0201dc74: vendor code (JieLi SDK or library, not reversed), as instructions
L0201d3d4:
    [--sp] = {rets, r15-r4}
    r0 = 263168
    r0 = [r0+0]
    r8 = L01c3740c
    r1 = h[r8+0] (u)
    r1 &= 4294967294
    r0 = r0 >> 11
    r2 = r0 & 0x1
    r1 |= r2
    h[r8+0] = r1
    if ((r0 & 1) != 0) goto L0201d40e
    r0 = 12
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 13
    r1 = 0
    call storage_fault_write_register  ; @call.xl
L0201d40e:
    r3 = 327688
    r9 = L01c1fa30
    r1 = r9  #
    r0 = [r3+0]
    [++r1=104] = r0
    r0 = [r3+4]
    [r1+4] = r0
    r0 = [r3+8]
    [r1+8] = r0
    r0 = [r3+12]
    [r1+12] = r0
    r2 = 0
    [r3+8] = r2
    r0 = -1
    [r3+0] = r0
    [r3+12] = r2
    [r3+4] = r2
    [r3+24] = r2
    r3 += 64
    r4 = [r3+0]
    [r1+16] = r4
    r4 = [r3+4]
    [r1+20] = r4
    r4 = [r3+8]
    [r1+24] = r4
    r4 = [r3+12]
    [r1+28] = r4
    [r3+8] = r2
    [r3+0] = r0
    [r3+12] = r2
    [r3+4] = r2
    [r3+24] = r2
    r3 += 64
    r4 = [r3+0]
    [r1+32] = r4
    r4 = [r3+4]
    [r1+36] = r4
    r4 = [r3+8]
    [r1+40] = r4
    r4 = [r3+12]
    [r1+44] = r4
    [r3+8] = r2
    [r3+0] = r0
    [r3+12] = r2
    [r3+4] = r2
    [r3+24] = r2
    r3 = b[r8+0] (u)
    if ((r3 & 1) != 0) goto L0201d4d8
    r3 = 327944
    r1 = r9  #
    r4 = [r3+0]
    [++r1=152] = r4
    r4 = [r3+4]
    [r1+4] = r4
    r4 = [r3+8]
    [r1+8] = r4
    r4 = [r3+12]
    [r1+12] = r4
    [r3+8] = r2
    [r3+0] = r0
    [r3+12] = r2
    [r3+4] = r2
    [r3+24] = r2
    r3 += 64
    r4 = [r3+0]
    [r1+16] = r4
    r4 = [r3+4]
    [r1+20] = r4
    r4 = [r3+8]
    [r1+24] = r4
    r4 = [r3+12]
    [r1+28] = r4
    [r3+8] = r2
    [r3+0] = r0
    [r3+12] = r2
    [r3+4] = r2
    [r3+24] = r2
    r3 += 64
    r4 = [r3+0]
    [r1+32] = r4
    r4 = [r3+4]
    [r1+36] = r4
    r4 = [r3+8]
    [r1+40] = r4
    r4 = [r3+12]
    [r1+44] = r4
    [r3+8] = r2
    [r3+0] = r0
    [r3+12] = r2
    [r3+4] = r2
    [r3+24] = r2
L0201d4d8:
    r7 = r1 + 48
    r1 = 328136
    r3 = [r1+0]
    [r7+0] = r3
    r3 = [r1+4]
    [r7+4] = r3
    r3 = [r1+8]
    [r7+8] = r3
    r3 = [r1+12]
    [r7+12] = r3
    [r1+8] = r2
    [r1+0] = r0
    [r1+12] = r2
    [r1+4] = r2
    r4 = 0x11800  #
    [r1+24] = r2
    r0 = [r4+0]
    [r7+16] = r0
    r5 = r4 + 3840  #
    r0 = [r4+4]
    [r7+20] = r0
    r0 = [r5+0]
    [r7+24] = r0
    r13 = 0x51000  #
    r0 = [r5+4]
    [r7+28] = r0
    r0 = [r13+0]
    [r7+32] = r0
    r0 = [r13+4]
    [r7+36] = r0
    r0 = [r13+8]
    r3 = 0x16A00  #
    [r7+40] = r0
    r0 = [r3+12]
    [r7+44] = r0
    r0 = [r3+16]
    [r7+48] = r0
    r0 = [r3+20]
    [r7+52] = r0
    r0 = [r3+0]
    [r7+56] = r0
    r0 = [r3+4]
    [r7+60] = r0
    r0 = r7 + 64  #
    r6 = [r3+8]
    r10 = 0x16800  #
    [r0+0] = r6
    r6 = [r10+0]
    [r0+4] = r6
    r6 = 2
    [r4+0] = r6
    [r4+4] = r2
    [r5+0] = r6
    [r5+4] = r2
    [r13+4] = r2
    r4 = [r8+24]
    r2 = [r13+0]
    if (r4 == 0) goto L0201d66a
    r2 &= 4294965247
    [r13+0] = r2
    [r13+8] &= 0xFFFFF7FF
    r2 = [r8+24]
    r3 = 0
    r4 = 0
    goto L0201d5a4
L0201d580:
    r1 = r2 >> r3
    r1 = r1.b0 (u)
    r5 = r1 + -148
    if (r5 > 3) goto L0201d5a2
    tbb [r5]
L0201d590:
    .byte (L0201d594 - L0201d590) / 2, (L0201d598 - L0201d590) / 2, (L0201d59c - L0201d590) / 2, (L0201d5a0 - L0201d590) / 2
L0201d594:
    r4 |= 1
    goto L0201d5a2
L0201d598:
    r4 |= 2
    goto L0201d5a2
L0201d59c:
    r4 |= 4
    goto L0201d5a2
L0201d5a0:
    r4 |= 8
L0201d5a2:
    r3 += 8  ; @add.ri.u5
L0201d5a4:
    if (r3 != 32) goto L0201d580
    r2 = r4.b0 (u)
    r4 = r2 << 13
    r10 = -8193
    r3 = r4 | r10
    r6 = r2 << 9
    r1 = -513
    r5 = r6 | r1
    r3 &= r5
    r5 = r2 << 6
    r1 = -65
    r1 |= r5
    r15 = r3 & r1
    r3 = r2 << 4
    r14 = -17
    r1 = r3 | r14
    r1 = r1 & r15
    r15 = -16385
    r4 = r4 | r15
    r1 &= r4
    r12 = -1025
    r6 = r6 | r12
    r1 &= r6
    r11 = -129
    r5 = r5 | r11
    r1 &= r5
    r5 = [r13+0]
    r8 = -33
    r9 = r3 | r8
    r1 = r1 & r9
    r1 &= r5
    r9 = [r13+8]
    [r13+0] = r1
    r1 = r2 << 11
    r10 = r10 | r1
    r5 = r2 << 7
    r4 = -513
    r4 |= r5
    r4 = r4 & r10
    r6 = -65
    r6 |= r3
    r4 &= r6
    r2 = r2 << 2
    r6 = r2 | r14
    r4 &= r6
    r1 = r1 | r15
    r1 &= r4
    r4 = r5 | r12
    r1 &= r4
    r3 = r3 | r11
    r1 &= r3
    r2 = r2 | r8
    r8 = L01c3740c
    r1 &= r2
    r1 = r1 & r9
    r9 = L01c1fa30
    [r13+8] = r1
    [r13+0] |= 0xC
    [r13+8] |= 0xC
    goto L0201d6ac
L0201d66a:
    r1 = -26353
    r2 &= r1
    [r13+0] = r2
    [r13+8] &= r1
    [r13+0] |= 0xC
    [r13+8] |= 0xC
    [r13+0] |= 0x800
    [r13+8] |= 0x800
    r1 = 0
    [r3+12] = r1
    [r3+16] = r1
    [r3+20] = r1
    [r10+0] = r1
    [r3+4] = r1
    r2 = [r3+8]
    r2 = r2 & 0x18
    if (r2 != 24) goto L0201d6a8
    r2 = b[r8+0] (u)
    if ((r2 & 1) != 0) goto L0201d6ac
L0201d6a8:
    [r3+0] = r1
    [r3+8] = r1
L0201d6ac:
    r3 = 78080
    r1 = [r3+0]
    [r0+8] = r1
    r1 = 65544
    r2 = [r1+8]
    [r0+12] = r2
    r2 = 0
    r3 = r1 + 6584  #
    [r3+0] = r2
    r4 = [r3+0]
    [r0+16] = r4
    r4 = [r3+4]
    [r0+20] = r4
    r4 = [r3+8]
    [r0+24] = r4
    r4 = [r3+12]
    [r0+28] = r4
    r4 = [r3+28]
    [r0+32] = r4
    r4 = [r3+32]
    [r0+36] = r4
    r4 = [r3+36]
    [r0+40] = r4
    r4 = [r3+40]
    [r0+44] = r4
    r4 = b[r9+95] (u)
    if ((r4 & 0x1) == 0) {
    [r3+0] = r2
    }
    [r3+0] &= 0xFFFFFFFE
    [r3+4] = r2
    [r3+8] = r2
    [r3+12] = r2
    [r3+28] = r2
    [r3+32] = r2
    [r3+36] = r2
    r3 = 0x13C00  #
    [r3+40] = r2
    r5 = [r3+0]
    [r0+48] = r5
    r5 = [r3+4]
    [r0+52] = r5
    [r3+0] = r2
    r3 = 0x13600  #
    [r3+4] = r2
    r5 = [r3+0]
    [r0+56] = r5
    [r3+0] = r2
    [r3+0] |= 0x40
    r1 = [r1+0]
    [r0+60] = r1
    if ((r4 & 2) != 0) goto L0201d7b8
    r10 = 32922
    r0 = r10
    call storage_fault_read_register  ; @call.xl
    r4 = r7 + 128
    r5 = r10 + 1  #
    [r4+0] = r0
    r0 = r5
    call storage_fault_read_register  ; @call.xl
    [r4+4] = r0
    r0 = 154
    call storage_fault_read_register  ; @call.xl
    [r4+8] = r0
    r0 = 155
    call storage_fault_read_register  ; @call.xl
    r6 = r5 + 10
    r0 = r6  #
    [r4+12] = r0
    call storage_fault_read_register  ; @call.xl
    [r4+16] = r0
    r0 = 148
    call storage_fault_read_register  ; @call.xl
    r0 = r10  #
    [r4+20] = r0
    r1 = 3
    call storage_fault_write_register  ; @call.xl
    r1 = 0
    r0 = r5
    call storage_fault_write_register  ; @call.xl
    r0 = 154
    r1 = 3
    call storage_fault_write_register  ; @call.xl
    r0 = 155
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r1 = 0
    r0 = r6
    call storage_fault_write_register  ; @call.xl
    r0 = 148
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r4 = r7 + 152
    goto L0201d7bc
L0201d7b8:
    r4 = r7 + 128
L0201d7bc:
    r0 = 0x13E00
    r1 = [r0+0]
    r1 = 8204  #
    [r4+0] = r1
    [r0+0] = r1
    r0 = 12
    call storage_fault_read_register  ; @call.xl
    [r4+4] = r0
    r0 = 13
    call storage_fault_read_register  ; @call.xl
    [r4+8] = r0
    r0 = 116
    call storage_fault_read_register  ; @call.xl
    [r4+12] = r0
    r0 = 117
    call storage_fault_read_register  ; @call.xl
    [r4+16] = r0
    r0 = 116
    r1 = 192
    call storage_fault_write_register  ; @call.xl
    r0 = 117
    r1 = 214
    call storage_fault_write_register  ; @call.xl
    r0 = 17
    call storage_fault_read_register  ; @call.xl
    [r4+20] = r0
    r0 = 17
    r1 = 0
    r5 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 48
    call storage_fault_read_register  ; @call.xl
    [r4+24] = r0
    r0 = 49
    call storage_fault_read_register  ; @call.xl
    [r4+28] = r0
    r0 = 50
    call storage_fault_read_register  ; @call.xl
    [r4+32] = r0
    r0 = 51
    call storage_fault_read_register  ; @call.xl
    [r4+36] = r0
    r0 = 53
    call storage_fault_read_register  ; @call.xl
    [r4+40] = r0
    r0 = 54
    call storage_fault_read_register  ; @call.xl
    [r4+44] = r0
    r0 = 55
    call storage_fault_read_register  ; @call.xl
    [r4+48] = r0
    r0 = 56
    call storage_fault_read_register  ; @call.xl
    [r4+52] = r0
    r0 = 57
    call storage_fault_read_register  ; @call.xl
    [r4+56] = r0
    r0 = 58
    call storage_fault_read_register  ; @call.xl
    [r4+60] = r0
    r0 = 59
    call storage_fault_read_register  ; @call.xl
    r6 = r4 + 64
    [r6+0] = r0
    r0 = 48
    r1 = 9
    call storage_fault_write_register  ; @call.xl
    r0 = 49
    r1 = 68
    call storage_fault_write_register  ; @call.xl
    r0 = 50
    r1 = 3
    call storage_fault_write_register  ; @call.xl
    r0 = 51
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 53
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 54
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 55
    r1 = 1
    call storage_fault_write_register  ; @call.xl
    r0 = 56
    r1 = 17
    call storage_fault_write_register  ; @call.xl
    r0 = 57
    r1 = 18
    call storage_fault_write_register  ; @call.xl
    r0 = 58
    r1 = 1
    call storage_fault_write_register  ; @call.xl
    r0 = 59
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 0x13400
    r1 = [r0+0]
    [r6+4] = r1
    [r0+0] = r5
    r2 = 32436672
    r0 = [r2+0]
    [r6+8] = r0
    [r2+0] = r5
    r0 = [r2+512]
    r1 = r9 + 104  #
    [r6+12] = r0
    r0 = r4 + 80
    r1 = r0 - r1
    [r2+512] = r5
    ifs (r1 >= 356) goto L0201d940
    r2 = b[r8+0] (u)
    [r9+456] = r5
    if ((r2 & 1) == 0) goto L0201d93e
    [r9+456] = r0
    ifs (r1 >= 308) goto L0201d940
L0201d93e:
    {pc, r15-r4} = [sp++]
L0201d940:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0201d94a:
    goto L0201d94a
L0201d94c:
    [--sp] = {rets, r7-r4}
    r4 = L01c1fa30
    r0 = r4
    r1 = [++r0=104]
    r2 = 327688
    [r2+0] = r1
    r1 = [r0+4]
    [r2+4] = r1
    r1 = [r0+8]
    [r2+8] = r1
    r1 = [r0+12]
    [r2+12] = r1
    r1 = [r0+16]
    r2 += 64
    [r2+0] = r1
    r1 = [r0+20]
    [r2+4] = r1
    r1 = [r0+24]
    [r2+8] = r1
    r1 = [r0+28]
    [r2+12] = r1
    r1 = [r0+32]
    r2 += 64
    [r2+0] = r1
    r1 = [r0+36]
    [r2+4] = r1
    r1 = [r0+40]
    [r2+8] = r1
    r1 = [r0+44]
    [r2+12] = r1
    r1 = L01c3740c
    r1 = b[r1+0] (u)
    if ((r1 & 1) != 0) goto L0201d9da
    r0 = r4
    r1 = [++r0=152]
    r2 = r2 + 128
    [r2+0] = r1
    r1 = [r0+4]
    [r2+4] = r1
    r1 = [r0+8]
    [r2+8] = r1
    r1 = [r0+12]
    [r2+12] = r1
    r1 = [r0+16]
    r2 += 64
    [r2+0] = r1
    r1 = [r0+20]
    [r2+4] = r1
    r1 = [r0+24]
    [r2+8] = r1
    r1 = [r0+28]
    [r2+12] = r1
    r1 = [r0+32]
    r2 += 64
    [r2+0] = r1
    r1 = [r0+36]
    [r2+4] = r1
    r1 = [r0+40]
    [r2+8] = r1
    r1 = [r0+44]
    [r2+12] = r1
L0201d9da:
    r5 = r0 + 48
    r0 = [r5+0]
    r1 = 328136
    [r1+0] = r0
    r0 = [r5+4]
    [r1+4] = r0
    r0 = [r5+8]
    [r1+8] = r0
    r0 = [r5+12]
    r1 = 0x11800  #
    [r1+12] = r0
    r0 = [r5+16]
    [r1+0] = r0
    r0 = [r5+20]
    r1 = r1 + 3840  #
    [r1+4] = r0
    r0 = [r5+24]
    [r1+0] = r0
    r0 = [r5+28]
    r1 = 0x51000  #
    [r1+4] = r0
    r0 = [r5+32]
    [r1+0] = r0
    r0 = [r5+36]
    [r1+4] = r0
    r0 = [r5+40]
    r1 = 0x16A00  #
    [r1+8] = r0
    r0 = [r5+44]
    [r1+12] = r0
    r0 = [r5+48]
    [r1+16] = r0
    r0 = [r5+52]
    [r1+20] = r0
    r0 = [r5+56]
    [r1+0] = r0
    r0 = [r5+60]
    r0 = r5 + 64  #
    [r1+4] = r0
    r2 = [r0+0]
    r2 = 0x16800  #
    [r1+8] = r2
    r1 = [r0+4]
    [r2+0] = r1
    r1 = [r0+8]
    r2 = 78080
    [r2+0] = r1
    r1 = [r0+12]
    r3 = 65544
    [r3+8] = r1
    [r2+0] |= 0x40
    r2 = r2 + -5952  #
    r1 = [r0+16]
    [r2+0] = r1
    r1 = [r0+20]
    [r2+4] = r1
    r1 = [r0+24]
    [r2+8] = r1
    r1 = [r0+28]
    [r2+12] = r1
    r1 = [r0+32]
    [r2+28] = r1
    r1 = [r0+36]
    [r2+32] = r1
    r1 = [r0+40]
    [r2+36] = r1
    r1 = [r0+44]
    r2 = 0x13C00  #
    [r2+40] = r1
    r1 = [r0+48]
    [r2+0] = r1
    r1 = [r0+52]
    r2 = 0x13600  #
    [r2+4] = r1
    r1 = [r0+56]
    [r2+0] = r1
    r0 = [r0+60]
    [r3+0] = r0
    r0 = b[r4+95] (u)
    if ((r0 & 2) != 0) goto L0201daf6
    r6 = r5 + 128
    r1 = b[r6+0] (u)
    r0 = 32922
    call storage_fault_write_register  ; @call.xl
    r1 = b[r6+4] (u)
    r0 = 32923
    call storage_fault_write_register  ; @call.xl
    r1 = b[r6+8] (u)
    r0 = 154
    call storage_fault_write_register  ; @call.xl
    r1 = b[r6+12] (u)
    r0 = 155
    call storage_fault_write_register  ; @call.xl
    r1 = b[r5+144] (u)
    r0 = 32933
    call storage_fault_write_register  ; @call.xl
    r1 = b[r5+148] (u)
    r0 = 148
    call storage_fault_write_register  ; @call.xl
    r5 = r5 + 152
    goto L0201dafa
L0201daf6:
    r5 = r5 + 128
L0201dafa:
    r1 = 0x13E00  #
    r0 = [r5+0]
    [r1+0] = r0
    r1 = b[r5+4] (u)
    r0 = 12
    call storage_fault_write_register  ; @call.xl
    r1 = b[r5+8] (u)
    r0 = 13
    call storage_fault_write_register  ; @call.xl
    r1 = b[r5+12] (u)
    r0 = 116
    call storage_fault_write_register  ; @call.xl
    r6 = r5 + 16
    r1 = b[r6+0] (u)
    r0 = 117
    call storage_fault_write_register  ; @call.xl
    r1 = b[r6+4] (u)
    r0 = 17
    call storage_fault_write_register  ; @call.xl
    r1 = b[r6+8] (u)
    r0 = 48
    call storage_fault_write_register  ; @call.xl
    r1 = b[r6+12] (u)
    r0 = 49
    call storage_fault_write_register  ; @call.xl
    r7 = r5 + 32
    r1 = b[r7+0] (u)
    r0 = 50
    call storage_fault_write_register  ; @call.xl
    r1 = b[r7+4] (u)
    r0 = 51
    call storage_fault_write_register  ; @call.xl
    r1 = b[r7+8] (u)
    r0 = 53
    call storage_fault_write_register  ; @call.xl
    r1 = b[r7+12] (u)
    r0 = 54
    call storage_fault_write_register  ; @call.xl
    r7 = r5 + 48
    r1 = b[r7+0] (u)
    r0 = 55
    call storage_fault_write_register  ; @call.xl
    r1 = b[r7+4] (u)
    r0 = 56
    call storage_fault_write_register  ; @call.xl
    r1 = b[r7+8] (u)
    r0 = 57
    call storage_fault_write_register  ; @call.xl
    r1 = b[r7+12] (u)
    r0 = 58
    call storage_fault_write_register  ; @call.xl
    r1 = b[r5+64] (u)
    r0 = 59
    call storage_fault_write_register  ; @call.xl
    r1 = 0x13400  #
    r0 = [r6+52]
    [r1+0] = r0
    r0 = [r6+56]
    r1 = 32436672
    r2 = r4 + 104  #
    [r1+0] = r0
    r3 = r5 + 80  #
    r0 = [r6+60]
    r2 = r3 - r2
    [r1+512] = r0
    ifs (r2 >= 356) goto L0201dbd6
    {pc, r7-r4} = [sp++]
L0201dbd6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0201dbe0:
    goto L0201dbe0
L0201dbe2:
    [--sp] = {rets, r5, r4}
    r2 = r0
    call storage_fault_acquire  ; @call.xl
    r5 = 81416
    [r5+0] &= 0xFFFFFEFF
    [r5+0] |= 0x1
    r0 = 32
    call storage_fault_exchange  ; @call.xl
    r0 = 96
    call storage_fault_exchange  ; @call.xl
    r0 = r2
    call storage_fault_exchange  ; @call.xl
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r2 = r0
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r3 = r0
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r4 = r0
    r0 = 0
    call storage_fault_exchange  ; @call.xl
    r1 = -258
    [r5+0] &= r1
    r1 = r2 << 24
    r1 <= insert(r3, p:16, l:8)
    r1 <= insert(r4, p:8, l:8)
    r0 |= r1
    r1 = 1000000
    r5_r4 = r0 * r1 (u)
    call storage_fault_release  ; @call.xl
    r0 = L01c1fa30
    r0 = [r0+460]
    r1_r0 = r5_r4 / r0 (u)
    {pc, r5, r4} = [sp++]
