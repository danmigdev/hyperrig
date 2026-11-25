; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_processing: 12 functions, 0x01c145fe..0x01c15dec

; ir_processing_input: 0x01c145fe..0x01c1477e, module ir-processing (input)
.type ir_processing_input,@function
ir_processing_input:
    [--sp] = {rets, r15-r4}
    r10 = r0
    r12 = r1
    r11 = r2
    r14 = r3
    r13 = r3 + 1024
    r15 = 16
L01c14610:
    r0 = [r11+0]
    r1 = [r11+4]
    r2 = [r11+256]
    r3 = [r11+260]
    r4 = [r10+0]
    r5 = [r10+4]
    r6 = [r10+256]
    r7 = [r10+260]
    r4 = r4 >>> 2
    r5 = r5 >>> 2
    r6 = r6 >>> 2
    r7 = r7 >>> 2
    r8 = 33554431
    r9 = 0x0 - r8
    r4 = smin(r4, r8)
    r4 = smax(r4, r9)
    r5 = smin(r5, r8)
    r5 = smax(r5, r9)
    r6 = smin(r6, r8)
    r6 = smax(r6, r9)
    r7 = smin(r7, r8)
    r7 = smax(r7, r9)
    [r12+0] = r4
    [r12+4] = r5
    [r12+256] = r6
    [r12+260] = r7
    r8 = r0 + r4
    r0 = r0 - r4
    r9 = r1 + r5
    r1 = r1 - r5
    r4 = r2 + r6
    r2 = r2 - r6
    r5 = r3 + r7
    r3 = r3 - r7
    r6 = [r13++=4]
    r6 += r14
    r7 = r8 + r4
    [r6+0] = r7
    r7 = r9 + r5
    [r6+4] = r7
    r8 = r8 - r4
    [r6+16] = r8
    r9 = r9 - r5
    [r6+20] = r9
    r4 = r0 + r3
    r5 = r1 - r2
    [r6+8] = r4
    [r6+12] = r5
    r0 = r0 - r3
    r1 = r1 + r2
    [r6+24] = r0
    [r6+28] = r1
    r10 = r10 + 8
    r11 = r11 + 8
    r12 = r12 + 8
    r0 = [r11+0]
    r1 = [r11+4]
    r2 = [r11+256]
    r3 = [r11+260]
    r4 = [r10+0]
    r5 = [r10+4]
    r6 = [r10+256]
    r7 = [r10+260]
    r4 = r4 >>> 2
    r5 = r5 >>> 2
    r6 = r6 >>> 2
    r7 = r7 >>> 2
    r8 = 33554431
    r9 = 0x0 - r8
    r4 = smin(r4, r8)
    r4 = smax(r4, r9)
    r5 = smin(r5, r8)
    r5 = smax(r5, r9)
    r6 = smin(r6, r8)
    r6 = smax(r6, r9)
    r7 = smin(r7, r8)
    r7 = smax(r7, r9)
    [r12+0] = r4
    [r12+4] = r5
    [r12+256] = r6
    [r12+260] = r7
    r8 = r0 + r4
    r0 = r0 - r4
    r9 = r1 + r5
    r1 = r1 - r5
    r4 = r2 + r6
    r2 = r2 - r6
    r5 = r3 + r7
    r3 = r3 - r7
    r6 = [r13++=4]
    r6 += r14
    r7 = r8 + r4
    [r6+0] = r7
    r7 = r9 + r5
    [r6+4] = r7
    r8 = r8 - r4
    [r6+16] = r8
    r9 = r9 - r5
    [r6+20] = r9
    r4 = r0 + r3
    r5 = r1 - r2
    [r6+8] = r4
    [r6+12] = r5
    r0 = r0 - r3
    r1 = r1 + r2
    [r6+24] = r0
    [r6+28] = r1
    r10 = r10 + 8
    r11 = r11 + 8
    r12 = r12 + 8
    if (--r15 != 0) goto L01c14610
    {pc, r15-r4} = [sp++]

; ir_processing_fft64: 0x01c1477e..0x01c1508c, module ir-processing (fft64)
.type ir_processing_fft64,@function
ir_processing_fft64:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1 >> 1
    r14 = r14 << 1
    r2 = r1 << 31
    if (r2 != 0) goto L01c14882
    r15 = 8
L01c14792:
    r0 = [r13+0]
    r1 = [r13+4]
    r2 = [r13+8]
    r3 = [r13+12]
    r4 = [r13+16]
    r5 = [r13+20]
    r6 = [r13+24]
    r7 = [r13+28]
    r8 = r0 + r4
    r9 = r1 + r5
    r0 = r0 - r4
    r1 = r1 - r5
    r10 = r2 + r6
    r11 = r3 + r7
    r2 = r2 - r6
    r3 = r3 - r7
    r4 = r8 + r10
    r5 = r9 + r11
    [r13+0] = r4
    [r13+4] = r5
    r4 = r8 - r10
    r5 = r9 - r11
    [r13+16] = r4
    [r13+20] = r5
    r4 = r0 + r3
    r5 = r1 - r2
    [r13+8] = r4
    [r13+12] = r5
    r4 = r0 - r3
    r5 = r1 + r2
    [r13+24] = r4
    [r13+28] = r5
    r13 = r13 + 32
    r0 = [r13+0]
    r1 = [r13+4]
    r2 = [r13+8]
    r3 = [r13+12]
    r4 = [r13+16]
    r5 = [r13+20]
    r6 = [r13+24]
    r7 = [r13+28]
    r8 = r0 + r4
    r9 = r1 + r5
    r0 = r0 - r4
    r1 = r1 - r5
    r10 = r2 + r6
    r11 = r3 + r7
    r2 = r2 - r6
    r3 = r3 - r7
    r4 = r8 + r10
    r5 = r9 + r11
    [r13+0] = r4
    [r13+4] = r5
    r4 = r8 - r10
    r5 = r9 - r11
    [r13+16] = r4
    [r13+20] = r5
    r4 = r0 + r3
    r5 = r1 - r2
    [r13+8] = r4
    [r13+12] = r5
    r4 = r0 - r3
    r5 = r1 + r2
    [r13+24] = r4
    [r13+28] = r5
    r13 = r13 + 32
    if (--r15 != 0) goto L01c14792
    r13 = r13 + -512
