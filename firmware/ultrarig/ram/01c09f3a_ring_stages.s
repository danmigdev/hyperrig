; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ring_stages: 5 functions, 0x01c09f3a..0x01c0a774

; ring_stages_line_sums: 0x01c09f3a..0x01c0a044, module ring-stages (line_sums)
.type ring_stages_line_sums,@function
ring_stages_line_sums:
    [--sp] = {rets, r15-r4}
    sp += -92
    r4 = [sp+152]
    r5 = [sp+156]
    r8 = [sp+160]
    [sp+48] = r4
    [sp+52] = r5
    r11 = [r8+0]
    r10 = r1
    r9 = r0
    [sp+56] = r11
    r12 = [sp+148]
    r13 = r2  #
    r7 = [sp+144]
    r5 = sp + 8
    r1 = 0
    r14 = r0 + 160
L01c09f60:
    r0 = b[r7+r1] (u)
    r4 = 0
    if (r0 == 255) goto L01c09f8a
    r4 = r9 + 80
    r6 = [r4+r0<<2]
    r0 = [r14+r0<<2]
    r4 = h[r12+r1<<1] (u)
    r2 = r6 - r3
    r0 = r0 + r2
    r4 = r0 - r4
    r0 = 0
    if (r4 >= r6) {
    r0 = r6
    }
    r4 = r4 - r0
L01c09f8a:
    r0 = sp + 60
    [r0+r1<<2] = r4
    r1 = r1 + 1
    if (r1 != 8) goto L01c09f60
    if (r13 == 0) goto L01c0a03c
    r15 = 0  #
    [sp] = r5
    [sp+4] = r8
    r11 = sp + 8
    r12 = L01c31ea4
L01c09faa:
    r4 = r13 - r15
    r14 = r15 << 2
    r1 = r14 + r12
    r2 = 0
L01c09fb8:
    r3 = b[r7+r2] (u)
    if (r3 == 255) goto L01c09fe0
    r0 = sp + 60
    r0 = [r0+r2<<2]
    r3 = r3 << 2
    r6 = r9
    r3 = [++r6=r3]
    r6 = [r6+80]
    r8 = r0 << 2
    r3 += r8
    r0 = r6 - r0
    r4 = umin(r4, r0)
    goto L01c09fe2
L01c09fe0:
    r3 = r1
L01c09fe2:
    r0 = sp + 8
    r0 = r0 + 4
    [r0+r2<<2] = r3
    r2 = r2 + 1
    if (r2 != 8) goto L01c09fb8
    r0 = r10 + r14
    [sp+8] = r0
    [r11+36] = r4
    r0 = sp + 8
    call diffusion_kernels_line_sum  ; @call.xl
    r0 = 0
L01c0a004:
    r2 = b[r7+r0] (u)
    if (r2 == 255) goto L01c0a028
    r3 = r9 + 80
    r1 = sp + 60
    r6 = [r1+r0<<2]
    r5 = [r3+r2<<2]
    r3 = r6 + r4
    r2 = 0
    if (r3 != r5) {
    r2 = r3
    }
    [r1+r0<<2] = r2
L01c0a028:
    r0 = r0 + 1
    if (r0 != 8) goto L01c0a004
    r15 += r4
    if (r15 < r13) goto L01c09faa
    r0 = [sp]
    r11 = [r0+48]
    r8 = [sp+4]
L01c0a03c:
    [r8+0] = r11
    sp += 92
    {pc, r15-r4} = [sp++]

; ring_stages_ring_step: 0x01c0a044..0x01c0a292, module ring-stages (ring_step)
.type ring_stages_ring_step,@function
ring_stages_ring_step:
    [--sp] = {rets, r15-r4}
    sp += -32
    r9 = r2
    r4 = r1
    r5 = r0
    r2 = setup_object1_short_lengths
    r3 = L0203b7c8
    call ring_stages_diffusion_pass
    r0 = 0x50000000
    r0 = r5  #
    [sp+8] = r0
    [sp+4] = r4
    r7 = 0
    r3 = L01c30d74
    r1 = 12
    r2 = 225
    [sp] = r7
    call ring_stages_all_pass_lines
    r3 = 4
