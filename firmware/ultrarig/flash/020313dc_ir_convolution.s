; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_convolution: 11 functions, 0x020313dc..0x02031bf8

; ir_convolution_sample: 0x020313dc..0x02031404, module ir-convolution (sample), ir-processing (sample)
.type ir_convolution_sample,@function
ir_convolution_sample:
    [--sp] = {rets, r4}
    r2 = r0
    r0 = 0
    ifs (r2 < 0) goto L02031402
    r3 = L01c32db0
    r4 = [r3+64]
    ifs (r4 > r2) {
    r0 = [r3+60]
    r0 = h[r0+r2<<1] (s)
    r0 = itof(r0)
    r0 = r0 * r1 (f)
    }
L02031402:
    {pc, r4} = [sp++]

; ir_convolution_resample: 0x02031404..0x02031542, module ir-convolution (resample), ir-processing (resample)
.type ir_convolution_resample,@function
ir_convolution_resample:
    [--sp] = {rets, r15-r4}
    sp += -48
    r14 = r2
    r6 = r1
    r8 = r0
    r0 = 1
    r1 = 1
    if (r3 != 0) goto L02031416
    r1 = r3
L02031416:
    r2 = L01c32db0
    r2 = [r2+68]
    if (r2 != 0) goto L02031424
    r0 = r2
L02031424:
    r2 = L01c1f7dc
    r0 ^= r1  #
    r2 = [r2+0]
    r1 = 0x38000000
    r1 = r2 * r1 (f)
    if (r0 == 0) goto L0203153a
    r0 = 0
    r2 = ir_resampling_coefficients
    r7 = r0 + 0x30800000
L02031446:
    r4 = [r0+r2]
    r4 = itof(r4)
    r4 = r4 * r7 (f)
    r5 = sp + 12
    [r5+r0] = r4
    r0 = r0 + 4
    if (r0 != 36) goto L02031446
    if (r14 == 0) goto L0203153e
    r12 = 1  #
    [sp+8] = r6
    r12 <= insert(r6, p:1, l:31)
    r0 = r6 << 1
    r9 = 0
    r11 = r6
    [sp+4] = r8
    r13 = r0 + -1  #
    [sp] = r3
L0203147a:
    r0 = r9 + r6
    if (r3 == 0) goto L02031492
    if ((r0 & 1) != 0) goto L020314d2
    r0 = r0 >> 1
    call ir_convolution_sample
    r2 = 0x3F000000
    r5 = r0 * r2 (f)
    goto L0203150a
L02031492:
    r15 = r0 << 1
    r4 = 0
    r7 = r12
    r6 = r13
    r8 = 0
L0203149e:
    r0 = sp + 12
    r10 = [r0+r4]
    r0 = r6
    call ir_convolution_sample
    r5 = r0
    r0 = r7
    call ir_convolution_sample
    r0 = r5 + r0 (f)
    r0 = r10 * r0 (f)
    r8 = r8 + r0 (f)
    r7 = r7 + 2
    r4 = r4 + 4
    r6 += -2
    if (r4 != 36) goto L0203149e
    r0 = r15
    call ir_convolution_sample
    r2 = r8 + r8 (f)
    r5 = r2 + r0 (f)
    goto L0203150a
L020314d2:
    r8 = r11 >> 1
    r4 = sp + 12
    r10 = 1
    r7 = r8
    r5 = 0
L020314e0:
    r15 = [r4++=4]
    r0 = r7
    call ir_convolution_sample
    r6 = r0
    r0 = r8 + r10
    call ir_convolution_sample
    r0 = r6 + r0 (f)
    r0 = r15 * r0 (f)
    r5 = r5 + r0 (f)
    r10 = r10 + 1
    r7 += -1
    if (r10 != 10) goto L020314e0
L0203150a:
    r11 = r11 + 1  #
    r0 = [sp+4]
    [r0+r9<<2] = r5
    r12 = r12 + 2  #
    r6 = [sp+8]
    r9 = r9 + 1  #
    r3 = [sp]
    r13 = r13 + 2
    if (r9 != r14) goto L0203147a
    goto L0203153e
