; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 9 functions, 0x01c02dbc..0x01c03278

; ram_callbacks_idle_watch: 0x01c02dbc..0x01c02ec4, module ram-callbacks (idle_watch)
.type ram_callbacks_idle_watch,@function
ram_callbacks_idle_watch:
    [--sp] = {rets, r8-r4}
    call storage_platform_clock  ; @call.xl
    r1 = L01c1f180
    r4 = [r1+24]
    r1 = L01c26890
    r2 = [r1+356]
    r5 = b[r1+29] (u)
    r3 = 0
    if (r5 == 0) goto L01c02dee
    r5 = b[r1+26] (u)
    if (r5 != 0) goto L01c02dee
    r5 = [r1+280]
    r3 = 1
    if (r5 != 0) goto L01c02dee
    r3 = r5
L01c02dee:
    r5 = 2044
    r6 = b[r1+r5] (u)
    if (r6 == 0) goto L01c02e0c
    r8 = 506
    r7 = [r1+r8<<2]
    r7 = r0 - r7
    r6 = 3333351
    if (r7 < r6) goto L01c02e68
L01c02e0c:
    r6 = 1
    b[r1+r5] = r6
    r5 = r1 + 2024
    [r5+4] = r4
    [r5+8] = r0
    [r5+12] = r2
    [r5+16] = r0
L01c02e1e:
    [r5+0] = r0
L01c02e20:
    r4 = 509
    r5 = [r1+r4<<2]
    r4 = 1
    if (r5 != r2) {
    r4 = 0
    }
    if ((r3 & r4) == 0) {
    r3 = 509
    [r1+r3<<2] = r2
    r2 = r3 + 1
    [r1+r2<<2] = r0
    }
    r2 = 508
    r2 = [r1+r2<<2]
    r2 = r0 - r2
    r3 = 166667500
    if (r2 > r3) goto L01c02e82
    r2 = 510
    r2 = [r1+r2<<2]
    r0 = r0 - r2
    r2 = r3 + 1
    if (r0 >= r2) goto L01c02e86
    {pc, r8-r4} = [sp++]
L01c02e68:
    r5 = 507
    r6 = [r1+r5<<2]
    [r1+r8<<2] = r0
    if (r6 == r4) goto L01c02e20
    [r1+r5<<2] = r4
    r5 = r1 + 2032
    goto L01c02e1e
L01c02e82:
    r4 = 1
    goto L01c02e88
L01c02e86:
    r4 = 0
L01c02e88:
    r0 = r1 + 2040
    r5 = r1 + 2032
    if (r4 != 0) goto L01c02e94
    r5 = r0
L01c02e94:
    call storage_platform_clock  ; @call.xl
    r1 = [r5+0]
    r0 = r0 - r1
    r1 = 66667
    r0 = r0 / r1 (u)
    r1 = 0x80000000
    if (r4 != 0) goto L01c02eb0
    r1 = r4
L01c02eb0:
    r2 = 32436348
    r1 |= r0  #
    r2 = [r2+0]
    r0 = 8
    call fault_record_fatal_record  ; @call.xl
L01c02ec2:
    goto L01c02ec2

; ram_callbacks_convert: 0x01c02ec4..0x01c02f4c, module ram-callbacks (convert)
.type ram_callbacks_convert,@function
ram_callbacks_convert:
    [--sp] = {rets, r12-r4}
    r5 = 0
    r9_r8 = 0
    goto L01c02f1e
L01c02ecc:
    r10 = [r1+24]
    r11 = [r1+16]
    r3 = r0  #
    r4 = [r1+8]
    r7 = [r1++=32]
    r5 = r5 << 2
    r7 = r7 << 8
    r7 = r7 >>> 1
    [++r3=r5] = r7
    r4 = r4 << 8
    r4 = r4 >>> 1
    r5 = r11 << 8
    r5 = r5 >>> 1
    d[r3+4] = r5_r4
    r6 = r10 << 8
    r6 = r6 >>> 1
    r10 = smin(r5, r6)  #
    [r3+12] = r6
    r3 = smin(r7, r4)
    r3 = smin(r3, r10)
    r8 = smin(r8, r3)
    r3 = smax(r5, r6)
    r4 = smax(r7, r4)
    r3 = smax(r4, r3)
    r9 = smax(r9, r3)
    r5 = r12
