; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; diffusion_kernels: 1 function, 0x01c1ea96..0x01c1ebcc

; diffusion_kernels_line_sum: 0x01c1ea96..0x01c1ebcc, module diffusion-kernels (line_sum)
.type diffusion_kernels_line_sum,@function
diffusion_kernels_line_sum:
    [--sp] = {rets, r15-r4}
    sp += -8
    [sp] = r0
    r15 = [r0+0]
    r4 = [r0+4]
    r5 = [r0+8]
    r6 = [r0+12]
    r7 = [r0+16]
    r8 = [r0+20]
    r9 = [r0+24]
    r10 = [r0+28]
    r11 = [r0+32]
    r2 = [r0+36]
    r12 = [r0+40]
    r13 = [r0+44]
    r14 = [r0+48]
    r2 = r2 << 2
    r2 += r15
    [sp+4] = r2
    r2 = [sp+4]
    r2 = r2 - r15
    r2 = r2 & 0x4
    if (r2 == 0) goto L01c1eb28
    r2 = [r4++=4]
    r3 = [r5++=4]
    r2 = r2 + r3
    r3 = [r6++=4]
    r2 = r2 + r3
    r3 = [r7++=4]
    r2 = r2 + r3
    r3 = [r8++=4]
    r2 = r2 - r3
    r3 = [r9++=4]
    r2 = r2 - r3
    r3 = [r10++=4]
    r2 = r2 - r3
    r3 = [r11++=4]
    r2 = r2 - r3
    r1_r0 = r2 * r12 (s)
    r1_r0 += r14 * r13 (s)
    r2 = r1 >>> 31
    r3 = 2147483649
    r1_r0 += r2 * r3 (s)
    r1_r0 >>>= 31
    r14 = r0
    r2 = [r15+0]
    r2 += r14
    [r15++=4] = r2
    r2 = [sp+4]
    if (r15 == r2) goto L01c1ebc2
L01c1eb28:
    r2 = [r4++=4]
    r3 = [r5++=4]
    r2 = r2 + r3
    r3 = [r6++=4]
    r2 = r2 + r3
    r3 = [r7++=4]
    r2 = r2 + r3
    r3 = [r8++=4]
    r2 = r2 - r3
    r3 = [r9++=4]
    r2 = r2 - r3
    r3 = [r10++=4]
    r2 = r2 - r3
    r3 = [r11++=4]
    r2 = r2 - r3
    r1_r0 = r2 * r12 (s)
    r1_r0 += r14 * r13 (s)
    r2 = r1 >>> 31
    r3 = 2147483649
    r1_r0 += r2 * r3 (s)
    r1_r0 >>>= 31
    r14 = r0
    r2 = [r15+0]
    r2 += r14
    [r15++=4] = r2
    r2 = [r4++=4]
    r3 = [r5++=4]
    r2 = r2 + r3
    r3 = [r6++=4]
    r2 = r2 + r3
    r3 = [r7++=4]
    r2 = r2 + r3
    r3 = [r8++=4]
    r2 = r2 - r3
    r3 = [r9++=4]
    r2 = r2 - r3
    r3 = [r10++=4]
    r2 = r2 - r3
    r3 = [r11++=4]
    r2 = r2 - r3
    r1_r0 = r2 * r12 (s)
    r1_r0 += r14 * r13 (s)
    r2 = r1 >>> 31
    r3 = 2147483649
    r1_r0 += r2 * r3 (s)
    r1_r0 >>>= 31
    r14 = r0
    r2 = [r15+0]
    r2 += r14
    [r15++=4] = r2
    r2 = [sp+4]
    if (r15 != r2) goto L01c1eb28
L01c1ebc2:
    r0 = [sp]
    [r0+48] = r14
    sp += 8
    {pc, r15-r4} = [sp++]