L01c14882:
    r4 = [r13+0]
    r5 = [r13+4]
    r6 = [r13+32]
    r7 = [r13+36]
    r8 = [r13+64]
    r9 = [r13+68]
    r10 = [r13+96]
    r11 = [r13+100]
    r4 = r4 >>> 1
    r5 = r5 >>> 1
    r6 = r6 >>> 1
    r7 = r7 >>> 1
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r10 = r10 >>> 1
    r11 = r11 >>> 1
    r0 = r4 + r8
    r1 = r5 + r9
    r4 = r4 - r8
    r5 = r5 - r9
    r2 = r6 + r10
    r3 = r7 + r11
    r6 = r6 - r10
    r7 = r7 - r11
    r8 = r0 + r2
    r9 = r1 + r3
    [r13+0] = r8
    [r13+4] = r9
    r0 = r0 - r2
    r1 = r1 - r3
    [r13+64] = r0
    [r13+68] = r1
    r2 = r4 + r7
    r3 = r5 - r6
    [r13+32] = r2
    [r13+36] = r3
    r4 = r4 - r7
    r5 = r5 + r6
    [r13+96] = r4
    [r13+100] = r5
    r4 = [r13+128]
    r5 = [r13+132]
    r6 = [r13+160]
    r7 = [r13+164]
    r8 = [r13+192]
    r9 = [r13+196]
    r10 = [r13+224]
    r11 = [r13+228]
    r4 = r4 >>> 1
    r5 = r5 >>> 1
    r6 = r6 >>> 1
    r7 = r7 >>> 1
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r10 = r10 >>> 1
    r11 = r11 >>> 1
    r0 = r4 + r8
    r1 = r5 + r9
    r4 = r4 - r8
    r5 = r5 - r9
    r2 = r6 + r10
    r3 = r7 + r11
    r6 = r6 - r10
    r7 = r7 - r11
    r8 = r0 + r2
    r9 = r1 + r3
    [r13+128] = r8
    [r13+132] = r9
    r0 = r0 - r2
    r1 = r1 - r3
    [r13+192] = r0
    [r13+196] = r1
    r2 = r4 + r7
    r3 = r5 - r6
    [r13+160] = r2
    [r13+164] = r3
    r4 = r4 - r7
    r5 = r5 + r6
    [r13+224] = r4
    [r13+228] = r5
    r4 = [r13+256]
    r5 = [r13+260]
    r6 = [r13+288]
    r7 = [r13+292]
    r8 = [r13+320]
    r9 = [r13+324]
    r10 = [r13+352]
    r11 = [r13+356]
    r4 = r4 >>> 1
    r5 = r5 >>> 1
    r6 = r6 >>> 1
    r7 = r7 >>> 1
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r10 = r10 >>> 1
    r11 = r11 >>> 1
    r0 = r4 + r8
    r1 = r5 + r9
    r4 = r4 - r8
    r5 = r5 - r9
    r2 = r6 + r10
    r3 = r7 + r11
    r6 = r6 - r10
    r7 = r7 - r11
    r8 = r0 + r2
    r9 = r1 + r3
    [r13+256] = r8
    [r13+260] = r9
    r0 = r0 - r2
    r1 = r1 - r3
    [r13+320] = r0
    [r13+324] = r1
    r2 = r4 + r7
    r3 = r5 - r6
    [r13+288] = r2
    [r13+292] = r3
    r4 = r4 - r7
    r5 = r5 + r6
    [r13+352] = r4
    [r13+356] = r5
    r4 = [r13+384]
    r5 = [r13+388]
    r6 = [r13+416]
    r7 = [r13+420]
    r8 = [r13+448]
    r9 = [r13+452]
    r10 = [r13+480]
    r11 = [r13+484]
    r4 = r4 >>> 1
    r5 = r5 >>> 1
    r6 = r6 >>> 1
    r7 = r7 >>> 1
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r10 = r10 >>> 1
    r11 = r11 >>> 1
    r0 = r4 + r8
    r1 = r5 + r9
    r4 = r4 - r8
    r5 = r5 - r9
    r2 = r6 + r10
    r3 = r7 + r11
    r6 = r6 - r10
    r7 = r7 - r11
    r8 = r0 + r2
    r9 = r1 + r3
    [r13+384] = r8
    [r13+388] = r9
    r0 = r0 - r2
    r1 = r1 - r3
    [r13+448] = r0
    [r13+452] = r1
    r2 = r4 + r7
    r3 = r5 - r6
    [r13+416] = r2
    [r13+420] = r3
    r4 = r4 - r7
    r5 = r5 + r6
    [r13+480] = r4
    [r13+484] = r5
    r13 = r13 + 8
    r14 = r14 + 24
    r15 = 3
