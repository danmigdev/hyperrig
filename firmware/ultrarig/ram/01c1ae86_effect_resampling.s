; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_resampling: 4 functions, 0x01c1ae86..0x01c1b582

; effect_resampling_up5: 0x01c1ae86..0x01c1b056, module effect-resampling (up5)
.type effect_resampling_up5,@function
effect_resampling_up5:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r2 = r2 << 2
    r2 += r13
    sp += -4
    [sp] = r2
    r4 = 670538396
    r5 = 4103877117
    r6 = 82421978
    r7 = 4260925266
    r8 = 11421924
    r12 = [r13+-36]
    r15 = [r13+-32]
L01c1aeba:
    r1_r0 = r12 * r8 (s)
    r12 = [r13+-28]
    r1_r0 += r15 * r7 (s)
    r3_r2 = r15 * r8 (s)
    r15 = [r13+-24]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r7 (s)
    r12 = [r13+-20]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r6 (s)
    r15 = [r13+-16]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+-12]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r4 (s)
    [r14+4] = r15
    r15 = [r13+-8]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r4 (s)
    [r14+12] = r12
    r12 = [r13+-4]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+0]
    r1_r0 += r12 * r7 (s)
    r3_r2 += r12 * r6 (s)
    r12 = [r13+4]
    r1_r0 += r15 * r8 (s)
    r3_r2 += r15 * r7 (s)
    r3_r2 += r12 * r8 (s)
    r15 = [r13+-28]
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r12 = r0 >>> 31
    if (r1 != r12) goto L01c1b00e
L01c1af4a:
    [r14+0] = r0
    r12 = [r13+-24]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b020
L01c1af58:
    [r14+8] = r2
    r1_r0 = r15 * r8 (s)
    r15 = [r13+-20]
    r1_r0 += r12 * r7 (s)
    r3_r2 = r12 * r8 (s)
    r12 = [r13+-16]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r7 (s)
    r15 = [r13+-12]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r6 (s)
    r12 = [r13+-8]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+-4]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r4 (s)
    [r14+20] = r12
    r12 = [r13+0]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r4 (s)
    [r14+28] = r15
    r15 = [r13+4]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+8]
    r1_r0 += r15 * r7 (s)
    r3_r2 += r15 * r6 (s)
    r15 = [r13+12]
    r1_r0 += r12 * r8 (s)
    r3_r2 += r12 * r7 (s)
    r3_r2 += r15 * r8 (s)
    r12 = [r13+-20]
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c1b030
L01c1afec:
    [r14+16] = r0
    r15 = [r13+-16]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b042
L01c1affa:
    [r14+24] = r2
    r13 = r13 + 16
    r14 = r14 + 32
    r2 = [sp]
    if (r13 != r2) goto L01c1aeba
    goto L01c1b052
L01c1b00e:
    r12 = r1 >> 31
    r12 += r12
    r1 = 2147483647
    r12 += r1
    r0 = r12
    goto L01c1af4a
L01c1b020:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1af58
L01c1b030:
    r15 = r1 >> 31
    r15 += r15
    r1 = 2147483647
    r15 += r1
    r0 = r15
    goto L01c1afec
L01c1b042:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1affa
L01c1b052:
    sp += 4
    {pc, r15-r4} = [sp++]

; effect_resampling_down5: 0x01c1b056..0x01c1b23a, module effect-resampling (down5)
.type effect_resampling_down5,@function
effect_resampling_down5:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r2 = r2 << 2
    r2 += r14
    sp += -4
    [sp] = r2
    r4 = 670538396
    r5 = 4103877117
    r6 = 82421978
    r7 = 4260925266
    r8 = 11421924
    r9 = 0x40000000
    r12 = [r13+-36]
    r15 = [r13+-28]
L01c1b08e:
    r1_r0 = r12 * r9 (s)
    r3_r2 = r15 * r9 (s)
    r12 = [r13+-72]
    r15 = [r13+-64]
    r1_r0 += r12 * r8 (s)
    r12 = [r13+-56]
    r1_r0 += r15 * r7 (s)
    r3_r2 += r15 * r8 (s)
    r15 = [r13+-48]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r7 (s)
    r12 = [r13+-40]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r6 (s)
    r15 = [r13+-32]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+-24]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r4 (s)
    r15 = [r13+-16]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r4 (s)
    r12 = [r13+-8]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+0]
    r1_r0 += r12 * r7 (s)
    r3_r2 += r12 * r6 (s)
    r12 = [r13+8]
    r1_r0 += r15 * r8 (s)
    r3_r2 += r15 * r7 (s)
    r3_r2 += r12 * r8 (s)
    r15 = [r13+-20]
    r1_r0 >>>= 31
    r3_r2 >>>= 31
    r12 = r0 >>> 31
    if (r1 != r12) goto L01c1b1f2
