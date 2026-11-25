; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_chain: 2 functions, 0x01c051a2..0x01c0539c

; biquad_chain_update: 0x01c051a2..0x01c051f0, module biquad-chain (update), biquad-pipeline (update)
.type biquad_chain_update,@function
biquad_chain_update:
    [--sp] = {rets, r7-r4}
    r1 = r0 * 0x2C
    r2 = L01c33190
    r2 = r2 + r1
    r3 = r2 + 176
    r4 = [r3+0]
    r5 = [r3+4]
    r6 = [r3+8]
    r7 = L01c33320
    [++r1=r7] = r4
    [r1+4] = r5
    [r1+8] = r6
    r4 = [r3+12]
    r3 = [r3+16]
    r5 = b[r2+216] (u)
    r2 = b[r2+217] (u)
    [r1+12] = r4
    [r1+16] = r3
    b[r1+40] = r5
    b[r1+41] = r2
    r1 = L01c32db0
    r0 = r0 + r1
    r1 = 0
    b[r0+164] = r1
    {pc, r7-r4} = [sp++]

; biquad_chain_process: 0x01c051f0..0x01c0539c, module biquad-chain (process), biquad-pipeline (process)
.type biquad_chain_process,@function
biquad_chain_process:
    [--sp] = {rets, r11-r4}
    r11 = L01c32db0
    r2 = b[r11+164] (u)
    r4 = r1
    r8 = r0
    if (r2 == 0) goto L01c0520a
    r0 = 0
    call biquad_chain_update
    r7 = 1
    goto L01c0520c
L01c0520a:
    r7 = 0
L01c0520c:
    r6 = L01c33320
    r5 = b[r6+40] (u)
    r0 = b[r11+165] (u)
    if (r0 == 0) goto L01c05222
    r0 = 1
    r7 = 1
    call biquad_chain_update
L01c05222:
    r0 = b[r6+84] (u)
    r1 = b[r11+166] (u)
    r5 = r5 + r0
    if (r1 == 0) goto L01c05234
    r0 = 2
    call biquad_chain_update
    r7 = 1
L01c05234:
    r0 = b[r6+128] (u)
    r1 = b[r11+167] (u)
    r5 = r5 + r0
    if (r1 == 0) goto L01c05246
    r0 = 3
    call biquad_chain_update
    r7 = 1
L01c05246:
    r0 = b[r6+172] (u)
    r1 = b[r11+168] (u)
    r5 = r5 + r0
    if (r1 == 0) goto L01c05258
    r0 = 4
    call biquad_chain_update
    r7 = 1
L01c05258:
    r0 = b[r6+216] (u)
    r1 = 0x0 - r5
    if (r0 == r1) goto L01c0539a
    r0 = L01c34488
    r9 = 0
    b[r0+0] = r9
    r10 = L01c34198
    r0 = [r10+0]
    if (r0 == 0) goto L01c05280
    call r0
    r9 = r0
L01c05280:
    r0 = b[r6+40] (u)
    if (r0 == 0) goto L01c052aa
    r0 = b[r6+41] (u)
    if (r0 == 0) goto L01c0529c
    if (r4 == 0) goto L01c052aa
    r0 = r8
    r1 = r4
    r2 = r6
    call biquad_residual  ; @call.xl
    goto L01c052aa
L01c0529c:
    if (r4 == 0) goto L01c052aa
    r0 = r8
    r1 = r4
    r2 = r6
    call biquad_rounded  ; @call.xl
L01c052aa:
    r0 = b[r6+84] (u)
    if (r0 == 0) goto L01c052d8
    r0 = b[r6+85] (u)
    if (r0 == 0) goto L01c052c8
    if (r4 == 0) goto L01c052d8
    r2 = r6 + 44
    r0 = r8
    r1 = r4
    call biquad_residual  ; @call.xl
    goto L01c052d8
L01c052c8:
    if (r4 == 0) goto L01c052d8
    r2 = r6 + 44
    r0 = r8
    r1 = r4
    call biquad_rounded  ; @call.xl
L01c052d8:
    r0 = b[r6+128] (u)
    if (r0 == 0) goto L01c05306
    r0 = b[r6+129] (u)
    if (r0 == 0) goto L01c052f6
    if (r4 == 0) goto L01c05306
    r2 = r6 + 88
    r0 = r8
    r1 = r4
    call biquad_residual  ; @call.xl
    goto L01c05306
L01c052f6:
    if (r4 == 0) goto L01c05306
    r2 = r6 + 88
    r0 = r8
    r1 = r4
    call biquad_rounded  ; @call.xl
L01c05306:
    r0 = b[r6+172] (u)
    if (r0 == 0) goto L01c05334
    r0 = b[r6+173] (u)
    if (r0 == 0) goto L01c05324
    if (r4 == 0) goto L01c05334
    r2 = r6 + 132
    r0 = r8
    r1 = r4
    call biquad_residual  ; @call.xl
    goto L01c05334
L01c05324:
    if (r4 == 0) goto L01c05334
    r2 = r6 + 132
    r0 = r8
    r1 = r4
    call biquad_rounded  ; @call.xl
L01c05334:
    r0 = b[r6+216] (u)
    if (r0 == 0) goto L01c05362
    r0 = b[r6+217] (u)
    if (r0 == 0) goto L01c05352
    if (r4 == 0) goto L01c05362
    r2 = r6 + 176
    r0 = r8
    r1 = r4
    call biquad_residual  ; @call.xl
    goto L01c05362
L01c05352:
    if (r4 == 0) goto L01c05362
    r2 = r6 + 176
    r0 = r8
    r1 = r4
    call biquad_rounded  ; @call.xl
L01c05362:
    r0 = [r10+0]
    if (r0 == 0) goto L01c0539a
    call r0
    r2 = 0
    if (r7 != 0) goto L01c05372
    r2 = [r11+24]
L01c05372:
    r1 = L01c34470
    r3 = [r1+0]
    r0 = r0 - r9
    r4 = r0
    if (r2 == 0) goto L01c05392
    if (r0 > r2) {
    r4 = r0 - r2
    r4 = r4 >> 2
    r4 = r4 + r2
    } else {
    r4 = r2 - r0
    r4 = r4 >> 2
    r4 = r2 - r4
    }
L01c05392:
    [r11+24] = r4
    r0 = r0 + r3
    [r1+0] = r0
L01c0539a:
    {pc, r11-r4} = [sp++]