L01c14abe:
    r4 = [r13+64]
    r5 = [r13+68]
    r6 = [r14+8]
    r7 = [r14+12]
    r9_r8 = r4 * r6 (s)
    r9_r8 -= r5 * r7 (s)
    r11_r10 = r4 * r7 (s)
    r11_r10 += r5 * r6 (s)
    r4 = [r13+32]
    r5 = [r13+36]
    r6 = [r14+0]
    r7 = [r14+4]
    r1_r0 = r4 * r6 (s)
    r1_r0 -= r5 * r7 (s)
    r3_r2 = r4 * r7 (s)
    r3_r2 += r5 * r6 (s)
    r0 = [r13+96]
    r2 = [r13+100]
    r8 = [r14+16]
    r10 = [r14+20]
    r5_r4 = r0 * r8 (s)
    r5_r4 -= r2 * r10 (s)
    r7_r6 = r0 * r10 (s)
    r7_r6 += r2 * r8 (s)
    r0 = r1 + r5
    r2 = r3 + r7
    r1 = r1 - r5
    r3 = r3 - r7
    r4 = [r13+0]
    r6 = [r13+4]
    r4 = r4 >>> 1
    r6 = r6 >>> 1
    r5 = r4 + r9
    r7 = r6 + r11
    r4 = r4 - r9
    r6 = r6 - r11
    r8 = r5 + r0
    r10 = r7 + r2
    [r13+0] = r8
    [r13+4] = r10
    r5 = r5 - r0
    r7 = r7 - r2
    [r13+64] = r5
    [r13+68] = r7
    r0 = r4 + r3
    r2 = r6 - r1
    [r13+32] = r0
    [r13+36] = r2
    r4 = r4 - r3
    r6 = r6 + r1
    [r13+96] = r4
    [r13+100] = r6
    r4 = [r13+192]
    r5 = [r13+196]
    r6 = [r14+8]
    r7 = [r14+12]
    r9_r8 = r4 * r6 (s)
    r9_r8 -= r5 * r7 (s)
    r11_r10 = r4 * r7 (s)
    r11_r10 += r5 * r6 (s)
    r4 = [r13+160]
    r5 = [r13+164]
    r6 = [r14+0]
    r7 = [r14+4]
    r1_r0 = r4 * r6 (s)
    r1_r0 -= r5 * r7 (s)
    r3_r2 = r4 * r7 (s)
    r3_r2 += r5 * r6 (s)
    r0 = [r13+224]
    r2 = [r13+228]
    r8 = [r14+16]
    r10 = [r14+20]
    r5_r4 = r0 * r8 (s)
    r5_r4 -= r2 * r10 (s)
    r7_r6 = r0 * r10 (s)
    r7_r6 += r2 * r8 (s)
    r0 = r1 + r5
    r2 = r3 + r7
    r1 = r1 - r5
    r3 = r3 - r7
    r4 = [r13+128]
    r6 = [r13+132]
    r4 = r4 >>> 1
    r6 = r6 >>> 1
    r5 = r4 + r9
    r7 = r6 + r11
    r4 = r4 - r9
    r6 = r6 - r11
    r8 = r5 + r0
    r10 = r7 + r2
    [r13+128] = r8
    [r13+132] = r10
    r5 = r5 - r0
    r7 = r7 - r2
    [r13+192] = r5
    [r13+196] = r7
    r0 = r4 + r3
    r2 = r6 - r1
    [r13+160] = r0
    [r13+164] = r2
    r4 = r4 - r3
    r6 = r6 + r1
    [r13+224] = r4
    [r13+228] = r6
    r4 = [r13+320]
    r5 = [r13+324]
    r6 = [r14+8]
    r7 = [r14+12]
    r9_r8 = r4 * r6 (s)
    r9_r8 -= r5 * r7 (s)
    r11_r10 = r4 * r7 (s)
    r11_r10 += r5 * r6 (s)
    r4 = [r13+288]
    r5 = [r13+292]
    r6 = [r14+0]
    r7 = [r14+4]
    r1_r0 = r4 * r6 (s)
    r1_r0 -= r5 * r7 (s)
    r3_r2 = r4 * r7 (s)
    r3_r2 += r5 * r6 (s)
    r0 = [r13+352]
    r2 = [r13+356]
    r8 = [r14+16]
    r10 = [r14+20]
    r5_r4 = r0 * r8 (s)
    r5_r4 -= r2 * r10 (s)
    r7_r6 = r0 * r10 (s)
    r7_r6 += r2 * r8 (s)
    r0 = r1 + r5
    r2 = r3 + r7
    r1 = r1 - r5
    r3 = r3 - r7
    r4 = [r13+256]
    r6 = [r13+260]
    r4 = r4 >>> 1
    r6 = r6 >>> 1
    r5 = r4 + r9
    r7 = r6 + r11
    r4 = r4 - r9
    r6 = r6 - r11
    r8 = r5 + r0
    r10 = r7 + r2
    [r13+256] = r8
    [r13+260] = r10
    r5 = r5 - r0
    r7 = r7 - r2
    [r13+320] = r5
    [r13+324] = r7
    r0 = r4 + r3
    r2 = r6 - r1
    [r13+288] = r0
    [r13+292] = r2
    r4 = r4 - r3
    r6 = r6 + r1
    [r13+352] = r4
    [r13+356] = r6
    r4 = [r13+448]
    r5 = [r13+452]
    r6 = [r14+8]
    r7 = [r14+12]
    r9_r8 = r4 * r6 (s)
    r9_r8 -= r5 * r7 (s)
    r11_r10 = r4 * r7 (s)
    r11_r10 += r5 * r6 (s)
    r4 = [r13+416]
    r5 = [r13+420]
    r6 = [r14+0]
    r7 = [r14+4]
    r1_r0 = r4 * r6 (s)
    r1_r0 -= r5 * r7 (s)
    r3_r2 = r4 * r7 (s)
    r3_r2 += r5 * r6 (s)
    r0 = [r13+480]
    r2 = [r13+484]
    r8 = [r14+16]
    r10 = [r14+20]
    r5_r4 = r0 * r8 (s)
    r5_r4 -= r2 * r10 (s)
    r7_r6 = r0 * r10 (s)
    r7_r6 += r2 * r8 (s)
    r0 = r1 + r5
    r2 = r3 + r7
    r1 = r1 - r5
    r3 = r3 - r7
    r4 = [r13+384]
    r6 = [r13+388]
    r4 = r4 >>> 1
    r6 = r6 >>> 1
    r5 = r4 + r9
    r7 = r6 + r11
    r4 = r4 - r9
    r6 = r6 - r11
    r8 = r5 + r0
    r10 = r7 + r2
    [r13+384] = r8
    [r13+388] = r10
    r5 = r5 - r0
    r7 = r7 - r2
    [r13+448] = r5
    [r13+452] = r7
    r0 = r4 + r3
    r2 = r6 - r1
    [r13+416] = r0
    [r13+420] = r2
    r4 = r4 - r3
    r6 = r6 + r1
    [r13+480] = r4
    [r13+484] = r6
    r13 = r13 + 8
    r14 = r14 + 24
    if (--r15 != 0) goto L01c14abe
    r13 = r13 + -32
    r4 = [r13+0]
    r5 = [r13+4]
    r6 = [r13+128]
    r7 = [r13+132]
    r8 = [r13+256]
    r9 = [r13+260]
    r10 = [r13+384]
    r11 = [r13+388]
    r4 = r4 >>> 1
    r5 = r5 >>> 1
    r6 = r6 >>> 1
    r7 = r7 >>> 1
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r10 = r10 >>> 1
    r11 = r11 >>> 1
    r0 = r4 + r8
    r1 = r5 + r9
    r4 = r4 - r8
    r5 = r5 - r9
    r2 = r6 + r10
    r3 = r7 + r11
    r6 = r6 - r10
    r7 = r7 - r11
    r8 = r0 + r2
    r9 = r1 + r3
    [r13+0] = r8
    [r13+4] = r9
    r0 = r0 - r2
    r1 = r1 - r3
    [r13+256] = r0
    [r13+260] = r1
    r2 = r4 + r7
    r3 = r5 - r6
    [r13+128] = r2
    [r13+132] = r3
    r4 = r4 - r7
    r5 = r5 + r6
    [r13+384] = r4
    [r13+388] = r5
    r13 = r13 + 8
    r14 = r14 + 24
    r15 = 5
