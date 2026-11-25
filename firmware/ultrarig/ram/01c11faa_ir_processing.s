; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_processing: 2 functions, 0x01c11faa..0x01c123fa

; ir_processing_crossfade: 0x01c11faa..0x01c12064, module ir-processing (crossfade)
.type ir_processing_crossfade,@function
ir_processing_crossfade:
    [--sp] = {rets, r15-r4}
    sp += -12
    r6 = [sp+64]
    r4 = [sp+72]
    r14 = r4 - r6  #
    r5 = [sp+68]
    r9 = r5 - r3  #
    [sp+8] = r2
    [sp] = r0
    [sp+4] = r1
    r0 = r6
    r8 = 2147483647
    r6 = r9
    r5 = r14
    r4 = 0
L01c11fd0:
    r2 = [sp+8]
    r10 = [r2+r4<<2]
    r1 = 128
    r7 = r5 / r1 (s)  #
    r2 = [sp+4]
    r7 = r7 + r0
    r13 = [r2+r4<<2]
    r11_r10 = r10 * r7 (s)
    r7 = r6 / r1 (s)
    r7 = r7 + r3
    r11_r10 += r13 * r7 (s)
    r11_r10 >>>= 15
    r13 = r10 - r8
    r2 = 0
    r15 = r11 - r2 - !c
    r7 = psr
    r12 = sextra(r7, p:0, l:1)
    r7 = sextra(r7, p:3, l:1)
    r7 = r7 ^ r12
    r7 = ~r7
    r2 = r13 | r15
    r15 = r4 + 1
    r13 = r8
    if ((r2 & r7) != 0) goto L01c12050
    r1 = r8 + 2
    r12 = r10 - r1
    r1 = -1
    r13 = r11 - r1 - !c
    r2 = psr
    r7 = sextra(r2, p:0, l:1)
    r2 = sextra(r2, p:3, l:1)
    r2 ^= r7
    r2 = ~r2
    r7 = r12 | r13
    if ((r7 & r2) == 0) {
    r10 = r8 + 2
    r11 = r1 + 0
    }
    r13 = r10
L01c12050:
    r6 += r9  #
    r1 = [sp]
    [r1+r4<<2] = r13
    r5 += r14
    r4 = r15
    if (r4 != 128) goto L01c11fd0
    sp += 12
    {pc, r15-r4} = [sp++]

; ir_processing_process: 0x01c12064..0x01c123fa, module ir-processing (process)
.type ir_processing_process,@function
ir_processing_process:
    [--sp] = {rets, r15-r4}
    sp += -24
    r11 = r3
    r15 = r1
    r5 = r0
    if (r5 == 0) goto L01c123f6
    if (r2 != 128) goto L01c123f6
    r0 = [r5+0]
    if (r0 == 0) goto L01c123f6
    r13 = r5 + 536  #
    r0 = [r5+48]
    r12 = [r13+12]
    r10 = [r5+32]
    r4 = r10 + 512  #
    r6 = [r5+8]
    r14 = [r5+4]
    r8 = L01c34490
    if (r12 == 0) goto L01c12106
    call ir_processing_hardware_input  ; @call.xl
    r0 = 256  #
    r3 = [r5+28]
    r2 = [r5+48]
    r1 = 0
    r7 = 0
    call ir_processing_start  ; @call.xl
    if (r0 != 0) goto L01c120c8
    call ir_processing_wait  ; @call.xl
    if (r0 == 0) goto L01c12294
L01c120c8:
    [r13+12] = r7
    r0 = [r5+4]
    r0 = r0 * 0x81
    if (r0 == 0) goto L01c120e2
    r1 = [r5+24]
    r2 = 0
    r3 = 0
L01c120da:
    [r1++=4] = r2
    [r1++=4] = r3
    if (--r0 != 0) goto L01c120da
L01c120e2:
    r0 = [r5+48]
    r1 = 0
    r2 = 0
L01c120e8:
    [r0+r2<<2] = r1
    r2 = r2 + 1
    if (r2 != 256) goto L01c120e8
    r0 = 0
    [r5+8] = r0
    [r5+12] = r0
    r0 = [r8+0]
    r0 = r0 + 1
    [r8+0] = r0
    sp += 24
    {pc, r15-r4} = [sp++]