L01c0a07c:
    r0 = r7 << 2
    r0 = r0 + r5
    r1 = r0 + 312
    r2 = [r1+0]
    r6 = [r0+376]
    r6 = r6 - r2
    r6 = r6 / r3 (s)
    r2 = r2 + r6
    [r1+0] = r2
    r2 = [r1+32]
    r0 = [r0+408]
    r0 = r0 - r2
    r0 = r0 / r3 (s)
    r0 = r0 + r2
    [r1+32] = r0
    r0 = r7 << 1
    r0 = r0 + r5
    r6 = r0 + 472
    r1 = h[r6+16] (u)
    r0 = h[r6+0] (u)
    call rate_leaves_step_toward
    r7 = r7 + 1
    h[r6+0] = r0
    if (r7 != 4) goto L01c0a07c
    r3 = sp + 28
    r1 = 0
    r0 = r5
    r2 = r4
    call modulation_modulator
    r3 = sp + 24
    r1 = 1
    r0 = r5
    r2 = r4
    call modulation_modulator
    r10 = [sp+28]
    if (r9 == 0) goto L01c0a0f2
    r1 = 0
    r0 = r5
    r2 = r10
    call rate_leaves_wrap_position
    r9 = [sp+24]
    r1 = 2
    r0 = r5
    r2 = r9
    call rate_leaves_wrap_position
    goto L01c0a0f4
L01c0a0f2:
    r9 = [sp+24]
L01c0a0f4:
    r7 = r5 + 472
    r13 = [r7+32]
    r6 = r5 + 276
    r15 = 1024  #
    r0 = [r6+48]
    r12 = 0  #
    r1 = [r6+12]
    [sp+16] = r15
    r1 = r6 + 176  #
    [sp+12] = r1
    r3 = r4  #
    [sp+8] = r1
    r1 = 0
    [sp] = r0
    [sp+4] = r1
    r11 = L01c30e84
    r1 = 3
    r0 = r5
    r2 = r11
    call ring_stages_ring_read
    r0 = r5  #
    r2 = h[r7+0] (u)
    r8 = 2791728742
    [sp+8] = r8
    r3 = r11  #
    [sp+4] = r4
    r1 = 4
    r14 = L01c30d74
    [sp] = r14
    call ring_stages_all_pass_lines
    r3 = r4  #
    r0 = [r6+40]
    r1 = [r6+4]
    [sp+16] = r15
    r1 = r6 + 168  #
    [sp+12] = r1
    [sp+8] = r1
    [sp+4] = r12
    r12 = r11 + 256  #
    [sp] = r0
    r1 = 1
    r0 = r5
    r2 = r12
    call ring_stages_ring_read
    r0 = r5  #
    r2 = h[r7+4] (u)
    [sp+8] = r8
    r3 = r12  #
    [sp+4] = r4
    r1 = 6
    [sp] = r14
    call ring_stages_all_pass_lines
    r3 = r4  #
    r0 = [r6+36]
    r1 = [r5+344]
    r2 = [r6+0]
    [sp+16] = r15
    r2 += r10
    r2 = r6 + 164  #
    [sp+12] = r2
    r10 = r11 + 512  #
    [sp+8] = r2
    [sp] = r0
    [sp+4] = r1
    r1 = 0
    r0 = r5
    r2 = r10
    call ring_stages_ring_read
    r8 = 0  #
    r2 = h[r7+2] (u)
    [sp+8] = r13
    r3 = r10  #
    [sp+4] = r4
    r1 = 5
    r0 = 0
    r0 = r5  #
    [sp] = r0
    call ring_stages_all_pass_lines
    r3 = r4  #
    r0 = [r6+44]
    r1 = [r5+352]
    r2 = [r6+8]
    [sp+16] = r15
    r2 += r9
    r2 = r6 + 172  #
    [sp+12] = r2
    r6 = r11 + 768  #
    [sp+8] = r2
    [sp] = r0
    [sp+4] = r1
    r1 = 2
    r0 = r5
    r2 = r6
    call ring_stages_ring_read
    r0 = r5  #
    r2 = h[r7+6] (u)
    [sp+8] = r13
    r3 = r6  #
    [sp+4] = r4
    r1 = 7
    [sp] = r8
    call ring_stages_all_pass_lines
    r0 = [r7+32]
    r1 = [r7+36]
    call rate_leaves_approach
    r0 = r5  #
    [r7+32] = r0
    r1 = 0
    r2 = r11
    r3 = r4
    call rate_leaves_ring_write
    r1 = 2
    r0 = r5
    r2 = r12
    r3 = r4
    call rate_leaves_ring_write
    r1 = 1
    r0 = r5
    r2 = r10
    r3 = r4
    call rate_leaves_ring_write
    r1 = 3
    r0 = r5
    r2 = r6
    r3 = r4
    call rate_leaves_ring_write
    r8 = r7 + 204
    r3 = -16