L0203152a:
    r0 = r6
    call ir_convolution_sample
    [r8++=4] = r0
    r14 = r14 + -1
    r6 = r6 + 1
L0203153a:
    if (r14 != 0) goto L0203152a
L0203153e:
    sp += 48
    {pc, r15-r4} = [sp++]

; ir_convolution_produce: 0x02031542..0x020315b8, module ir-convolution (produce), ir-processing (produce)
.type ir_convolution_produce,@function
ir_convolution_produce:
    [--sp] = {rets, r12-r4}
    r7 = r0
    r8 = [r7+8]
    r4 = r3
    r5 = r2
    r6 = r1
    r0 = r6
    r1 = r5
    r2 = r4
    r3 = r8
    call ir_convolution_resample
    r0 = r4 + r5
    if (r0 <= r5) goto L020315b6
    r0 = [r7+0]
    r1 = [r7+4]
    r8 = r1 - r0
    r7 = r0 - r1
    r0 = r1 + 1
    r9 = utof(r0)
    r10 = 1078530011
    r11 = 0x3F800000
    r12 = 0x3F000000
    goto L020315aa
L02031582:
    r0 = r8 + r5
    r0 = r0 + 1
    r0 = utof(r0)
    r0 = r0 * r10 (f)
    r0 = r0 / r9 (f)
    call biquad_generator_cosine
    r0 = r0 + r11 (f)  #
    r1 = [r6+0]
    r0 = r0 * r12 (f)
    r0 = r1 * r0 (f)
    [r6+0] = r0
    goto L020315ae
L020315aa:
    if (r5 >= r7) goto L02031582
L020315ae:
    r5 = r5 + 1
    r6 = r6 + 4
    if (--r4 != 0) goto L020315aa
L020315b6:
    {pc, r12-r4} = [sp++]

; ir_convolution_copy: 0x020315b8..0x020315c8, module ir-convolution (copy), ir-processing (copy)
.type ir_convolution_copy,@function
ir_convolution_copy:
    if (r3 == 0) goto L020315c6
    r2 = r2 << 2
    r0 = r0 + r2
L020315be:
    r2 = [r0++=4]
    [r1++=4] = r2
    if (--r3 != 0) goto L020315be
L020315c6:
    rts

; ir_convolution_cosine: 0x020315c8..0x02031626, module ir-convolution (cosine), ir-processing (cosine)
.type ir_convolution_cosine,@function
ir_convolution_cosine:
    r0 = r0 * r0 (f)
    r1 = 3261071360
    r1 = r0 / r1 (f)
    r2 = 3266576384
    r2 = r0 / r2 (f)
    r3 = 0x3F800000
    r2 = r2 + r3 (f)
    r1 = r1 * r2 (f)
    r1 = r1 + r3 (f)
    r2 = 3253731328
    r2 = r0 / r2 (f)
    r1 = r2 * r1 (f)
    r1 = r1 + r3 (f)
    r2 = 3242196992
    r2 = r0 / r2 (f)
    r1 = r2 * r1 (f)
    r1 = r1 + r3 (f)
    r2 = r3 + 0x7F800000
    r0 = r0 * r2 (f)
    r0 = r0 * r1 (f)
    r0 = r0 + r3 (f)
    rts

; ir_convolution_sine: 0x02031626..0x0203167a, module ir-convolution (sine), ir-processing (sine)
.type ir_convolution_sine,@function
ir_convolution_sine:
    [--sp] = {rets, r4}
    r1 = r0 * r0 (f)
    r2 = 3257401344
    r2 = r1 / r2 (f)
    r3 = 3264217088
    r3 = r1 / r3 (f)
    r4 = 0x3F800000
    r3 = r3 + r4 (f)
    r2 = r2 * r3 (f)
    r2 = r2 + r4 (f)
    r3 = 3248488448
    r3 = r1 / r3 (f)
    r2 = r3 * r2 (f)
    r2 = r2 + r4 (f)
    r3 = 3233808384
    r1 = r1 / r3 (f)
    r1 = r1 * r2 (f)
    r1 = r1 + r4 (f)
    r0 = r1 * r0 (f)
    {pc, r4} = [sp++]