L01c1b126:
    [r14+0] = r0
    r12 = [r13+-12]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b204
L01c1b134:
    [r14+4] = r2
    r1_r0 = r15 * r9 (s)
    r3_r2 = r12 * r9 (s)
    r15 = [r13+-56]
    r12 = [r13+-48]
    r1_r0 += r15 * r8 (s)
    r15 = [r13+-40]
    r1_r0 += r12 * r7 (s)
    r3_r2 += r12 * r8 (s)
    r12 = [r13+-32]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r7 (s)
    r15 = [r13+-24]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r6 (s)
    r12 = [r13+-16]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+-8]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r4 (s)
    r12 = [r13+0]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r4 (s)
    r15 = [r13+8]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+16]
    r1_r0 += r15 * r7 (s)
    r3_r2 += r15 * r6 (s)
    r15 = [r13+24]
    r1_r0 += r12 * r8 (s)
    r3_r2 += r12 * r7 (s)
    r3_r2 += r15 * r8 (s)
    r12 = [r13+-4]
    r1_r0 >>>= 31
    r3_r2 >>>= 31
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c1b214
L01c1b1d0:
    [r14+8] = r0
    r15 = [r13+4]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b226
L01c1b1de:
    [r14+12] = r2
    r13 = r13 + 32
    r14 = r14 + 16
    r2 = [sp]
    if (r14 != r2) goto L01c1b08e
    goto L01c1b236
L01c1b1f2:
    r12 = r1 >> 31
    r12 += r12
    r1 = 2147483647
    r12 += r1
    r0 = r12
    goto L01c1b126
L01c1b204:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1b134
L01c1b214:
    r15 = r1 >> 31
    r15 += r15
    r1 = 2147483647
    r15 += r1
    r0 = r15
    goto L01c1b1d0
L01c1b226:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1b1de
L01c1b236:
    sp += 4
    {pc, r15-r4} = [sp++]

; effect_resampling_up4: 0x01c1b23a..0x01c1b3d4, module effect-resampling (up4)
.type effect_resampling_up4,@function
effect_resampling_up4:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r2 = r2 << 2
    r2 += r13
    sp += -4
    [sp] = r2
    r4 = 665320397
    r5 = 4117437020
    r6 = 65670763
    r7 = 4274656822
    r12 = [r13+-28]
    r15 = [r13+-24]
L01c1b268:
    r1_r0 = r12 * r7 (s)
    r12 = [r13+-20]
    r1_r0 += r15 * r6 (s)
    r3_r2 = r15 * r7 (s)
    r15 = [r13+-16]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r6 (s)
    r12 = [r13+-12]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+-8]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r4 (s)
    [r14+4] = r12
    r12 = [r13+-4]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r4 (s)
    [r14+12] = r15
    r15 = [r13+0]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+4]
    r1_r0 += r15 * r7 (s)
    r3_r2 += r15 * r6 (s)
    r3_r2 += r12 * r7 (s)
    r15 = [r13+-20]
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r12 = r0 >>> 31
    if (r1 != r12) goto L01c1b38c
L01c1b2e0:
    [r14+0] = r0
    r12 = [r13+-16]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b39e
L01c1b2ee:
    [r14+8] = r2
    r1_r0 = r15 * r7 (s)
    r15 = [r13+-12]
    r1_r0 += r12 * r6 (s)
    r3_r2 = r12 * r7 (s)
    r12 = [r13+-8]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r6 (s)
    r15 = [r13+-4]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+0]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r4 (s)
    [r14+20] = r15
    r15 = [r13+4]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r4 (s)
    [r14+28] = r12
    r12 = [r13+8]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+12]
    r1_r0 += r12 * r7 (s)
    r3_r2 += r12 * r6 (s)
    r3_r2 += r15 * r7 (s)
    r12 = [r13+-12]
    r1_r0 >>>= 30
    r3_r2 >>>= 30
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c1b3ae
L01c1b36a:
    [r14+16] = r0
    r15 = [r13+-8]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b3c0
