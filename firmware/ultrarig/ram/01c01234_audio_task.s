; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_task: 2 functions, 0x01c01234..0x01c012d8

; audio_task_fir: 0x01c01234..0x01c01292, module audio-task (fir)
.type audio_task_fir,@function
audio_task_fir:
    [--sp] = {rets, r11-r4}
    r8 = r1
    r9 = r0
    r0 = r1 & 0xFFFFFFFE
    r0 = h[r9+r0] (s)
    r11 = [sp+36]  ; @ld.w.sp.l
    r10 = r1 >>> 1
    r5 = r3 + -1
    r1 = r5 - r10
    r1 = r1 & r11
    r1 = [r2+r1<<2]
    r1_r0 = r1 * r0 (s)
    r8 = r3 - r8
    r4 = 0
    goto L01c01288
L01c01266:
    r7 = r5 & r11
    r7 = [r2+r7<<2]
    r3 = r8 + r4
    r3 = r3 & r11
    r3 = [r2+r3<<2]
    r6 = h[r9+r4<<1] (s)
    r3 += r7  ; @add.rr
    r1_r0 += r3 * r6 (s)
    r5 += -1
    r4 += 1  ; @add.ri.u5
L01c01288:
    ifs (r4 < r10) goto L01c01266
    r1_r0 >>= 15
    {pc, r11-r4} = [sp++]

; audio_task_tap: 0x01c01292..0x01c012d8, module audio-task (tap)
.type audio_task_tap,@function
audio_task_tap:
    [--sp] = {rets, r6-r4}
    r2 = L01c26890
    r3 = b[r2+25] (u)
    if (r3 != r0) goto L01c012d6
    r0 = r2
    r3 = [++r0=456]
    r4 = [r0+8]
    r0 = [r0+4]
    if (r3 == 0) goto L01c012d6
    if (r4 <= r0) goto L01c012d6
    r5 = r0 << 2
    r3 += r5  ; @add.rr
    r4 = r4 - r0
    if (r4 >= 128) {  ; @if.ge.ri.s12
    r4 = 128
    }
    r5 = 0
    goto L01c012cc
L01c012c2:
    r6 = [r1+r5<<2]
    [r3+r5<<2] = r6
    r5 += 1  ; @add.ri.u5
L01c012cc:
    if (r5 < r4) goto L01c012c2
    r0 += r4  ; @add.rr
    [r2+460] = r0
L01c012d6:
    {pc, r6-r4} = [sp++]