L01c02f1e:
    r12 = r5 + 4
    ifs (r12 <= r2) goto L01c02ecc
    goto L01c02f3e
L01c02f28:
    r3 = [r1++=8]
    r3 = r3 << 8
    r3 = r3 >>> 1
    [r0+r5<<2] = r3
    r8 = smin(r8, r3)
    r9 = smax(r9, r3)
    r5 += 1  ; @add.ri.u5
L01c02f3e:
    ifs (r5 < r2) goto L01c02f28
    r0 = 0x0 - r8
    r0 = smax(r9, r0)
    {pc, r12-r4} = [sp++]

; ram_callbacks_count_loud: 0x01c02f4c..0x01c02f7a, module ram-callbacks (count_loud)
.type ram_callbacks_count_loud,@function
ram_callbacks_count_loud:
    [--sp] = {rets, r7-r4}
    r2 = r0
    r0 = 0
    r3 = 1062731775
    r4 = 2125463550
    r5 = 0
    goto L01c02f74
L01c02f62:
    r6 = [r2+r5<<2]
    r7 = r6 + r3
    r6 = 1
    if (r7 <= r4) {
    r6 = 0
    }
    r0 += r6  ; @add.rr
    r5 += 1  ; @add.ri.u5
L01c02f74:
    ifs (r5 < r1) goto L01c02f62
    {pc, r7-r4} = [sp++]

; ram_callbacks_input_block: 0x01c02f7a..0x01c03076, module ram-callbacks (input_block)
.type ram_callbacks_input_block,@function
ram_callbacks_input_block:
    [--sp] = {rets, r15-r4}
    r8 = L01c26890
    r0 = r8 + 4076
    [r0+0] += 1  ; @rmw.add.s12
    r0 = [r8+280]
    r11 = r1
    if (r0 == 0) goto L01c03074
    r0 = 8
    r14 = r2 / r0 (s)
    r12 = [r8+380]
    r4 = [r8+544]
    r10 = 0
    r13 = L01c234a8
    r9 = 0
L01c02faa:
    r15 = r12 & 0x3
L01c02fae:
    ifs (r14 < 1) goto L01c0302c
    r0 = 0x80 - r4
    r5 = smin(r0, r14)
    r0 = r4 << 2
    r1 = r15 << 9
    r0 += r1  ; @add.rr
    r7 = r0 + r13
    r0 = r7
    r1 = r11
    r2 = r5
    call ram_callbacks_convert
    r6 = r0
    r0 = r6 >> 19
    if (r0 < 2027) goto L01c02fe2
    r0 = r7
    r1 = r5
    call ram_callbacks_count_loud
    r9 += r0
L01c02fe2:
    r10 = umax(r6, r10)
    r4 += r5  ; @add.rr
    r14 = r14 - r5
    r0 = r5 << 3
    r11 += r0
    if (r4 != 128) goto L01c02fae
    r4 = r8 + 1764
    call storage_platform_clock  ; @call.xl
    [r4+r15<<2] = r0
    r0 = [r8+384]
    r0 = r12 - r0
    if (r0 < 4) {  ; @if.lt.ri.s12
    r12 = r12 + 1
    [r8+380] = r12
    } else {
    r0 = r8 + 4088
    [r0+0] += 1  ; @rmw.add.s12
    }
    r0 = r8 + 3508
    call L020403ee  ; @call.xl
    r4 = 0
    goto L01c02faa