L01c14e46:
    r4 = [r13+256]
    r5 = [r13+260]
    r6 = [r14+8]
    r7 = [r14+12]
    r9_r8 = r4 * r6 (s)
    r9_r8 -= r5 * r7 (s)
    r11_r10 = r4 * r7 (s)
    r11_r10 += r5 * r6 (s)
    r4 = [r13+128]
    r5 = [r13+132]
    r6 = [r14+0]
    r7 = [r14+4]
    r1_r0 = r4 * r6 (s)
    r1_r0 -= r5 * r7 (s)
    r3_r2 = r4 * r7 (s)
    r3_r2 += r5 * r6 (s)
    r0 = [r13+384]
    r2 = [r13+388]
    r8 = [r14+16]
    r10 = [r14+20]
    r5_r4 = r0 * r8 (s)
    r5_r4 -= r2 * r10 (s)
    r7_r6 = r0 * r10 (s)
    r7_r6 += r2 * r8 (s)
    r0 = r1 + r5
    r2 = r3 + r7
    r1 = r1 - r5
    r3 = r3 - r7
    r4 = [r13+0]
    r6 = [r13+4]
    r4 = r4 >>> 1
    r6 = r6 >>> 1
    r5 = r4 + r9
    r7 = r6 + r11
    r4 = r4 - r9
    r6 = r6 - r11
    r8 = r5 + r0
    r10 = r7 + r2
    [r13+0] = r8
    [r13+4] = r10
    r5 = r5 - r0
    r7 = r7 - r2
    [r13+256] = r5
    [r13+260] = r7
    r0 = r4 + r3
    r2 = r6 - r1
    [r13+128] = r0
    [r13+132] = r2
    r4 = r4 - r3
    r6 = r6 + r1
    [r13+384] = r4
    [r13+388] = r6
    r13 = r13 + 8
    r14 = r14 + 24
    r4 = [r13+256]
    r5 = [r13+260]
    r6 = [r14+8]
    r7 = [r14+12]
    r9_r8 = r4 * r6 (s)
    r9_r8 -= r5 * r7 (s)
    r11_r10 = r4 * r7 (s)
    r11_r10 += r5 * r6 (s)
    r4 = [r13+128]
    r5 = [r13+132]
    r6 = [r14+0]
    r7 = [r14+4]
    r1_r0 = r4 * r6 (s)
    r1_r0 -= r5 * r7 (s)
    r3_r2 = r4 * r7 (s)
    r3_r2 += r5 * r6 (s)
    r0 = [r13+384]
    r2 = [r13+388]
    r8 = [r14+16]
    r10 = [r14+20]
    r5_r4 = r0 * r8 (s)
    r5_r4 -= r2 * r10 (s)
    r7_r6 = r0 * r10 (s)
    r7_r6 += r2 * r8 (s)
    r0 = r1 + r5
    r2 = r3 + r7
    r1 = r1 - r5
    r3 = r3 - r7
    r4 = [r13+0]
    r6 = [r13+4]
    r4 = r4 >>> 1
    r6 = r6 >>> 1
    r5 = r4 + r9
    r7 = r6 + r11
    r4 = r4 - r9
    r6 = r6 - r11
    r8 = r5 + r0
    r10 = r7 + r2
    [r13+0] = r8
    [r13+4] = r10
    r5 = r5 - r0
    r7 = r7 - r2
    [r13+256] = r5
    [r13+260] = r7
    r0 = r4 + r3
    r2 = r6 - r1
    [r13+128] = r0
    [r13+132] = r2
    r4 = r4 - r3
    r6 = r6 + r1
    [r13+384] = r4
    [r13+388] = r6
    r13 = r13 + 8
    r14 = r14 + 24
    r4 = [r13+256]
    r5 = [r13+260]
    r6 = [r14+8]
    r7 = [r14+12]
    r9_r8 = r4 * r6 (s)
    r9_r8 -= r5 * r7 (s)
    r11_r10 = r4 * r7 (s)
    r11_r10 += r5 * r6 (s)
    r4 = [r13+128]
    r5 = [r13+132]
    r6 = [r14+0]
    r7 = [r14+4]
    r1_r0 = r4 * r6 (s)
    r1_r0 -= r5 * r7 (s)
    r3_r2 = r4 * r7 (s)
    r3_r2 += r5 * r6 (s)
    r0 = [r13+384]
    r2 = [r13+388]
    r8 = [r14+16]
    r10 = [r14+20]
    r5_r4 = r0 * r8 (s)
    r5_r4 -= r2 * r10 (s)
    r7_r6 = r0 * r10 (s)
    r7_r6 += r2 * r8 (s)
    r0 = r1 + r5
    r2 = r3 + r7
    r1 = r1 - r5
    r3 = r3 - r7
    r4 = [r13+0]
    r6 = [r13+4]
    r4 = r4 >>> 1
    r6 = r6 >>> 1
    r5 = r4 + r9
    r7 = r6 + r11
    r4 = r4 - r9
    r6 = r6 - r11
    r8 = r5 + r0
    r10 = r7 + r2
    [r13+0] = r8
    [r13+4] = r10
    r5 = r5 - r0
    r7 = r7 - r2
    [r13+256] = r5
    [r13+260] = r7
    r0 = r4 + r3
    r2 = r6 - r1
    [r13+128] = r0
    [r13+132] = r2
    r4 = r4 - r3
    r6 = r6 + r1
    [r13+384] = r4
    [r13+388] = r6
    r13 = r13 + 8
    r14 = r14 + 24
    if (--r15 != 0) goto L01c14e46
    {pc, r15-r4} = [sp++]

; ir_processing_merge: 0x01c1508c..0x01c15148, module ir-processing (merge)
.type ir_processing_merge,@function
ir_processing_merge:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r0 + 512
    r6 = r1
    r15 = 32
L01c1509a:
    r8 = [r5+0]
    r9 = [r5+4]
    r10 = [r6++=4]
    r11 = [r6++=4]
    r1_r0 = r8 * r10 (s)
    r1_r0 -= r9 * r11 (s)
    r3_r2 = r8 * r11 (s)
    r3_r2 += r9 * r10 (s)
    r8 = [r4+0]
    r9 = [r4+4]
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r10 = r8 + r1
    r11 = r9 + r3
    r8 = r8 - r1
    r9 = r9 - r3
    [r4+0] = r10
    [r4+4] = r11
    [r5+0] = r8
    [r5+4] = r9
    r4 = r4 + 8
    r5 = r5 + 8
    r8 = [r5+0]
    r9 = [r5+4]
    r10 = [r6++=4]
    r11 = [r6++=4]
    r1_r0 = r8 * r10 (s)
    r1_r0 -= r9 * r11 (s)
    r3_r2 = r8 * r11 (s)
    r3_r2 += r9 * r10 (s)
    r8 = [r4+0]
    r9 = [r4+4]
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r10 = r8 + r1
    r11 = r9 + r3
    r8 = r8 - r1
    r9 = r9 - r3
    [r4+0] = r10
    [r4+4] = r11
    [r5+0] = r8
    [r5+4] = r9
    r4 = r4 + 8
    r5 = r5 + 8
    if (--r15 != 0) goto L01c1509a
    {pc, r15-r4} = [sp++]

