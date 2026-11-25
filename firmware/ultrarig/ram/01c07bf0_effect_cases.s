; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_cases: 1 function, 0x01c07bf0..0x01c089e8

; effect_cases_effect_cases: 0x01c07bf0..0x01c089e8, module effect-cases (effect_cases)
.type effect_cases_effect_cases,@function
effect_cases_effect_cases:
    [--sp] = {rets, r14-r4}
    sp += -888
    r14 = r2  #
    r4 = b[r0+6] (u)
    r9 = r1  #
    r3 = b[r0+0] (u)
    r13 = r0 + 288
    r1 = r3 + -3
    if (r4 != 3) goto L01c07ca0
    if (r1 > 20) goto L01c07cda
    r2 = r1 << 1
    r7 = L01c30e84
    r10 = L01c32db0
    r12 = r0 + 352
    r11 = r0 + 456
    tbh [r2]
effect_cases_table_01c07c26:
    .short (L01c07c50 - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07ce0 - effect_cases_table_01c07c26) / 2, (L01c07d30 - effect_cases_table_01c07c26) / 2
    .short (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07cda - effect_cases_table_01c07c26) / 2, (L01c07d8c - effect_cases_table_01c07c26) / 2, (L01c07de8 - effect_cases_table_01c07c26) / 2, (L01c07e44 - effect_cases_table_01c07c26) / 2
    .short (L01c07e94 - effect_cases_table_01c07c26) / 2, (L01c07f5c - effect_cases_table_01c07c26) / 2, (L01c0804c - effect_cases_table_01c07c26) / 2, (L01c080aa - effect_cases_table_01c07c26) / 2, (L01c0812e - effect_cases_table_01c07c26) / 2
L01c07c50:
    r0 = [r13+0]
    r4 = [r13+4]
    r2 = 0
    [sp+232] = r2
    r3 = r4 << 5
    r1 = 2147483647
    r2 = r1  #
    [sp+236] = r2
    ifs (r4 < 67108864) {
    r2 = r3
    }
    r3 = r0 << 4
    [sp+240] = r2
    ifs (r0 < 134217728) {
    r1 = r3
    }
    r0 = r9  #
    [sp+244] = r1
    r2 = sp + 232
    r1 = r14
    call clamp_stage_clamp_stage  ; @call.xl
    r1 = b[r10+140] (u)
    r0 = [r13+20]
    if (r1 == 0) goto L01c081b4
    r1 = [r10+452]
    r2 = [r10+448]
    goto L01c081e0
L01c07ca0:
    if (r1 > 20) goto L01c07cda
    r2 = r1 << 1
    tbh [r2]
effect_cases_table_01c07ca8:
    .short (L01c0816c - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c08184 - effect_cases_table_01c07ca8) / 2, (L01c0819c - effect_cases_table_01c07ca8) / 2
    .short (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cda - effect_cases_table_01c07ca8) / 2, (L01c07cd2 - effect_cases_table_01c07ca8) / 2, (L01c07cd2 - effect_cases_table_01c07ca8) / 2, (L01c07cd2 - effect_cases_table_01c07ca8) / 2
    .short (L01c07cd2 - effect_cases_table_01c07ca8) / 2, (L01c07cd2 - effect_cases_table_01c07ca8) / 2, (L01c07cd2 - effect_cases_table_01c07ca8) / 2, (L01c07cd2 - effect_cases_table_01c07ca8) / 2, (L01c07cd2 - effect_cases_table_01c07ca8) / 2
L01c07cd2:
    r1 = r9
    r2 = r14
    call drive_dispatch_dispatch
L01c07cda:
    sp += 888
    {pc, r14-r4} = [sp++]