L01c0302c:
    [r8+544] = r4
    r1 = 1025
    r2 = [r8+r1<<2]
    r0 = r10 >> 7
    if (r0 > r2) {
    [r8+r1<<2] = r0
    }
    r1 += 16  ; @add.ri.u5
    r2 = [r8+r1<<2]
    if (r0 > r2) {
    [r8+r1<<2] = r0
    }
    r0 = 1048704
    if (r10 >= r0) {
    r0 = 1019
    r0 = [r8+r0<<2]
    [r8+404] = r0
    }
    if (r9 != 0) {  ; @if.ne.ri.s12
    r0 = r8 + 4144
    [r0+0] += r9
    }
L01c03074:
    {pc, r15-r4} = [sp++]

; ram_callbacks_zero_fill: 0x01c03076..0x01c03088, module ram-callbacks (zero_fill)
.type ram_callbacks_zero_fill,@function
ram_callbacks_zero_fill:
    r1 = r1 << 1
    r3_r2 = 0
    goto L01c03082
L01c0307c:
    [r0+r3<<2] = r2
    r3 += 1  ; @add.ri.u5
L01c03082:
    ifs (r3 < r1) goto L01c0307c
    rts

; ram_callbacks_copy_pairs: 0x01c03088..0x01c030ac, module ram-callbacks (copy_pairs)
.type ram_callbacks_copy_pairs,@function
ram_callbacks_copy_pairs:
    [--sp] = {rets, r6-r4}
    r4 = 0
    goto L01c030a6
L01c0308e:
    r5 = [r1+r4<<2]
    r6 = [r2+r4<<2]
    r5 = r5 & 0xFFFFFF
    r5 = r6 & 0xFFFFFF  #
    [r0+0] = r5
    [r0+4] = r5
    r0 += 8  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L01c030a6:
    ifs (r4 < r3) goto L01c0308e
    {pc, r6-r4} = [sp++]

; ram_callbacks_copy_frames: 0x01c030ac..0x01c03100, module ram-callbacks (copy_frames)
.type ram_callbacks_copy_frames,@function
ram_callbacks_copy_frames:
    [--sp] = {rets, r7-r4}
    r3 = 0
    goto L01c030e2
L01c030b2:
    r3 = r3 << 2
    r3 += r1  ; @add.rr
    r5 = [r3+0]
    r5 = r5 & 0xFFFFFF  #
    r6 = [r3+12]
    r7 = [r3+8]
    r3 = [r3+4]
    r3 = r3 & 0xFFFFFF  #
    [r0+0] = r5
    [r0+4] = r5
    [r0+8] = r3
    r3 = r7 & 0xFFFFFF  #
    [r0+12] = r3
    [r0+16] = r3
    r3 = r6 & 0xFFFFFF  #
    [r0+20] = r3
    [r0+24] = r3
    r3 = r4  #
    [r0+28] = r3
    r0 += 32
L01c030e2:
    r4 = r3 + 4
    ifs (r4 <= r2) goto L01c030b2
    goto L01c030fa
L01c030ea:
    r4 = [r1+r3<<2]
    r4 = r4 & 0xFFFFFF
    [r0+0] = r4
    [r0+4] = r4
    r0 += 8  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L01c030fa:
    ifs (r3 < r2) goto L01c030ea
    {pc, r7-r4} = [sp++]

; ram_callbacks_output_block: 0x01c03100..0x01c031f4, module ram-callbacks (output_block)
.type ram_callbacks_output_block,@function
ram_callbacks_output_block:
    [--sp] = {rets, r13-r4}
    r8 = L01c26890
    r0 = r8 + 4080
    [r0+0] += 1  ; @rmw.add.s12
    r3 = [r8+524]
    r10 = r1
    r0 = 8
    if (r3 == 0) goto L01c0319a
L01c0311a:
    r1 = [r8+524]
    r5 = r2 / r0 (s)
    if (r1 == 0) goto L01c031d0
    r0 = r8 + 532
    r9 = [r0+8]
    r4 = [r0+4]
    r12 = 580  #
    r7 = [r0+0]
    r11 = L01c224a8
    r13 = L01c22ca8
    goto L01c03192
