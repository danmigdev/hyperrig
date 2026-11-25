; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sample_leaves: 1 function, 0x01c0b524..0x01c0b5d6

; sample_leaves_post_filter: 0x01c0b524..0x01c0b5d6, module sample-leaves (post_filter)
.type sample_leaves_post_filter,@function
sample_leaves_post_filter:
    [--sp] = {rets, r15-r10, r8-r4}
    r12 = r2
    r4 = r1
    r5 = r0
    r8 = L01c31c94
    if (r4 == 0) goto L01c0b566
    r13 = r2 >>> 31
    r0 = r4
    r1 = r8
    r2 = r5
L01c0b540:
    r6 = [r1++=4]
    r14 = [r2+0]
    r7_r6 = r6 * r12 (s)
    r7_r6 >>= 16
    r15 = r14 >>> 31
    r10 = r14 - r6
    r11 = r15 - r7 - !c
    r11_r10 >>= 2
    [r2++=4] = r10
    if (--r0 != 0) goto L01c0b540
L01c0b566:
    r6 = [sp+48]
    if (r3 == 0) goto L01c0b578
    r0 = r5
    r1 = r4
    r2 = r3
    r3 = r6
    call sample_leaves_high_pass
    goto L01c0b59c
L01c0b578:
    r0 = [r6+0]
    if (r4 == 0) goto L01c0b58e
    r1 = r5
    r2 = r4
L01c0b580:
    r3 = [r1+0]
    r3 = r3 - r0
    [r1++=4] = r3
    r3 = r0 >>> 9
    r0 = r0 - r3
    if (--r2 != 0) goto L01c0b580
L01c0b58e:
    r2 = r0 + 511
    r1 = 0
    if (r2 >= 1023) {
    r1 = r0
    }
    [r6+0] = r1
L01c0b59c:
    if (r4 == 0) goto L01c0b5d2
    r0 = 2147483647
    goto L01c0b5ae
L01c0b5a6:
    r1 = r7 >> 31
    r1 = r1 << 1
    r6 = r1 + r0
    goto L01c0b5cc
L01c0b5ae:
    r2 = [r5+0]
    r10 = [r8++=4]
    r3 = r2 >>> 31
    r3_r2 <<= 2
    r11 = r10 >>> 31
    r6 = r2 + r10
    r7 = r3 + r11 + c
    r1 = r6 >>> 31
    if (r7 != r1) goto L01c0b5a6
L01c0b5cc:
    [r5++=4] = r6
    if (--r4 != 0) goto L01c0b5ae
L01c0b5d2:
    {pc, r15-r10, r8-r4} = [sp++]