L01c07ce0:
    r4 = [r0+300]
    r5 = [r0+304]
    r0 = [r13+0]
    r2 = [r13+4]
    r1 = r2 << 5
    [sp+32] = r4
    [sp+36] = r5
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    r1 = r7  #
    [sp+40] = r1
    r0 = r9  #
    [sp+44] = r0
    r3 = sp + 32
    r2 = r14
    call input_stage_input_stage  ; @call.xl
    r0 = [sp+36]
    [r13+16] = r0
    r1 = b[r10+140] (u)
    r0 = [r13+48]
    if (r1 == 0) goto L01c08224
    r1 = [r10+452]
    r2 = [r10+448]
    goto L01c08250
L01c07d30:
    r4 = [r0+300]
    r5 = [r0+304]
    r0 = [r13+0]
    r2 = [r13+4]
    r1 = r2 << 5
    [sp+280] = r4
    [sp+284] = r5
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    [sp+288] = r1
    [sp+292] = r0
    r3 = sp + 280
    r0 = r9
    r1 = r9
    r2 = r14
    call input_stage_input_stage  ; @call.xl
    r0 = [sp+284]
    [r13+16] = r0
    r1 = b[r10+140] (u)
    r0 = [r13+48]
    if (r1 == 0) goto L01c08294
    r1 = [r10+460]
    r2 = [r10+456]
    goto L01c082c0
L01c07d8c:
    r1 = [r13+48]
    r2 = [r13+16]
    r3 = [r12+32]
    r0 = [r13+0]
    [sp+328] = r1
    r1 = r2 << 5
    [sp+332] = r3
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    [sp+336] = r1
    [sp+340] = r0
    r3 = sp + 328
    r0 = r9
    r1 = r7
    r2 = r14
    call input_stage_input_stage  ; @call.xl
    r0 = [sp+332]
    [r12+32] = r0
    r1 = b[r10+140] (u)
    r0 = [r12+44]
    if (r1 == 0) goto L01c0830e
    r1 = [r10+468]
    r2 = [r10+464]
    goto L01c08338
L01c07de8:
    r1 = [r13+48]
    r2 = [r13+16]
    r3 = [r12+32]
    r0 = [r13+0]
    [sp+376] = r1
    r1 = r2 << 5
    [sp+380] = r3
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    [sp+384] = r1
    [sp+388] = r0
    r3 = sp + 376
    r0 = r9
    r1 = r9
    r2 = r14
    call input_stage_input_stage  ; @call.xl
    r0 = [sp+380]
    [r12+32] = r0
    r1 = b[r10+140] (u)
    r0 = [r12+44]
    if (r1 == 0) goto L01c08392
    r1 = [r10+476]
    r2 = [r10+472]
    goto L01c083bc
L01c07e44:
    r1 = [r13+48]
    r2 = [r13+16]
    r3 = [r12+32]
    r0 = [r13+0]
    [sp+80] = r1
    r1 = r2 << 5
    [sp+84] = r3
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    r1 = r9  #
    [sp+88] = r1
    r0 = r9  #
    [sp+92] = r0
    r3 = sp + 80
    r2 = r14
    call input_stage_input_stage  ; @call.xl
    r0 = [sp+84]
    [r12+32] = r0
    r1 = b[r10+140] (u)
    r0 = [r12+44]
    if (r1 == 0) goto L01c08414
    r1 = [r10+484]
    r2 = [r10+480]
    goto L01c0843e
L01c07e94:
    r1 = [r13+48]
    r2 = [r13+16]
    r3 = [r12+32]
    r0 = [r13+0]
    [sp+128] = r1
    r1 = r2 << 5
    [sp+132] = r3
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    r1 = r9  #
    [sp+136] = r1
    r0 = r9  #
    [sp+140] = r0
    r3 = sp + 128
    r2 = r14
    call input_stage_input_stage  ; @call.xl
    r0 = [sp+132]
    [r12+32] = r0
    r0 = [r12+16]
    r1 = 357913941
    r3_r2 = r0 * r1 (s)
    r8 = [r12+44]
    r1 = [r12+4]
    r5 = [r12+12]
    r6 = [r12+8]
    r0 = b[r10+140] (u)
    r4 = [r12+0]
    r7 = r5 >>> 3
    r5 = 0x10000 - r6
    r6 = r5 << 14
    if (r0 != 0) goto L01c07f26
    r0 = 0x40000000
    r5 = r10 + 448
    [r5+4] = r0
    [r5+0] = r0
    [r5+12] = r0
    [r5+8] = r0
    r0 += -2
    [r5+20] = r0
    [r5+16] = r0
    r0 = r0 + 4
    [r5+28] = r0
    [r5+24] = r0
    r0 = r0 + 2
    [r5+36] = r0
    [r5+32] = r0
    r0 = 1
    b[r10+140] = r0