L01c03142:
    if (r9 == r4) goto L01c031da
    r0 = 0x80 - r7
    r6 = smin(r0, r5)
    r0 = r4 & 0x3
    r1 = r0 + r8
    r2 = b[r1+r12] (u)
    r1 = r7 << 2
    r0 = r0 << 9
    r0 += r1  ; @add.rr
    r1 = r0 + r11
    if (r2 == 0) goto L01c03172
    r2 = r0 + r13
    r0 = r10
    r3 = r6
    call ram_callbacks_copy_pairs
    goto L01c03178
L01c03172:
    r0 = r10
    r2 = r6
    call ram_callbacks_copy_frames
L01c03178:
    r5 = r5 - r6
    r0 = r6 + r7
    r7 = 0
    if (r0 != 128) {  ; @if.ne.ri.s12
    r7 = r0
    }
    r1 = r6 << 3
    r10 += r1
    r1 = 1
    if (r0 != 128) {  ; @if.ne.ri.s12
    r1 = 0
    }
    r4 += r1  ; @add.rr
L01c03192:
    ifs (r5 >= 1) goto L01c03142
    r9 = r4
    goto L01c031ea
L01c0319a:
    r1 = [r8+280]
    if (r1 == 0) goto L01c0311a
    r1 = [r8+548]
    r1 += 1  ; @add.ri.u5
    [r8+548] = r1
    r3 = 1027
    r3 = [r8+r3<<2]
    r4 = 1
    r4 <= insert(r3, p:1, l:31)
    if (r1 < r4) goto L01c0311a
    r1 = [r8+540]
    r3 = [r8+536]
    if (r1 != r3) {
    r1 = 1
    [r8+524] = r1
    }
    goto L01c0311a
L01c031d0:
    r0 = r10
    r1 = r5
    call ram_callbacks_zero_fill
    {pc, r13-r4} = [sp++]
L01c031da:
    r0 = r8 + 4092
    [r0+0] += r5
    r0 = r10
    r1 = r5
    call ram_callbacks_zero_fill
L01c031ea:
    [r8+532] = r7
    [r8+536] = r9
    {pc, r13-r4} = [sp++]

; ram_callbacks_stall_check: 0x01c031f4..0x01c03278, module ram-callbacks (stall_check)
.type ram_callbacks_stall_check,@function
ram_callbacks_stall_check:
    [--sp] = {rets, r5, r4}
    r2 = r1
    r1 = cnum
    r3 = r2
    r3 <= insert(r1, p:0, l:1)
    r0 = r0 >> 4
    r4 = r0 & 0x1C
    r0 = L01c26890
    r4 += r0  ; @add.rr
    r5 = 589
    [r4+r5<<2] = r3
    r1 = r1 & 0x1
    r3 = L01c1fc64
    r1 = [r3+r1<<2]
    r3 = 581
    [r4+r3<<2] = r1
    r1 = b[r0+29] (u)
    if (r1 == 0) goto L01c0323a
    r1 = b[r0+26] (u)
    if (r1 == 0) goto L01c0323c
L01c0323a:
    {pc, r5, r4} = [sp++]
L01c0323c:
    r1 = [r0+280]
    if (r1 == 0) goto L01c0323a
    r1 = L01c1f180
    r3 = [r1+24]
    r1 = [r0+204]
    r0 = [r0+560]
    if (r1 == 0) goto L01c0323a
    if (r0 == 0) goto L01c0323a
    r1 = r3 - r1
    r1 = r1 * 0xA
    r4 = 6001
    if (r1 < r4) goto L01c0323a
    r0 = r3 - r0
    r0 = r0 * 0xA
    if (r0 < r4) goto L01c0323a
    r0 = 4
    call fault_record_fatal_record  ; @call.xl
L01c03276:
    goto L01c03276