; ir_convolution_phase: 0x0203167a..0x020316f4, module ir-convolution (phase), ir-processing (phase)
.type ir_convolution_phase,@function
ir_convolution_phase:
    [--sp] = {rets, r7-r4}
    r1 = r1 << 2
    r7 = r1 / r2 (u)
    r3 = r7 * r2
    r1 = r1 - r3
    r3 = utof(r1)
    r1 = 1070141403
    r3 = r3 * r1 (f)
    r2 = utof(r2)
    r6 = r3 / r2 (f)
    r2 = 1061752795
    r4 = r0
    iff (r6 <= r2) goto L020316ba
    r6 = r1 - r6 (f)
    r0 = r6
    call ir_convolution_sine
    r5 = r0
    r0 = r6
    call ir_convolution_cosine
    goto L020316c4
L020316ba:
    r0 = r6
    call ir_convolution_cosine
    r5 = r0
    r0 = r6
    call ir_convolution_sine
L020316c4:
    r1 = r7 & 0x3
    if (r1 == 2) goto L020316de
    if (r1 == 1) goto L020316e4
    if (r1 == 0) {
    r0 ^= 2147483648
    r1 = r5
    } else {
    r1 = r0
    r0 = r5
    }
    goto L020316ee
L020316de:
    r1 = r5 ^ 0x80000000
    goto L020316ee
L020316e4:
    r2 = r5 ^ 0x80000000
    r1 = r0 ^ 0x80000000
    r0 = r2
L020316ee:
    [r4+0] = r1
    [r4+4] = r0
    {pc, r7-r4} = [sp++]

; ir_convolution_fft128: 0x020316f4..0x020317c8, module ir-convolution (fft128), ir-processing (fft128)
.type ir_convolution_fft128,@function
ir_convolution_fft128:
    [--sp] = {rets, r15-r4}
    sp += -16
    r3 = 0
    r4 = r2  #
    [sp] = r2
L020316fe:
    r5 = b[r0+r3] (u)
    if (r5 <= r3) goto L0203172a
    r5 = r5 << 3
    r6 = [sp]
    r8 = [++r6=r5]
    r9 = [r6+4]
    r10 = [r4+0]
    r11 = [r4+4]
    [r4+0] = r8
    [r4+4] = r9
    [r6+0] = r10
    [r6+4] = r11
L0203172a:
    r3 = r3 + 1
    r4 = r4 + 8
    if (r3 != 128) goto L020316fe
    r2 = 2
L02031734:
    r0 = 128
    r14 = r0 / r2 (u)
    r0 = r2 << 1
    r15 = r2 << 2  #
    [sp+8] = r0
    r0 = r2 >> 1
    r13 = 0  #
    [sp+12] = r0
    r12 = [sp]
    [sp+4] = r2
L0203174c:
    r0 = [sp+12]
    if (r0 == 0) goto L020317ae
    r3 = 0
    r4 = r12  #
    r7 = [sp+12]
L02031756:
    r0 = r4 + r15  #
    r2 = [r4+0]
    r6 = r3 * r14  #
    r5 = [r0+4]
    r6 = r6 << 3
    r6 = r6 + r1
    r8 = [r6+4]
    r6 = [r6+0]
    r9 = [r0+0]
    r10 = r8 * r5 (f)
    r11 = r6 * r9 (f)
    r10 = r11 - r10 (f)
    r2 = r2 - r10 (f)
    r5 = r6 * r5 (f)  #
    [r0+0] = r2
    r6 = r8 * r9 (f)  #
    r2 = [r4+4]
    r5 = r6 + r5 (f)
    r2 = r2 - r5 (f)
    [r0+4] = r2
    r0 = [r4+0]
    r0 = r10 + r0 (f)
    [r4+0] = r0
    r0 = [r4+4]
    r0 = r5 + r0 (f)
    [r4+4] = r0
    r4 = r4 + 8
    r3 = r3 + 1
    if (--r7 != 0) goto L02031756
L020317ae:
    r2 = [sp+4]
    r13 += r2  #
    r0 = [sp+8]
    r3 = r0 << 2
    r12 += r3
    if (r13 < 128) goto L0203174c
    r0 = [sp+8]
    r2 = r0
    if (r0 < 129) goto L02031734
    sp += 16
    {pc, r15-r4} = [sp++]