L01c12106:
    r3 = r10  #
    r2 = [r5+12]
    r1 = r2 << 9
    r1 = r1 + r0
    r7 = r2 ^ 0x1
    r2 = r7 << 9
    r2 = r2 + r0
    r0 = r15
    call ir_processing_input  ; @call.xl
    r0 = r5 + 56  #
    [r5+12] = r7
    r7 = r0 | 0x1
    r0 = r10
    r1 = r7
    call ir_processing_fft64  ; @call.xl
    r0 = r4  #
    [sp+20] = r4
    r1 = r7
    call ir_processing_fft64  ; @call.xl
    r0 = r10  #
    r1 = [r5+40]
    call ir_processing_merge  ; @call.xl
    r3 = r14  #
    r0 = [r5+24]
    r1 = r6 << 3
    r1 = r1 + r0  #
    r2 = [r5+44]
    r0 = r10
    call ir_processing_forward  ; @call.xl
    r8 = r5 + 28
L01c1215e:
    r7 = r5 + 24
    r3 = [r8+0]
    r0 = [r7+0]
    r2 = r6 << 16
    r2 = r2 | r14  #
    r1 = [r5+20]
    call ir_processing_multiply  ; @call.xl
    r9 = r0
    if (r6 == 0) goto L01c1217a
    r14 = r6
L01c1217a:
    r0 = r14 + -1
    [r5+8] = r0
    r0 = [r8+0]
    if (r12 == 0) goto L01c121ea
    r1 = r9
    call ir_processing_hardware_scale  ; @call.xl
    r2 = [r8+0]
    r0 = 256
    r1 = 1
    r3 = r10
    call ir_processing_start  ; @call.xl
    if (r0 != 0) goto L01c121ac
    call ir_processing_wait  ; @call.xl
    if (r0 == 0) goto L01c1220e
L01c121ac:
    r0 = 0
    [r13+12] = r0
    r1 = [r5+4]
    r1 = r1 * 0x81
    if (r1 == 0) goto L01c121c8
    r2 = [r7+0]
    r6 = 0
    r7 = 0
L01c121c0:
    [r2++=4] = r6
    [r2++=4] = r7
    if (--r1 != 0) goto L01c121c0
L01c121c8:
    r1 = [r5+48]
    r2 = 0
    r3 = L01c34490
L01c121d2:
    [r1+r2<<2] = r0
    r2 = r2 + 1
    if (r2 != 256) goto L01c121d2
    [r5+8] = r0
    [r5+12] = r0
    r0 = [r3+0]
    r0 = r0 + 1
    [r3+0] = r0
    sp += 24
    {pc, r15-r4} = [sp++]
L01c121ea:
    r1 = r10  #
    r2 = [r5+44]
    r3 = r9
    call ir_processing_inverse  ; @call.xl
    r6 = r5 + 56
    r0 = r10
    r1 = r6
    call ir_processing_fft64  ; @call.xl
    r1 = r6  #
    r0 = [sp+20]
    call ir_processing_fft64  ; @call.xl
L01c1220e:
    r0 = 16
    if (r12 == 0) {
    r0 = 8
    }
    r1 = [r5+16]
    r1 = r9 - r1
    r0 = r0 + r1
    r1 = r0
    ifs (r0 <= -31) {
    r1 = -31
    }
    r7 = 30
    ifs (r0 <= 30) {
    r7 = r1
    }
    r0 = 0x47000000  #
    r1 = [sp+76]
    r4 = r11 * r0 (f)
    r3 = 0
    r2 = 0
    r9 = 0
    iff (r4 u<= r2) goto L01c12254
    r6 = ftoi(r4) (trunc)
    r8 = r0 + 0x1000000
    r9 = 0x20000
    iff (r4 u< r8) {
    r9 = r6
    }
L01c12254:
    r4 = r1 * r0 (f)
    iff (r4 u<= r2) goto L01c1226e
    r2 = ftoi(r4) (trunc)
    r6 = r0 + 0x1000000
    r3 = 0x20000
    iff (r4 u< r6) {
    r3 = r2
    }
L01c1226e:
    r0 = [r13+4]
    r2 = [r13+8]
    r6 = [r13+0]
    [sp+12] = r0
    if (r2 == 0) goto L01c122ac
    r2 = 1
    r4 = 1
    if (r3 == r0) {
    r4 = 0
    }
    if (r9 == r6) {
    r2 = 0
    }
    r14 = r2 | r4
    goto L01c122ae
