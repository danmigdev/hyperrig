; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_task: 1 function, 0x01c04c42..0x01c04cd8

; audio_task_warmup: 0x01c04c42..0x01c04cd8, module audio-task (warmup)
.type audio_task_warmup,@function
audio_task_warmup:
    [--sp] = {rets, r7-r4}
    sp += -12
    r0 = 0
    r7 = L01c2bff0
    r2 = 3999999
L01c04c54:
    r1 = [r7+8]
    if (r0 > r2) goto L01c04c5e
    r0 = r0 + 1
    if (r1 != 0) goto L01c04c54
L01c04c5e:
    call ir_processing_wait
    r4 = 0
    [sp+8] = r4
    r0 = 0
    r1 = 0
    [sp] = r0
    [sp+4] = r1
    r0 = r7 + 76
    r1 = sp + 0
    call capture_live_warmup
    [r7+52] = r4
    r5 = [sp+8]
    r2 = [sp]
    r3 = [sp+4]
    b[r7+56] = r4
    b[r7+60] = r4
    r6 = L01c2a8e0
L01c04c8e:
    r0 = r4 << 2
    r0 = r0 + r6
    r1 = r0 + 1524
    [r1+0] = r2
    [r0+0] = r2
    [r1+4] = r3
    [r0+4] = r3
    [r1+8] = r5
    r4 = r4 + 3
    [r0+8] = r5
    if (r4 < 381) goto L01c04c8e
    r0 = L01c1f7c8
    r0 = [r0+0]
    r1 = 0
    if (r0 == 0) goto L01c04cd2
    r0 = b[r7+79] (u)
    r0 += -1
    r0 = r0.b0 (u)
    if (r0 > 63) goto L01c04cd2
    r0 = b[r7+133] (s)
    ifs (r0 < 1) goto L01c04cd2
    r0 = [r7+144]
    r1 = 1
    if (r0 != 0) goto L01c04cd2
    r1 = r0
L01c04cd2:
    [r7+12] = r1
    sp += 12
    {pc, r7-r4} = [sp++]
