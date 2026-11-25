; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; drive_dispatch: 1 function, 0x01c07a4c..0x01c07bf0

; drive_dispatch_dispatch: 0x01c07a4c..0x01c07bf0, module drive-dispatch (dispatch)
.type drive_dispatch_dispatch,@function
drive_dispatch_dispatch:
    [--sp] = {rets, r11-r4}
    sp += -8
    r5 = r2  #
    r3 = b[r0+0] (u)
    r3 += -16
    r6 = r1
    if (r3 > 7) goto L01c07bec
    r4 = r0 + 288
    r7 = r0 + 456
    tbb [r3]
drive_dispatch_table:
    .byte (L01c07a6e - drive_dispatch_table) / 2, (L01c07a82 - drive_dispatch_table) / 2, (L01c07a96 - drive_dispatch_table) / 2, (L01c07aaa - drive_dispatch_table) / 2, (L01c07abe - drive_dispatch_table) / 2, (L01c07ad2 - drive_dispatch_table) / 2, (L01c07afc - drive_dispatch_table) / 2, (L01c07b1e - drive_dispatch_table) / 2
L01c07a6e:
    if (r5 == 0) goto L01c07bec
    r0 = r6
    r1 = r5
    r2 = r4
    call blended_drive_blended_drive  ; @call.xl
    sp += 8
    {pc, r11-r4} = [sp++]
L01c07a82:
    if (r5 == 0) goto L01c07bec
    r0 = r6
    r1 = r5
    r2 = r4
    call filtered_drive_filtered_drive  ; @call.xl
    sp += 8
    {pc, r11-r4} = [sp++]
L01c07a96:
    if (r5 == 0) goto L01c07bec
    r0 = r6
    r1 = r5
    r2 = r4
    call crossover_drive_crossover_drive  ; @call.xl
    sp += 8
    {pc, r11-r4} = [sp++]
L01c07aaa:
    if (r5 == 0) goto L01c07bec
    r0 = r6
    r1 = r5
    r2 = r4
    call shaped_drive_shaped_drive  ; @call.xl
    sp += 8
    {pc, r11-r4} = [sp++]
L01c07abe:
    if (r5 == 0) goto L01c07bec
    r0 = r6
    r1 = r5
    r2 = r4
    call asymmetric_drive_asymmetric_drive  ; @call.xl
    sp += 8
    {pc, r11-r4} = [sp++]
L01c07ad2:
    r8 = r0 + 364
    r9 = [r8+32]
    if (r5 == 0) goto L01c07b4a
    r0 = r6
    r1 = r5
    r2 = r4
    call cubic_drive_cubic_drive  ; @call.xl
    r2 = r4 + 128  #
    r0 = b[r7+1] (u)
    if (r0 == 0) goto L01c07b40
    r0 = r6
    r1 = r5
    call biquad_residual  ; @call.xl
    goto L01c07b4a
L01c07afc:
    if (r5 == 0) goto L01c07bec
    r0 = r6
    r1 = r5
    r2 = r4
    call two_stage_drive_two_stage_drive  ; @call.xl
    r2 = r4 + 128  #
    r0 = b[r7+1] (u)
    if (r0 == 0) goto L01c07bbc
    r0 = r6
    r1 = r5
    call biquad_residual  ; @call.xl
    goto L01c07bc6
L01c07b1e:
    if (r5 == 0) goto L01c07bec
    r0 = r6
    r1 = r5
    r2 = r4
    call two_pass_drive_two_pass_drive  ; @call.xl
    r2 = r4 + 128  #
    r0 = b[r7+1] (u)
    if (r0 == 0) goto L01c07bd6
    r0 = r6
    r1 = r5
    call biquad_residual  ; @call.xl
    goto L01c07be0
L01c07b40:
    r0 = r6
    r1 = r5
    call biquad_rounded  ; @call.xl
L01c07b4a:
    r0 = [r4+4]
    r1 = [r8+0]
    r3_r2 = r1 * r9 (s)
    r3_r2 >>= 30
    r1 = 0x10000 - r2
    r1_r0 = r1 * r0 (s)
    r1_r0 >>= 16
    r2 = r0
    ifs (r0 <= 1) {
    r2 = 1
    }
    r11 = 16383
    r10 = -1
    r3_r2 = r11_r10 / r2 (u)
    if (r5 == 0) goto L01c07baa
    r7 = r10 + 0x80000000
    r10 = 0
    r7 = r2 - r7
    r7 = r3 - r10 - !c
    r7 = psr
    if ((r7 & 0x2) != 0) {
    r2 = 2147483647
    r3 = 0
    }
    r2 = r4  #
    [sp] = r2
    r0 = r6  #
    [sp+4] = r0
    r3 = sp + 0
    r1 = r5
    call waveshapers_cubic  ; @call.xl
    goto L01c07bac
L01c07baa:
    r0 = 0
L01c07bac:
    r0 = r0 - r9
    r0 = r0 >>> 5
    r0 += r9
    [r8+32] = r0
    sp += 8
    {pc, r11-r4} = [sp++]
L01c07bbc:
    r0 = r6
    r1 = r5
    call biquad_rounded  ; @call.xl
L01c07bc6:
    r0 = r6
    r1 = r5
    r2 = r4
    call waveshapers_quadratic  ; @call.xl
    sp += 8
    {pc, r11-r4} = [sp++]
L01c07bd6:
    r0 = r6
    r1 = r5
    call biquad_rounded  ; @call.xl
L01c07be0:
    r0 = r6
    r1 = r5
    r2 = r4
    call waveshapers_soft_quadratic  ; @call.xl
L01c07bec:
    sp += 8
    {pc, r11-r4} = [sp++]