L01c1b378:
    [r14+24] = r2
    r13 = r13 + 16
    r14 = r14 + 32
    r2 = [sp]
    if (r13 != r2) goto L01c1b268
    goto L01c1b3d0
L01c1b38c:
    r12 = r1 >> 31
    r12 += r12
    r1 = 2147483647
    r12 += r1
    r0 = r12
    goto L01c1b2e0
L01c1b39e:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1b2ee
L01c1b3ae:
    r15 = r1 >> 31
    r15 += r15
    r1 = 2147483647
    r15 += r1
    r0 = r15
    goto L01c1b36a
L01c1b3c0:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1b378
L01c1b3d0:
    sp += 4
    {pc, r15-r4} = [sp++]

; effect_resampling_down4: 0x01c1b3d4..0x01c1b582, module effect-resampling (down4)
.type effect_resampling_down4,@function
effect_resampling_down4:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r2 = r2 << 2
    r2 += r14
    sp += -4
    [sp] = r2
    r4 = 665320397
    r5 = 4117437020
    r6 = 65670763
    r7 = 4274656822
    r8 = 0x40000000
    r12 = [r13+-28]
    r15 = [r13+-20]
L01c1b406:
    r1_r0 = r12 * r8 (s)
    r3_r2 = r15 * r8 (s)
    r12 = [r13+-56]
    r15 = [r13+-48]
    r1_r0 += r12 * r7 (s)
    r12 = [r13+-40]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r7 (s)
    r15 = [r13+-32]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r6 (s)
    r12 = [r13+-24]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+-16]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r4 (s)
    r12 = [r13+-8]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r4 (s)
    r15 = [r13+0]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+8]
    r1_r0 += r15 * r7 (s)
    r3_r2 += r15 * r6 (s)
    r3_r2 += r12 * r7 (s)
    r15 = [r13+-12]
    r1_r0 >>>= 31
    r3_r2 >>>= 31
    r12 = r0 >>> 31
    if (r1 != r12) goto L01c1b53a
L01c1b486:
    [r14+0] = r0
    r12 = [r13+-4]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b54c
L01c1b494:
    [r14+4] = r2
    r1_r0 = r15 * r8 (s)
    r3_r2 = r12 * r8 (s)
    r15 = [r13+-40]
    r12 = [r13+-32]
    r1_r0 += r15 * r7 (s)
    r15 = [r13+-24]
    r1_r0 += r12 * r6 (s)
    r3_r2 += r12 * r7 (s)
    r12 = [r13+-16]
    r1_r0 += r15 * r5 (s)
    r3_r2 += r15 * r6 (s)
    r15 = [r13+-8]
    r1_r0 += r12 * r4 (s)
    r3_r2 += r12 * r5 (s)
    r12 = [r13+0]
    r1_r0 += r15 * r4 (s)
    r3_r2 += r15 * r4 (s)
    r15 = [r13+8]
    r1_r0 += r12 * r5 (s)
    r3_r2 += r12 * r4 (s)
    r12 = [r13+16]
    r1_r0 += r15 * r6 (s)
    r3_r2 += r15 * r5 (s)
    r15 = [r13+24]
    r1_r0 += r12 * r7 (s)
    r3_r2 += r12 * r6 (s)
    r3_r2 += r15 * r7 (s)
    r12 = [r13+4]
    r1_r0 >>>= 31
    r3_r2 >>>= 31
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c1b55c
L01c1b518:
    [r14+8] = r0
    r15 = [r13+12]
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c1b56e
L01c1b526:
    [r14+12] = r2
    r13 = r13 + 32
    r14 = r14 + 16
    r2 = [sp]
    if (r14 != r2) goto L01c1b406
    goto L01c1b57e
L01c1b53a:
    r12 = r1 >> 31
    r12 += r12
    r1 = 2147483647
    r12 += r1
    r0 = r12
    goto L01c1b486
L01c1b54c:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1b494
L01c1b55c:
    r15 = r1 >> 31
    r15 += r15
    r1 = 2147483647
    r15 += r1
    r0 = r15
    goto L01c1b518
L01c1b56e:
    r0 = r3 >> 31
    r0 = r0 + r0
    r3 = 2147483647
    r0 = r0 + r3
    r2 = r0
    goto L01c1b526
L01c1b57e:
    sp += 4
    {pc, r15-r4} = [sp++]
