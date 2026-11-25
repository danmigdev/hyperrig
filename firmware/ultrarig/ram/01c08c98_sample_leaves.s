; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sample_leaves: 1 function, 0x01c08c98..0x01c08d34

; sample_leaves_high_pass: 0x01c08c98..0x01c08d34, module sample-leaves (high_pass)
.type sample_leaves_high_pass,@function
sample_leaves_high_pass:
    [--sp] = {rets, r12-r4}
    r8 = r2  #
    r6 = [r3+0]
    r2 = 0
    if (r1 < 4) goto L01c08d0c
    r9 = r8 >>> 31
    r12 = 0
L01c08caa:
    r2 = r12 << 2
    r7 = r0
    r2 = [++r7=r2]
    r5 = r2 - r6
    r11_r10 = r5 * r8 (s)
    r11_r10 >>= 31
    r5 = r10 + r6
    r2 = r2 - r5
    [r7+0] = r2
    r2 = [r7+4]
    r6 = r2 - r5
    r11_r10 = r6 * r8 (s)
    r11_r10 >>= 31
    r5 += r10
    r2 = r2 - r5
    [r7+4] = r2
    r2 = [r7+8]
    r6 = r2 - r5
    r11_r10 = r6 * r8 (s)
    r11_r10 >>= 31
    r5 += r10
    r2 = r2 - r5
    [r7+8] = r2
    r2 = [r7+12]
    r6 = r2 - r5
    r11_r10 = r6 * r8 (s)
    r11_r10 >>= 31
    r6 = r10 + r5
    r5 = r2 - r6
    r2 = r12 + 4  #
    [r7+12] = r5
    r4 = r12 + 8
    r12 = r2
    if (r4 <= r1) goto L01c08caa
L01c08d0c:
    if (r2 >= r1) goto L01c08d30
    r1 = r1 - r2
    r2 = r2 << 2
    r0 = r0 + r2
    r9 = r8 >>> 31
L01c08d1a:
    r2 = [r0+0]
    r4 = r2 - r6
    r5_r4 = r4 * r8 (s)
    r5_r4 >>= 31
    r6 = r6 + r4
    r2 = r2 - r6
    [r0++=4] = r2
    if (--r1 != 0) goto L01c08d1a
L01c08d30:
    [r3+0] = r6
    {pc, r12-r4} = [sp++]