; ir_convolution_real256: 0x020317c8..0x0203187c, module ir-convolution (real256), ir-processing (real256)
.type ir_convolution_real256,@function
ir_convolution_real256:
    [--sp] = {rets, r15-r4}
    sp += -4
    r5 = r2  #
    r4 = [sp+60]
    [sp] = r4
    r10 = [sp+56]
    r2 = 0
L020317d6:
    r7 = r3  #
    r4 = [sp]
    r9 = [++r7=r2]
    r4 = r4 + r2
    [r4+0] = r9
    r7 = [r7+4]
    r2 = r2 + 8
    [r4+4] = r7
    if (r2 != 1024) goto L020317d6
    r2 = [sp]
    call ir_convolution_fft128
    r0 = 0
    r3 = 0
L020317f8:
    r4 = r0 & 0x7F  #
    r1 = [sp]
    r4 = r4 << 3
    r12 = [++r4=r1]
    r2 = r3 & 0x7F
    r2 = r2 << 3
    r13 = [++r1=r2]
    r15 = [r4+4]
    r11 = r13 + r12 (f)  #
    r1 = [r1+4]
    r9 = [r5+0]
    r8 = 0x3F000000  #
    r4 = [r5+4]
    r11 = r11 * r8 (f)
    r2 = r1 + r15 (f)
    r2 = r2 * r8 (f)
    r14 = r9 * r2 (f)
    r11 = r11 + r14 (f)
    r7 = r13 - r12 (f)
    r6 = r8 + 0x80000000
    r7 = r7 * r6 (f)
    r6 = r7 * r4 (f)
    r6 = r11 - r6 (f)
    [r10+0] = r6
    r1 = r1 - r15 (f)
    r1 = r1 * r8 (f)
    r2 = r2 * r4 (f)
    r1 = r1 + r2 (f)
    r2 = r7 * r9 (f)
    r1 = r2 + r1 (f)
    [r10+4] = r1
    r10 = r10 + 8
    r5 = r5 + 8
    r3 = r3 + 1
    r0 += -1
    if (r3 != 129) goto L020317f8
    sp += 4
    {pc, r15-r4} = [sp++]

; ir_convolution_q31: 0x0203187c..0x020318a8, module ir-convolution (q31), ir-processing (q31)
.type ir_convolution_q31,@function
ir_convolution_q31:
    r2 = 0x3F800000
    r1 = r0
    iff (r1 >= r2) {
    r0 = 2147483647
    rts
    }
    r2 = r2 + 0x80000000
    r0 = 0x80000000
    iff (r1 u> r2) {
    r0 = r0 + 0xCF000000
    r0 = r1 * r0 (f)
    r0 = ftoi(r0) (trunc)
    }
    rts

; ir_convolution_construct: 0x020318a8..0x02031bf8, module ir-convolution (construct), ir-processing (construct)
.type ir_convolution_construct,@function
ir_convolution_construct:
    [--sp] = {rets, r15-r4}
    sp += -184
    r7 = r0  #
    [sp+20] = r3
    [sp+28] = r2
    r0 = 0
    if (r1 == 0) goto L02031bf4
    if (r7 == 0) goto L02031bf4
    r2 = [sp+28]
    if (r2 == 0) goto L02031bf4
    r3 = 1
    r0 = r1 + 127  #
    [r7+0] = r3
    r2 = r0 >> 7
    r15 = 32
    if (r2 <= 32) {
    r15 = r2
    }
    [r7+4] = r15
    r2 = 0
    r4 = r7 + 544  #
    [r7+8] = r2
    [r7+12] = r2
    [r4+0] = r2
    r5 = L01c1fa14
    r5 = [r5+0]
    if (r5 != 0) goto L020318f8
    r3 = r5