; ir_processing_forward: 0x01c15148..0x01c1533e, module ir-processing (forward)
.type ir_processing_forward,@function
ir_processing_forward:
    [--sp] = {rets, r15-r4}
    sp += -4
    r4 = r3 << 3
    [sp] = r4
    r12 = r2
    r8 = r1
    r13 = r0
    r2 = [r13+0]
    r3 = [r13+4]
    r3 = r3 + r3
    r9 = r12 + 0
    r4 = [r9+0]
    r5 = [r9+4]
    r1_r0 = r3 * r4 (s)
    r11_r10 = r3 * r5 (s)
    r2 = r2 + r1
    r6 = r8
    [r6+0] = r2
    [r6+4] = r11
    r2 = [r13+512]
    r3 = [r13+516]
    r3 = r3 + r3
    r9 = r12 + 512
    r4 = [r9+0]
    r5 = [r9+4]
    r1_r0 = r3 * r4 (s)
    r11_r10 = r3 * r5 (s)
    r2 = r2 + r1
    r6 = [sp]
    r6 = r6 << 6
    r6 += r8
    [r6+0] = r2
    [r6+4] = r11
    r2 = [r13+0]
    r3 = [r13+4]
    r3 = r3 + r3
    r9 = r12 + 1024
    r4 = [r9+0]
    r5 = [r9+4]
    r1_r0 = r3 * r4 (s)
    r11_r10 = r3 * r5 (s)
    r2 = r2 + r1
    r6 = [sp]
    r6 = r6 << 7
    r6 += r8
    [r6+0] = r2
    [r6+4] = r11
    r14 = r13 + 1016
    r13 = r13 + 8
    r6 = r12 + 8
    r4 = [sp]
    r7 = r8 + r4
    r4 = r4 << 7
    r10 = r8 + r4
    r5 = [sp]
    r10 = r10 - r5
    r15 = 31
    r2 = [r13+0]
    r3 = [r13+4]
    r4 = [r14+0]
    r5 = [r14+4]
    r11 = [r6+0]
    r12 = [r6+4]
    r6 = r6 + 8
    r1 = r3 + r5
    r0 = r4 - r2
    r8 = r2 + r4
    r8 = r8 >>> 1
    r9 = r3 - r5
    r9 = r9 >>> 1
    r3_r2 = r1 * r11 (s)
    r3_r2 -= r0 * r12 (s)
    r5_r4 = r1 * r12 (s)
    r5_r4 += r0 * r11 (s)
    r0 = r8 + r3
    r8 = r8 - r3
    r1 = r9 + r5
    r9 = r5 - r9
    [r7+0] = r0
    [r7+4] = r1
    [r10+0] = r8
    [r10+4] = r9
    r4 = [sp]
    r7 = r7 + r4
    r10 = r10 - r4
    r13 = r13 + 8
    r14 = r14 + -8
L01c15262:
    r2 = [r13+0]
    r3 = [r13+4]
    r4 = [r14+0]
    r5 = [r14+4]
    r11 = [r6+0]
    r12 = [r6+4]
    r6 = r6 + 8
    r1 = r3 + r5
    r0 = r4 - r2
    r8 = r2 + r4
    r8 = r8 >>> 1
    r9 = r3 - r5
    r9 = r9 >>> 1
    r3_r2 = r1 * r11 (s)
    r3_r2 -= r0 * r12 (s)
    r5_r4 = r1 * r12 (s)
    r5_r4 += r0 * r11 (s)
    r0 = r8 + r3
    r8 = r8 - r3
    r1 = r9 + r5
    r9 = r5 - r9
    [r7+0] = r0
    [r7+4] = r1
    [r10+0] = r8
    [r10+4] = r9
    r4 = [sp]
    r7 = r7 + r4
    r10 = r10 - r4
    r13 = r13 + 8
    r14 = r14 + -8
    r2 = [r13+0]
    r3 = [r13+4]
    r4 = [r14+0]
    r5 = [r14+4]
    r11 = [r6+0]
    r12 = [r6+4]
    r6 = r6 + 8
    r1 = r3 + r5
    r0 = r4 - r2
    r8 = r2 + r4
    r8 = r8 >>> 1
    r9 = r3 - r5
    r9 = r9 >>> 1
    r3_r2 = r1 * r11 (s)
    r3_r2 -= r0 * r12 (s)
    r5_r4 = r1 * r12 (s)
    r5_r4 += r0 * r11 (s)
    r0 = r8 + r3
    r8 = r8 - r3
    r1 = r9 + r5
    r9 = r5 - r9
    [r7+0] = r0
    [r7+4] = r1
    [r10+0] = r8
    [r10+4] = r9
    r4 = [sp]
    r7 = r7 + r4
    r10 = r10 - r4
    r13 = r13 + 8
    r14 = r14 + -8
    if (--r15 != 0) goto L01c15262
    sp += 4
    {pc, r15-r4} = [sp++]

; ir_processing_multiply: 0x01c1533e..0x01c154a4, module ir-processing (multiply)
.type ir_processing_multiply,@function
ir_processing_multiply:
    [--sp] = {rets, r15-r4}
    sp += -4
    r11 = r2 >> 16
    r12 = r2 << 16
    r12 = r12 >> 16
    r4 = r12 - r11
    [sp] = r4
    r12 = r12 << 3
    r5 = r1
    r13 = r3
    r10 = 129
    r14 = 0
    r4 = r11 << 3
    r4 = r0 + r4
    r0 = [r4++=4]
    r1 = [r4++=4]
    r2 = [r5++=4]
    r3 = [r5++=4]
    if (r11 != 0) goto L01c153ca
L01c15374:
    r6 = 0
    r7 = 0
    r8 = 0
    r9 = 0
    r15 = [sp]
L01c1537e:
    rep r15 {
    r7_r6 += r0 * r2 (s)
    r9_r8 += r1 * r2 (s)
    r7_r6 -= r1 * r3 (s)
    r9_r8 += r0 * r3 (s)
    r0 = [r4++=4]
    r1 = [r4++=4]
    r2 = [r5++=4]
    r3 = [r5++=4]
    }
    if (r15 != 0) goto L01c1537e
    [r13++=4] = r6
    [r13++=4] = r7
    [r13++=4] = r8
    [r13++=4] = r9
    r15 = r7 >>> 31
    r11 = r7 ^ r15
    r14 = r14 | r11
    r15 = r9 >>> 31
    r11 = r9 ^ r15
    r14 = r14 | r11
    if (--r10 != 0) goto L01c15374
    goto L01c1544a
L01c153ca:
    r6 = 0
    r7 = 0
    r8 = 0
    r9 = 0
    r15 = [sp]
L01c153d4:
    rep r15 {
    r7_r6 += r0 * r2 (s)
    r9_r8 += r1 * r2 (s)
    r7_r6 -= r1 * r3 (s)
    r9_r8 += r0 * r3 (s)
    r0 = [r4++=4]
    r1 = [r4++=4]
    r2 = [r5++=4]
    r3 = [r5++=4]
    }
    if (r15 != 0) goto L01c153d4
    r4 = r4 - r12
    r0 = [r4+-8]
    r1 = [r4+-4]
    r15 = r11
