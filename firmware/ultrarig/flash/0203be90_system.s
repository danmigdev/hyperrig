; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0203be90..0x0203bebe: system layer code (not reversed), as instructions
L0203be90:
    [--sp] = {rets, r4}
    r0 = 104
    call L0203c15c  ; @call.xl
    r4 = r0
    r0 = L01c267d0
    [r0+0] = r4
    if (r4 == 0) goto L0203bebc
    r1 = 0
    r2 = 104
    r0 = r4
    call effect_enable_memset  ; @call.xl
    r0 = phase3_p3_update_common_state_cbk
    [r4+96] = r0
L0203bebc:
    {pc, r4} = [sp++]

; 0x0203bebe..0x0203c018: data
    .fill ((30 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0203bebe:
    .byte 0x00,0x00
L0203bec0:
    .byte 0x49,0x4e,0x43,0x4c,0x55,0x44,0x45,0x5f,0x42,0x54,0x43,0x54,0x52,0x4c,0x45,0x52
    .byte 0x2d,0x24,0x36,0x35,0x35,0x36,0x34,0x62,0x30,0x00,0x49,0x4e,0x43,0x4c,0x55,0x44
    .byte 0x45,0x5f,0x42,0x54,0x53,0x54,0x41,0x43,0x4b,0x2d,0x24,0x35,0x30,0x37,0x65,0x61
    .byte 0x65,0x30,0x00,0x49,0x4e,0x43,0x4c,0x55,0x44,0x45,0x5f,0x44,0x52,0x49,0x56,0x45
    .byte 0x52,0x2d,0x24,0x61,0x35,0x66,0x35,0x66,0x62,0x63,0x00,0x49,0x4e,0x43,0x4c,0x55
    .byte 0x44,0x45,0x5f,0x4d,0x45,0x44,0x49,0x41,0x2d,0x24,0x61,0x36,0x32,0x62,0x30,0x32
    .byte 0x37,0x00,0x49,0x4e,0x43,0x4c,0x55,0x44,0x45,0x5f,0x4e,0x45,0x54,0x2d,0x24,0x37
    .byte 0x66,0x37,0x32,0x32,0x36,0x30,0x00,0x49,0x4e,0x43,0x4c,0x55,0x44,0x45,0x5f,0x53
    .byte 0x45,0x52,0x56,0x45,0x52,0x2d,0x24,0x35,0x36,0x34,0x39,0x37,0x64,0x61,0x00,0x49
    .byte 0x4e,0x43,0x4c,0x55,0x44,0x45,0x5f,0x53,0x59,0x53,0x54,0x45,0x4d,0x2d,0x24,0x64
    .byte 0x36,0x30,0x34,0x63,0x38,0x34,0x00,0x49,0x4e,0x43,0x4c,0x55,0x44,0x45,0x5f,0x55
    .byte 0x50,0x44,0x41,0x54,0x45,0x2d,0x24,0x61,0x63,0x64,0x62,0x64,0x38,0x65,0x00,0x49
    .byte 0x4e,0x43,0x4c,0x55,0x44,0x45,0x5f,0x55,0x54,0x49,0x4c,0x53,0x2d,0x24,0x30,0x38
    .byte 0x39,0x66,0x30,0x31,0x62,0x00,0x4e,0x45,0x54,0x2d,0x24,0x30,0x31,0x36,0x32,0x34
    .byte 0x66,0x37,0x33,0x00,0x53,0x45,0x52,0x56,0x45,0x52,0x2d,0x24,0x65,0x32,0x65,0x32
    .byte 0x66,0x64,0x65,0x00,0x55,0x54,0x49,0x4c,0x53,0x2d,0x24,0x37,0x35,0x63,0x38,0x32
    .byte 0x37,0x66,0x00,0x44,0x52,0x49,0x56,0x45,0x52,0x2d,0x24,0x63,0x35,0x39,0x33,0x36
    .byte 0x39,0x33,0x65,0x00,0x53,0x59,0x53,0x54,0x45,0x4d,0x2d,0x24,0x62,0x31,0x39,0x62
    .byte 0x37,0x39,0x37,0x00,0x55,0x50,0x44,0x41,0x54,0x45,0x2d,0x24,0x62,0x61,0x63,0x36
    .byte 0x34,0x38,0x37,0x00,0x42,0x54,0x43,0x54,0x52,0x4c,0x45,0x52,0x2d,0x24,0x35,0x36
    .byte 0x35,0x36,0x30,0x36,0x37,0x00,0x42,0x54,0x53,0x54,0x41,0x43,0x4b,0x2d,0x24,0x33
    .byte 0x63,0x64,0x38,0x31,0x33,0x36,0x00
L0203c017:
    .byte 0x00

; 0x0203c018..0x0203e18c: system layer code (not reversed), as instructions
L0203c018:
    [--sp] = {rets, r5, r4}
    r2 = L01c26890
    r3 = 0
    b[r2+69] = r3
    r0 = 8220
    b[r2+r0] = r3
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 69
L0203c03a:
    testset b[r0]
    ifeq goto L0203c03a
    csync
    r0 = 524
    r0 = [r2+r0<<2]
    if (r0 == 0) goto L0203c05a
L0203c04c:
    csync
    b[r2+69] = r3
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
L0203c05a:
    r0 = r2 + 2096
    r4 = r3 + 4096
    r5 = r4
    d[r0+4] = r5_r4
    r4 = r3 + 0xFFFFFFFF  ; @add.modimm.rri
    r5 = r3 + 0x200000
    d[r0+12] = r5_r4
    r1 = 2
    r4 = 2054  #
    [r0+20] = r1
    [r2+r4<<2] = r1
    r1 = L01c1f180
    r1 = [r1+24]
    r1 = r1 & 0xFFFFFFF0
    r4 = 1437226408
    r1 ^= r4
    [r0+0] = r1
    goto L0203c04c
L0203c098:
    r1 = r0
    r0 = 8224
    r2 = L01c26890
    r0 += r2  ; @add.rr
L0203c0a6:
    r2 = [r0+0]
    if (r2 > r1) goto L0203c0b4
    r3 = [r0+4]
    r2 += r3  ; @add.rr
    if (r2 > r1) goto L0203c0ba
L0203c0b4:
    r0 = [r0+8]
    if (r0 != 0) goto L0203c0a6
    r0 = 0
L0203c0ba:
    rts
L0203c0bc:
    [--sp] = {rets, r10-r4}
    r9 = 1
    r3 = 1
    ifs (r0 <= 0) {  ; @ifs.le.ri.s12
    r3 = 0
    }
    r8 = L01c25cf4
    r7 = [r8+0]
    if (r7 != 0) {  ; @if.ne.ri.s12
    r5 = r7
    } else {
    r5 = ultrarig_heap_start
    }
    r6 = r5 + r0
    r10 = 29883296
    r2 = 1
    if (r6 < r10) {
    r2 = 0
    }
    r1 = -1
    if ((r3 & r2) == 0) {
    r1 = r5
    }
    r4 = 1
    ifs (r0 >= 1) {  ; @ifs.ge.ri.s12
    r4 = 0
    }
    if (r6 >= r10) {
    r9 = 0
    }
    if (r7 == 0) goto L0203c10e
    r0 = r4 | r9
    if (r0 == 0) goto L0203c11a
L0203c10e:
    r0 = r3 & r2
    if (r0 != 0) goto L0203c116
    r5 = r6
L0203c116:
    [r8+0] = r5
L0203c11a:
    r0 = r1
    {pc, r10-r4} = [sp++]
L0203c11e:
    [--sp] = {rets, r4}
    r2 = -8
    r2 = r2 - r0
    r3 = r2 & 0x1F
    r4 = r0 + 8
    r2 = 0
    if ((r4 & 0x1F) != 0) {
    r2 = r3
    }
    r0 += r2  ; @add.rr
    r3 = L01c26890
    r4 = r3 + 7784
    r1 = r1 - r2  #
    [r4+12] = r0
    r2 = r1 | 0x1  #
    [r4+0] = r1
    r0 += r1  #  ; @add.rr.p
    [r0+4] = r2
    [r0+4] = 0x58
    r0 = 528
    r0 = [r3+r0<<2]
    [r4+16] = r0
    {pc, r4} = [sp++]
L0203c15c:
    [--sp] = {rets, r15-r4}
    r1 = 524
    r12 = L01c26890
    r1 = [r12+r1<<2]
    r4 = r0
    if (r1 != 0) goto L0203c174
    call L0203c018
L0203c174:
    r0 = 8216
    r0 = b[r12+r0] (u)
    if ((r0 & 2) == 0) goto L0203c198
    r0 = 8220
    r2 = r12 + r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0203c190:
    testset b[r2]
    ifeq goto L0203c190
    csync
L0203c198:
    if (r4 > 220) goto L0203c206
    r0 = r4 + 35
    r0 = r0 & 0xFFFFFFE0
    r6 = 32
    if (r4 >= 27) {  ; @if.ge.ri.s12
    r6 = r0
    }
    r0 = 1943
    r15 = [r12+r0<<2]
    r2 = r6 >> 3
    r3 = r15 >> r2
    if ((r3 & 0x3) == 0) goto L0203c2d6
    r1 = r3 & 0x1
    r1 |= r2
    r5 = r1 ^ 0x1
    r3 = r5 << 3
    r1 = r3 + r12
    r4 = r1 + 7812
    r1 = [r4+8]
    r2 = [r1+4]
    r2 = r2 & 0xFFFFFFF8
    if (r2 != r3) goto L0203c200
    r6 = [r1+8]
    if (r1 == r4) goto L0203c202
    if (r1 == r6) goto L0203c204
    r3 = r1 + 8
    if (r4 == r6) goto L0203c60a
    r0 += 4  ; @add.ri.u5
    r0 = [r12+r0<<2]
    if (r6 >= r0) goto L0203c618
L0203c1fe:
    goto L0203c1fe
L0203c200:
    goto L0203c200
L0203c202:
    goto L0203c202
L0203c204:
    goto L0203c204
L0203c206:
    r0 = -129
    r6 = -1
    if (r4 > r0) goto L0203c502
    r0 = 1944
    r9 = [r12+r0<<2]
    r0 = r4 + 35
    r6 = r0 & 0xFFFFFFE0
    if (r9 == 0) goto L0203c502
    r0 = r0 >> 8
    r1 = 0
    r10 = 0
    if (r0 == 0) goto L0203c27a
    r2 = r6 >> 24
    r10 = 31
    if (r2 != 0) goto L0203c27a
    r2 = 1048320
    r2 += r0  ; @add.rr
    r2 = r2 >> 16
    r2 = r2 & 0x8
    r0 <<= r2
    r3 = r0 + 0x7F000
    r3 = r3 >> 16
    r3 = r3 & 0x4
    r0 <<= r3
    r4 = r0 + 0x3C000
    r4 = r4 >> 16
    r4 = r4 & 0x2
    r0 <<= r4
    r0 = r0 >> 15
    r2 |= r3
    r2 |= r4
    r2 = 0xE - r2
    r0 += r2  ; @add.rr
    r2 = r0 + 7
    r2 = r6 >> r2
    r10 = r2 & 0x1
    r10 <= insert(r0, p:1, l:31)
L0203c27a:
    r8 = r12 + 8076
    r5 = [r8+r10<<2]
    r2 = 0x0 - r6
    if (r5 == 0) goto L0203c366
    r0 = r10 >> 1
    r0 = 0x19 - r0
    r3 = 0
    if (r10 != 31) {  ; @if.ne.ri.s12
    r3 = r0
    }
    r7 = r6 << r3
    r0 = 0
L0203c29e:
    r3 = [r5+4]
    r3 = r3 & 0xFFFFFFF8
    r4 = r3 - r6
    if (r4 >= r2) goto L0203c2b2
    r2 = r4
    r0 = r5
    if (r4 == 0) goto L0203c488
L0203c2b2:
    r3 = r7 >> 31
    r3 = r3 << 2
    r3 += r5  #  ; @add.rr.p
    r5 = [r5+20]
    r3 = r1  #
    r4 = [r3+16]
    if (r5 != r4) {
    r3 = r5
    }
    if (r5 == 0) goto L0203c2c8
    r1 = r3
L0203c2c8:
    r3 = 1
    if (r4 != 0) goto L0203c2ce
    r3 = r4
L0203c2ce:
    r7 <<= r3
    r5 = r4
    if (r4 != 0) goto L0203c29e
    goto L0203c368
L0203c2d6:
    r1 = r0 + 2
    r14 = [r12+r1<<2]
    if (r6 <= r14) goto L0203c502
    if (r3 == 0) goto L0203c3ca
    r1 = 2
    r1 <<= r2
    r4 = 0x0 - r1
    r1 |= r4
    r2 = r3 << r2
    r1 &= r2
    r2 = 0x0 - r1
    r1 &= r2
    r1 += -1
    r2 = r1 >> 12
    r2 = r2 & 0x10
    r1 >>= r2
    r3 = r1 >> 5
    r3 = r3 & 0x8
    r1 >>= r3
    r4 = r1 >> 2
    r4 = r4 & 0x4
    r1 >>= r4
    r5 = r1 >> 1
    r5 = r5 & 0x2
    r1 >>= r5
    r7 = uextra(r1, p:1, l:1)
    r1 >>= r7
    r2 |= r3
    r2 |= r4
    r2 |= r5
    r2 |= r7
    r5 = r2 + r1
    r1 = r5 << 3
    r2 = r1 + r12
    r2 = r2 + 7812
    r3 = [r2+8]
    r4 = [r3+4]
    r4 = r4 & 0xFFFFFFF8
    if (r4 != r1) goto L0203c360
    r7 = [r3+8]
    if (r3 == r2) goto L0203c362
    if (r3 == r7) goto L0203c364
    if (r2 == r7) goto L0203c756
    r1 = r0 + 4
    r1 = [r12+r1<<2]
    if (r7 >= r1) goto L0203c76a
L0203c35e:
    goto L0203c35e
L0203c360:
    goto L0203c360
L0203c362:
    goto L0203c362
L0203c364:
    goto L0203c364
L0203c366:
    r0 = 0
L0203c368:
    r3 = r1 | r0
    if (r3 != 0) goto L0203c3c6
    r0 = 2
    r0 = r0 << r10
    r1 = 0x0 - r0
    r1 |= r0
    r0 = 0
    if ((r9 & r1) == 0) goto L0203c48c
    r1 = r1 & r9
    r3 = 0x0 - r1
    r1 &= r3
    r1 += -1
    r3 = r1 >> 12
    r10 = r3 & 0x10
    r1 = r1 >> r10
    r4 = r1 >> 5
    r4 = r4 & 0x8
    r1 >>= r4
    r5 = r1 >> 2
    r5 = r5 & 0x4
    r1 >>= r5
    r7 = r1 >> 1
    r7 = r7 & 0x2
    r1 >>= r7
    r3 = uextra(r1, p:1, l:1)
    r1 >>= r3
    r4 = r4 | r10
    r4 |= r5
    r4 |= r7
    r3 |= r4
    r1 += r3  ; @add.rr
    r5 = [r8+r1<<2]
    goto L0203c4b4
L0203c3c6:
    r5 = r1
    goto L0203c4b4
L0203c3ca:
    r1 = r0 + 1
    r11 = [r12+r1<<2]
    if (r11 == 0) goto L0203c502
    r1 = 0x0 - r11
    r1 = r1 & r11
    r1 += -1
    r2 = r1 >> 12
    r2 = r2 & 0x10
    r1 >>= r2
    r3 = r1 >> 5
    r3 = r3 & 0x8
    r1 >>= r3
    r4 = r1 >> 2
    r4 = r4 & 0x4
    r1 >>= r4
    r5 = r1 >> 1
    r5 = r5 & 0x2
    r1 >>= r5
    r7 = uextra(r1, p:1, l:1)
    r1 >>= r7
    r2 |= r3
    r2 |= r4
    r2 |= r5
    r2 |= r7
    r1 += r2  ; @add.rr
    r2 = r12 + 8076
    r7 = [r2+r1<<2]
    r4 = r7  #
    r1 = [r7+4]
    r1 = r1 & 0xFFFFFFF8
    r5 = r1 - r6
    goto L0203c434
L0203c422:
    r7 = r4  #
    r0 = [r4+4]
    r0 = r0 & 0xFFFFFFF8
    r5 = r0 - r6
    if (r5 >= r3) {
    r5 = r3
    r7 = r2
    }
L0203c434:
    r0 = [++r4=16]
    r2 = r7
    r3 = r5
    r1 = 1
    if (r0 == 0) goto L0203c442
    r1 = 0
L0203c442:
    r4 = [r4+r1<<2]
    if (r4 != 0) goto L0203c422
    r0 = 1947
    r13 = [r12+r0<<2]
    if (r2 < r13) goto L0203c486
    r1 = r3 + r6  #
    r0 = [r2+4]
    r9 = r0 & 0xFFFFFFF8
    r8 = r2 + r6
    if (r9 != r1) goto L0203c484
    if (r2 >= r8) goto L0203c486
    r7 = [r2+12]
    r10 = [r2+24]
    if (r7 == r2) goto L0203c762
    r1 = [r2+8]
    if (r1 < r13) goto L0203c482
    r0 = [r1+12]
    if (r0 == r2) goto L0203c832
L0203c482:
    goto L0203c482
L0203c484:
    goto L0203c484
L0203c486:
    goto L0203c486
L0203c488:
    r2 = 0
    goto L0203c4b4
L0203c48c:
    r5 = 0
    goto L0203c4b4
L0203c490:
    r3 = r5  #
    r1 = [r5+4]
    r1 = r1 & 0xFFFFFFF8
    r1 = r1 - r6
    if (r1 >= r2) {
    r1 = r2
    r3 = r0
    }
    r2 = [++r5=16]
    r0 = 1
    if (r2 == 0) goto L0203c4ac
    r0 = 0
L0203c4ac:
    r5 = [r5+r0<<2]
    r2 = r1
    r0 = r3
L0203c4b4:
    if (r5 != 0) goto L0203c490
    if (r0 == 0) goto L0203c502
    r1 = 1945
    r1 = [r12+r1<<2]
    r1 = r1 - r6
    if (r2 >= r1) goto L0203c502
    r1 = 1947
    r1 = [r12+r1<<2]
    if (r0 < r1) goto L0203c55e
    r4 = r2 + r6  #
    r3 = [r0+4]
    r11 = r3 & 0xFFFFFFF8
    r8 = r0 + r6
    if (r11 != r4) goto L0203c500
    if (r0 >= r8) goto L0203c55e
    r5 = [r0+12]
    r10 = [r0+24]
    if (r5 == r0) goto L0203c632
    r3 = [r0+8]
    if (r3 < r1) goto L0203c4fe
    r1 = [r3+12]
    if (r1 == r0) goto L0203c7fa
L0203c4fe:
    goto L0203c4fe
L0203c500:
    goto L0203c500
L0203c502:
    r0 = 1945
    r1 = [r12+r0<<2]
    if (r1 >= r6) goto L0203c534
    r0 += 1  ; @add.ri.u5
    r0 = [r12+r0<<2]
    if (r0 <= r6) goto L0203c560
L0203c518:
    r0 = r0 - r6
    r1 = r12 + 7784
    [r1+0] = r0
    r2 = [r1+12]
    r3 = r2 + r6
    [r1+12] = r3
    r0 |= 1
    r0 = r6 | 0x3  #
    [r3+4] = r0
    [r2+4] = r0
L0203c530:
    r3 = r2 + 8
    goto L0203c5e0
L0203c534:
    r2 = r0 + 3
    r0 = [r12+r2<<2]
    r3 = r1 - r6
    if (r3 < 32) goto L0203c5c4
    r1 = r0 + r6
    [r12+r2<<2] = r1
    r2 += -3
    [r12+r2<<2] = r3
    r2 = r3 | 0x1
    [r1+4] = r2
    [r1+r3] = r3
    r1 = r6 | 0x3
    [r0+4] = r1
    goto L0203c5de
L0203c55e:
    goto L0203c55e
L0203c560:
    r0 = 524
    r0 = [r12+r0<<2]
    if (r0 != 0) goto L0203c56e
    call L0203c018
L0203c56e:
    r0 = 526
    r0 = [r12+r0<<2]
    r4 = r6 + 119
    r1 = r0 + r4
    r0 = 0x0 - r0
    r5 = r1 & r0
    r3 = 0
    if (r5 <= r6) goto L0203c5e0
    r0 = 2053
    r0 = [r12+r0<<2]
    if (r0 == 0) goto L0203c5a6
    r1 = 2051
    r2 = [r12+r1<<2]
    r1 = r2 + r5
    if (r1 <= r2) goto L0203c5e0
    if (r1 > r0) goto L0203c5e0
L0203c5a6:
    r0 = 8216
    r0 = b[r12+r0] (u)
    if ((r0 & 4) != 0) goto L0203c602
    r0 = 1949
    r0 = [r12+r0<<2]
    if (r0 == 0) goto L0203c63c
    call L0203c098
    r8 = r0
    goto L0203c63e
L0203c5c4:
    r3 = 1945
    r4 = 0
    [r12+r3<<2] = r4
    [r12+r2<<2] = r4
    r2 = r1 | 0x3
    r1 += r0  #  ; @add.rr.p
    [r0+4] = r2
L0203c5da:
    [r1+4] |= 0x1
L0203c5de:
    r3 = r0 + 8
L0203c5e0:
    r0 = 8216
    r0 = b[r12+r0] (u)
    if ((r0 & 2) == 0) goto L0203c5fe
    csync
    r0 = 8220
    r1 = 0
    b[r12+r0] = r1
    call storage_coordination_irq_leave  ; @call.xl
L0203c5fe:
    r0 = r3
    {pc, r15-r4} = [sp++]
L0203c602:
    r10 = -1
    r9 = 0
    goto L0203cace
L0203c60a:
    r0 = r15 & ~(1 << r5)
    r4 = 1943
    [r12+r4<<2] = r0
    goto L0203c624
L0203c618:
    r0 = [r6+12]
    if (r0 != r1) goto L0203c1fe
    [r6+12] = r4
    [r4+8] = r6
L0203c624:
    r0 = r2 | 0x3
    r0 = r1 + r2  #
    [r1+4] = r0
    [r0+4] |= 0x1
    goto L0203c5e0
L0203c632:
    r3 = [r0+20]
    if (r3 == 0) goto L0203c7cc
    r7 = r0 + 20
    goto L0203c7d4
L0203c63c:
    r8 = 0
L0203c63e:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r12 + 69
L0203c64a:
    testset b[r0]
    ifeq goto L0203c64a
    csync
    if (r8 == 0) goto L0203c6a0
    r0 = 526
    r1 = 1946
    r1 = [r12+r1<<2]
    r0 = [r12+r0<<2]
    r1 = r4 - r1
    r1 += r0  ; @add.rr
    r0 = 0x0 - r0
    r9 = r1 & r0
    r0 = 2147483646
    r11 = 0
    if (r9 > r0) goto L0203cab0
    r0 = r9
    call L0203c0bc
    r1 = [r8+4]
    r2 = [r8+0]
    r1 += r2  ; @add.rr
    r10 = r0
    if (r0 != r1) goto L0203c712
    r11 = r9
    if (r0 != -1) goto L0203cac0
    goto L0203cab0
L0203c6a0:
    r0 = 0
    r11 = 0
    call L0203c0bc
    r10 = r0
    if (r0 == -1) goto L0203cab0
    r0 = 525
    r0 = [r12+r0<<2]
    r1 = r0 + -1
    r9 = r5
    if ((r1 & r10) == 0) goto L0203c6d2
    r2 = r5 - r10
    r1 += r10
    r0 = 0x0 - r0
    r0 &= r1
    r9 = r2 + r0
L0203c6d2:
    if (r9 <= r6) goto L0203cab0
    r0 = 2147483646
    if (r9 > r0) goto L0203cab0
    r0 = 2053
    r0 = [r12+r0<<2]
    if (r0 == 0) goto L0203c706
    r1 = 2051
    r2 = [r12+r1<<2]
    r1 = r2 + r9
    if (r1 <= r2) goto L0203cab0
    if (r1 > r0) goto L0203cab0
L0203c706:
    r0 = r9
    call L0203c0bc
    if (r0 == r10) goto L0203cac0
L0203c712:
    r1 = r6 + 120
    r10 = r0
    if (r1 <= r9) goto L0203c7f2
    r0 = 2147483646
    if (r9 > r0) goto L0203c7f2
    if (r10 == -1) goto L0203c7f2
    r1 = 526
    r1 = [r12+r1<<2]
    r2 = r4 - r9
    r2 += r1  ; @add.rr
    r1 = 0x0 - r1
    r8 = r2 & r1
    if (r8 > r0) goto L0203cac0
    r0 = r8
    call L0203c0bc
    if (r0 == -1) goto L0203caa8
    r9 += r8
    goto L0203cac0
L0203c756:
    r15 = r15 & ~(1 << r5)
    r1 = r0
    [r12+r1<<2] = r15
    goto L0203c776
L0203c762:
    r5 = [r2+20]
    if (r5 == 0) goto L0203c808
    r4 = r2 + 20
    goto L0203c814
L0203c76a:
    r1 = [r7+12]
    if (r1 != r3) goto L0203c35e
    [r7+12] = r2
    [r2+8] = r7
L0203c776:
    r1 = r6 | 0x3
    r2 = r3 + r6  #
    [r3+4] = r1
    r4 = r4 - r6
    r1 = r4 | 0x1
    [r2+4] = r1
    [r2+r4] = r4
    if (r14 >= 256) goto L0203c7c8
    r3 += 8  ; @add.ri.u5
    if (r14 == 0) goto L0203ce84
    r5 = r14 >> 3
    r1 = r0 + 5
    r6 = r5 << 3
    r6 += r12
    if (r14 <= 31) goto L0203c7ca
    r1 = [r12+r1<<2]
    r7 = 1
    r7 <<= r5
    r5 = r6 + 7812
    if ((r15 & r7) == 0) goto L0203ce6c
    r0 += 4  ; @add.ri.u5
    r7 = [r12+r0<<2]
    r0 = r5
    r6 = [++r0=8]
    if (r6 >= r7) goto L0203ce7c
L0203c7c6:
    goto L0203c7c6
L0203c7c8:
    goto L0203c7c8
L0203c7ca:
    goto L0203c7ca
L0203c7cc:
    r7 = r0
    r3 = [++r7=16]
    if (r3 == 0) goto L0203c840
L0203c7d4:
    r5 = r3
    r4 = r7  #
    r3 = [r5+20]
    r7 = r5 + 20
    if (r3 != 0) goto L0203c7d4
    r7 = r5
    r3 = [++r7=16]
    if (r3 != 0) goto L0203c7d4
    if (r4 < r1) goto L0203c7f0
    [r4+0] = 0x0
    goto L0203c842
L0203c7f0:
    goto L0203c7f0
L0203c7f2:
    if (r10 != -1) goto L0203cac0
    goto L0203cab0
L0203c7fa:
    r1 = [r5+8]
    if (r1 != r0) goto L0203c4fe
    [r3+12] = r5
    [r5+8] = r3
    goto L0203c842
L0203c808:
    r4 = r2
    r5 = [++r4=16]
    if (r5 == 0) goto L0203ca2c
L0203c814:
    r7 = r5
    r1 = r4  #
    r5 = [r7+20]
    r4 = r7 + 20
    if (r5 != 0) goto L0203c814
    r4 = r7
    r5 = [++r4=16]
    if (r5 != 0) goto L0203c814
    if (r1 < r13) goto L0203c830
    [r1+0] = 0x0
    goto L0203ca2e
L0203c830:
    goto L0203c830
L0203c832:
    r0 = [r7+8]
    if (r0 != r2) goto L0203c482
    [r1+12] = r7
    [r7+8] = r1
    goto L0203ca2e
L0203c840:
    r5 = 0
L0203c842:
    if (r10 == 0) goto L0203c8c2
    r1 = [r0+28]
    r3 = r1 << 2
    r3 += r12
    r3 = r3 + 8076
    r4 = [r3+0]
    if (r0 == r4) goto L0203c87a
    r1 = 1947
    r1 = [r12+r1<<2]
    if (r10 < r1) goto L0203c878
    r1 = r10
    r4 = [++r1=16]
    r3 = 1
    if (r4 == r0) {
    r3 = 0
    }
    [r1+r3<<2] = r5
    if (r5 != 0) goto L0203c87e
    goto L0203c8c2
L0203c878:
    goto L0203c878
L0203c87a:
    [r3+0] = r5
    if (r5 == 0) goto L0203c8b6
L0203c87e:
    r1 = 1947
    r1 = [r12+r1<<2]
    if (r5 < r1) goto L0203c8b0
    [r5+24] = r10
    r3 = [r0+16]
    if (r3 == 0) goto L0203c89a
    if (r3 < r1) goto L0203c8b2
    [r5+16] = r3
    [r3+24] = r5
L0203c89a:
    r1 = [r0+20]
    if (r1 == 0) goto L0203c8c2
    r3 = 1947
    r3 = [r12+r3<<2]
    if (r1 < r3) goto L0203c8b4
    [r5+20] = r1
    [r1+24] = r5
    goto L0203c8c2
L0203c8b0:
    goto L0203c8b0
L0203c8b2:
    goto L0203c8b2
L0203c8b4:
    goto L0203c8b4
L0203c8b6:
    r9 = r9 & ~(1 << r1)
    r1 = 1944
    [r12+r1<<2] = r9
L0203c8c2:
    if (r2 > 31) goto L0203c8d2
    r1 = r11 | 0x3
    r1 = r0 + r11  #
    [r0+4] = r1
    goto L0203c5da
L0203c8d2:
    r1 = r6 | 0x3
    r1 = r2 | 0x1  #
    [r0+4] = r1
    [r8+4] = r1
    [r8+r2] = r2
    if (r2 > 255) goto L0203c914
    r1 = r2 >> 3
    r4 = 1
    r2 = 1943
    r3 = [r12+r2<<2]
    r4 <<= r1
    r1 = r1 << 3
    r1 += r12
    r1 = r1 + 7812
    if ((r3 & r4) == 0) goto L0203c962
    r2 += 4  ; @add.ri.u5
    r4 = [r12+r2<<2]
    r2 = r1
    r3 = [++r2=8]
    if (r3 >= r4) goto L0203c96c
L0203c912:
    goto L0203c912
L0203c914:
    r3 = r2 >> 8
    if (r3 == 0) goto L0203c97e
    r4 = r2 >> 24
    r1 = 31
    if (r4 != 0) goto L0203c980
    r1 = 1048320
    r1 += r3  ; @add.rr
    r1 = r1 >> 16
    r1 = r1 & 0x8
    r3 <<= r1
    r4 = r3 + 0x7F000
    r4 = r4 >> 16
    r4 = r4 & 0x4
    r3 <<= r4
    r5 = r3 + 0x3C000
    r5 = r5 >> 16
    r5 = r5 & 0x2
    r3 <<= r5
    r3 = r3 >> 15
    r1 |= r4
    r1 |= r5
    r1 = 0xE - r1
    r3 += r1  ; @add.rr
    r1 = r3 + 7
    r1 = r2 >> r1
    r1 = r1 & 0x1
    r1 <= insert(r3, p:1, l:31)
    goto L0203c980
L0203c962:
    r3 |= r4
    [r12+r2<<2] = r3
    r2 = r1 + 8
    r3 = r1
L0203c96c:
    [r2+0] = r8
    [r3+12] = r8
    [r8+8] = r3
    [r8+12] = r1
    goto L0203c5de
L0203c97e:
    r1 = 0
L0203c980:
    [r8+28] = r1
    r4 = 0
    r5 = 0
    d[r8+16] = r5_r4
    r3 = 1
    r4 = r3 << r1
    r3 = r1 << 2
    r3 += r12
    r3 = r3 + 8076
    if ((r9 & r4) == 0) goto L0203c9e4
    r4 = r1 >> 1
    r5 = 0x19 - r4
    r4 = 0
    if (r1 != 31) {  ; @if.ne.ri.s12
    r4 = r5
    }
    r3 = r2 << r4  #
    r5 = [r3+0]
L0203c9b2:
    r1 = r5
    r4 = [r1+4]
    r4 = r4 & 0xFFFFFFF8
    if (r4 == r2) goto L0203ca02
    r4 = r3 >> 31
    r4 = r4 << 2
    r4 += r1  ; @add.rr
    r5 = [++r4=16]
    r3 = r3 << 1
    if (r5 != 0) goto L0203c9b2
    r2 = 1947
    r2 = [r12+r2<<2]
    if (r4 < r2) goto L0203c9e2
    [r4+0] = r8
    [r8+24] = r1
    goto L0203c9f8
L0203c9e2:
    goto L0203c9e2
L0203c9e4:
    r1 = r9 | r4
    r2 = 1944
    [r12+r2<<2] = r1
    [r3+0] = r8
    [r8+24] = r3
L0203c9f8:
    [r8+12] = r8
    [r8+8] = r8
    goto L0203c5de
L0203ca02:
    r2 = 1947
    r3 = [r12+r2<<2]
    r2 = [r1+8]
    if (r2 < r3) goto L0203ca2a
    if (r1 < r3) goto L0203ca2a
    [r2+12] = r8
    [r1+8] = r8
    [r8+8] = r2
    [r8+12] = r1
    [r8+24] = 0x0
    goto L0203c5de
L0203ca2a:
    goto L0203ca2a
L0203ca2c:
    r7 = 0
L0203ca2e:
    if (r10 == 0) goto L0203ce00
    r1 = [r2+28]
    r0 = r1 << 2
    r0 += r12
    r4 = r0 + 8076
    r0 = [r4+0]
    if (r2 == r0) goto L0203ca68
    r0 = 1947
    r0 = [r12+r0<<2]
    if (r10 < r0) goto L0203ca66
    r1 = r10
    r0 = [++r1=16]
    r4 = 1
    if (r0 == r2) {
    r4 = 0
    }
    [r1+r4<<2] = r7
    if (r7 != 0) goto L0203ca70
    goto L0203ce00
L0203ca66:
    goto L0203ca66
L0203ca68:
    [r4+0] = r7
    if (r7 == 0) goto L0203cdf4
L0203ca70:
    r0 = 1947
    r1 = [r12+r0<<2]
    if (r7 < r1) goto L0203caa2
    [r7+24] = r10
    r4 = [r2+16]
    if (r4 == 0) goto L0203ca8c
    if (r4 < r1) goto L0203caa4
    [r7+16] = r4
    [r4+24] = r7
L0203ca8c:
    r1 = [r2+20]
    if (r1 == 0) goto L0203ce00
    r0 = [r12+r0<<2]
    if (r1 < r0) goto L0203caa6
    [r7+20] = r1
    [r1+24] = r7
    goto L0203ce00
L0203caa2:
    goto L0203caa2
L0203caa4:
    goto L0203caa4
L0203caa6:
    goto L0203caa6
L0203caa8:
    r0 = 0x0 - r9
    call L0203c0bc
L0203cab0:
    r0 = 8216
    r0 += r12
    [r0+0] |= 0x4
    r10 = -1
    r9 = r11
L0203cac0:
    csync
    r0 = 0
    b[r12+69] = r0
    call storage_coordination_irq_leave  ; @call.xl
L0203cace:
    r0 = 2147483646
    if (r5 > r0) goto L0203cb28
    if (r10 != -1) goto L0203cb28
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r12 + 69
L0203cae8:
    testset b[r0]
    ifeq goto L0203cae8
    csync
    r0 = r5
    call L0203c0bc
    r10 = r0
    r0 = 0
    r4 = 0
    call L0203c0bc
    r3 = r0
    csync
    b[r12+69] = r4
    call storage_coordination_irq_leave  ; @call.xl
    if (r10 >= r3) goto L0203cbc6
    if (r10 == -1) goto L0203cbc6
    if (r3 == -1) goto L0203cbc6
    r9 = r3 - r10
    r0 = r6 + 88
    if (r9 > r0) goto L0203cb2c
    goto L0203cbc6
L0203cb28:
    if (r10 == -1) goto L0203cbc6
L0203cb2c:
    r0 = 8204
    r1 = r12
    r0 = [++r1=r0]
    r0 += r9
    [r1+0] = r0
    r1 = [r1+4]
    if (r0 > r1) {
    r1 = 2052
    [r12+r1<<2] = r0
    }
    r0 = 1949
    r13 = [r12+r0<<2]
    if (r13 == 0) goto L0203cb6c
    r0 = 8224
    r0 += r12
    goto L0203cb68
L0203cb5c:
    r1 = [r0+4]
    r2 = [r0+0]
    r3 = r2 + r1
    if (r10 == r3) goto L0203cbce
    r0 = [r0+8]
L0203cb68:
    if (r0 != 0) goto L0203cb5c
    goto L0203cbf0
L0203cb6c:
    r0 += -2
    r1 = [r12+r0<<2]
    if (r1 == 0) goto L0203cb78
    if (r10 >= r1) goto L0203cb7c
L0203cb78:
    [r12+r0<<2] = r10
L0203cb7c:
    r0 = 8224
    [++r0=r12] = r10
    [r0+4] = r9
    [r0+12] = 0x0
    r0 = 524
    r1 = [r12+r0<<2]
    r0 = r12 + 7804
    [r0+4] = r1
    r1 = -1
    [r0++=8] = r1
    r1 = 32
    goto L0203cbac
L0203cba4:
    [r0+12] = r0
    [++r0=8] = r0
    r1 += -1
L0203cbac:
    if (r1 != 0) goto L0203cba4
    r1 = r9 + -88
    r0 = r10
L0203cbb4:
    call L0203c11e
L0203cbb8:
    r0 = 1946
    r0 = [r12+r0<<2]
    if (r0 > r6) goto L0203c518
L0203cbc6:
    [r12+96] = 0xC
    r3 = 0
    goto L0203c5e0
L0203cbce:
    r3 = b[r0+12] (u)
    if ((r3 & 8) != 0) goto L0203cbf0
    if (r13 >= r10) goto L0203cbf0
    if (r13 < r2) goto L0203cbf0
    r1 += r9
    r0 = 1946  #
    [r0+4] = r1
    r0 = [r12+r0<<2]
    r1 = r0 + r9
    r0 = r13
    goto L0203cbb4
L0203cbf0:
    r0 = 1947
    r4 = [r12+r0<<2]
    if (r10 < r4) {
    [r12+r0<<2] = r10
    r4 = r10
    }
    r0 = 8224
    r0 += r12
    r1 = r10 + r9
    goto L0203cc16
L0203cc0e:
    r2 = [r0+0]
    if (r2 == r1) goto L0203cc1a
    r0 = [r0+8]
L0203cc16:
    if (r0 != 0) goto L0203cc0e
    goto L0203cc7a
L0203cc1a:
    r2 = b[r0+12] (u)
    if ((r2 & 8) != 0) goto L0203cc7a
    [r0+0] = r10
    [r0+4] += r9
    r8 = -8
    r0 = r8 - r10
    r0 = r0 & 0x1F
    r3 = r10 + 8
    r2 = 0
    r7 = 0
    if ((r3 & 0x1F) != 0) {
    r7 = r0
    }
    r11 = r10 + r7
    r7 = r6 | 0x3
    r3 = r8 - r1
    r3 = r3 & 0x1F
    r0 = r1 + 8
    [r11+4] = r7
    if ((r0 & 0x1F) != 0) {
    r2 = r3
    }
    r3 = r1 + r2
    r1 = r11 + r6
    r2 = r3 - r11
    if (r3 <= r1) goto L0203cc78
    r10 = r2 - r6  #
    r7 = [r3+4]
    if ((r7 & 1) != 0) goto L0203cd48
L0203cc76:
    goto L0203cc76
L0203cc78:
    goto L0203cc78
L0203cc7a:
    r0 = r13
    call L0203c098
    r1 = r9 + -88  #
    r4 = [r0+4]
    r0 = r10  #
    r7 = [r0+0]
    call L0203c11e
    r0 = r7 + r4
    r3 = r0 + -71
    r1 = 0x47 - r0
    r2 = r1 & 0x1F
    r1 = 0
    if ((r3 & 0x1F) != 0) {
    r1 = r2
    }
    r1 += r0  ; @add.rr
    r2 = r1 + -79
    r3 = r13 + 32
    r1 = r13
    if (r2 >= r3) {
    r1 = r2
    }
    r3 = r1 + 8
    if ((r3 & 0x1F) == 0) goto L0203ccc0
L0203ccbe:
    goto L0203ccbe
L0203ccc0:
    r2 = 8224
    r4 = r12 + r2
    [r1+4] = 0x23
    r2 = r4
    r7 = r3
    rep 4 {
    r5 = [r2++=4]
    [r7++=4] = r5
    }
    [r4+0] = r10
    [r4+4] = r9
    r2 = 0
    [r4+12] = r2
    r3 = r1 + 36  #
    [r4+8] = r3
    r4 = 7
L0203ccea:
    [r3++=4] = r4
    r2 += 1  ; @add.ri.u5
    if (r3 < r0) goto L0203ccea
    ifs (r2 <= 1) goto L0203cd44
    if (r1 == r13) goto L0203cbb8
    [r1+4] &= 0xFFFFFFFE
    r0 = r1 - r13
    r2 = r0 | 0x1
    [r13+4] = r2
    [r1+0] = r0
    if (r0 > 255) goto L0203cda6
    r1 = r0 >> 3
    r2 = r1 << 3
    r2 += r12
    if (r0 <= 31) goto L0203cd46
    r3 = 1943
    r4 = [r12+r3<<2]
    r0 = 1
    r1 = r0 << r1
    r0 = r2 + 7812
    if ((r4 & r1) == 0) goto L0203cf82
    r1 = r3 + 4
    r3 = [r12+r1<<2]
    r1 = r0
    r2 = [++r1=8]
    if (r2 >= r3) goto L0203cf8c
L0203cd42:
    goto L0203cd42
L0203cd44:
    goto L0203cd44
L0203cd46:
    goto L0203cd46
L0203cd48:
    if (r10 <= 31) goto L0203cd9e
    if (r3 == r13) goto L0203cf6e
    r0 = 1948
    r0 = [r12+r0<<2]
    if (r3 == r0) goto L0203cf9e
    r0 = r7 & 0x3
    if (r0 != 1) goto L0203d0bc
    r9 = r7 & 0xFFFFFFF8
    if (r7 > 255) goto L0203cfb6
    r5 = [r3+12]
    r6 = [r3+8]
    if (r3 == r5) goto L0203cda0
    r7 = r7 >> 3
    if (r3 == r6) goto L0203cda2
    r2 = r7 << 3
    if (r9 != r2) goto L0203cda4
    r0 = r2 + r12
    r2 = r0 + 7812
    if (r6 == r2) goto L0203d00e
    if (r6 >= r4) goto L0203d006
L0203cd9c:
    goto L0203cd9c
L0203cd9e:
    goto L0203cd9e
L0203cda0:
    goto L0203cda0
L0203cda2:
    goto L0203cda2
L0203cda4:
    goto L0203cda4
L0203cda6:
    r2 = r0 >> 8
    if (r2 == 0) goto L0203ce96
    r3 = r0 >> 24
    r1 = 31
    if (r3 != 0) goto L0203ce98
    r1 = 1048320
    r1 += r2  ; @add.rr
    r1 = r1 >> 16
    r1 = r1 & 0x8
    r2 <<= r1
    r3 = r2 + 0x7F000
    r3 = r3 >> 16
    r3 = r3 & 0x4
    r2 <<= r3
    r4 = r2 + 0x3C000
    r4 = r4 >> 16
    r4 = r4 & 0x2
    r2 <<= r4
    r2 = r2 >> 15
    r1 |= r3
    r1 |= r4
    r1 = 0xE - r1
    r2 += r1  ; @add.rr
    r1 = r2 + 7
    r1 = r0 >> r1
    r1 = r1 & 0x1
    r1 <= insert(r2, p:1, l:31)
    goto L0203ce98
L0203cdf4:
    r0 = r11 & ~(1 << r1)
    r1 = 1944
    [r12+r1<<2] = r0
L0203ce00:
    if (r3 > 31) goto L0203ce16
    r0 = r9 | 0x3
    r0 = r2 + r9  #
    [r2+4] = r0
    [r0+4] |= 0x1
    goto L0203c530
L0203ce16:
    r0 = r6 | 0x3
    r0 = r3 | 0x1  #
    [r2+4] = r0
    [r8+4] = r0
    [r8+r3] = r3
    if (r14 >= 256) goto L0203ce68
    if (r14 == 0) goto L0203cf5c
    r4 = r14 >> 3
    r1 = 1948
    r0 = r4 << 3
    r5 = r0 + r12
    if (r14 <= 31) goto L0203ce6a
    r1 = [r12+r1<<2]
    r0 = 1
    r6 = r0 << r4
    r4 = r5 + 7812
    if ((r15 & r6) == 0) goto L0203cf44
    r0 = 1947
    r6 = [r12+r0<<2]
    r0 = r4
    r5 = [++r0=8]
    if (r5 >= r6) goto L0203cf54
L0203ce66:
    goto L0203ce66
L0203ce68:
    goto L0203ce68
L0203ce6a:
    goto L0203ce6a
L0203ce6c:
    r0 = r15 | r7
    r6 = 1943
    [r12+r6<<2] = r0
    r0 = r5 + 8
    r6 = r5
L0203ce7c:
    [r0+0] = r1
    [r6+12] = r1
    [r1+8] = r6
    [r1+12] = r5
L0203ce84:
    r0 = 1945
    [r12+r0<<2] = r4
    r0 += 3  ; @add.ri.u5
    [r12+r0<<2] = r2
    goto L0203c5e0
L0203ce96:
    r1 = 0
L0203ce98:
    [r13+28] = r1
    r2 = 0
    r3 = 0
    d[r13+16] = r3_r2
    r2 = 1
    r3 = 1944
    r4 = [r12+r3<<2]
    r7 = r2 << r1
    r2 = r1 << 2
    r2 += r12
    r2 = r2 + 8076
    if ((r4 & r7) == 0) goto L0203cf04
    r3 = r1 >> 1
    r4 = 0x19 - r3
    r3 = 0
    if (r1 != 31) {  ; @if.ne.ri.s12
    r3 = r4
    }
    r2 = r0 << r3  #
    r4 = [r2+0]
L0203ced2:
    r1 = r4
    r3 = [r1+4]
    r3 = r3 & 0xFFFFFFF8
    if (r3 == r0) goto L0203cf1e
    r3 = r2 >> 31
    r3 = r3 << 2
    r3 += r1  ; @add.rr
    r4 = [++r3=16]
    r2 = r2 << 1
    if (r4 != 0) goto L0203ced2
    r0 = 1947
    r0 = [r12+r0<<2]
    if (r3 < r0) goto L0203cf02
    [r3+0] = r13
    [r13+24] = r1
    goto L0203cf14
L0203cf02:
    goto L0203cf02
L0203cf04:
    r0 = r4 | r7
    [r12+r3<<2] = r0
    [r2+0] = r13
    [r13+24] = r2
L0203cf14:
    [r13+12] = r13
    [r13+8] = r13
    goto L0203cbb8
L0203cf1e:
    r0 = 1947
    r2 = [r12+r0<<2]
    r0 = [r1+8]
    if (r0 < r2) goto L0203cf42
    if (r1 < r2) goto L0203cf42
    [r0+12] = r13
    [r1+8] = r13
    d[r13+8] = r1_r0
    [r13+24] = 0x0
    goto L0203cbb8
L0203cf42:
    goto L0203cf42
L0203cf44:
    r0 = r15 | r6
    r5 = 1943
    [r12+r5<<2] = r0
    r0 = r4 + 8
    r5 = r4
L0203cf54:
    [r0+0] = r1
    [r5+12] = r1
    [r1+8] = r5
    [r1+12] = r4
L0203cf5c:
    r0 = 1945
    [r12+r0<<2] = r3
    r0 += 3  ; @add.ri.u5
    [r12+r0<<2] = r8
    goto L0203c530
L0203cf6e:
    r0 = r12 + 7784
    r2 = [r0+0]
    r2 += r10
    [r0+0] = r2
    r0 = r2 | 0x1  #
    [r0+12] = r1
    [r1+4] = r0
    goto L0203d208
L0203cf82:
    r1 |= r4
    [r12+r3<<2] = r1
    r1 = r0 + 8
    r2 = r0
L0203cf8c:
    [r1+0] = r13
    [r2+12] = r13
    [r13+8] = r2
    [r13+12] = r0
    goto L0203cbb8
L0203cf9e:
    r0 = r12 + 7780
    r2 = [r0+0]
    r2 += r10
    [r0+0] = r2
    r0 = r2 | 0x1  #
    [r0+12] = r1
    [r1+4] = r0
    [r1+r2] = r2
    goto L0203d208
L0203cfb6:
    r6 = [r3+12]
    r8 = [r3+24]
    if (r6 == r3) goto L0203cfce
    r2 = [r3+8]
    if (r2 < r4) goto L0203cfcc
    r0 = [r2+12]
    if (r0 == r3) goto L0203cffa
L0203cfcc:
    goto L0203cfcc
L0203cfce:
    r5 = [r3+20]
    if (r5 == 0) goto L0203cfd6
    r7 = r3 + 20
    goto L0203cfdc
L0203cfd6:
    r7 = r3 + 16
    r5 = [r7+0]
    if (r5 == 0) goto L0203d01c
L0203cfdc:
    r6 = r5
    r2 = r7  #
    r5 = [r6+20]
    r7 = r6 + 20
    if (r5 != 0) goto L0203cfdc
    r7 = r6
    r5 = [++r7=16]
    if (r5 != 0) goto L0203cfdc
    if (r2 < r4) goto L0203cff8
    [r2+0] = 0x0
    goto L0203d01e
L0203cff8:
    goto L0203cff8
L0203cffa:
    r0 = [r6+8]
    if (r0 != r3) goto L0203cfcc
    [r2+12] = r6
    [r6+8] = r2
    goto L0203d01e
L0203d006:
    r0 = [r6+12]
    if (r0 != r3) goto L0203cd9c
L0203d00e:
    if (r5 == r6) goto L0203d092
    if (r5 == r2) goto L0203d0a6
    if (r5 >= r4) goto L0203d0aa
L0203d01a:
    goto L0203d01a
L0203d01c:
    r6 = 0
L0203d01e:
    if (r8 == 0) goto L0203d0b8
    r2 = [r3+28]
    r0 = r2 << 2
    r0 += r12
    r4 = r0 + 8076
    r0 = [r4+0]
    if (r3 == r0) goto L0203d056
    r0 = 1947
    r0 = [r12+r0<<2]
    if (r8 < r0) goto L0203d054
    r2 = r8
    r0 = [++r2=16]
    r4 = 1
    if (r0 == r3) {
    r4 = 0
    }
    [r2+r4<<2] = r6
    if (r6 != 0) goto L0203d05a
    goto L0203d0b8
L0203d054:
    goto L0203d054
L0203d056:
    [r4+0] = r6
    if (r6 == 0) goto L0203d09c
L0203d05a:
    r0 = 1947
    r4 = [r12+r0<<2]
    if (r6 < r4) goto L0203d08c
    [r6+24] = r8
    r2 = r3
    r5 = [++r2=16]
    if (r5 == 0) goto L0203d07a
    if (r5 < r4) goto L0203d08e
    [r6+16] = r5
    [r5+24] = r6
L0203d07a:
    r2 = [r2+4]
    if (r2 == 0) goto L0203d0b8
    r0 = [r12+r0<<2]
    if (r2 < r0) goto L0203d090
    [r6+20] = r2
    [r2+24] = r6
    goto L0203d0b8
L0203d08c:
    goto L0203d08c
L0203d08e:
    goto L0203d08e
L0203d090:
    goto L0203d090
L0203d092:
    r0 = r12 + 7772
    [r0+0] &= ~(1 << r7)
    goto L0203d0b8
L0203d09c:
    r0 = r12 + 7776
    [r0+0] &= ~(1 << r2)
    goto L0203d0b8
L0203d0a6:
    r2 = r5 + 8
    goto L0203d0b4
L0203d0aa:
    r2 = r5
    r0 = [++r2=8]
    if (r0 != r3) goto L0203d01a
L0203d0b4:
    [r6+12] = r5
    [r2+0] = r6
L0203d0b8:
    r10 += r9
    r3 += r9
L0203d0bc:
    [r3+4] &= 0xFFFFFFFE
    r0 = r10 | 0x1
    [r1+4] = r0
    [r1+r10] = r10
    if (r10 > 255) goto L0203d106
    r2 = r10 >> 3
    r0 = r2 << 3
    r3 = r0 + r12
    if (r10 <= 31) goto L0203d104
    r4 = 1943
    r5 = [r12+r4<<2]
    r0 = 1
    r6 = r0 << r2
    r2 = r3 + 7812
    if ((r5 & r6) == 0) goto L0203d1f4
    r0 = r4 + 4
    r0 = [r12+r0<<2]
    r3 = r2
    r4 = [++r3=8]
    if (r4 >= r0) goto L0203d200
L0203d102:
    goto L0203d102
L0203d104:
    goto L0203d104
L0203d106:
    r2 = r10 >> 8
    if (r2 == 0) goto L0203d158
    r0 = r10 >> 24
    r3 = 31
    if (r0 != 0) goto L0203d15a
    r0 = 1048320
    r0 += r2  ; @add.rr
    r0 = r0 >> 16
    r0 = r0 & 0x8
    r2 <<= r0
    r3 = r2 + 0x7F000
    r3 = r3 >> 16
    r3 = r3 & 0x4
    r2 <<= r3
    r4 = r2 + 0x3C000
    r4 = r4 >> 16
    r4 = r4 & 0x2
    r2 <<= r4
    r2 = r2 >> 15
    r0 |= r3
    r0 |= r4
    r0 = 0xE - r0
    r0 += r2  ; @add.rr
    r2 = r0 + 7
    r2 = r10 >> r2
    r3 = r2 & 0x1
    r3 <= insert(r0, p:1, l:31)
    goto L0203d15a
L0203d158:
    r3 = 0
L0203d15a:
    r2 = 1944  #
    [r1+28] = r3
    r4 = 0
    r5 = 0
    d[r1+16] = r5_r4
    r0 = 1
    r5 = [r12+r2<<2]
    r6 = r0 << r3
    r0 = r3 << 2
    r0 += r12
    r4 = r0 + 8076
    if ((r5 & r6) == 0) goto L0203d1c0
    r0 = r3 >> 1
    r5 = 0x19 - r0
    r2 = 0
    if (r3 != 31) {  ; @if.ne.ri.s12
    r2 = r5
    }
    r4 = r10 << r2  #
    r5 = [r4+0]
L0203d192:
    r3 = r5
    r0 = [r3+4]
    r0 = r0 & 0xFFFFFFF8
    if (r0 == r10) goto L0203d1d2
    r0 = r4 >> 31
    r0 = r0 << 2
    r2 = r3 + r0
    r5 = [++r2=16]
    r4 = r4 << 1
    if (r5 != 0) goto L0203d192
    r0 = 1947
    r0 = [r12+r0<<2]
    if (r2 < r0) goto L0203d1be
    [r2+0] = r1
    [r1+24] = r3
    goto L0203d1cc
L0203d1be:
    goto L0203d1be
L0203d1c0:
    r0 = r5 | r6
    [r12+r2<<2] = r0
    [r4+0] = r1
    [r1+24] = r4
L0203d1cc:
    [r1+12] = r1
    [r1+8] = r1
    goto L0203d208
L0203d1d2:
    r0 = 1947  #
    r2 = [r3+8]
    r4 = [r12+r0<<2]
    if (r2 < r4) goto L0203d1f2
    if (r3 < r4) goto L0203d1f2
    [r2+12] = r1
    [r3+8] = r1
    d[r1+8] = r3_r2
    [r1+24] = 0x0
    goto L0203d208
L0203d1f2:
    goto L0203d1f2
L0203d1f4:
    r0 = r5 | r6
    [r12+r4<<2] = r0
    r3 = r2 + 8
    r4 = r2
L0203d200:
    [r3+0] = r1
    [r4+12] = r1
    [r1+8] = r4
    [r1+12] = r2
L0203d208:
    r3 = r11 + 8
    goto L0203c5e0
L0203d210:
    [--sp] = rets
    call L0203c15c
    pc = [sp++]
L0203d218:
    [--sp] = {rets, r11-r4}
    r3 = r0
    if (r3 == 0) goto L0203d77a
    r0 = 8216
    r11 = L01c26890
    r0 = b[r11+r0] (u)
    r2 = r3 + -8
    if ((r0 & 2) == 0) goto L0203d250
    r0 = 8220
    r4 = r11 + r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0203d248:
    testset b[r4]
    ifeq goto L0203d248
    csync
L0203d250:
    r0 = 1947
    r4 = [r11+r0<<2]
    if (r2 < r4) goto L0203d444
    r5 = [r3+-4]
    r3 = r5 & 0x3
    if (r3 == 1) goto L0203d444
    r0 = r5 & 0xFFFFFFF8
    r1 = r2 + r0
    if ((r5 & 1) != 0) goto L0203d3e0
    if (r3 == 0) goto L0203d75c
    r6 = [r2+0]
    r2 = r2 - r6
    if (r2 < r4) goto L0203d444
    r3 = 1948
    r3 = [r11+r3<<2]
    r0 += r6  ; @add.rr
    if (r2 == r3) goto L0203d2c6
    if (r6 > 255) goto L0203d2de
    r5 = [r2+12]
    r3 = [r2+8]
    if (r2 == r5) goto L0203d2c0
    r8 = r6 >> 3
    if (r2 == r3) goto L0203d2c2
    r7 = r8 << 3  #
    r6 = [r2+4]
    r6 = r6 & 0xFFFFFFF8
    if (r6 != r7) goto L0203d2c4
    r6 = r7 + r11
    r7 = r6 + 7812
    if (r3 == r7) goto L0203d334
    if (r3 >= r4) goto L0203d32e
L0203d2be:
    goto L0203d2be
L0203d2c0:
    goto L0203d2c0
L0203d2c2:
    goto L0203d2c2
L0203d2c4:
    goto L0203d2c4
L0203d2c6:
    r3 = [r1+4]
    r4 = r3 & 0x3
    if (r4 != 3) goto L0203d3e0
    r4 = 1945
    [r11+r4<<2] = r0
    r3 &= 4294967294
    [r1+4] = r3
    goto L0203d606
L0203d2de:
    r3 = [r2+12]
    r8 = [r2+24]
    if (r3 == r2) goto L0203d2f6
    r5 = [r2+8]
    if (r5 < r4) goto L0203d2f4
    r4 = [r5+12]
    if (r4 == r2) goto L0203d322
L0203d2f4:
    goto L0203d2f4
L0203d2f6:
    r5 = [r2+20]
    if (r5 == 0) goto L0203d2fe
    r6 = r2 + 20
    goto L0203d304
L0203d2fe:
    r6 = r2 + 16
    r5 = [r6+0]
    if (r5 == 0) goto L0203d342
L0203d304:
    r3 = r5
    r7 = r6  #
    r5 = [r3+20]
    r6 = r3 + 20
    if (r5 != 0) goto L0203d304
    r6 = r3
    r5 = [++r6=16]
    if (r5 != 0) goto L0203d304
    if (r7 < r4) goto L0203d320
    [r7+0] = 0x0
    goto L0203d344
L0203d320:
    goto L0203d320
L0203d322:
    r4 = [r3+8]
    if (r4 != r2) goto L0203d2f4
    [r5+12] = r3
    [r3+8] = r5
    goto L0203d344
L0203d32e:
    r6 = [r3+12]
    if (r6 != r2) goto L0203d2be
L0203d334:
    if (r5 == r3) goto L0203d3ba
    if (r5 == r7) goto L0203d3ce
    if (r5 >= r4) goto L0203d3d2
L0203d340:
    goto L0203d340
L0203d342:
    r3 = 0
L0203d344:
    if (r8 == 0) goto L0203d3e0
    r4 = [r2+28]
    r5 = r4 << 2
    r5 += r11
    r5 = r5 + 8076
    r6 = [r5+0]
    if (r2 == r6) goto L0203d37c
    r4 = 1947
    r4 = [r11+r4<<2]
    if (r8 < r4) goto L0203d37a
    r4 = r8
    r6 = [++r4=16]
    r5 = 1
    if (r6 == r2) {
    r5 = 0
    }
    [r4+r5<<2] = r3
    if (r3 != 0) goto L0203d380
    goto L0203d3e0
L0203d37a:
    goto L0203d37a
L0203d37c:
    [r5+0] = r3
    if (r3 == 0) goto L0203d3c4
L0203d380:
    r4 = 1947
    r5 = [r11+r4<<2]
    if (r3 < r5) goto L0203d3b4
    [r3+24] = r8
    r6 = [r2+16]
    r4 = r2 + 16
    if (r6 == 0) goto L0203d39e
    if (r6 < r5) goto L0203d3b6
    [r3+16] = r6
    [r6+24] = r3
L0203d39e:
    r4 = [r4+4]
    if (r4 == 0) goto L0203d3e0
    r5 = 1947
    r5 = [r11+r5<<2]
    if (r4 < r5) goto L0203d3b8
    [r3+20] = r4
    [r4+24] = r3
    goto L0203d3e0
L0203d3b4:
    goto L0203d3b4
L0203d3b6:
    goto L0203d3b6
L0203d3b8:
    goto L0203d3b8
L0203d3ba:
    r3 = r11 + 7772
    [r3+0] &= ~(1 << r8)
    goto L0203d3e0
L0203d3c4:
    r3 = r11 + 7776
    [r3+0] &= ~(1 << r4)
    goto L0203d3e0
L0203d3ce:
    r4 = r5 + 8
    goto L0203d3dc
L0203d3d2:
    r4 = r5
    r6 = [++r4=8]
    if (r6 != r2) goto L0203d340
L0203d3dc:
    [r3+12] = r5
    [r4+0] = r3
L0203d3e0:
    if (r2 >= r1) goto L0203d444
    r5 = [r1+4]
    if ((r5 & 1) == 0) goto L0203d444
    if ((r5 & 2) != 0) goto L0203d44c
    r3 = 1949
    r3 = [r11+r3<<2]
    if (r1 == r3) goto L0203d4e8
    r3 = 1948
    r3 = [r11+r3<<2]
    if (r1 == r3) goto L0203d5fa
    r6 = r5 & 0xFFFFFFF8
    r0 += r6  ; @add.rr
    if (r5 > 255) goto L0203d68c
    r4 = [r1+12]
    r3 = [r1+8]
    if (r1 == r4) goto L0203d446
    r5 = r5 >> 3
    if (r1 == r3) goto L0203d448
    r7 = r5 << 3
    if (r6 != r7) goto L0203d44a
    r6 = r7 + r11
    r6 = r6 + 7812
    if (r3 == r6) goto L0203d784
    r7 = 1947
    r7 = [r11+r7<<2]
    if (r3 >= r7) goto L0203d77c
L0203d442:
    goto L0203d442
L0203d444:
    goto L0203d444
L0203d446:
    goto L0203d446
L0203d448:
    goto L0203d448
L0203d44a:
    goto L0203d44a
L0203d44c:
    r3 = r5 & 0xFFFFFFFE
    r1 = r0 | 0x1  #
    [r1+4] = r3
    [r2+4] = r1
    [r2+r0] = r0
L0203d45c:
    if (r0 > 255) goto L0203d496
    r1 = r0 >> 3
    r3 = r1 << 3
    r3 += r11
    if (r0 <= 31) goto L0203d494
    r4 = 1943
    r5 = [r11+r4<<2]
    r0 = 1
    r1 = r0 << r1
    r0 = r3 + 7812
    if ((r5 & r1) == 0) goto L0203d6ee
    r1 = r4 + 4
    r4 = [r11+r1<<2]
    r1 = r0
    r3 = [++r1=8]
    if (r3 >= r4) goto L0203d6f8
L0203d492:
    goto L0203d492
L0203d494:
    goto L0203d494
L0203d496:
    r3 = r0 >> 8
    if (r3 == 0) goto L0203d612
    r4 = r0 >> 24
    r1 = 31
    if (r4 != 0) goto L0203d614
    r1 = 1048320
    r1 += r3  ; @add.rr
    r1 = r1 >> 16
    r1 = r1 & 0x8
    r3 <<= r1
    r4 = r3 + 0x7F000
    r4 = r4 >> 16
    r4 = r4 & 0x4
    r3 <<= r4
    r5 = r3 + 0x3C000
    r5 = r5 >> 16
    r5 = r5 & 0x2
    r3 <<= r5
    r3 = r3 >> 15
    r1 |= r4
    r1 |= r5
    r1 = 0xE - r1
    r3 += r1  ; @add.rr
    r1 = r3 + 7
    r1 = r0 >> r1
    r1 = r1 & 0x1
    r1 <= insert(r3, p:1, l:31)
    goto L0203d614
L0203d4e8:
    r1 = r11 + 7784
    r3 = [r1+0]
    r0 += r3  ; @add.rr
    r3 = r0 | 0x1  #
    [r1+0] = r0
    [r1+12] = r2
    [r2+4] = r3
    r1 = [r1+8]
    if (r2 != r1) goto L0203d510
    r1 = 1948
    r3 = 0
    [r11+r1<<2] = r3
    r1 += -3
    [r11+r1<<2] = r3
L0203d510:
    r1 = 1950
    r1 = [r11+r1<<2]
    if (r0 <= r1) goto L0203d75c
    r0 = 524
    r0 = [r11+r0<<2]
    if (r0 != 0) goto L0203d53a
    call L0203c018
    r0 = 1949
    r2 = [r11+r0<<2]
    if (r2 == 0) goto L0203d75c
L0203d53a:
    r0 = 1946
    r6 = [r11+r0<<2]
    if (r6 < 89) goto L0203d74a  ; @blt.ri.l
    r0 = 526
    r10 = [r11+r0<<2]
    r0 = r2
    call L0203c098
    r4 = r0
    r0 = b[r4+12] (u)
    if ((r0 & 8) != 0) goto L0203d74a
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r11 + 69
L0203d56a:
    testset b[r0]
    ifeq goto L0203d56a
    csync
    r0 = 0
    r8 = 0
    call L0203c0bc
    r9 = r0  #
    r1 = [r4+4]
    r2 = [r4++=4]
    r0 = r2 + r1
    r5 = 0
    if (r9 != r0) goto L0203d5c4
    r0 = r6 + r10
    r0 += -89
    r0 = r0 / r10 (u)
    r0 += -1
    r1 = r0 * r10
    r0 = 0x80000000 - r10
    r2 = 2147483646
    if (r1 <= r2) {
    r0 = r1
    }
    r0 = 0x0 - r0
    call L0203c0bc
    r6 = r0
    r0 = 0
    call L0203c0bc
    if (r6 == -1) goto L0203d5c4
    if (r0 < r9) {
    r5 = r9 - r0
    }
L0203d5c4:
    csync
    b[r11+69] = r8
    call storage_coordination_irq_leave  ; @call.xl
    if (r5 == 0) goto L0203d742
    [r4+0] -= r5
    r0 = 8204
    r0 += r11
    [r0+0] -= r5
    r0 = 1949
    r1 = 1946
    r1 = [r11+r1<<2]
    r0 = [r11+r0<<2]
    r1 = r1 - r5
    call L0203c11e
    goto L0203d75c
L0203d5fa:
    r1 = r11 + 7780
    r3 = [r1+0]
    r0 += r3  ; @add.rr
    [r1+0] = r0
    [r1+12] = r2
L0203d606:
    r1 = r0 | 0x1
    [r2+4] = r1
    [r2+r0] = r0
    goto L0203d75c
L0203d612:
    r1 = 0
L0203d614:
    [r2+28] = r1
    r4 = 0
    r5 = 0
    d[r2+16] = r5_r4
    r3 = 1
    r4 = 1944
    r5 = [r11+r4<<2]
    r6 = r3 << r1
    r3 = r1 << 2
    r3 += r11
    r3 = r3 + 8076
    if ((r5 & r6) == 0) goto L0203d67a
    r4 = r1 >> 1
    r5 = 0x19 - r4
    r4 = 0
    if (r1 != 31) {  ; @if.ne.ri.s12
    r4 = r5
    }
    r3 = r0 << r4  #
    r5 = [r3+0]
L0203d64c:
    r1 = r5
    r4 = [r1+4]
    r4 = r4 & 0xFFFFFFF8
    if (r4 == r0) goto L0203d6ac
    r4 = r3 >> 31
    r4 = r4 << 2
    r4 += r1  ; @add.rr
    r5 = [++r4=16]
    r3 = r3 << 1
    if (r5 != 0) goto L0203d64c
    r0 = 1947
    r0 = [r11+r0<<2]
    if (r4 < r0) goto L0203d678
    [r4+0] = r2
    [r2+24] = r1
    goto L0203d686
L0203d678:
    goto L0203d678
L0203d67a:
    r0 = r5 | r6
    [r11+r4<<2] = r0
    [r3+0] = r2
    [r2+24] = r3
L0203d686:
    [r2+12] = r2
    [r2+8] = r2
    goto L0203d6ca
L0203d68c:
    r4 = [r1+12]
    r8 = [r1+24]
    if (r4 == r1) goto L0203d702
    r3 = 1947
    r5 = [r11+r3<<2]
    r3 = [r1+8]
    if (r3 < r5) goto L0203d6aa
    r5 = [r3+12]
    if (r5 == r1) goto L0203d736
L0203d6aa:
    goto L0203d6aa
L0203d6ac:
    r0 = 1947
    r3 = [r11+r0<<2]
    r0 = [r1+8]
    if (r0 < r3) goto L0203d6ec
    if (r1 < r3) goto L0203d6ec
    [r0+12] = r2
    [r1+8] = r2
    d[r2+8] = r1_r0
    [r2+24] = 0x0
L0203d6ca:
    r0 = 1951
    r1 = [r11+r0<<2]
    r1 += -1
    [r11+r0<<2] = r1
    if (r1 != 0) goto L0203d75c
    r0 = 8232
    r0 += r11
L0203d6e0:
    r1 = [r0+0]
    r0 = r1 + 8
    if (r1 != 0) goto L0203d6e0
    r0 = 1951
    goto L0203d756
L0203d6ec:
    goto L0203d6ec
L0203d6ee:
    r1 |= r5
    [r11+r4<<2] = r1
    r1 = r0 + 8
    r3 = r0
L0203d6f8:
    [r1+0] = r2
    [r3+12] = r2
    [r2+8] = r3
    [r2+12] = r0
    goto L0203d75c
L0203d702:
    r5 = [r1+20]
    if (r5 == 0) goto L0203d70a
    r6 = r1 + 20
    goto L0203d710
L0203d70a:
    r5 = [r1+16]
    if (r5 == 0) goto L0203d79a
    r6 = r1 + 16
L0203d710:
    r4 = r5
    r3 = r6  #
    r5 = [r4+20]
    r6 = r4 + 20
    if (r5 != 0) goto L0203d710
    r6 = r4
    r5 = [++r6=16]
    if (r5 != 0) goto L0203d710
    r5 = 1947
    r5 = [r11+r5<<2]
    if (r3 < r5) goto L0203d734
    [r3+0] = 0x0
    goto L0203d79c
L0203d734:
    goto L0203d734
L0203d736:
    r5 = [r4+8]
    if (r5 != r1) goto L0203d6aa
    [r3+12] = r4
    [r4+8] = r3
    goto L0203d79c
L0203d742:
    r0 = 1946
    r6 = [r11+r0<<2]
L0203d74a:
    r0 = 1950
    r1 = [r11+r0<<2]
    if (r6 <= r1) goto L0203d75c
L0203d756:
    r1 = -1
    [r11+r0<<2] = r1
L0203d75c:
    r0 = 8216
    r0 = b[r11+r0] (u)
    if ((r0 & 2) == 0) goto L0203d77a
    csync
    r0 = 8220
    r1 = 0
    b[r11+r0] = r1
    call storage_coordination_irq_leave  ; @call.xl
L0203d77a:
    {pc, r11-r4} = [sp++]
L0203d77c:
    r7 = [r3+12]
    if (r7 != r1) goto L0203d442
L0203d784:
    if (r4 == r3) goto L0203d812
    if (r4 == r6) goto L0203d826
    r5 = 1947
    r5 = [r11+r5<<2]
    if (r4 >= r5) goto L0203d82a
L0203d798:
    goto L0203d798
L0203d79a:
    r4 = 0
L0203d79c:
    if (r8 == 0) goto L0203d838
    r3 = [r1+28]
    r5 = r3 << 2
    r5 += r11
    r5 = r5 + 8076
    r6 = [r5+0]
    if (r1 == r6) goto L0203d7d4
    r3 = 1947
    r3 = [r11+r3<<2]
    if (r8 < r3) goto L0203d7d2
    r3 = r8
    r6 = [++r3=16]
    r5 = 1
    if (r6 == r1) {
    r5 = 0
    }
    [r3+r5<<2] = r4
    if (r4 != 0) goto L0203d7d8
    goto L0203d838
L0203d7d2:
    goto L0203d7d2
L0203d7d4:
    [r5+0] = r4
    if (r4 == 0) goto L0203d81c
L0203d7d8:
    r3 = 1947
    r3 = [r11+r3<<2]
    if (r4 < r3) goto L0203d80c
    [r4+24] = r8
    r5 = [++r1=16]
    if (r5 == 0) goto L0203d7f6
    if (r5 < r3) goto L0203d80e
    [r4+16] = r5
    [r5+24] = r4
L0203d7f6:
    r1 = [r1+4]
    if (r1 == 0) goto L0203d838
    r3 = 1947
    r3 = [r11+r3<<2]
    if (r1 < r3) goto L0203d810
    [r4+20] = r1
    [r1+24] = r4
    goto L0203d838
L0203d80c:
    goto L0203d80c
L0203d80e:
    goto L0203d80e
L0203d810:
    goto L0203d810
L0203d812:
    r1 = r11 + 7772
    [r1+0] &= ~(1 << r5)
    goto L0203d838
L0203d81c:
    r1 = r11 + 7776
    [r1+0] &= ~(1 << r3)
    goto L0203d838
L0203d826:
    r5 = r4 + 8
    goto L0203d834
L0203d82a:
    r5 = r4
    r6 = [++r5=8]
    if (r6 != r1) goto L0203d798
L0203d834:
    [r3+12] = r4
    [r5+0] = r3
L0203d838:
    r1 = r0 | 0x1
    r1 = 1948  #
    [r2+4] = r1
    [r2+r0] = r0
    r1 = [r11+r1<<2]
    if (r2 != r1) goto L0203d45c
    r1 = 1945
    [r11+r1<<2] = r0
    goto L0203d75c
L0203d85a:
    [--sp] = rets
    call L0203d218
    pc = [sp++]
L0203d862:
    [--sp] = {rets, r9-r4}
    r0 = 524
    r8 = L01c26890
    r0 = [r8+r0<<2]
    if (r0 != 0) goto L0203d878
    call L0203c018
L0203d878:
    r0 = 8216
    r0 = b[r8+r0] (u)
    if ((r0 & 2) == 0) goto L0203d89c
    r0 = 8220
    r2 = r8 + r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0203d894:
    testset b[r2]
    ifeq goto L0203d894
    csync
L0203d89c:
    r0 = 1949
    r0 = [r8+r0<<2]
    if (r0 == 0) goto L0203d90e
    r1 = 1946
    r2 = 2051
    r2 = [r8+r2<<2]
    r1 = [r8+r1<<2]
    r2 += -88
    r3 = r2 - r1
    r1 = 8224
    r1 += r8
    r9 = -8
    goto L0203d90a
L0203d8c6:
    r5 = [r1+0]
    r4 = r9 - r5
    r6 = r4 & 0x1F
    r4 = r5 + 8
    r7 = 0
    if ((r4 & 0x1F) != 0) {
    r7 = r6
    }
    r6 = r5 + r7
    goto L0203d8f2
L0203d8de:
    r7 = r4 & 0xFFFFFFF8
    r2 = r4 & 0x3
    r4 = r7
    if (r2 != 1) {  ; @if.ne.ri.s12
    r4 = 0
    }
    r3 = r3 - r4
    r6 += r7  ; @add.rr
L0203d8f2:
    if (r6 < r5) goto L0203d908
    r4 = [r1+4]
    r4 += r5  ; @add.rr
    if (r6 >= r4) goto L0203d908
    if (r6 == r0) goto L0203d908
    r4 = [r6+4]
    if (r4 != 7) goto L0203d8de
L0203d908:
    r1 = [r1+8]
L0203d90a:
    if (r1 != 0) goto L0203d8c6
    goto L0203d910
L0203d90e:
    r3 = 0
L0203d910:
    r0 = 8216
    r0 = b[r8+r0] (u)
    if ((r0 & 2) == 0) goto L0203d92e
    csync
    r0 = 8220
    r1 = 0
    b[r8+r0] = r1
    call storage_coordination_irq_leave  ; @call.xl
L0203d92e:
    r0 = ultrarig_heap_start
    r1 = 29883296
    r0 = r1 - r0
    r0 = r0 - r3
    {pc, r9-r4} = [sp++]
L0203d940:
    [--sp] = {rets, r5, r4}
    r4 = r0
    call L0203c15c
    r5 = r0
    if (r5 == 0) goto L0203d956
    r1 = 0
    r2 = r4
    call effect_enable_memset  ; @call.xl
L0203d956:
    r0 = r5
    {pc, r5, r4} = [sp++]
    [--sp] = {rets, r5, r4}
    if (r0 == 0) goto L0203d978
    r2 = r1 | r0
    r4 = r1 * r0
    if (r2 < 65536) goto L0203d97a
    r0 = r4 / r0 (u)
    if (r0 != r1) {
    r4 = -1
    }
    goto L0203d97a
L0203d978:
    r4 = 0
L0203d97a:
    r0 = r4
    call L0203c15c
    r5 = r0
    if (r5 == 0) goto L0203d98e
    r1 = 0
    r2 = r4
    call effect_enable_memset  ; @call.xl
L0203d98e:
    r0 = r5
    {pc, r5, r4} = [sp++]
L0203d992:
    [--sp] = {rets, r9-r4}
    r3 = r0 + r1  #
    r2 = [r0+4]
    r9 = L01c26890
    if ((r2 & 1) != 0) goto L0203db18
    if ((r2 & 0x3) == 0) goto L0203dcfc
    r2 = 1947  #
    r7 = [r0+0]
    r6 = [r9+r2<<2]
    r0 = r0 - r7
    if (r0 < r6) goto L0203d9fc
    r2 += 1  ; @add.ri.u5
    r2 = [r9+r2<<2]
    r1 += r7  ; @add.rr
    if (r0 == r2) goto L0203d9fe
    if (r7 > 255) goto L0203da16
    r5_r4 = d[r0+8]
    if (r0 == r5) goto L0203d9f6
    r8 = r7 >> 3
    if (r0 == r4) goto L0203d9f8
    r2 = r8 << 3  #
    r7 = [r0+4]
    r7 = r7 & 0xFFFFFFF8
    if (r7 != r2) goto L0203d9fa
    r2 += r9
    r2 = r2 + 7812
    if (r4 == r2) goto L0203da6c
    if (r4 >= r6) goto L0203da66
L0203d9f4:
    goto L0203d9f4
L0203d9f6:
    goto L0203d9f6
L0203d9f8:
    goto L0203d9f8
L0203d9fa:
    goto L0203d9fa
L0203d9fc:
    goto L0203d9fc
L0203d9fe:
    r2 = [r3+4]
    r4 = r2 & 0x3
    if (r4 != 3) goto L0203db18
    r4 = 1945
    [r9+r4<<2] = r1
    r2 &= 4294967294
    [r3+4] = r2
    goto L0203dc40
L0203da16:
    r4 = [r0+12]
    r8 = [r0+24]
    if (r4 == r0) goto L0203da2e
    r2 = [r0+8]
    if (r2 < r6) goto L0203da2c
    r5 = [r2+12]
    if (r5 == r0) goto L0203da5a
L0203da2c:
    goto L0203da2c
L0203da2e:
    r5 = [r0+20]
    if (r5 == 0) goto L0203da36
    r7 = r0 + 20
    goto L0203da3c
L0203da36:
    r7 = r0 + 16
    r5 = [r7+0]
    if (r5 == 0) goto L0203da7a
L0203da3c:
    r4 = r5
    r2 = r7  #
    r5 = [r4+20]
    r7 = r4 + 20
    if (r5 != 0) goto L0203da3c
    r7 = r4
    r5 = [++r7=16]
    if (r5 != 0) goto L0203da3c
    if (r2 < r6) goto L0203da58
    [r2+0] = 0x0
    goto L0203da7c
L0203da58:
    goto L0203da58
L0203da5a:
    r5 = [r4+8]
    if (r5 != r0) goto L0203da2c
    [r2+12] = r4
    [r4+8] = r2
    goto L0203da7c
L0203da66:
    r7 = [r4+12]
    if (r7 != r0) goto L0203d9f4
L0203da6c:
    if (r5 == r4) goto L0203daf2
    if (r5 == r2) goto L0203db06
    if (r5 >= r6) goto L0203db0a
L0203da78:
    goto L0203da78
L0203da7a:
    r4 = 0
L0203da7c:
    if (r8 == 0) goto L0203db18
    r2 = [r0+28]
    r5 = r2 << 2
    r5 += r9
    r5 = r5 + 8076
    r6 = [r5+0]
    if (r0 == r6) goto L0203dab4
    r2 = 1947
    r2 = [r9+r2<<2]
    if (r8 < r2) goto L0203dab2
    r2 = r8
    r6 = [++r2=16]
    r5 = 1
    if (r6 == r0) {
    r5 = 0
    }
    [r2+r5<<2] = r4
    if (r4 != 0) goto L0203dab8
    goto L0203db18
L0203dab2:
    goto L0203dab2
L0203dab4:
    [r5+0] = r4
    if (r4 == 0) goto L0203dafc
L0203dab8:
    r2 = 1947
    r5 = [r9+r2<<2]
    if (r4 < r5) goto L0203daec
    [r4+24] = r8
    r6 = [r0+16]
    r2 = r0 + 16
    if (r6 == 0) goto L0203dad6
    if (r6 < r5) goto L0203daee
    [r4+16] = r6
    [r6+24] = r4
L0203dad6:
    r2 = [r2+4]
    if (r2 == 0) goto L0203db18
    r5 = 1947
    r5 = [r9+r5<<2]
    if (r2 < r5) goto L0203daf0
    [r4+20] = r2
    [r2+24] = r4
    goto L0203db18
L0203daec:
    goto L0203daec
L0203daee:
    goto L0203daee
L0203daf0:
    goto L0203daf0
L0203daf2:
    r2 = r9 + 7772
    [r2+0] &= ~(1 << r8)
    goto L0203db18
L0203dafc:
    r4 = r9 + 7776
    [r4+0] &= ~(1 << r2)
    goto L0203db18
L0203db06:
    r2 = r5 + 8
    goto L0203db14
L0203db0a:
    r2 = r5
    r6 = [++r2=8]
    if (r6 != r0) goto L0203da78
L0203db14:
    [r4+12] = r5
    [r2+0] = r4
L0203db18:
    r2 = 1947
    r6 = [r9+r2<<2]
    if (r3 < r6) goto L0203db7a
    r7 = [r3+4]
    if ((r7 & 2) != 0) goto L0203db7c
    r2 += 2  ; @add.ri.u5
    r2 = [r9+r2<<2]
    if (r3 == r2) goto L0203dc12
    r2 = 1948
    r2 = [r9+r2<<2]
    if (r3 == r2) goto L0203dc34
    r2 = r7 & 0xFFFFFFF8
    r1 += r2  ; @add.rr
    if (r7 > 255) goto L0203dcc6
    r5_r4 = d[r3+8]
    if (r3 == r5) goto L0203db74
    r8 = r7 >> 3
    if (r3 == r4) goto L0203db76
    r7 = r8 << 3
    if (r2 != r7) goto L0203db78
    r2 = r7 + r9
    r2 = r2 + 7812
    if (r4 == r2) goto L0203dd52
    if (r4 >= r6) goto L0203dd4c
L0203db72:
    goto L0203db72
L0203db74:
    goto L0203db74
L0203db76:
    goto L0203db76
L0203db78:
    goto L0203db78
L0203db7a:
    goto L0203db7a
L0203db7c:
    r2 = r7 & 0xFFFFFFFE
    r2 = r1 | 0x1  #
    [r3+4] = r2
    [r0+4] = r2
    [r0+r1] = r1
L0203db8c:
    if (r1 > 255) goto L0203dbc4
    r2 = r1 >> 3
    r3 = r2 << 3
    r3 += r9
    if (r1 <= 31) goto L0203dbc2
    r4 = 1943
    r5 = [r9+r4<<2]
    r1 = 1
    r2 = r1 << r2
    r1 = r3 + 7812
    if ((r5 & r2) == 0) goto L0203dd00
    r2 = r4 + 4
    r4 = [r9+r2<<2]
    r2 = r1
    r3 = [++r2=8]
    if (r3 >= r4) goto L0203dd0a
L0203dbc0:
    goto L0203dbc0
L0203dbc2:
    goto L0203dbc2
L0203dbc4:
    r2 = r1 >> 8
    if (r2 == 0) goto L0203dc4c
    r4 = r1 >> 24
    r3 = 31
    if (r4 != 0) goto L0203dc4e
    r3 = 1048320
    r3 += r2  ; @add.rr
    r3 = r3 >> 16
    r3 = r3 & 0x8
    r2 <<= r3
    r4 = r2 + 0x7F000
    r4 = r4 >> 16
    r4 = r4 & 0x4
    r2 <<= r4
    r5 = r2 + 0x3C000
    r5 = r5 >> 16
    r5 = r5 & 0x2
    r2 <<= r5
    r2 = r2 >> 15
    r3 |= r4
    r3 |= r5
    r3 = 0xE - r3
    r2 += r3  ; @add.rr
    r3 = r2 + 7
    r3 = r1 >> r3
    r3 = r3 & 0x1
    r3 <= insert(r2, p:1, l:31)
    goto L0203dc4e
L0203dc12:
    r2 = r9 + 7784
    r3 = [r2+0]
    r1 += r3  ; @add.rr
    [r2+0] = r1
    [r2+12] = r0
    r1 |= 1
    [r0+4] = r1
    r1 = [r2+8]
    if (r0 != r1) goto L0203dcfc
    r0 = 1948
    r1 = 0
    [r9+r0<<2] = r1
    goto L0203de16
L0203dc34:
    r2 = r9 + 7780
    r3 = [r2+0]
    r1 += r3  ; @add.rr
    [r2+0] = r1
    [r2+12] = r0
L0203dc40:
    r2 = r1 | 0x1
    [r0+4] = r2
    [r0+r1] = r1
    {pc, r9-r4} = [sp++]
L0203dc4c:
    r3 = 0
L0203dc4e:
    r2 = 1944  #
    [r0+28] = r3
    r4 = 0
    r5 = 0
    d[r0+16] = r5_r4
    r4 = 1
    r5 = [r9+r2<<2]
    r6 = r4 << r3
    r4 = r3 << 2
    r4 += r9
    r4 = r4 + 8076
    if ((r5 & r6) == 0) goto L0203dcb4
    r2 = r3 >> 1
    r5 = 0x19 - r2
    r2 = 0
    if (r3 != 31) {  ; @if.ne.ri.s12
    r2 = r5
    }
    r4 = r1 << r2  #
    r5 = [r4+0]
L0203dc86:
    r3 = r5
    r2 = [r3+4]
    r2 = r2 & 0xFFFFFFF8
    if (r2 == r1) goto L0203dcde
    r2 = r4 >> 31
    r2 = r2 << 2
    r2 += r3  ; @add.rr
    r5 = [++r2=16]
    r4 = r4 << 1
    if (r5 != 0) goto L0203dc86
    r1 = 1947
    r1 = [r9+r1<<2]
    if (r2 < r1) goto L0203dcb2
    [r2+0] = r0
    [r0+24] = r3
    goto L0203dcc0
L0203dcb2:
    goto L0203dcb2
L0203dcb4:
    r1 = r5 | r6
    [r9+r2<<2] = r1
    [r4+0] = r0
    [r0+24] = r4
L0203dcc0:
    [r0+12] = r0
    [r0+8] = r0
    {pc, r9-r4} = [sp++]
L0203dcc6:
    r4 = [r3+12]
    r8 = [r3+24]
    if (r4 == r3) goto L0203dd14
    r2 = [r3+8]
    if (r2 < r6) goto L0203dcdc
    r5 = [r2+12]
    if (r5 == r3) goto L0203dd40
L0203dcdc:
    goto L0203dcdc
L0203dcde:
    r1 = 1947
    r2 = [r9+r1<<2]
    r1 = [r3+8]
    if (r1 < r2) goto L0203dcfe
    if (r3 < r2) goto L0203dcfe
    [r1+12] = r0
    [r3+8] = r0
    [r0+8] = r1
    [r0+12] = r3
    [r0+24] = 0x0
L0203dcfc:
    {pc, r9-r4} = [sp++]
L0203dcfe:
    goto L0203dcfe
L0203dd00:
    r2 |= r5
    [r9+r4<<2] = r2
    r2 = r1 + 8
    r3 = r1
L0203dd0a:
    [r2+0] = r0
    [r3+12] = r0
    [r0+8] = r3
    [r0+12] = r1
    {pc, r9-r4} = [sp++]
L0203dd14:
    r7 = [r3+20]
    if (r7 == 0) goto L0203dd1c
    r5 = r3 + 20
    goto L0203dd22
L0203dd1c:
    r7 = [r3+16]
    if (r7 == 0) goto L0203dd60
    r5 = r3 + 16
L0203dd22:
    r4 = r7
    r2 = r5  #
    r7 = [r4+20]
    r5 = r4 + 20
    if (r7 != 0) goto L0203dd22
    r5 = r4
    r7 = [++r5=16]
    if (r7 != 0) goto L0203dd22
    if (r2 < r6) goto L0203dd3e
    [r2+0] = 0x0
    goto L0203dd62
L0203dd3e:
    goto L0203dd3e
L0203dd40:
    r5 = [r4+8]
    if (r5 != r3) goto L0203dcdc
    [r2+12] = r4
    [r4+8] = r2
    goto L0203dd62
L0203dd4c:
    r7 = [r4+12]
    if (r7 != r3) goto L0203db72
L0203dd52:
    if (r5 == r4) goto L0203ddd8
    if (r5 == r2) goto L0203ddec
    if (r5 >= r6) goto L0203ddf0
L0203dd5e:
    goto L0203dd5e
L0203dd60:
    r4 = 0
L0203dd62:
    if (r8 == 0) goto L0203ddfe
    r2 = [r3+28]
    r5 = r2 << 2
    r5 += r9
    r5 = r5 + 8076
    r6 = [r5+0]
    if (r3 == r6) goto L0203dd9a
    r2 = 1947
    r2 = [r9+r2<<2]
    if (r8 < r2) goto L0203dd98
    r2 = r8
    r6 = [++r2=16]
    r5 = 1
    if (r6 == r3) {
    r5 = 0
    }
    [r2+r5<<2] = r4
    if (r4 != 0) goto L0203dd9e
    goto L0203ddfe
L0203dd98:
    goto L0203dd98
L0203dd9a:
    [r5+0] = r4
    if (r4 == 0) goto L0203dde2
L0203dd9e:
    r2 = 1947
    r2 = [r9+r2<<2]
    if (r4 < r2) goto L0203ddd2
    [r4+24] = r8
    r5 = [++r3=16]
    if (r5 == 0) goto L0203ddbc
    if (r5 < r2) goto L0203ddd4
    [r4+16] = r5
    [r5+24] = r4
L0203ddbc:
    r2 = [r3+4]
    if (r2 == 0) goto L0203ddfe
    r3 = 1947
    r3 = [r9+r3<<2]
    if (r2 < r3) goto L0203ddd6
    [r4+20] = r2
    [r2+24] = r4
    goto L0203ddfe
L0203ddd2:
    goto L0203ddd2
L0203ddd4:
    goto L0203ddd4
L0203ddd6:
    goto L0203ddd6
L0203ddd8:
    r2 = r9 + 7772
    [r2+0] &= ~(1 << r8)
    goto L0203ddfe
L0203dde2:
    r3 = r9 + 7776
    [r3+0] &= ~(1 << r2)
    goto L0203ddfe
L0203ddec:
    r2 = r5 + 8
    goto L0203ddfa
L0203ddf0:
    r2 = r5
    r6 = [++r2=8]
    if (r6 != r3) goto L0203dd5e
L0203ddfa:
    [r4+12] = r5
    [r2+0] = r4
L0203ddfe:
    r2 = r1 | 0x1
    r2 = 1948  #
    [r0+4] = r2
    [r0+r1] = r1
    r2 = [r9+r2<<2]
    if (r0 != r2) goto L0203db8c
L0203de16:
    r0 = 1945
    [r9+r0<<2] = r1
    {pc, r9-r4} = [sp++]
    [--sp] = {rets, r14-r4}
    r5_r4 = r1_r0
    if (r4 == 0) goto L0203de3c
    r0 = -128
    r13 = L01c26890
    if (r5 < r0) goto L0203de46
    [r13+96] = 0xC
L0203de38:
    r6 = 0
    goto L0203e040
L0203de3c:
    r0 = r5
    call L0203c15c
    r6 = r0
    goto L0203e040
L0203de46:
    r0 = r5 + 35
    r0 = r0 & 0xFFFFFFE0
    r2 = 32
    if (r5 >= 27) {  ; @if.ge.ri.s12
    r2 = r0
    }
    r0 = 8216
    r0 = b[r13+r0] (u)
    if ((r0 & 2) == 0) goto L0203de7a
    r0 = 8220
    r3 = r13 + r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0203de72:
    testset b[r3]
    ifeq goto L0203de72
    csync
L0203de7a:
    r1 = 1947  #
    r0 = [r4+-4]
    r7 = [r13+r1<<2]
    r9 = r4 + -8
    r3 = r0 & 0x3
    r1 = r0 & 0xFFFFFFF8
    if (r3 == 1) goto L0203df10
    r6 = r1 + -8
    if (r9 < r7) goto L0203df10
    r12 = r4 + r6
    ifs (r6 <= -8) goto L0203df10
    r6 = [r12+4]
    if ((r6 & 1) == 0) goto L0203df10
    if (r3 == 0) goto L0203df18
    if (r1 >= r2) goto L0203df3c
    r3 = 1949
    r3 = [r13+r3<<2]
    if (r12 == r3) goto L0203df64
    r3 = 1948
    r3 = [r13+r3<<2]
    if (r12 == r3) goto L0203df96
    r3 = 0
    if ((r6 & 2) != 0) goto L0203dfec
    r11 = r6 & 0xFFFFFFF8
    r8 = r11 + r1
    if (r8 < r2) goto L0203dfec
    r1 = r8 - r2
    if (r6 > 255) goto L0203e044
    r3 = [r12+12]
    r10 = [r12+8]
    if (r12 == r3) goto L0203df12
    r14 = r6 >> 3
    if (r12 == r10) goto L0203df14
    r6 = r14 << 3
    if (r11 != r6) goto L0203df16
    r6 += r13
    r11 = r6 + 7812
    if (r10 == r11) goto L0203e0ae
    if (r10 >= r7) goto L0203e0a6
L0203df0e:
    goto L0203df0e
L0203df10:
    goto L0203df10
L0203df12:
    goto L0203df12
L0203df14:
    goto L0203df14
L0203df16:
    goto L0203df16
L0203df18:
    r3 = 0
    if (r2 < 256) goto L0203dfec
    r0 = r2 | 0x4
    if (r1 < r0) goto L0203df38
    r0 = 526
    r0 = [r13+r0<<2]
    r1 = r1 - r2
    r0 = r0 << 1
    r3 = r9
    if (r1 <= r0) goto L0203dfec
L0203df38:
    r3 = 0
    goto L0203dfec
L0203df3c:
    r1 = r1 - r2
    r3 = r9
    if (r1 < 32) goto L0203dfec
L0203df44:
    r0 = r0 & 0x1
    r0 |= r2
    r0 |= 2
    r0 = r9 + r2  #
    [r4+-4] = r0
    r2 = r1 | 0x3
    r2 = r0 + r1  #
    [r0+4] = r2
    [r2+4] |= 0x1
    call L0203d992
    goto L0203dfea
L0203df64:
    r6 = 1946
    r3 = [r13+r6<<2]
    r1 += r3  ; @add.rr
    r3 = 0
    if (r1 <= r2) goto L0203dfec
    r0 = r0 & 0x1
    r0 |= r2
    r0 |= 2
    r0 = r9 + r2  #
    [r4+-4] = r0
    r1 = r1 - r2
    r2 = r1 | 0x1
    [r0+4] = r2
    r2 = r6 + 3
    [r13+r2<<2] = r0
    [r13+r6<<2] = r1
    goto L0203dfea
L0203df96:
    r3 = 1945
    r3 = [r13+r3<<2]
    r6 = r3 + r1
    r3 = 0
    if (r6 < r2) goto L0203dfec
    r0 = r0 & 0x1
    r1 = r6 - r2
    if (r1 < 32) goto L0203dfcc
    r0 |= r2
    r0 |= 2
    r0 = r9 + r2  #
    [r4+-4] = r0
    r2 = r1 | 0x1
    r2 = r0  #
    [r0+4] = r2
    [++r2=r1] = r1
    [r2+4] &= 0xFFFFFFFE
    goto L0203dfdc
L0203dfcc:
    r0 |= r6
    r0 |= 2
    r0 = r9 + r6  #
    [r4+-4] = r0
    [r0+4] |= 0x1
    r1_r0 = 0
L0203dfdc:
    r2 = 1945
    [r13+r2<<2] = r1
    r1 = r2 + 3
    [r13+r1<<2] = r0
L0203dfea:
    r3 = r9
L0203dfec:
    r0 = 8216
    r0 = b[r13+r0] (u)
    if ((r0 & 2) == 0) goto L0203e00a
    csync
    r0 = 8220
    r1 = 0
    b[r13+r0] = r1
    call storage_coordination_irq_leave  ; @call.xl
L0203e00a:
    if (r3 == 0) goto L0203e010
    r6 = r3 + 8
    goto L0203e040
L0203e010:
    r0 = r5
    call L0203c15c
    r6 = r0
    if (r6 == 0) goto L0203de38
    r0 = [r4+-4]
    r1 = 8
    if ((r0 & 0x3) != 0) {
    r1 = 4
    }
    r0 = r0 & 0xFFFFFFF8
    r0 = r0 - r1
    r2 = umin(r0, r5)
    r0 = r6
    r1 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r4
    call L0203d218
L0203e040:
    r0 = r6
    {pc, r14-r4} = [sp++]
L0203e044:
    r10 = [r12+12]
    r11 = [r12+24]
    if (r10 == r12) goto L0203e060
    r3 = [r12+8]
    if (r3 < r7) goto L0203e05e
    r6 = [r3+12]
    if (r6 == r12) goto L0203e094
L0203e05e:
    goto L0203e05e
L0203e060:
    r6 = [r12+20]
    if (r6 == 0) goto L0203e06c
    r3 = r12 + 20
    goto L0203e074
L0203e06c:
    r3 = r12 + 16
    r6 = [r3+0]
    if (r6 == 0) goto L0203e0bc
L0203e074:
    r10 = r6  #
    r6 = [r6+20]
    r14 = r3
    r3 = r10 + 20
    if (r6 != 0) goto L0203e074
    r3 = r10
    r6 = [++r3=16]
    if (r6 != 0) goto L0203e074
    if (r14 < r7) goto L0203e092
    [r14+0] = 0x0
    goto L0203e0be
L0203e092:
    goto L0203e092
L0203e094:
    r6 = [r10+8]
    if (r6 != r12) goto L0203e05e
    [r3+12] = r10
    [r10+8] = r3
    goto L0203e0be
L0203e0a6:
    r6 = [r10+12]
    if (r6 != r12) goto L0203df0e
L0203e0ae:
    if (r3 == r10) goto L0203e146
    if (r3 == r11) goto L0203e15a
    if (r3 >= r7) goto L0203e15e
L0203e0ba:
    goto L0203e0ba
L0203e0bc:
    r10 = 0
L0203e0be:
    if (r11 == 0) goto L0203e170
    r3 = [r12+28]
    r6 = r3 << 2
    r6 += r13
    r6 = r6 + 8076
    r7 = [r6+0]
    if (r12 == r7) goto L0203e0fa
    r3 = 1947
    r3 = [r13+r3<<2]
    if (r11 < r3) goto L0203e0f8
    r3 = r11
    r7 = [++r3=16]
    r6 = 1
    if (r7 == r12) {
    r6 = 0
    }
    [r3+r6<<2] = r10
    if (r10 != 0) goto L0203e102
    goto L0203e170
L0203e0f8:
    goto L0203e0f8
L0203e0fa:
    [r6+0] = r10
    if (r10 == 0) goto L0203e150
L0203e102:
    r3 = 1947
    r3 = [r13+r3<<2]
    if (r10 < r3) goto L0203e140
    [r10+24] = r11
    r6 = [++r12=16]
    if (r6 == 0) goto L0203e124
    if (r6 < r3) goto L0203e142
    [r10+16] = r6
    [r6+24] = r10
L0203e124:
    r3 = [r12+4]
    if (r3 == 0) goto L0203e170
    r6 = 1947
    r6 = [r13+r6<<2]
    if (r3 < r6) goto L0203e144
    [r10+20] = r3
    [r3+24] = r10
    goto L0203e170
L0203e140:
    goto L0203e140
L0203e142:
    goto L0203e142
L0203e144:
    goto L0203e144
L0203e146:
    r3 = r13 + 7772
    [r3+0] &= ~(1 << r14)
    goto L0203e170
L0203e150:
    r6 = r13 + 7776
    [r6+0] &= ~(1 << r3)
    goto L0203e170
L0203e15a:
    r6 = r3 + 8
    goto L0203e168
L0203e15e:
    r6 = r3
    r7 = [++r6=8]
    if (r7 != r12) goto L0203e0ba
L0203e168:
    [r10+12] = r3
    [r6+0] = r10
L0203e170:
    if (r1 > 31) goto L0203df44
    r0 = r0 & 0x1
    r0 = r0 | r8
    r0 |= 2
    r0 = r9 + r8  #
    [r4+-4] = r0
    [r0+4] |= 0x1
    goto L0203dfea