L01c07f26:
    [sp+96] = r7
    [sp+100] = r3
    r0 = 0
    [sp+104] = r0
    r0 = r9  #
    [sp+108] = r0
    [sp+112] = r6
    [sp+116] = r4
    r1 = r14  #
    [sp+120] = r1
    [sp+124] = r8
    r2 = sp + 96
    call scaled_clip_scaled_clip  ; @call.xl
    r1 = r14  #
    r0 = [sp+124]
    [r12+44] = r0
    r0 = r9
    r2 = r13
    call band_stage_band_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c07f5c:
    r4 = [r13+16]
    r0 = [r13+0]
    r2 = 0
    [sp+424] = r2
    r3 = r4 << 5
    r1 = 2147483647
    [sp+428] = r2
    r2 = r1
    ifs (r4 < 67108864) {
    r2 = r3
    }
    r3 = r0 << 4
    [sp+432] = r2
    ifs (r0 < 134217728) {
    r1 = r3
    }
    [sp+436] = r1
    r2 = sp + 424
    r0 = r9
    r1 = r14
    call clamp_stage_clamp_stage  ; @call.xl
    r0 = [r12+16]
    r2 = 0x10000 - r0
    r0 = r2 << 13
    r2 = r2 << 14
    r5_r4 = r2 * r2 (s)
    r1_r0 <<= 29
    r7_r6 = r5_r4
    r7_r6 >>= 31
    r5 = r5 + r6
    r6 = b[r10+140] (u)
    r3 = [r12+44]
    r4 = 4116010325
    r1_r0 += r5 * r4 (s)
    r1_r0 >>= 27
    if (r6 != 0) goto L01c07ff8
    r5 = 0x40000000
    r6 = r10 + 448
    [r6+4] = r5
    [r6+0] = r5
    [r6+12] = r5
    [r6+8] = r5
    r5 += -2
    [r6+20] = r5
    [r6+16] = r5
    r5 = r5 + 4
    [r6+28] = r5
    [r6+24] = r5
    r5 = r5 + 2
    [r6+36] = r5
    [r6+32] = r5
    r5 = 1
    b[r10+140] = r5
L01c07ff8:
    r5 = 0x20000000
    [sp+392] = r5
    [sp+396] = r4
    r4 = 0
    [sp+400] = r4
    [sp+404] = r4
    [sp+408] = r2
    r2 = 1073741822
    [sp+412] = r2
    [sp+416] = r0
    [sp+420] = r3
    r2 = sp + 392
    r0 = r9
    r1 = r14
    call scaled_clip_scaled_clip  ; @call.xl
    r0 = [sp+420]
    [r12+44] = r0
    r0 = r9
    r1 = r14
    r2 = r13
    call contour_stage_contour_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c0804c:
    r1 = [r13+48]
    r2 = [r13+16]
    r3 = [r12+32]
    r0 = [r13+0]
    [sp+472] = r1
    r1 = r2 << 5
    [sp+476] = r3
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    [sp+480] = r1
    [sp+484] = r0
    r8 = sp + 472
    r0 = r9
    r1 = r9
    r2 = r14
    r3 = r8
    call input_stage_input_stage  ; @call.xl
    r0 = [sp+476]
    [r12+32] = r0
    r1 = b[r10+140] (u)
    r0 = [r12+52]
    if (r1 == 0) goto L01c08484
    r1 = [r10+452]
    r2 = [r10+448]
    goto L01c084b0
