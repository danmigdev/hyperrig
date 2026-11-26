; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_convolution: 2 functions, 0x02029604..0x02029728

; ir_convolution_installation_raw_length: 0x02029604..0x0202962a, module ir-convolution (installation_raw_length), ir-installation (raw_length), ir-processing (installation_raw_length)
.type ir_convolution_installation_raw_length,@function
ir_convolution_installation_raw_length:
    [--sp] = {rets, r5, r4}
    sp += -4
    r3 = L01c32db0
    r2 = [r3+68]
    r3 = [r3+64]
    r4 = r1
    r5 = r0  #
    [sp] = r4
    r1 = 0
    r0 = r3
    r3 = r5
    call ir_convolution_installation_limit
    sp += 4
    {pc, r5, r4} = [sp++]

; ir_convolution_prepare: 0x0202962a..0x02029728, module ir-convolution (prepare), ir-processing (prepare)
.type ir_convolution_prepare,@function
ir_convolution_prepare:
    [--sp] = {rets, r13-r4}
    sp += -12
    r11 = r0
    r4 = r0 + 76
    r5 = h[r4+0] (s)
    r7 = r1
    r0 = r7
    r1 = r5
    call ir_convolution_installation_effective
    r9 = r0
    r0 = r7
    r1 = r5
    call ir_convolution_installation_raw_length
    r5 = r0
    if (r7 == 0) goto L0202965e
    r0 = r9
    call ir_convolution_size  ; @call.xl
    r0 = r0 + 3
    r10 = r0 & 0xFFFFFFFC
    goto L02029660
L0202965e:
    r10 = 0
L02029660:
    r12 = L01c32db0
    r1 = [r12+52]
    r6 = -3
    if (r1 == 0) goto L02029676
    r0 = r10
    call r1
    r8 = r0
    if (r0 != 0) goto L0202967c
; HyperRig MINI, product option: the block's convolution of now gives its place to the new one (mini/product/cab.c)
.if MINI_PRODUCT
    r0 = r11
    r1 = r10
    call hyperrig_cab_room
    r8 = r0
    if (r0 != 0) goto L0202967c
.endif
L02029676:
    r0 = r6
    sp += 12
    {pc, r13-r4} = [sp++]
L0202967c:
    [sp] = r9
    r0 = 0
    r6 = 256  #
    [sp+4] = r0
    [sp+8] = r7
    if (r7 != 0) goto L0202968c
    r6 = 128
L0202968c:
    r13 = sp + 0
    if (r9 >= r5) goto L020296b2
    r1 = [r12+68]
    r0 = [r12+80]
    r2 = r7
    call ir_convolution_installation_convert
    r1 = r9 - r0
    if (r9 <= r0) {
    r1 = 0
    }
    r6 = umin(r1, r6)
    goto L020296bc
L020296b2:
    r1 = 0
    r0 = r7
    call ir_convolution_installation_raw_length
    if (r9 >= r0) goto L020296c8
L020296bc:
    r0 = r9 >> 1
    r0 = umin(r6, r0)
    [r13+4] = r0
L020296c8:
    if (r7 == 0) goto L0202971c
    r2 = ir_convolution_produce
    r3 = sp + 0
    r1_r0 = r9_r8
    call ir_convolution_construct  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L0202971c
    r0 = [r4+8]
    if (r0 == 0) goto L020296ea
    r1 = [r12+56]
    if (r1 == 0) goto L020296ea
    call r1
L020296ea:
    [r4+8] = r8
    r0 = r10 >> 1
    r1 = 480  #
    [r4+12] = r0
    [r11+288] = r5
    [r11+292] = r9
    r0 = L01c2c220
    r0 = r11 - r0
    r0 = r0 / r1 (s)
    r1 = L01c343d8
    r6 = 0
    [r1+r0<<2] = r6
    goto L02029676
L0202971c:
    r1 = [r12+56]
    r0 = r8
    call r1
    r6 = -1
    goto L02029676