L01c12294:
    r8 = r5 + 28  #
    [sp+20] = r4
    r1 = [r5+24]
    r2 = r6 << 3
    r1 = r1 + r2  #
    r0 = [r5+28]
    r2 = r14
    call ir_processing_hardware_forward  ; @call.xl
    goto L01c1215e
L01c122ac:
    r14 = 0
L01c122ae:
    [r13+0] = r9
    r8 = r11  #
    [sp+16] = r3
    [r13+4] = r3
    [r13+8] = 0x1
    r0 = 0x47000000
    iff (r8 u<= r1) {
    r8 = r1
    }
    r2 = 0x3F800000
    r3 = r7
    iff (r8 > r2) {
    r1 = r1 / r8 (f)
    r11 = r11 / r8 (f)
    } else {
    r8 = r2
    }
    r1 = r1 * r0 (f)
    r4 = ftou(r1) (trunc)
    if (r4 >= 32768) {
    r4 = 0x8000
    }
    r2 = 1
    r1 = 1
    if (r4 == 0) goto L01c122f4
    r1 = 0
L01c122f4:
    r13 = r6
    r0 = r11 * r0 (f)
    r7 = ftou(r0) (trunc)
    r0 = r7 >> 15
    if (r0 != 0) goto L01c12304
    r2 = r0
L01c12304:
    r0 = r2 & ~r14
    r6 = r0 & r1
    if (r7 >= 32768) {
    r7 = 0x8000
    }
    if (r12 == 0) goto L01c1232a
    r1 = r15
    if (r6 != 0) goto L01c1231e
    r1 = [r5+52]
L01c1231e:
    r2 = r3  #
    r0 = [sp+20]
    call ir_processing_hardware_output  ; @call.xl
    goto L01c1233a
L01c1232a:
    r1 = r15
    if (r6 != 0) goto L01c12330
    r1 = [r5+52]
L01c12330:
    r0 = r10  #
    r2 = [r5+40]
    call ir_processing_output  ; @call.xl
L01c1233a:
    if (r14 == 0) goto L01c12358
    r2 = r15  #
    r1 = [r5+52]
    r3 = r13  #
    r0 = [sp+16]
    [sp+8] = r0
    [sp+4] = r9
    r0 = [sp+12]
    r0 = r15  #
    [sp] = r0
    call ir_processing_crossfade
    sp += 24
    {pc, r15-r4} = [sp++]
L01c12358:
    if (r6 != 0) goto L01c12370
    r2 = r15
    if (r4 != 0) goto L01c12360
    r2 = r4
L01c12360:
    r1 = r4 << 16
    r3 = r1 | r7  #
    r0 = [r5+52]
    r1 = r15
    call ir_processing_mix  ; @call.xl
L01c12370:
    r0 = 0x3F800000
    iff (r8 u<= r0) goto L01c123f6
    r0 = r0 + 0x8000000
    r0 = r8 * r0 (f)
    r0 = ftoi(r0) (trunc)
    r1 = r0 >>> 31
    r12 = 0
    r3 = 2147483647
    r10 = r3 + 2
    r11 = -1
    r6 = 0
L01c12398:
    r7 = [r15+r6<<2]
    r9_r8 = r7 * r0 (s)
    r9_r8 >>>= 16
    r7 = r8 - r3
    r4 = r9 - r12 - !c
    r5 = psr
    r2 = sextra(r5, p:0, l:1)
    r5 = sextra(r5, p:3, l:1)
    r2 ^= r5
    r2 = ~r2
    r4 |= r7
    r7 = r3
    if ((r4 & r2) != 0) goto L01c123ec
    r2 = r8 - r10
    r4 = r9 - r11 - !c
    r5 = psr
    r7 = sextra(r5, p:0, l:1)
    r5 = sextra(r5, p:3, l:1)
    r5 ^= r7
    r5 = ~r5
    r2 |= r4
    if ((r2 & r5) == 0) {
    r8 = r3 + 2
    r9 = r3 + 0x80000000
    }
    r7 = r8
L01c123ec:
    [r15+r6<<2] = r7
    r6 = r6 + 1
    if (r6 != 128) goto L01c12398
L01c123f6:
    sp += 24
    {pc, r15-r4} = [sp++]
