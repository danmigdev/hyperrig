; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; diffusion_kernels: 1 function, 0x01c1dab2..0x01c1dd46

; diffusion_kernels_all_pass_cascade: 0x01c1dab2..0x01c1dd46, module diffusion-kernels (all_pass_cascade)
.type diffusion_kernels_all_pass_cascade,@function
diffusion_kernels_all_pass_cascade:
    [--sp] = {rets, r15-r4}
    r4 = [r0+4]
    r5 = [r0+8]
    r6 = [r0+12]
    r7 = [r0+16]
    r8 = [r0+20]
    r9 = [r0+24]
    r10 = [r0+32]
    r11 = [r0+36]
    r12 = [r0+40]
    r2 = [r0+28]
    r13 = [r0+0]
    r14 = 2147483649
    r2 = r2 << 2
    r2 += r13
    sp += -4
    [sp] = r2
    r2 = r2 - r13
    r2 = r2 & 0x4
    if (r2 == 0) goto L01c1db84
    r15 = [r13+0]
    r3 = [r4++=4]
    r1_r0 = r3 * r10 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r10 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dca0
L01c1db1e:
    r3 = [r5++=4]
    r1_r0 = r3 * r11 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r8++=4] = r15
    r1_r0 = r15 * r11 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dcb2
L01c1db4a:
    r3 = [r6++=4]
    r1_r0 = r3 * r12 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r9++=4] = r15
    r1_r0 = r15 * r12 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dcc4
L01c1db76:
    [r13+0] = r15
    r13 = r13 + 4
    r2 = [sp]
    if (r13 == r2) goto L01c1dd42
L01c1db84:
    r15 = [r13+0]
    r3 = [r4++=4]
    r1_r0 = r3 * r10 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r10 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dcd6
L01c1dbb4:
    r3 = [r5++=4]
    r1_r0 = r3 * r11 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r8++=4] = r15
    r1_r0 = r15 * r11 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dce8
L01c1dbe0:
    r3 = [r6++=4]
    r1_r0 = r3 * r12 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r9++=4] = r15
    r1_r0 = r15 * r12 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dcfa
L01c1dc0a:
    [r13+0] = r15
    r15 = [r13+4]
    r3 = [r4++=4]
    r1_r0 = r3 * r10 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r7++=4] = r15
    r1_r0 = r15 * r10 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dd0c
L01c1dc3c:
    r3 = [r5++=4]
    r1_r0 = r3 * r11 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r8++=4] = r15
    r1_r0 = r15 * r11 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dd1e
L01c1dc66:
    r3 = [r6++=4]
    r1_r0 = r3 * r12 (s)
    r2 = r1 >>> 31
    r1_r0 += r2 * r14 (s)
    r1_r0 >>>= 31
    r15 += r0
    [r9++=4] = r15
    r1_r0 = r15 * r12 (s)
    r1_r0 >>>= 31
    r15 = r3 - r0
    r2 = abs(r15)
    r2 = r2 >> 24
    if (r2 != 0) goto L01c1dd30
L01c1dc90:
    [r13+4] = r15
    r13 = r13 + 8
    r2 = [sp]
    if (r13 != r2) goto L01c1db84
    goto L01c1dd42
L01c1dca0:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1db1e
L01c1dcb2:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1db4a
L01c1dcc4:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1db76
L01c1dcd6:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1dbb4
L01c1dce8:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1dbe0
L01c1dcfa:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1dc0a
L01c1dd0c:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1dc3c
L01c1dd1e:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1dc66
L01c1dd30:
    r2 = r15 >>> 31
    r15 = 0x1000000
    r15 = r15 ^ r2
    r15 = r15 - r2
    goto L01c1dc90
L01c1dd42:
    sp += 4
    {pc, r15-r4} = [sp++]