L01c080aa:
    r0 = 0
    [sp+760] = r0
    [sp+808] = r0
    r1 = [r13+16]
    r1 = r1 >>> 1
    [sp+728] = r1
    r1 = 0x0 - r1
    [sp+744] = r1
    r1 = [r13+0]
    r1 = r1 << 1
    [sp+712] = r1
    r1 = [r13+48]
    [sp+764] = r1
    r1 = [r12+32]
    [sp+812] = r1
    r1 = [r13+4]
    [sp+716] = r1
    r2 = [r13+20]
    r1 = r2 << 5
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    r1 = r14  #
    [sp+144] = r1
    r0 = r9  #
    [sp+148] = r0
    r2 = sp + 712
    r3 = sp + 144
    call drive_stage_drive_stage  ; @call.xl
    r0 = [sp+812]
    [r12+32] = r0
    r1 = b[r10+140] (u)
    r0 = [r12+52]
    if (r1 == 0) goto L01c0855c
    r1 = [r10+468]
    r2 = [r10+464]
    goto L01c08586
L01c0812e:
    r1 = [r13+20]
    r0 = r1 << 5
    ifs (r1 >= 67108864) {
    r0 = 2147483647
    }
    r1 = r14  #
    [sp+144] = r0
    r0 = 0
    r0 = r9  #
    [sp+148] = r0
    r3 = sp + 144
    r2 = r13
    call drive_stage_drive_stage  ; @call.xl
    r1 = b[r10+140] (u)
    r0 = [r12+52]
    if (r1 == 0) goto L01c08634
    r1 = [r10+468]
    r2 = [r10+464]
    goto L01c0865e