L01c0a236:
    r0 = r5 + r3
    r7 = r0 + 692
    r1 = h[r7+16] (u)
    r0 = h[r7+0] (u)
    call rate_leaves_step_toward
    r3 = r3 + 2
    h[r7+0] = r0
    if (r3 != 0) goto L01c0a236
    r7 = r5 + 708
    r1 = [r7+8]
    r0 = [r7+0]
    call rate_leaves_approach
    r6 = r14  #
    [r7+0] = r0
    r1 = L01c31ea4
    r0 = r6
    r2 = r4
    call dsp_stage_copy  ; @call.xl
    r0 = 0
    r3 = r4  #
    [sp+20] = r0
    r1 = [r7+0]
    r2 = sp + 20
    r2 = r4  #
    [sp+16] = r2
    [sp+12] = r0
    r1 = r6  #
    [sp+8] = r1
    [sp+4] = r8
    r0 = model_object1_routes
    r0 = r5  #
    [sp] = r0
    call ring_stages_line_sums
    sp += 32
    {pc, r15-r4} = [sp++]

; ring_stages_voice_lines: 0x01c0a292..0x01c0a432, module ring-stages (voice_lines)
.type ring_stages_voice_lines,@function
ring_stages_voice_lines:
    [--sp] = {rets, r15-r4}
    sp += -64
    r15 = r0
    r0 = r0 + 633
    [sp+40] = r0
    r0 = b[r0+0] (u)
    [sp+48] = r1
    if (r0 == 0) goto L01c0a42e
    r13 = 0  #
    r0 = [sp+40]
    r2 = r0 + 91
    r10 = r0 + 43
    r1 = r0 + 151
    r9 = r2  #
    [sp+28] = r1
    r4 = r10  #
    r1 = [sp+48]
    r6 = r1 >> 2
    r3 = r0 + 175
    r1 = r0 + 187
    r1 = r0 + 163  #
    [sp+44] = r1
    r11 = r0 + 139  #
    [sp+20] = r1
    r12 = L0203b7d8
    [sp+36] = r2
    [sp+32] = r4
    [sp+24] = r11
    [sp+60] = r3
L01c0a2e2:
    r0 = r13 << 4  #
    [sp+52] = r4
    r14 = r10 + r0
    r1 = r13 << 3
    r2 = 8
    r3 = r4
    r0 = 0
L01c0a2f6:
    r5 = h[r3+48] (u)
    r7 = h[r3++=2] (u)
    r4 = 1
    if (r7 == r5) {
    r4 = 0
    }
    r0 |= r4
    if (--r2 != 0) goto L01c0a2f6
    r2 = [sp+36]
    r1 = h[r2+r1<<1] (u)
    r2 = h[r11+r13<<1] (u)
    if (r2 != r1) goto L01c0a32a
    r2 = r10 + r13
    r1 = b[++r2=102] (u)
    if (r1 <= 7) {
    r1 = r1 + 1
    b[r2+0] = r1
    }
    goto L01c0a338
L01c0a32a:
    h[r11+r13<<1] = r1
    r2 = r10 + r13
    r1 = 0
    b[r2+102] = r1
L01c0a338:
    if (r0 == 0) goto L01c0a344
    r4 = 0
    r0 = r1.b0 (u)
    r1 = 0
    if (r0 > 7) goto L01c0a34c
L01c0a344:
    r0 = [sp+20]
    r1 = [r0+r13<<2]
    r4 = 1
L01c0a34c:
    r5 = [sp+28]
    r7 = [r5+r13<<2]
    r0 = r7
    call rate_leaves_approach
    [r5+r13<<2] = r0
    if (r4 != 0) goto L01c0a378
    if (r0 != 0) goto L01c0a378
    r1 = 8
    r2 = r9
