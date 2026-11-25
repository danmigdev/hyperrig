; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_sample_processing: 1 function, 0x01c08b3e..0x01c08c76

; effect_sample_processing_cascade: 0x01c08b3e..0x01c08c76, module effect-sample-processing (cascade)
.type effect_sample_processing_cascade,@function
effect_sample_processing_cascade:
    [--sp] = {rets, r15-r4}
    sp += -68
    r8 = r1  #
    [sp+4] = r0
    r4 = r1 << 2
    r0 = r0 + r4  #
    r5 = [sp+120]
    r15 = [r0+-4]
    r0 += -8
    r11 = r3
    r7 = r2
    if (r1 <= 1) {
    r0 = r5
    }
    r1 = [sp+128]
    r4 = [r0+0]
    [sp+20] = r1
    if (r1 == 0) goto L01c08c68  ; @beq.ri
    r12 = [sp+136]
    r14 = 0  #
    r0 = [sp+132]
    [sp+16] = r0
    r0 = [sp+124]
    [sp+8] = r0
    r6 = sp + 24
    r0 = r3 << 2
    [sp+12] = r0
    [sp] = r8
L01c08b7a:
    r0 = 1
    r0 = r0 << r14  #
    r1 = [sp+16]
    if ((r0 & r1) == 0) goto L01c08bac
    r1 = [r7+0]
    [sp+24] = r1
    r1 = [r7+4]
    if (r11 != 3) goto L01c08bbe
    [r6+12] = r1
    r1 = [r7+4]
    r1 = 0x0 - r1
    [r6+4] = r1
    r1 = [r7+8]
    [r6+16] = r1
    r1 = [r7+8]
    r1 = 0x10000000 - r1  #
    r2 = [r7+0]
    r1 = r1 - r2
    [r6+8] = r1
    goto L01c08bd4
L01c08bac:
    r0 = r14 << 3
    r1 = r5
    [++r1=r0] = r15
    r9 = r14 + 1  #
    [r1+4] = r4
    goto L01c08c5c
L01c08bbe:
    [r6+8] = r1
    r1 = [r7+8]
    [r6+12] = r1
    if (r11 < 5) {
    r1 = 0x0 - r1
    } else {
    r1 = [r7+16]
    }
    [r6+4] = r1
    r1 = [r7+12]
    [r6+16] = r1
L01c08bd4:
    r1 = 1
    r13 = r6 + 40
    b[r13+0] = r1
    if ((r0 & r12) == 0) {
    r1 = 0
    }
    b[r13+1] = r1
    r10 = r14 << 3
    r1 = [++r10=r5]
    r9 = r14 + 1  #
    [r6+20] = r1
    r1 = [r10+4]
    r1 = r9 << 3  #
    [r6+24] = r1
    r2 = r5
    r1 = [++r2=r1]
    [r6+28] = r1
    r1 = [r2+4]
    [r6+32] = r1
    if ((r0 & r12) == 0) goto L01c08c2a
    r0 = [sp+8]
    r0 = [r0+r14<<2]
    [r6+36] = r0
    if (r8 == 0) goto L01c08c40
    r2 = sp + 24
    r1 = r8  #
    r0 = [sp+4]
    call biquad_residual  ; @call.xl
    goto L01c08c3e
L01c08c2a:
    r0 = 0
    [r6+36] = r0
    if (r8 == 0) goto L01c08c40
    r2 = sp + 24
    r1 = r8  #
    r0 = [sp+4]
    call biquad_rounded  ; @call.xl
L01c08c3e:
    r8 = [sp]
L01c08c40:
    r0 = b[r13+1] (u)
    if (r0 == 0) goto L01c08c4e
    r0 = [r6+36]
    r1 = [sp+8]
    [r1+r14<<2] = r0
L01c08c4e:
    [r10++=4] = r15
    [r10+0] = r4
    r4 = [r6+32]
    r15 = [r6+28]
L01c08c5c:
    r14 = r9  #
    r0 = [sp+12]
    r7 = r7 + r0  #
    r0 = [sp+20]
    if (r9 != r0) goto L01c08b7a
L01c08c68:
    r0 = [sp+20]
    r0 = r0 << 3
    [++r5=r0] = r15
    [r5+4] = r4
    sp += 68
    {pc, r15-r4} = [sp++]