L01c0816c:
    if (r14 == 0) goto L01c07cda
    r0 = r9
    r1 = r14
    r2 = r13
    call drive_glide_drive  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c08184:
    if (r14 == 0) goto L01c07cda
    r0 = r9
    r1 = r14
    r2 = r13
    call soft_clip_drive_soft_clip_drive  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c0819c:
    if (r14 == 0) goto L01c07cda
    r0 = r9
    r1 = r14
    r2 = r13
    call tilt_drive_tilt_drive  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c081b4:
    r1 = 0x40000000
    r2 = r10 + 448
    r3 = r1 + -2  #
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    [r2+20] = r3
    [r2+16] = r3
    r3 = r1 + 2
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 4
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c081e0:
    r3 = 0x18000000
    r4 = 0xFC000000  #
    [sp+200] = r3
    r3 = 0
    [sp+204] = r3
    [sp+208] = r4
    r3 = 0x40000000  #
    [sp+212] = r3
    [sp+216] = r3
    [sp+220] = r2
    r1 = r14  #
    [sp+224] = r1
    r0 = r9  #
    [sp+228] = r0
    r2 = sp + 200
    call cubic_clip_cubic_clip  ; @call.xl
    r1 = r14  #
    r0 = [sp+228]
    [r13+20] = r0
    r0 = r9
    r2 = r13
    call smooth_stage_smooth_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c08224:
    r1 = 0x40000000
    r2 = r10 + 448
    r3 = r1 + -2  #
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    [r2+20] = r3
    [r2+16] = r3
    r3 = r1 + 2
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 4
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c08250:
    r3 = 0x18000000
    r4 = 0xFC000000  #
    [sp] = r3
    r3 = 0
    [sp+4] = r3
    [sp+8] = r4
    r3 = 0x40000000  #
    [sp+12] = r3
    [sp+16] = r3
    [sp+20] = r2
    r1 = r14  #
    [sp+24] = r1
    r0 = r7  #
    [sp+28] = r0
    r2 = sp + 0
    call cubic_clip_cubic_clip  ; @call.xl
    r1 = r7  #
    r0 = [sp+28]
    [r13+48] = r0
    r0 = r9
    r2 = r14
    r3 = r13
    call mix_stage_mix_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c08294:
    r1 = 0x40000000
    r2 = r10 + 448
    r3 = r1 + -2  #
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    [r2+20] = r3
    [r2+16] = r3
    r3 = r1 + 2
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 4
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c082c0:
    r3 = 0x10000000
    [sp+248] = r3
    r3 = 0
    [sp+252] = r3
    [sp+256] = r3
    [sp+260] = r3
    r3 = 0x40000000
    [sp+264] = r3
    [sp+268] = r2
    [sp+272] = r1
    [sp+276] = r0
    r2 = sp + 248
    r0 = r9
    r1 = r14
    call antialiased_clip_antialiased_clip  ; @call.xl
    r0 = [sp+276]
    [r13+48] = r0
    r0 = r9
    r1 = r14
    r2 = r13
    call tilt_stage_tilt_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c0830e:
    r1 = 0x40000000
    r2 = r10 + 448
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    r1 += -2
    [r2+20] = r1
    [r2+16] = r1
    r3 = r1 + 4
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 6
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c08338:
    r3 = 0x20000000
    [sp+296] = r3
    r3 = 4116010325
    [sp+300] = r3
    r3 = 0
    [sp+304] = r3
    [sp+308] = r3
    r3 = 0x40000000
    [sp+312] = r3
    [sp+316] = r2
    [sp+320] = r1
    [sp+324] = r0
    r2 = sp + 296
    r0 = r7
    r1 = r14
    call asymmetric_clip_asymmetric_clip  ; @call.xl
    r0 = [sp+324]
    [r12+44] = r0
    r0 = r9
    r1 = r7
    r2 = r14
    r3 = r13
    call blend_stage_blend_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c08392:
    r1 = 0x40000000
    r2 = r10 + 448
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    r1 += -2
    [r2+20] = r1
    [r2+16] = r1
    r1 = r1 + 4
    [r2+28] = r1
    [r2+24] = r1
    r3 = r1 + 2
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c083bc:
    r3 = 0x18000000
    [sp+344] = r3
    r3 = 4205488811
    [sp+348] = r3
    r3 = 0
    [sp+352] = r3
    [sp+356] = r3
    r3 = 0x40000000
    [sp+360] = r3
    [sp+364] = r2
    [sp+368] = r1
    [sp+372] = r0
    r2 = sp + 344
    r0 = r9
    r1 = r14
    call asymmetric_clip_asymmetric_clip  ; @call.xl
    r0 = [sp+372]
    [r12+44] = r0
    r0 = r9
    r1 = r14
    r2 = r13
    call filter_stage_filter_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c08414:
    r1 = 0x40000000
    r2 = r10 + 448
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    r1 += -2
    [r2+20] = r1
    [r2+16] = r1
    r1 = r1 + 4
    [r2+28] = r1
    [r2+24] = r1
    r1 = r1 + 2
    [r2+36] = r1
    [r2+32] = r1
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c0843e:
    r3 = 0x40000000
    r4 = 0xC0000000  #
    [sp+48] = r3
    r4 = 0x20000000  #
    [sp+52] = r4
    [sp+56] = r4
    r4 = 4187593114
    [sp+60] = r4
    [sp+64] = r3
    [sp+68] = r2
    r1 = r14  #
    [sp+72] = r1
    r0 = r9  #
    [sp+76] = r0
    r2 = sp + 48
    call polynomial_clip_polynomial_clip  ; @call.xl
    r1 = r14  #
    r0 = [sp+76]
    [r12+44] = r0
    r0 = r9
    r2 = r13
    call tone_stage_tone_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