L01c153fc:
    rep r15 {
    r7_r6 += r0 * r2 (s)
    r9_r8 += r1 * r2 (s)
    r7_r6 -= r1 * r3 (s)
    r9_r8 += r0 * r3 (s)
    r0 = [r4++=4]
    r1 = [r4++=4]
    r2 = [r5++=4]
    r3 = [r5++=4]
    }
    if (r15 != 0) goto L01c153fc
    [r13++=4] = r6
    [r13++=4] = r7
    [r13++=4] = r8
    [r13++=4] = r9
    r0 = r7 >>> 31
    r1 = r7 ^ r0
    r14 = r14 | r1
    r0 = r9 >>> 31
    r1 = r9 ^ r0
    r14 = r14 | r1
    r4 += r12
    r0 = [r4+-8]
    r1 = [r4+-4]
    if (--r10 != 0) goto L01c153ca
L01c1544a:
    r12 = 0
    if (r14 != 0) goto L01c15484
    r13 = r13 + -2064
    r15 = 129
L01c15458:
    rep r15 {
    r0 = [r13++=4]
    r1 = [r13++=4]
    r0 ^= r1
    r12 = r12 | r0
    }
    if (r15 != 0) goto L01c15458
    r15 = 129
L01c15470:
    rep r15 {
    r0 = [r13++=4]
    r1 = [r13++=4]
    r0 ^= r1
    r12 = r12 | r0
    }
    if (r15 != 0) goto L01c15470
L01c15484:
    r0 = r12
    r1 = r14
    r2 = 0
    r3 = 33554431
L01c15490:
    if (r1 != 0) goto L01c15496
    if (r0 <= r3) goto L01c1549e
L01c15496:
    r1_r0 >>= 1
    r2 = r2 + 1
    goto L01c15490
L01c1549e:
    r0 = r2
    sp += 4
    {pc, r15-r4} = [sp++]

; ir_processing_inverse: 0x01c154a4..0x01c15a42, module ir-processing (inverse)
.type ir_processing_inverse,@function
ir_processing_inverse:
    [--sp] = {rets, r15-r4}
    sp += -8
    [sp] = r0
    [sp+4] = r2
    r13 = r1
    r14 = r3 + -1
    if (r3 == 0) goto L01c157f4
    r10 = [sp]
    r12 = [sp+4]
    r11 = r10 + 2048
    r9 = r13 + 1024
    r0 = [r10+0]
    r1 = [r10+4]
    r2 = [r10+8]
    r3 = [r10+12]
    r4 = [r11+0]
    r5 = [r11+4]
    r6 = [r11+8]
    r7 = [r11+12]
    r1_r0 >>>= r14
    r0 = r0 + 1
    r0 = r0 >>> 1
    r3_r2 >>>= r14
    r2 = r2 + 1
    r2 = r2 >>> 1
    r5_r4 >>>= r14
    r4 = r4 + 1
    r4 = r4 >>> 1
    r7_r6 >>>= r14
    r6 = r6 + 1
    r6 = r6 >>> 1
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r7 = [r9+0]
    [r13+r7] = r3
    r10 = [sp]
    r12 = [sp+4]
    r10 = r10 + 16
    r11 = r10 + 2016
    r12 = r12 + 8
    r9 = r13 + 1028
    r8 = r13 + 1532
    r15 = 31
    r0 = [r10+0]
    r1 = [r10+4]
    r2 = [r10+8]
    r3 = [r10+12]
    r4 = [r11+0]
    r5 = [r11+4]
    r6 = [r11+8]
    r7 = [r11+12]
    r1_r0 >>>= r14
    r0 = r0 + 1
    r0 = r0 >>> 1
    r3_r2 >>>= r14
    r2 = r2 + 1
    r2 = r2 >>> 1
    r5_r4 >>>= r14
    r4 = r4 + 1
    r4 = r4 >>> 1
    r7_r6 >>>= r14
    r6 = r6 + 1
    r6 = r6 >>> 1
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r7 = r3 - r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r6 = [r8+0]
    r6 = r6 + 4
    [r13+r6] = r7
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r1 = r1 + r7
    r7 = [r9+0]
    [r13+r7] = r3
    r9 = r9 + 4
    r7 = [r8+0]
    [r13+r7] = r1
    r8 = r8 + -4
    r10 = r10 + 16
    r11 = r11 + -16
L01c1560a:
    r0 = [r10+0]
    r1 = [r10+4]
    r2 = [r10+8]
    r3 = [r10+12]
    r4 = [r11+0]
    r5 = [r11+4]
    r6 = [r11+8]
    r7 = [r11+12]
    r1_r0 >>>= r14
    r0 = r0 + 1
    r0 = r0 >>> 1
    r3_r2 >>>= r14
    r2 = r2 + 1
    r2 = r2 >>> 1
    r5_r4 >>>= r14
    r4 = r4 + 1
    r4 = r4 >>> 1
    r7_r6 >>>= r14
    r6 = r6 + 1
    r6 = r6 >>> 1
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r7 = r3 - r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r6 = [r8+0]
    r6 = r6 + 4
    [r13+r6] = r7
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r1 = r1 + r7
    r7 = [r9+0]
    [r13+r7] = r3
    r9 = r9 + 4
    r7 = [r8+0]
    [r13+r7] = r1
    r8 = r8 + -4
    r10 = r10 + 16
    r11 = r11 + -16
    r0 = [r10+0]
    r1 = [r10+4]
    r2 = [r10+8]
    r3 = [r10+12]
    r4 = [r11+0]
    r5 = [r11+4]
    r6 = [r11+8]
    r7 = [r11+12]
    r1_r0 >>>= r14
    r0 = r0 + 1
    r0 = r0 >>> 1
    r3_r2 >>>= r14
    r2 = r2 + 1
    r2 = r2 >>> 1
    r5_r4 >>>= r14
    r4 = r4 + 1
    r4 = r4 >>> 1
    r7_r6 >>>= r14
    r6 = r6 + 1
    r6 = r6 >>> 1
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r7 = r3 - r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r6 = [r8+0]
    r6 = r6 + 4
    [r13+r6] = r7
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r1 = r1 + r7
    r7 = [r9+0]
    [r13+r7] = r3
    r9 = r9 + 4
    r7 = [r8+0]
    [r13+r7] = r1
    r8 = r8 + -4
    r10 = r10 + 16
    r11 = r11 + -16
    if (--r15 != 0) goto L01c1560a
    r10 = [sp]
    r12 = [sp+4]
    r10 = r10 + 1024
    r11 = r10
    r12 = r12 + 512
    r9 = r13 + 1280
    r0 = [r10+0]
    r1 = [r10+4]
    r2 = [r10+8]
    r3 = [r10+12]
    r4 = [r11+0]
    r5 = [r11+4]
    r6 = [r11+8]
    r7 = [r11+12]
    r1_r0 >>>= r14
    r0 = r0 + 1
    r0 = r0 >>> 1
    r3_r2 >>>= r14
    r2 = r2 + 1
    r2 = r2 >>> 1
    r5_r4 >>>= r14
    r4 = r4 + 1
    r4 = r4 >>> 1
    r7_r6 >>>= r14
    r6 = r6 + 1
    r6 = r6 >>> 1
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r7 = [r9+0]
    [r13+r7] = r3
    goto L01c15a3e