L020318f8:
    r11 = r4 + 8  #
    [r4+4] = r3
    [r7+28] = r11
    r3 = r7 + 2616
    r4 = r15 * 0x408  #
    [r7+20] = r3
    r8 = r3 + r4
    [r7+24] = r8
    r9 = r8 + r4
    [r7+32] = r9
    r3 = r9 + 1024
    r3 = r9 + 1536  #
    [r7+36] = r3
    r3 = r9 + 2048  #
    [r7+40] = r3
    [sp+24] = r3
    r3 = r9 + 3080  #
    [r7+44] = r3
    r3 = r9 + 4104  #
    [r7+48] = r3
    [sp+16] = r3
    [r7+52] = r3
L0203193e:
    r3 = 0
    r4 = 6
    r5 = 0
L02031944:
    r6 = r2 >> r5
    r6 = r6 & 0x1
    r6 <<= r4
    r3 |= r6
    r4 += -1
    r5 = r5 + 1
    if (r4 != -1) goto L02031944
    r4 = sp + 56
    b[r4+r2] = r3
    r2 = r2 + 1
    if (r2 != 128) goto L0203193e
    r2 = 4096  #
    [sp+8] = r7
    r0 = r0 >> 7
    [sp+12] = r2
    if (r0 <= 32) {
    [sp+12] = r1
    }
    r14 = 0
    r12 = [sp+16]
L02031978:
    r0 = sp + 48
    r2 = 128
    r1 = r14
    call ir_convolution_phase
    r0 = [sp+48]
    r1 = [sp+52]
    r14 = r14 + 1
    [r12++=4] = r0
    [r12++=4] = r1
    if (r14 != 64) goto L02031978
    r14 = 0
    r12 = [sp+24]
L0203199a:
    if (r14 == 128) goto L020319c0
    r0 = sp + 40
    r2 = 256
    r1 = r14
    call ir_convolution_phase
    r0 = [sp+40]
    r1 = [sp+44]
    r14 = r14 + 1
    [r12++=4] = r0
    [r12++=4] = r1
    if (r14 != 129) goto L0203199a
    goto L020319d6
L020319c0:
    r0 = 3212836864
    [r12+0] = r0
    r0 = 257  #
    r2 = [sp+24]
    r1 = 0
    [r2+r0<<2] = r1
L020319d6:
    r6 = 0
    r5 = 0
    if (r15 == 0) goto L02031a68
    r7 = 0
    r14 = 0
    r13 = r5 + 0x3C000000
    r12 = r8
    r5 = 0
L020319ea:
    r2 = r14 << 7  #
    r0 = [sp+12]
    r4 = r0 - r2
    if (r4 >= 128) {
    r4 = 128
    }
    r1 = r11  #
    r0 = [sp+20]
    r3 = r4
    r10 = [sp+28]
    call r10
    r0 = 0
    r1 = r11
L02031a06:
    r2 = 0
    if (r0 < r4) {
    r2 = [r1+0]
    r2 = r2 * r13 (f)
    }
    r0 = r0 + 1
    [r1++=4] = r2
    if (r0 != 256) goto L02031a06
    [sp+4] = r9
    r0 = r14 * 0x408
    r1 = r8 + r0
    r0 = sp + 56
    r3 = r11  #
    [sp] = r1
    r1 = [sp+16]
    r2 = [sp+24]
    call ir_convolution_real256
    r0 = 129
    r1 = r12
    r2 = r5
L02031a38:
    r5 = [r1+4]
    iff (r5 < r7) {
    r5 ^= 2147483648
    }
    r3 = [r1++=8]
    iff (r3 < r7) {
    r3 ^= 2147483648
    }
    iff (r3 u<= r2) {
    r3 = r2
    }
    iff (r5 u<= r3) {
    r5 = r3
    }
    r2 = r5
    if (--r0 != 0) goto L02031a38
    r14 = r14 + 1
    r12 = r12 + 1032
    if (r14 != r15) goto L020319ea
L02031a68:
    r0 = 0
    r10 = r8
    r9 = 0
L02031a6e:
    r1 = 0
    if (r15 == 0) goto L02031a98
    r4 = r15
    r7 = r10
L02031a78:
    r3 = [r7+4]
    iff (r3 < r6) {
    r3 ^= 2147483648
    }
    r2 = [r7+0]
    iff (r2 < r6) {
    r2 ^= 2147483648
    }
    r2 = r2 + r3 (f)
    r1 = r1 + r2 (f)
    r7 = r7 + 1032
    if (--r4 != 0) goto L02031a78