L01c0a364:
    r3 = h[r2+0] (u)
    h[r2+-48] = r3
    r2 = r2 + 2
    if (--r1 != 0) goto L01c0a364
    r1 = [sp+44]
    r2 = 0
    [r1+r13<<2] = r2
L01c0a378:
    [sp+56] = r9
    r1 = r0 | r7  #
    r3 = [sp+60]
    if (r1 != 0) goto L01c0a38a
    r1 = [sp+44]
    r1 = [r1+r13<<2]
    if (r1 == 0) goto L01c0a414
L01c0a38a:
    r9 = r14  #
    r1 = [sp+48]
    if ((r1 & 0x3) != 0) goto L01c0a3ee
    if (r0 == r7) goto L01c0a3ee
    r10 = r0 - r7  #
    r1 = [sp+44]
    r11 = r10 >>> 31  #
    r5 = [sp+48]
    r0 = r13 << 2
    r8 = r1 + r0
    r14 = 1
    r4 = L01c30818
L01c0a3b6:
    r0 = [r3+r13<<2]
    [sp+16] = r8
    r1_r0 = r14 * r10 (s)  #
    [sp+12] = r0
    [sp+4] = r9
    [sp] = r12
    r2 = 4
    r1_r0 = r1_r0 / r2 (s)
    r0 = r0 + r7
    r0 = r15  #
    [sp+8] = r0
    r1 = r4
    r2 = r6
    r3 = r5
    call ring_stages_line_sums
    r5 = r5 - r6  #
    r3 = [sp+60]
    r0 = r6 << 2
    r14 = r14 + 1
    r4 = r4 + r0
    if (r14 != 5) goto L01c0a3b6
    goto L01c0a414
L01c0a3ee:
    r1 = [r3+r13<<2]
    r2 = r13 << 2  #
    r3 = [sp+44]
    r2 = r2 + r3
    [sp+16] = r2
    [sp+8] = r0
    [sp+12] = r1
    [sp+4] = r9
    [sp] = r12
    r0 = r15  #
    r2 = [sp+48]
    r1 = L01c30818
    r3 = r2
    call ring_stages_line_sums
L01c0a414:
    r0 = [sp+40]
    r9 = [sp+56]
    r9 = r9 + 16  #
    r0 = b[r0+0] (u)
    r13 = r13 + 1  #
    r4 = [sp+52]
    r4 = r4 + 16
    r10 = [sp+32]
    r11 = [sp+24]
    if (r13 < r0) goto L01c0a2e2
L01c0a42e:
    sp += 64
    {pc, r15-r4} = [sp++]

; ring_stages_split_lines: 0x01c0a432..0x01c0a57a, module ring-stages (split_lines)
.type ring_stages_split_lines,@function
ring_stages_split_lines:
    [--sp] = {rets, r15-r4}
    sp += -80
    r9_r8 = r3_r2  #
    r3 = [sp+144]
    r12 = r0
    r0 = sp + 76
    r15 = r1  #
    [sp+4] = r0
    r0 = 1024
    r0 = r12  #
    [sp] = r0
    r2 = r9
    call rate_leaves_read_rate
    r6 = [sp+156]
    r10 = [sp+152]
    r7 = [sp+148]
    r5 = [sp+140]
    r1 = [sp+136]
    r3 = [sp+76]
    r2 = [sp+132]
    if (r3 == 0) goto L01c0a48c
    r3 = 1
    [sp+16] = r3
    r0 = r12  #
    [sp+12] = r0
    [sp+8] = r5
    r1 = r15  #
    [sp+4] = r1
    r3_r2 = r9_r8  #
    [sp] = r2
    call ring_stages_ring_chunks
    r1 = r7  #
    [sp+8] = r6
    [sp+4] = r9
    r0 = 0
    r0 = r12  #
    [sp] = r0
    r2 = r10
    r3 = r8
    call ring_stages_all_pass_lines
    goto L01c0a576