L01c157f4:
    r10 = [sp]
    r12 = [sp+4]
    r11 = r10 + 2048
    r9 = r13 + 1024
    r0 = [r10+0]
    r2 = [r10+8]
    r4 = [r11+0]
    r6 = [r11+8]
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r7 = [r9+0]
    [r13+r7] = r3
    r10 = [sp]
    r12 = [sp+4]
    r10 = r10 + 16
    r11 = r10 + 2016
    r12 = r12 + 8
    r9 = r13 + 1028
    r8 = r13 + 1532
    r15 = 31
    r0 = [r10+0]
    r2 = [r10+8]
    r4 = [r11+0]
    r6 = [r11+8]
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r7 = r3 - r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r6 = [r8+0]
    r6 = r6 + 4
    [r13+r6] = r7
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r1 = r1 + r7
    r7 = [r9+0]
    [r13+r7] = r3
    r9 = r9 + 4
    r7 = [r8+0]
    [r13+r7] = r1
    r8 = r8 + -4
    r10 = r10 + 16
    r11 = r11 + -16
L01c158e6:
    r0 = [r10+0]
    r2 = [r10+8]
    r4 = [r11+0]
    r6 = [r11+8]
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r7 = r3 - r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r6 = [r8+0]
    r6 = r6 + 4
    [r13+r6] = r7
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r1 = r1 + r7
    r7 = [r9+0]
    [r13+r7] = r3
    r9 = r9 + 4
    r7 = [r8+0]
    [r13+r7] = r1
    r8 = r8 + -4
    r10 = r10 + 16
    r11 = r11 + -16
    r0 = [r10+0]
    r2 = [r10+8]
    r4 = [r11+0]
    r6 = [r11+8]
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r7 = r3 - r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r6 = [r8+0]
    r6 = r6 + 4
    [r13+r6] = r7
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r1 = r1 + r7
    r7 = [r9+0]
    [r13+r7] = r3
    r9 = r9 + 4
    r7 = [r8+0]
    [r13+r7] = r1
    r8 = r8 + -4
    r10 = r10 + 16
    r11 = r11 + -16
    if (--r15 != 0) goto L01c158e6
    r10 = [sp]
    r12 = [sp+4]
    r10 = r10 + 1024
    r11 = r10
    r12 = r12 + 512
    r9 = r13 + 1280
    r0 = [r10+0]
    r2 = [r10+8]
    r4 = [r11+0]
    r6 = [r11+8]
    r1 = r0 + r4
    r1 = r1 >>> 1
    r3 = r2 - r6
    r3 = r3 >>> 1
    r0 = r0 - r4
    r2 = r2 + r6
    r4 = [r12+0]
    r5 = [r12+4]
    r12 = r12 + 8
    r7_r6 = r0 * r4 (s)
    r7_r6 += r2 * r5 (s)
    r6 = r3 + r7
    r6 = 0x0 - r6
    r3 = [r9+0]
    r3 = r3 + 4
    [r13+r3] = r6
    r7_r6 = r2 * r4 (s)
    r7_r6 -= r0 * r5 (s)
    r3 = r1 - r7
    r7 = [r9+0]
    [r13+r7] = r3
L01c15a3e:
    sp += 8
    {pc, r15-r4} = [sp++]

; ir_processing_output: 0x01c15a42..0x01c15bc8, module ir-processing (output)
.type ir_processing_output,@function
ir_processing_output:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r0 + 512
    r6 = r2
    r7 = r1
    r15 = 32
    ifs (r3 >= 0) goto L01c15a5c
    r14 = 0x0 - r3
    goto L01c15b2a
L01c15a5c:
    r14 = r3
    r12 = 2147483647
    r12 = r12 >> r14
    r13 = 0x0 - r12
L01c15a6c:
    r8 = [r5+0]
    r9 = [r5+4]
    r10 = [r6++=4]
    r11 = [r6++=4]
    r1_r0 = r8 * r10 (s)
    r1_r0 -= r9 * r11 (s)
    r3_r2 = r8 * r11 (s)
    r3_r2 += r9 * r10 (s)
    r8 = [r4+0]
    r9 = [r4+4]
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r8 = r8 - r1
    r9 = r3 - r9
    r8 = smin(r8, r12)
    r8 = smax(r8, r13)
    r8 = r8 << r14
    r9 = smin(r9, r12)
    r9 = smax(r9, r13)
    r9 = r9 << r14
    [r7++=4] = r8
    [r7++=4] = r9
    r4 = r4 + 8
    r5 = r5 + 8
    r8 = [r5+0]
    r9 = [r5+4]
    r10 = [r6++=4]
    r11 = [r6++=4]
    r1_r0 = r8 * r10 (s)
    r1_r0 -= r9 * r11 (s)
    r3_r2 = r8 * r11 (s)
    r3_r2 += r9 * r10 (s)
    r8 = [r4+0]
    r9 = [r4+4]
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r8 = r8 - r1
    r9 = r3 - r9
    r8 = smin(r8, r12)
    r8 = smax(r8, r13)
    r8 = r8 << r14
    r9 = smin(r9, r12)
    r9 = smax(r9, r13)
    r9 = r9 << r14
    [r7++=4] = r8
    [r7++=4] = r9
    r4 = r4 + 8
    r5 = r5 + 8
    if (--r15 != 0) goto L01c15a6c
    goto L01c15bc6
