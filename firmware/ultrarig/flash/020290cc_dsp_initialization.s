; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_initialization: 3 functions, 0x020290cc..0x02029204

; dsp_initialization_reset_slot: 0x020290cc..0x02029112, module dsp-initialization (reset_slot), dsp-transition-notification (initialization_reset_slot)
.type dsp_initialization_reset_slot,@function
dsp_initialization_reset_slot:
    [--sp] = {rets, r6-r4}
    r2 = 0
    r3 = L01c2e5a0
    r1 = L01c32db0
    r4 = 0
L020290de:
    r5 = r4 + r1
    r6 = b[r5+210] (u)
    if (r6 == 0) goto L020290f8
    r6 = b[r3+1] (u)
    if (r6 != r0) goto L020290f8
    b[r3+0] = r2
    r6 = b[r3+4] (u)
    r6 = r6 + 1
    b[r3+4] = r6
    b[r5+210] = r2
L020290f8:
    r4 = r4 + 1
    r3 = r3 + 448
    if (r4 != 8) goto L020290de
    if (r0 < 16) {
    r0 = r0 + r1
    r1 = 316
    b[r0+r1] = r2
    }
    {pc, r6-r4} = [sp++]

; dsp_initialization_initialize: 0x02029112..0x020291f8, module dsp-initialization (initialize), dsp-transition-notification (initialization_initialize)
.type dsp_initialization_initialize,@function
dsp_initialization_initialize:
    [--sp] = {rets, r14-r4}
    r2 = L01c1f7f0
    [r2+8] = r0
    r13 = L01c32db0
    [r13+48] = r1
    r6 = L01c2c222
    r7 = 0
    r8 = L01c343d8
    r4 = 0
L02029136:
    r0 = r4
    call dsp_initialization_reset_slot
    b[r6+0] = r7
    [r8+r4<<2] = r7
    r4 = r4 + 1
    r6 = r6 + 480
    if (r4 != 16) goto L02029136
    r0 = L01c3443c
    r4 = 0
    [r0+0] = r4
    b[r13+6] = r4
    [r13+24] = r4
    call dsp_initialization_reset_filters
    b[r13+15] = r4
    b[r13+14] = r4
    r11 = L01c32fa0
    r14 = 0x8000
    r12 = 255
    r9_r8 = 0
    r10 = 0
L0202917a:
    r3 = 3
    r7_r6 = r9_r8
L0202917e:
    r0 = r13 + 230
    r2 = r0 + 140
    h[r2+r7<<1] = r4
    r2 = r0 + 138
    h[r2+r7<<1] = r4
    r2 = r7 << 2
    r2 += r11
    [r2+4] = r14
    [r2+0] = r14
    r2 = r6 + r13
    r5 = r2 + 174
    r1 = r0 + 162  #
    b[r5+0] = r4
    b[r5+6] = r12
    [r1+r6<<2] = r4
    b[r5+12] = r4
    b[++r2=192] = r4
    b[r2+6] = r4
    h[r0+r6<<1] = r4
    b[r2+12] = r4
    r6 = r6 + 1
    r7 = r7 + 2
    if (--r3 != 0) goto L0202917e
    r8 = r8 + 3
    r10 = r10 + 1
    r9 = r9 + 6
    if (r10 != 2) goto L0202917a
    r0 = 0
    b[r13+7] = r0
    r1 = -2
    r2 = 1
L020291e4:
    r3 = r1 + r13
    b[++r3=18] = r0
    b[r3+2] = r0
    b[r3+4] = r2
    r1 = r1 + 1
    r2 = r2 + 1
    if (r1 != 0) goto L020291e4
    {pc, r14-r4} = [sp++]

; dsp_initialization_bind: 0x020291f8..0x02029204, module dsp-initialization (bind), dsp-transition-notification (initialization_bind)
.type dsp_initialization_bind,@function
dsp_initialization_bind:
    r2 = L01c32db0
    [r2+52] = r0
    [r2+56] = r1
    rts