L01c0a48c:
    r0 = r12 + 80
    r13 = [r0+r15<<2]
    r3 = r15 << 2
    r3 += r12
    r3 = r3 + 240
    [sp+32] = r3
    r11 = h[r3+2] (u)
    r3 = r7 << 2
    r3 += r12
    r14 = [++r3=160]
    [sp+28] = r3
    r4 = [r0+r7<<2]
    [sp+52] = r2
    [sp+56] = r1
    [sp+72] = r6
    r1 = [r5+0]
    [sp+60] = r1
    r2 = sp + 40
    if (r9 == 0) goto L01c0a566
    r0 = r4 - r10  #
    [sp+24] = r5
    r0 += r14  #
    [sp+36] = r7
    [sp+20] = r2
    r1 = r2 + 20
    r7 = 0
    r1 = 0
    if (r0 >= r4) {
    r1 = r4
    }
    r6 = r0 - r1
    r5 = sp + 40
L01c0a4de:
    r10 = r15
    r0 = [r12+r10<<2]
    r1 = r11 << 2
    r0 = r0 + r1
    r15 = r8  #
    [sp+40] = r0
    r0 = r7 << 2
    r0 += r8
    r0 = r13 - r11  #
    [r5+4] = r0
    r1 = r9 - r7
    r0 = umin(r1, r0)
    r1 = r4 - r6
    r0 = umin(r0, r1)
    r1 = r4 - r14
    r8 = umin(r0, r1)
    [r5+8] = r8
    r0 = [sp+36]
    r0 = [r12+r0<<2]
    r1 = r6 << 2
    r1 = r1 + r0
    r1 = r14 << 2  #
    [r5+24] = r1
    r0 = r0 + r1
    [r5+28] = r0
    r0 = sp + 40
    call filter_kernels_split_filter  ; @call.xl
    r1 = r8 + r14
    r0 = 0
    r14 = 0
    if (r1 != r4) {
    r14 = r1
    }
    r1 = r8 + r6
    r6 = 0
    if (r1 != r4) {
    r6 = r1
    }
    r1 = r8 + r11
    if (r1 != r13) {
    r0 = r1
    }
    r7 += r8
    r11 = r0
    r8 = r15
    r15 = r10
    if (r7 < r9) goto L01c0a4de
    r1 = [sp+20]
    r1 = [r1+20]
    r5 = [sp+24]
    goto L01c0a568
L01c0a566:
    r0 = r11
L01c0a568:
    r2 = [sp+32]
    r3 = [sp+28]
    [r5+0] = r1
    r0 = r0 << 16
    [r2+0] = r0
    [r3+0] = r14
L01c0a576:
    sp += 80
    {pc, r15-r4} = [sp++]

; ring_stages_ring_setup: 0x01c0a57a..0x01c0a774, module ring-stages (ring_setup)
.type ring_stages_ring_setup,@function
ring_stages_ring_setup:
    [--sp] = {rets, r15-r4}
    sp += -100
    r5 = r1  #
    r4 = b[r0+0] (u)
    r0 = r4  #
    [sp+48] = r3
    [sp+52] = r2
    call effect_model_construction_object_record
    r7 = r0  #
    [sp+40] = r4
    r6 = r5 + 632
    if (r4 != 31) goto L01c0a5b2
    r0 = [sp+52]
    if (r0 == 0) goto L01c0a5b2
    r0 = [r6+48]
    r1 = L01c30d74
    r2 = [sp+52]
L01c0a5a6:
    r3 = [r1+0]
    r4 = [r0++=4]
    r3 = r3 + r4
    [r1++=4] = r3
    if (--r2 != 0) goto L01c0a5a6
L01c0a5b2:
    r0 = h[r7+32] (u)
    if (r0 == 0) goto L01c0a5c8
    r2 = r7 + 32  #
    r1 = [sp+52]
    r3 = r7 + 40
    r0 = r5
    call ring_stages_diffusion_pass
L01c0a5c8:
    r0 = b[r6+1] (u)
    if (r0 == 0) goto L01c0a5ea
    r0 = L01c30818
    r1 = L01c31ea4
    r4 = [sp+52]
    r2 = r4
    call dsp_stage_copy  ; @call.xl
    r0 = r5
    r1 = r4
    call ring_stages_voice_lines
L01c0a5ea:
    r6 = r5 + 580  #
    [sp+32] = r6
    r1 = [r6+0]
    r0 = [r6+4]
    r2 = r0 - r1
    r3 = r2 + 4095
    r8 = 8191
    r4 = r5 + 504
    if (r3 >= r8) {
    r0 = 32
    r0 = r2 / r0 (s)
    r0 = r0 + r1
    }
    r14 = r7 + 16  #
    [sp+28] = r6
    r10 = 0  #
    [r6+0] = r0
    r12 = 440  #
    [sp+36] = r4
    r13 = r5 + 276  #
    r0 = [r4+0]
    r15 = 4  #
    [sp+44] = r0
    r6 = L01c30e84
    r4 = 0
    r11 = r7