L02031a98:
    iff (r1 u<= r9) {
    r1 = r9
    }
    r0 = r0 + 1
    r10 = r10 + 8
    r9 = r1
    if (r0 != 129) goto L02031a6e
    r2 = 0
    r0 = r2 + 0x3F800000  #
    r7 = [sp+8]
    r3 = r0 + 0xF000000
    r4 = 1342175455
L02031abc:
    r6 = r5 * r0 (f)
    r6 = r6 + r6 (f)
    iff (r6 u>= r3) goto L02031ade
    r6 = r1 * r0 (f)
    r6 = r6 + r6 (f)
    iff (r6 u>= r4) goto L02031ade
    r2 = r2 + 1
    r0 = r0 + r0 (f)
    ifs (r2 < 48) goto L02031abc
L02031ade:
    [r7+16] = r2
    r1 = 0
    r2 = 0
L02031ae4:
    if (r15 == 0) goto L02031b16
    r5 = r8  #
    r3 = [r7+20]
    r4 = r1 << 3
    r3 = r3 + r4
    r3 = r3 + 4
    r4 = r15
L02031af4:
    r6 = [r5+0]
    r6 = r0 * r6 (f)
    r6 = ftoi(r6) (trunc)
    [r3+-4] = r6
    r6 = [r5+4]
    r6 = r0 * r6 (f)
    r6 = ftoi(r6) (trunc)
    [r3++=8] = r6
    r5 = r5 + 1032
    if (--r4 != 0) goto L02031af4
L02031b16:
    r1 += r15
    r2 = r2 + 1
    r8 = r8 + 8
    if (r2 != 129) goto L02031ae4
    r0 = r15 * 0x810  #
    r4 = [r7+40]
    r3 = r7 + r0
    r5 = r3 + 6724
    r6 = 64
L02031b30:
    r0 = [r5+-4]
    call ir_convolution_q31
    [r4+0] = r0
    r0 = [r5++=8]
    call ir_convolution_q31
    [r4+4] = r0
    r4 = r4 + 8
    if (--r6 != 0) goto L02031b30
    r5 = r3 + 4668  #
    r4 = [r7+44]
    r6 = 129
L02031b50:
    r3 = [r5+0]
    r0 = [r5+-4]
    call ir_convolution_q31
    r0 = r3  #
    [r4+0] = r0
    call ir_convolution_q31
    [r4+4] = r0
    r4 = r4 + 8
    r5 = r5 + 8
    if (--r6 != 0) goto L02031b50
    r8 = r7 + 60
    r10 = sp + 32
    r11 = 0
L02031b74:
    r0 = r11 + -4
    r12 = r11 << 2
    if (r11 >= 4) {
    r12 = r0
    }
    r13 = 3
    r14 = r8
    r9 = r12
L02031b8a:
    r0 = sp + 32
    r2 = 64
    r1 = r9
    call ir_convolution_phase
    r0 = [sp+32]
    call ir_convolution_q31
    [r14+-4] = r0
    r0 = [r10+4]
    call ir_convolution_q31
    [r14++=8] = r0
    r9 += r12
    if (--r13 != 0) goto L02031b8a
    r11 = r11 + 1
    r8 = r8 + 24
    if (r11 != 20) goto L02031b74
    r3_r2 = 0  #
    r0 = [sp+8]
    r6 = [r0+36]
    r1 = 0
L02031bc4:
    r4 = r1 & 0x30
    r5 = r3 >> 1
    r5 = r5 & 0xC
    r4 |= r5
    r5 = uextra(r3, p:5, l:2)
    r4 |= r5
    r5 = r2 & 0x200
    r5 <= insert(r4, p:3, l:6)
    [r6+r3<<2] = r5
    r1 = r1 + 8
    r3 = r3 + 1
    r2 = r2 + 512
    if (r3 != 128) goto L02031bc4
    call ir_convolution_reset  ; @call.xl
L02031bf4:
    sp += 184
    {pc, r15-r4} = [sp++]