L01c08484:
    r1 = 0x40000000
    r2 = r10 + 448
    r3 = r1 + -2  #
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    [r2+20] = r3
    [r2+16] = r3
    r3 = r1 + 2
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 4
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c084b0:
    r3 = 0x18000000
    [sp+440] = r3
    r3 = 0
    [sp+444] = r3
    r4 = 0xFC000000
    [sp+448] = r4
    [sp+452] = r3
    r3 = 0x40000000
    [sp+456] = r3
    [sp+460] = r2
    [sp+464] = r1
    [sp+468] = r0
    r7 = sp + 440
    r0 = r9
    r1 = r14
    r2 = r7
    call cubic_clip_cubic_clip  ; @call.xl
    r0 = [sp+468]
    [r12+52] = r0
    r0 = [r13+60]
    [sp+548] = r0
    r0 = [r12+8]
    [sp+560] = r0
    r0 = [r12+0]
    [sp+552] = r0
    r0 = [r12+36]
    [sp+592] = r0
    r0 = [r12+40]
    [sp+596] = r0
    r2 = sp + 488
    r0 = r9
    r1 = r14
    call shelf_stage_shelf_stage  ; @call.xl
    r0 = [sp+592]
    [r12+36] = r0
    r0 = [sp+596]
    [r12+40] = r0
    r0 = b[r11+1] (u)
    r2 = r13 + 128
    if (r0 == 0) goto L01c08754  ; @beq.ri.l
    if (r14 == 0) goto L01c08762  ; @beq.ri.l
    r0 = r9
    r1 = r14
    call biquad_residual  ; @call.xl
    goto L01c08762
L01c0855c:
    r1 = 0x40000000
    r2 = r10 + 448
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    r1 += -2
    [r2+20] = r1
    [r2+16] = r1
    r3 = r1 + 4
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 6
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c08586:
    r3 = 0x20000000
    [sp+664] = r3
    r8 = 4116010325
    [sp+668] = r8
    r3 = 0
    [sp+672] = r3
    [sp+676] = r3
    r3 = 0x40000000
    [sp+680] = r3
    [sp+684] = r2
    [sp+688] = r1
    [sp+692] = r0
    r7 = sp + 664
    r0 = r9
    r1 = r14
    r2 = r7
    call asymmetric_clip_asymmetric_clip  ; @call.xl
    r0 = [sp+692]
    [r12+52] = r0
    r0 = [r13+60]
    [sp+772] = r0
    r0 = [r12+8]
    [sp+784] = r0
    r0 = [r12+0]
    [sp+776] = r0
    r0 = [r12+36]
    [sp+816] = r0
    r0 = [r12+40]
    [sp+820] = r0
    r2 = sp + 712
    r0 = r9
    r1 = r14
    call shelf_stage_shelf_stage  ; @call.xl
    r0 = [sp+816]
    [r12+36] = r0
    r0 = [sp+820]
    [r12+40] = r0
    r0 = b[r11+1] (u)
    r2 = r13 + 128
    if (r0 == 0) goto L01c08874
    if (r14 == 0) goto L01c08882
    r0 = r9
    r1 = r14
    call biquad_residual  ; @call.xl
    goto L01c08882
L01c08634:
    r1 = 0x40000000
    r2 = r10 + 448
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    r1 += -2
    [r2+20] = r1
    [r2+16] = r1
    r3 = r1 + 4
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 6
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c0865e:
    r3 = 0x20000000
    [sp+152] = r3
    r3 = 4116010325
    r3 = 0x40000000  #
    [sp+156] = r3
    r4 = 0
    [sp+160] = r4
    [sp+164] = r4
    [sp+168] = r3
    [sp+172] = r2
    r1 = r14  #
    [sp+176] = r1
    r0 = r9  #
    [sp+180] = r0
    r7 = sp + 152
    r2 = r7
    call asymmetric_clip_asymmetric_clip  ; @call.xl
    r0 = [sp+180]
    [r12+52] = r0
    r2 = [r13+24]
    r0 = [r13+8]
    [sp+184] = r4
    r1 = r2 << 5
    [sp+188] = r4
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    r1 = r14  #
    [sp+192] = r1
    r0 = r9  #
    [sp+196] = r0
    r8 = sp + 184
    r2 = r8
    call halved_clamp_halved_clamp  ; @call.xl
    r1 = b[r10+140] (u)
    r0 = [r12+56]
    if (r1 == 0) goto L01c086d4
    r1 = [r10+460]
    r2 = [r10+456]
    goto L01c08700
