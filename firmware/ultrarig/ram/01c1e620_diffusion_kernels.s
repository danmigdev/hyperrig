; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; diffusion_kernels: 1 function, 0x01c1e620..0x01c1e780

; diffusion_kernels_all_pass: 0x01c1e620..0x01c1e780, module diffusion-kernels (all_pass)
.type diffusion_kernels_all_pass,@function
diffusion_kernels_all_pass:
    [--sp] = {rets, r15-r4}
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r7 = [r0+12]
    r10 = [r0+16]
    r8 = [r0+20]
    r9 = 2147483649
    if (r5 == 0) goto L01c1e6e6
    r11 = r10 & 0x1
    if (r11 == 0) goto L01c1e674
    r15 = [r4+0]
    r14 = [r5++=4]
    r15 += r14
    r3 = [r6++=4]
    r1_r0 = r3 * r8 (s)
    r14 = r1 >>> 31
    r1_r0 += r14 * r9 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r8 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    [r4++=4] = r15
L01c1e674:
    r10 = r10 >> 1
    if (r10 == 0) goto L01c1e6e4
L01c1e67c:
    r15 = [r4+0]
    r14 = [r5++=4]
    r15 += r14
    r3 = [r6++=4]
    r1_r0 = r3 * r8 (s)
    r14 = r1 >>> 31
    r1_r0 += r14 * r9 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r8 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    [r4++=4] = r15
    r15 = [r4+0]
    r14 = [r5++=4]
    r15 += r14
    r3 = [r6++=4]
    r1_r0 = r3 * r8 (s)
    r14 = r1 >>> 31
    r1_r0 += r14 * r9 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r8 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    [r4++=4] = r15
    if (--r10 != 0) goto L01c1e67c
L01c1e6e4:
    goto L01c1e77e
L01c1e6e6:
    r11 = r10 & 0x1
    if (r11 == 0) goto L01c1e71a
    r15 = [r4+0]
    r3 = [r6++=4]
    r1_r0 = r3 * r8 (s)
    r14 = r1 >>> 31
    r1_r0 += r14 * r9 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r8 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    [r4++=4] = r15
L01c1e71a:
    r10 = r10 >> 1
    if (r10 == 0) goto L01c1e77e
L01c1e722:
    r15 = [r4+0]
    r3 = [r6++=4]
    r1_r0 = r3 * r8 (s)
    r14 = r1 >>> 31
    r1_r0 += r14 * r9 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r8 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    [r4++=4] = r15
    r15 = [r4+0]
    r3 = [r6++=4]
    r1_r0 = r3 * r8 (s)
    r14 = r1 >>> 31
    r1_r0 += r14 * r9 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r8 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    [r4++=4] = r15
    if (--r10 != 0) goto L01c1e722
L01c1e77e:
    {pc, r15-r4} = [sp++]