L01c15b2a:
    r8 = [r5+0]
    r9 = [r5+4]
    r10 = [r6++=4]
    r11 = [r6++=4]
    r1_r0 = r8 * r10 (s)
    r1_r0 -= r9 * r11 (s)
    r3_r2 = r8 * r11 (s)
    r3_r2 += r9 * r10 (s)
    r8 = [r4+0]
    r9 = [r4+4]
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r8 = r8 - r1
    r9 = r3 - r9
    r8 = r8 >>> r14
    r9 = r9 >>> r14
    [r7++=4] = r8
    [r7++=4] = r9
    r4 = r4 + 8
    r5 = r5 + 8
    r8 = [r5+0]
    r9 = [r5+4]
    r10 = [r6++=4]
    r11 = [r6++=4]
    r1_r0 = r8 * r10 (s)
    r1_r0 -= r9 * r11 (s)
    r3_r2 = r8 * r11 (s)
    r3_r2 += r9 * r10 (s)
    r8 = [r4+0]
    r9 = [r4+4]
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r8 = r8 - r1
    r9 = r3 - r9
    r8 = r8 >>> r14
    r9 = r9 >>> r14
    [r7++=4] = r8
    [r7++=4] = r9
    r4 = r4 + 8
    r5 = r5 + 8
    if (--r15 != 0) goto L01c15b2a
L01c15bc6:
    {pc, r15-r4} = [sp++]

; ir_processing_mix: 0x01c15bc8..0x01c15c8c, module ir-processing (mix)
.type ir_processing_mix,@function
ir_processing_mix:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r1
    r6 = r2
    r8 = r3 << 16
    r8 = r8 >> 16
    r9 = r3 >> 16
    r15 = 2147483647
    r13 = 0x80000000
    r14 = 127
    r10 = [r4++=4]
    if (r6 == 0) goto L01c15c46
    r11 = [r6++=4]
L01c15bf4:
    r1_r0 = r10 * r8 (s)
    r1_r0 += r11 * r9 (s)
    r10 = [r4++=4]
    r11 = [r6++=4]
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r15
    if (r1 != r3) {
    r0 = r2
    }
    if (r0 == r13) {
    r0 = r2
    }
    [r5++=4] = r0
    if (--r14 != 0) goto L01c15bf4
    r1_r0 = r10 * r8 (s)
    r1_r0 += r11 * r9 (s)
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r15
    if (r1 != r3) {
    r0 = r2
    }
    if (r0 == r13) {
    r0 = r2
    }
    [r5++=4] = r0
    goto L01c15c8a
L01c15c46:
    r1_r0 = r10 * r8 (s)
    r10 = [r4++=4]
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r15
    if (r1 != r3) {
    r0 = r2
    }
    if (r0 == r13) {
    r0 = r2
    }
    [r5++=4] = r0
    if (--r14 != 0) goto L01c15c46
    r1_r0 = r10 * r8 (s)
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r15
    if (r1 != r3) {
    r0 = r2
    }
    if (r0 == r13) {
    r0 = r2
    }
    [r5++=4] = r0
L01c15c8a:
    {pc, r15-r4} = [sp++]

; ir_processing_hardware_input: 0x01c15c8c..0x01c15cf2, module ir-processing (hardware_input)
.type ir_processing_hardware_input,@function
ir_processing_hardware_input:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r0 + 512
    r6 = r1
    r12 = 262143
    r13 = 0x0 - r12
    r15 = 64
L01c15ca4:
    r8 = [r6++=4]
    r9 = [r6++=4]
    r10 = [r5+0]
    r11 = [r5+4]
    r8 = r8 >>> 8
    r9 = r9 >>> 8
    r8 = r8 + 1
    r9 = r9 + 1
    r8 = r8 >>> 1
    r9 = r9 >>> 1
    r8 = smin(r8, r12)
    r9 = smin(r9, r12)
    r8 = smax(r8, r13)
    r9 = smax(r9, r13)
    [r4++=4] = r10
    [r4++=4] = r11
    [r5++=4] = r8
    [r5++=4] = r9
    if (--r15 != 0) goto L01c15ca4
    {pc, r15-r4} = [sp++]

; ir_processing_hardware_forward: 0x01c15cf2..0x01c15d3a, module ir-processing (hardware_forward)
.type ir_processing_hardware_forward,@function
ir_processing_hardware_forward:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r1
    r6 = r2 << 3
    r15 = 64
    r8 = [r4++=4]
    r9 = [r4++=4]
    [r5+0] = r8
    [r5+4] = r9
    r5 = r5 + r6
L01c15d10:
    r8 = [r4++=4]
    r9 = [r4++=4]
    r10 = [r4++=4]
    r11 = [r4++=4]
    [r5+0] = r8
    [r5+4] = r9
    r5 = r5 + r6
    [r5+0] = r10
    [r5+4] = r11
    r5 = r5 + r6
    if (--r15 != 0) goto L01c15d10
    {pc, r15-r4} = [sp++]

; ir_processing_hardware_scale: 0x01c15d3a..0x01c15d7e, module ir-processing (hardware_scale)
.type ir_processing_hardware_scale,@function
ir_processing_hardware_scale:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r5 = r0
    r15 = 129
    if (r1 == 0) goto L01c15d6e
    r14 = r1 - 0x1
L01c15d4a:
    r0 = [r4+0]
    r1 = [r4+4]
    r2 = [r4+8]
    r3 = [r4+12]
    r1_r0 >>>= r14
    r3_r2 >>>= r14
    r0 = r0 + 1
    r2 = r2 + 1
    r0 = r0 >>> 1
    r2 = r2 >>> 1
    [r5++=4] = r0
    [r5++=4] = r2
    r4 = r4 + 16
    if (--r15 != 0) goto L01c15d4a
    goto L01c15d7c
L01c15d6e:
    r0 = [r4+0]
    r2 = [r4+8]
    [r5++=4] = r0
    [r5++=4] = r2
    r4 = r4 + 16
    if (--r15 != 0) goto L01c15d6e
L01c15d7c:
    {pc, r15-r4} = [sp++]

; ir_processing_hardware_output: 0x01c15d7e..0x01c15dec, module ir-processing (hardware_output)
.type ir_processing_hardware_output,@function
ir_processing_hardware_output:
    [--sp] = {rets, r15-r4}
    r4 = r0
    r7 = r1
    r15 = 64
    ifs (r2 >= 0) goto L01c15dae
    r14 = 0x0 - r2
L01c15d90:
    r8 = [r4++=4]
    r9 = [r4++=4]
    r8 = r8 >>> r14
    r9 = r9 >>> r14
    [r7++=4] = r8
    [r7++=4] = r9
    if (--r15 != 0) goto L01c15d90
    goto L01c15dea
L01c15dae:
    r14 = r2
    r12 = 2147483647
    r12 = r12 >> r14
    r13 = 0x0 - r12
L01c15dbe:
    r8 = [r4++=4]
    r9 = [r4++=4]
    r8 = smin(r8, r12)
    r9 = smin(r9, r12)
    r8 = smax(r8, r13)
    r9 = smax(r9, r13)
    r8 = r8 << r14
    r9 = r9 << r14
    [r7++=4] = r8
    [r7++=4] = r9
    if (--r15 != 0) goto L01c15dbe
L01c15dea:
    {pc, r15-r4} = [sp++]