L01c086d4:
    r1 = 0x40000000
    r2 = r10 + 448
    r3 = r1 + -2  #
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    [r2+20] = r3
    [r2+16] = r3
    r3 = r1 + 2
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 4
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c08700:
    r3 = 0x10000000
    [sp+152] = r3
    r3 = 0
    [r7+4] = r3
    [r7+8] = r3
    [r7+12] = r3
    [r7+16] = 0x40000000
    [r7+20] = r2
    r1 = r14  #
    [r7+24] = r1
    r0 = r9  #
    [r7+28] = r0
    r2 = sp + 152
    call antialiased_clip_antialiased_clip  ; @call.xl
    r1 = r14  #
    r0 = [r7+28]
    [r12+56] = r0
    r0 = r9
    r2 = r13
    call shelf_stage_shelf_stage  ; @call.xl
    r0 = b[r11+1] (u)
    r2 = r13 + 128
    if (r0 == 0) goto L01c08926
    if (r14 == 0) goto L01c08934
    r0 = r9
    r1 = r14
    call biquad_residual  ; @call.xl
    goto L01c08934
L01c08754:
    if (r14 != 0) {
    r0 = r9
    r1 = r14
    call biquad_rounded  ; @call.xl
    }
L01c08762:
    r0 = [r13+4]
    r1 = [r12+12]
    r11 = [r12+44]
    r2 = 0
    [sp+472] = r2
    [r8+4] = r2
    r2 = 2147483647
    [r8+8] = r2
    r3_r2 = r1 * r11 (s)
    r3_r2 >>= 30
    r1 = 0x10000 - r2
    r1_r0 = r1 * r0 (s)
    r1_r0 >>= 16
    [r8+12] = r0
    r2 = sp + 472
    r0 = r9
    r1 = r14
    call clamp_stage_clamp_stage  ; @call.xl
    r1 = b[r10+140] (u)
    r0 = [r12+56]
    if (r1 == 0) goto L01c087bc
    r1 = [r10+452]
    r2 = [r10+448]
    goto L01c087e8
L01c087bc:
    r1 = 0x40000000
    r2 = r10 + 448
    r3 = r1 + -2  #
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    [r2+20] = r3
    [r2+16] = r3
    r3 = r1 + 2
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 4
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c087e8:
    r3 = 0x18000000
    [sp+440] = r3
    r5 = 0
    [r7+4] = r5
    [r7+8] = 0xFC000000
    [r7+12] = r5
    [r7+16] = 0x40000000
    [r7+20] = r2
    r1 = r14  #
    [r7+24] = r1
    r0 = r9  #
    [r7+28] = r0
    r2 = sp + 440
    call cubic_clip_cubic_clip  ; @call.xl
    r0 = [r7+28]
    [r12+56] = r0
    r6 = 0
    if (r14 < 16) goto L01c0883c
    r4 = 0
    r7 = r9
L01c08822:
    r0 = r7
    call effect_processing_peak16  ; @call.xl
    r6 = smax(r0, r6)
    r5 = r4 + 16
    r0 = r4 + 32
    r7 += 64
    r4 = r5
    if (r0 <= r14) goto L01c08822
L01c0883c:
    if (r5 >= r14) goto L01c08856
    r0 = r14 - r5
    r1 = r5 << 2
    r1 += r9
L01c08848:
    r2 = [r1++=4]
    r2 = abs(r2)
    r6 = smax(r2, r6)
    if (--r0 != 0) goto L01c08848
