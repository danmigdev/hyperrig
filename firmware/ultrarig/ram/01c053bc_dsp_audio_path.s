; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_audio_path: 3 functions, 0x01c053bc..0x01c0558c

; dsp_audio_path_update: 0x01c053bc..0x01c05406, module dsp-audio-path (update), dsp-transition-notification (audio_update)
.type dsp_audio_path_update,@function
dsp_audio_path_update:
    [--sp] = {rets, r4}
    r2 = 0
    r1 = L01c33058
    r0 = L01c33190
L01c053cc:
    r3 = r1 + 136
    r3 = [r3+r2<<2]
    [r0+r2<<2] = r3
    r2 = r2 + 1
    if (r2 != 44) goto L01c053cc
    r2 = 0
L01c053e0:
    r3 = r2 + r0  #
    r4 = b[r1+0] (u)
    r3 = b[r3+168] (u)
    r3 |= r4
    r2 = r2 + 1
    b[r1++=44] = r3
    if (r2 != 4) goto L01c053e0
    r0 = [r0+172]
    r1 = L01c32db0
    [r1+32] = r0
    r0 = 0
    b[r1+1] = r0
    {pc, r4} = [sp++]

; dsp_audio_path_block: 0x01c05406..0x01c054a6, module dsp-audio-path (block), dsp-transition-notification (audio_block)
.type dsp_audio_path_block,@function
dsp_audio_path_block:
    [--sp] = {rets, r11-r4}
    r8 = r2
    r5 = r1
    r6 = r0
    r0 = r5 << 2
    r0 = r0 + r6
    r10 = r0 + -8
    r11 = r5 + -1
    r9 = 0
    r7 = L01c32fa0
    r4 = 0
L01c05424:
    r0 = r4 + r7
    r1 = b[r0+184] (u)
    if (r1 == 0) goto L01c05444
    r1 = b[r0+185] (u)
    if (r1 == 0) goto L01c05464
    if (r5 == 0) goto L01c05474
    r2 = r0 + 144
    r0 = r6
    r1 = r5
    call biquad_residual  ; @call.xl
    goto L01c05474
L01c05444:
    r0 = r0 + 164
    r1 = r10
    if (r5 <= 1) {
    r1 = r0
    }
    r2 = [r6+r11<<2]
    r1 = [r1+0]
    [r0+0] = r2
    [r0+8] = r2
    [r0+4] = r1
    [r0+12] = r1
    [r0+16] = r9
    goto L01c05474
L01c05464:
    if (r5 == 0) goto L01c05474
    r2 = r0 + 144
    r0 = r6
    r1 = r5
    call biquad_rounded  ; @call.xl
L01c05474:
    r4 += 44
    if (r4 != 176) goto L01c05424
    r0 = L01c1f7d4
    r0 = [r0+0]
    if (r0 != r8) goto L01c05490
    if (r8 == 65536) goto L01c054a4
    r3 = 0
    goto L01c05498
L01c05490:
    r0 = r0 - r8
    r3 = r0 / r5 (s)
L01c05498:
    r0 = r6
    r1 = r5
    r2 = r8
    call dsp_audio_path_ramp  ; @call.xl
L01c054a4:
    {pc, r11-r4} = [sp++]

; dsp_audio_path_process: 0x01c054a6..0x01c0558c, module dsp-audio-path (process), dsp-transition-notification (audio_process)
.type dsp_audio_path_process,@function
dsp_audio_path_process:
    [--sp] = {rets, r15-r4}
    sp += -8
    r4 = r1  #
    [sp+4] = r0
    if (r4 == 0) goto L01c05588
    r11 = L01c32db0
    r0 = b[r11+28] (u)
    if ((r0 & 1) == 0) goto L01c05588
    r0 = b[r11+1] (u)
    if (r0 == 0) goto L01c054c8
    call dsp_audio_path_update
L01c054c8:
    r0 = [r11+32]
    r5 = L01c1f7d4
    if (r0 == 0) goto L01c0557e
    r14 = 0  #
    [sp] = r4
    r12 = L01c32fa0
    r13 = L01c33190
    goto L01c0551e
L01c054e6:
    r5 = L01c1f7d4
    r3 = [r5+0]
    r4 = [r13+164]
    r3 = r3 + r4
    if (r0 == 1) {
    r3 = [r13+160]
    }
    r4 = [sp]
    [r5+0] = r3
    r0 += -1
    [r11+32] = r0
L01c05506:
    r0 = r14 << 2  #
    r3 = [sp+4]
    r0 = r0 + r3
    call dsp_audio_path_block
    r14 = r14 + 32
    if (r14 >= r4) goto L01c05588
    r0 = [r11+32]
L01c0551e:
    r1 = r4 - r14
    if (r1 >= 32) {
    r1 = 32
    }
    r2 = [r5+0]
    if (r0 == 0) goto L01c05506
    r15 = r12 + 144
    r10 = 0
    r9 = r13
L01c05534:
    r7 = 5
    r3 = r15
    r5 = r9
L01c0553a:
    r6 = [r3+0]
    if (r0 != 1) {
    r4 = [r5+80]
    r8 = r4 + r6
    } else {
    r8 = [r5+0]
    }
    [r3++=4] = r8
    r5 = r5 + 4
    if (--r7 != 0) goto L01c0553a
    if (r0 != 1) goto L01c0556c
    r3 = r10 + r13
    r3 = b[r3+168] (u)
    r4 = r10 * 0x2C
    r4 += r12
    b[r4+184] = r3
L01c0556c:
    r15 = r15 + 44
    r10 = r10 + 1
    r9 = r9 + 20
    if (r10 != 4) goto L01c05534
    goto L01c054e6
L01c0557e:
    r1 = r4  #
    r2 = [r5+0]
    r0 = [sp+4]
    call dsp_audio_path_block
L01c05588:
    sp += 8
    {pc, r15-r4} = [sp++]
