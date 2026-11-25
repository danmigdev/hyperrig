; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ring_stages: 2 functions, 0x01c09cfe..0x01c09eaa

; ring_stages_diffusion_pass: 0x01c09cfe..0x01c09e0a, module ring-stages (diffusion_pass)
.type ring_stages_diffusion_pass,@function
ring_stages_diffusion_pass:
    [--sp] = {rets, r14-r4}
    sp += -80
    r11_r10 = r1_r0
    r0 = 0
L01c09d06:
    r1 = r0 << 2
    r4 = r10 + r1
    r1 = [r4+116]
    r5 = sp + 68
    [r5+r0<<2] = r1
    r4 = [r4+196]
    r5 = sp + 56
    [r5+r0<<2] = r4
    r5 = h[r2+r0<<1] (u)
    r4 = r4 + r1
    r4 = r4 - r5
    r5 = 0
    if (r4 >= r1) {
    r5 = r1
    }
    r1 = r4 - r5
    r4 = sp + 44
    [r4+r0<<2] = r1
    r1 = [r3+r0<<2]
    r4 = sp + 0
    r4 += 32
    [r4+r0<<2] = r1
    r0 = r0 + 1
    if (r0 != 3) goto L01c09d06
    if (r11 == 0) goto L01c09df0
    r14 = r10 + 36
    r8 = sp + 0
    r13_r12 = 0
    r9 = L01c30d74
L01c09d5e:
    r5 = r11 - r12
    r0 = 0
L01c09d64:
    r1 = sp + 44
    r1 = [r1+r0]
    r2 = [r14+r0]
    r3 = r1 << 2
    r3 = r3 + r2
    r4 = sp + 68
    r4 = [r4+r0]
    r7 = sp + 56
    r7 = [r7+r0]
    r6 = sp + 0
    r6 = r6 + r0
    [r6+4] = r3
    r3 = r7 << 2
    r2 = r2 + r3
    r2 = r4 - r7  #
    [r6+16] = r2
    r1 = r4 - r1
    r1 = umin(r5, r1)
    r0 = r0 + 4
    r5 = umin(r1, r2)
    if (r0 != 12) goto L01c09d64
    r0 = r12 << 2
    r0 += r9
    [sp] = r0
    [r8+28] = r5
    r0 = sp + 0
    call diffusion_kernels_all_pass_cascade  ; @call.xl
    r0 = 0
L01c09db2:
    r2 = sp + 44
    r3 = [r2+r0<<2]
    r4 = sp + 56
    r6 = [r4+r0<<2]
    r1 = sp + 68
    r1 = [r1+r0<<2]
    r3 = r3 + r5
    [r2+r0<<2] = r3
    r2 = r6 + r5
    [r4+r0<<2] = r2
    if (r3 == r1) {
    r3 = sp + 44
    [r3+r0<<2] = r13
    }
    if (r2 == r1) {
    r1 = sp + 56
    [r1+r0<<2] = r13
    }
    r0 = r0 + 1
    if (r0 != 3) goto L01c09db2
    r12 += r5
    if (r12 < r11) goto L01c09d5e
L01c09df0:
    r0 = r10 + 196
    r1 = 0
L01c09df6:
    r2 = sp + 56
    r2 = [r2+r1<<2]
    [r0+r1<<2] = r2
    r1 = r1 + 1
    if (r1 != 3) goto L01c09df6
    sp += 80
    {pc, r14-r4} = [sp++]

; ring_stages_all_pass_lines: 0x01c09e0a..0x01c09eaa, module ring-stages (all_pass_lines)
.type ring_stages_all_pass_lines,@function
ring_stages_all_pass_lines:
    [--sp] = {rets, r15-r4}
    sp += -24
    r10 = r0
    r0 = r1 << 2
    r8 = r10 + r0
    r15 = [r8+160]
    r9 = r1  #
    r0 = [sp+84]
    r12 = [sp+80]
    r14 = [r8+80]
    r11 = r3  #
    [sp+20] = r0
    if (r12 == 0) goto L01c09ea2
    r0 = r14 - r2
    r0 += r15
    r6 = 0
    r1 = 0
    if (r0 >= r14) {
    r1 = r14
    }
    r13 = [sp+76]
    r5 = r0 - r1
    r4 = sp + 0
L01c09e42:
    r0 = r6 << 2
    r1 = r11 + r0
    r0 += r13  #
    [sp] = r1
    if (r13 == 0) {
    r0 = r13
    }
    [r4+4] = r0
    r0 = [r10+r9<<2]
    r1 = r5 << 2
    r1 = r1 + r0
    r1 = r15 << 2  #
    [r4+8] = r1
    r0 = r0 + r1
    r0 = r14 - r5  #
    [r4+12] = r0
    r1 = r12 - r6
    r0 = umin(r1, r0)
    r1 = r14 - r15
    r7 = umin(r0, r1)
    [r4+16] = r7
    r0 = sp + 0
    call diffusion_kernels_all_pass  ; @call.xl
    r1 = r7 + r15
    r0 = 0
    r15 = 0
    if (r1 != r14) {
    r15 = r1
    }
    r1 = r7 + r5
    if (r1 != r14) {
    r0 = r1
    }
    r6 = r6 + r7
    r5 = r0
    if (r6 < r12) goto L01c09e42
L01c09ea2:
    [r8+160] = r15
    sp += 24
    {pc, r15-r4} = [sp++]