L01c08856:
    r0 = r9
    r1 = r14
    r2 = r13
    call gain_stage_gain_stage  ; @call.xl
    r0 = r6 - r11
    r0 = r0 >>> 5
    r0 += r11
    [r12+44] = r0
    sp += 888
    {pc, r14-r4} = [sp++]
L01c08874:
    if (r14 != 0) {
    r0 = r9
    r1 = r14
    call biquad_rounded  ; @call.xl
    }
L01c08882:
    r2 = [r13+24]
    r0 = [r13+8]
    r3 = 0
    [sp+696] = r3
    r1 = r2 << 5
    [sp+700] = r3
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    [sp+704] = r1
    [sp+708] = r0
    r2 = sp + 696
    r0 = r9
    r1 = r14
    call clamp_stage_clamp_stage  ; @call.xl
    r1 = b[r10+140] (u)
    r0 = [r12+56]
    if (r1 == 0) goto L01c088ca
    r1 = [r10+468]
    r2 = [r10+464]
    goto L01c088f4
L01c088ca:
    r1 = 0x40000000
    r2 = r10 + 448
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    r1 += -2
    [r2+20] = r1
    [r2+16] = r1
    r3 = r1 + 4
    [r2+28] = r3
    [r2+24] = r3
    r3 = r1 + 6
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c088f4:
    r3 = 0x20000000
    [sp+664] = r3
    [r7+4] = r8
    r3 = 0
    [r7+8] = r3
    [r7+12] = r3
    [r7+16] = 0x40000000
    [r7+20] = r2
    r1 = r14  #
    [r7+24] = r1
    r0 = r9  #
    [r7+28] = r0
    r2 = sp + 664
    call asymmetric_clip_asymmetric_clip  ; @call.xl
    r0 = [r7+28]
    [r12+56] = r0
    goto L01c089d6
L01c08926:
    if (r14 != 0) {
    r0 = r9
    r1 = r14
    call biquad_rounded  ; @call.xl
    }
L01c08934:
    r2 = [r13+28]
    r0 = [r13+12]
    r3 = 0
    [sp+184] = r3
    r1 = r2 << 5
    [r8+4] = r3
    ifs (r2 >= 67108864) {
    r1 = 2147483647
    }
    [r8+8] = r1
    [r8+12] = r0
    r2 = sp + 184
    r0 = r9
    r1 = r14
    call clamp_stage_clamp_stage  ; @call.xl
    r1 = b[r10+140] (u)
    r0 = [r12+60]
    if (r1 == 0) goto L01c0897a
    r1 = [r10+476]
    r2 = [r10+472]
    goto L01c089a4
L01c0897a:
    r1 = 0x40000000
    r2 = r10 + 448
    [r2+4] = r1
    [r2+0] = r1
    [r2+12] = r1
    [r2+8] = r1
    r1 += -2
    [r2+20] = r1
    [r2+16] = r1
    r1 = r1 + 4
    [r2+28] = r1
    [r2+24] = r1
    r3 = r1 + 2
    [r2+36] = r3
    [r2+32] = r3
    r2 = 1
    b[r10+140] = r2
    r2 = r1
L01c089a4:
    r3 = 0x18000000
    [sp+152] = r3
    r3 = 4205488811
    [r7+4] = r3
    r3 = 0
    [r7+8] = r3
    [r7+12] = r3
    [r7+16] = 0x40000000
    [r7+20] = r2
    r1 = r14  #
    [r7+24] = r1
    r0 = r9  #
    [r7+28] = r0
    r2 = sp + 152
    call asymmetric_clip_asymmetric_clip  ; @call.xl
    r0 = [r7+28]
    [r12+60] = r0
L01c089d6:
    r0 = r9
    r1 = r14
    r2 = r13
    call gain_stage_gain_stage  ; @call.xl
    sp += 888
    {pc, r14-r4} = [sp++]