L01c0a634:
    r0 = b[r7+57] (u)
    r9 = [r13+r4<<2]
    r0 = r0 & (1 << r4)
    if (r0 == 0) goto L01c0a662
    r3 = sp + 96
    r0 = r5  #
    r2 = [sp+52]
    r1 = r10
    call modulation_modulator
    r2 = [sp+96]
    r0 = [sp+48]
    if (r0 == 0) goto L01c0a65c
    r0 = r5
    r1 = r4
    call rate_leaves_wrap_position
L01c0a65c:
    r9 += r2
    r10 = r10 + 1
L01c0a662:
    r0 = r4 << 2
    r0 = r0 + r5
    r3 = r0 + 312
    r1 = [r3+0]
    r2 = [r0+376]
    r2 = r2 - r1
    r2 = r2 / r15 (s)
    r1 = r1 + r2
    [r3+0] = r1
    r1 = [r3+32]
    r0 = [r0+408]
    r0 = r0 - r1
    r0 = r0 / r15 (s)
    r0 = r0 + r1
    [r3+32] = r0
    r0 = r4 << 1
    r0 = r0 + r5
    r8 = r0 + 472
    r1 = h[r8+16] (u)
    r0 = h[r8+0] (u)
    call rate_leaves_step_toward
    h[r8+0] = r0
    r7 = h[r14+r4<<1] (u)
    r1 = [r3+0]
    r3 = r5 + r12  #
    r2 = [r3+32]
    if (r7 == 0) goto L01c0a6d0
    r7 = [sp+44]
    [sp+24] = r7
    [sp+20] = r0
    r0 = r4 + 12
    r0 = r5  #
    [sp+16] = r0
    [sp+12] = r9
    [sp+4] = r2
    [sp+8] = r3
    r1 = r4  #
    [sp] = r1
    r2 = r6  #
    r3 = [sp+52]
    call ring_stages_split_lines
    goto L01c0a6ea
L01c0a6d0:
    r0 = 1024
    r0 = r5  #
    [sp+16] = r0
    [sp+12] = r9
    [sp+4] = r2
    [sp+8] = r3
    r1 = r4  #
    [sp] = r1
    r2 = r6  #
    r3 = [sp+52]
    call ring_stages_ring_read
L01c0a6ea:
    r7 = r11
    r12 = r12 + 4
    r4 = r4 + 1
    r6 = r6 + 256
    if (r4 != 8) goto L01c0a634
    r4 = [sp+36]
    r0 = [r4+0]
    r1 = [r4+4]
    call rate_leaves_approach
    [r4+0] = r0
    r0 = [sp+40]
    if (r0 != 31) goto L01c0a770
    r5 = r5 + 696
    r0 = [r5+0]
    r1 = [r5+4]
    call rate_leaves_approach
    r4 = r0
    [r5+0] = r4
    r0 = [r5+12]
    r1 = [r5+16]
    call rate_leaves_approach
    [r5+12] = r0
    r1 = L01c30e84
    [sp+56] = r1
    r6 = [sp+32]
    r1 = [r6+44]
    [sp+60] = r1
    r1 = [r6+48]
    [sp+64] = r1
    r1 = [sp+52]
    [sp+68] = r1
    r1 = [r6+52]
    [sp+72] = r1
    r1 = [r6+56]
    [sp+76] = r1
    r1 = [r6+60]
    [sp+80] = r1
    r1 = [sp+28]
    r1 = [r1+8]
    r3_r2 = r4 * r1 (s)
    r3_r2 >>= 16
    [sp+84] = r2
    r1 = [r5+8]
    [sp+88] = r1
    [sp+92] = r0
    r0 = sp + 56
    call resampling_kernels_pitch_shift  ; @call.xl
    r0 = [sp+72]
    [r6+52] = r0
    r0 = [sp+76]
    [r6+56] = r0
    r0 = [sp+88]
    [r5+8] = r0
L01c0a770:
    sp += 100
    {pc, r15-r4} = [sp++]
