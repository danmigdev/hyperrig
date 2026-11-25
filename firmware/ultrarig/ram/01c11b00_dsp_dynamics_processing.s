; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_dynamics_processing: 4 functions, 0x01c11b00..0x01c11d06

; dsp_dynamics_processing_reset: 0x01c11b00..0x01c11bfa, module dsp-dynamics-processing (reset)
.type dsp_dynamics_processing_reset,@function
dsp_dynamics_processing_reset:
    r0 = L01c1f7f0
    r2 = 0
    r3 = 0
    [r0+48] = r2
    [r0+52] = r3
    [r0+56] = r2
    [r0+60] = r3
    [r0+64] = r2
    [r0+68] = r3
    [r0+72] = r2
    [r0+76] = r3
    [r0+80] = r2
    [r0+84] = r3
    [r0+88] = r2
    [r0+92] = r3
    [r0+96] = r2
    [r0+100] = r3
    [r0+104] = r2
    [r0+108] = r3
    [r0+112] = r2
    [r0+116] = r3
    [r0+120] = r2
    [r0+124] = r3
    [r0+128] = r2
    [r0+132] = r3
    [r0+136] = r2
    [r0+140] = r3
    [r0+144] = r2
    [r0+148] = r3
    [r0+152] = r2
    [r0+156] = r3
    [r0+160] = r2
    [r0+164] = r3
    [r0+168] = r2
    [r0+172] = r3
    [r0+176] = r2
    [r0+180] = r3
    [r0+184] = r2
    [r0+188] = r3
    [r0+192] = r2
    [r0+196] = r3
    [r0+200] = r2
    [r0+204] = r3
    [r0+208] = r2
    [r0+212] = r3
    [r0+216] = r2
    [r0+220] = r3
    [r0+224] = r2
    [r0+228] = r3
    [r0+232] = r2
    [r0+236] = r3
    r2 = r2 + 0x1000000
    r3 = r2
    [r0+240] = r2
    [r0+244] = r3
    [r0+248] = r2
    [r0+252] = r3
    [r0+256] = r2
    [r0+260] = r3
    [r0+264] = r2
    [r0+268] = r3
    r3 = 0
    [r0+272] = r2
    [r0+276] = r3
    r1 = 0
    [r0+280] = r1
    rts

; dsp_dynamics_processing_single: 0x01c11bfa..0x01c11c66, module dsp-dynamics-processing (single)
.type dsp_dynamics_processing_single,@function
dsp_dynamics_processing_single:
    [--sp] = {rets, r6-r4}
    r5 = L01c32db0
    r2 = [r5+108]
    r4 = r0
    r6 = L01c1f7f0
    if (r2 == r1) goto L01c11c32
    r2 = [r6+24]
    r3 = 0
    r3_r2 <<= 16
    r3_r2 = r3_r2 / r1 (u)
    r0 = r2 << 3
    r2 = r2 >> 24
    if (r2 == 0) goto L01c11c2a
    r0 = 134217720
L01c11c2a:
    [r5+116] = r0
    [r5+108] = r1
L01c11c32:
    r2 = [r5+116]
    r0 = r6 + 48  #
    r3 = [r6+28]
    r1 = r4
    call dsp_dynamics_processing_kernel  ; @call.xl
    r0 = [r6+284]
    if (r0 == 0) goto L01c11c64
    r0 = [r5+112]
    r1 = [r6+32]
    r2 = [r6+284]
    r0 = r0 + r2
    [r5+112] = r0
    r0 = [r6+288]
    r0 = smin(r1, r0)
    [r6+32] = r0
L01c11c64:
    {pc, r6-r4} = [sp++]

; dsp_dynamics_processing_clone: 0x01c11c66..0x01c11c7e, module dsp-dynamics-processing (clone)
.type dsp_dynamics_processing_clone,@function
dsp_dynamics_processing_clone:
    [--sp] = rets
    r1 = L01c1f820
    r0 = L01c1f920
    r2 = 61
    call dsp_stage_copy  ; @call.xl
    pc = [sp++]

; dsp_dynamics_processing_dual: 0x01c11c7e..0x01c11d06, module dsp-dynamics-processing (dual)
.type dsp_dynamics_processing_dual,@function
dsp_dynamics_processing_dual:
    [--sp] = {rets, r6-r4}
    r5 = L01c32db0
    r2 = [r5+108]
    r4 = r0
    r6 = L01c1f7f0
    if (r2 == r1) goto L01c11cf0
    r0 = [r5+108]
    if (r0 == r1) goto L01c11cbe
    r2 = [r6+24]
    r3 = 0
    r3_r2 <<= 16
    r3_r2 = r3_r2 / r1 (u)
    r0 = r2 << 3
    r2 = r2 >> 24
    if (r2 == 0) goto L01c11cb6
    r0 = 134217720
L01c11cb6:
    [r5+116] = r0
    [r5+108] = r1
L01c11cbe:
    r2 = [r5+116]
    r0 = r6 + 48  #
    r3 = [r6+28]
    r1 = r4
    call dsp_dynamics_processing_kernel  ; @call.xl
    r0 = [r6+284]
    if (r0 == 0) goto L01c11cf0
    r0 = [r5+112]
    r1 = [r6+32]
    r2 = [r6+284]
    r0 = r0 + r2
    [r5+112] = r0
    r0 = [r6+288]
    r0 = smin(r1, r0)
    [r6+32] = r0
L01c11cf0:
    r2 = [r5+116]
    r1 = r4  #
    r3 = [r6+28]
    r0 = L01c1f920
    call dsp_dynamics_processing_kernel  ; @call.xl
    {pc, r6-r4} = [sp++]
