; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_task: 1 function, 0x01c05118..0x01c05160

; audio_task_effect_scan: 0x01c05118..0x01c05160, module audio-task (effect_scan)
.type audio_task_effect_scan,@function
audio_task_effect_scan:
    [--sp] = {rets, r4}
    r1 = 0
    r2 = L01c2c220
    r4 = L01c32db0
L01c05128:
    r3 = b[r2+0] (u)
    if (r3 != 28) goto L01c0513e
    r3 = b[r2+2] (u)
    if (r3 == 0) goto L01c0513e
    r3 = b[r2+1] (u)
    if (r3 != 0) goto L01c0514e
    r3 = h[r2+8] (u)
    if (r3 != 0) goto L01c0514e
    r3 = b[r2+10] (u)
    if (r3 != 0) goto L01c0514e
L01c0513e:
    r1 = r1 + 1
    r2 = r2 + 480
    ifs (r1 < 16) goto L01c05128
    r0 = 0
    b[r4+0] = r0
    {pc, r4} = [sp++]
L01c0514e:
    r1 = r4 + 416
    r2 = 8
    call sample_leaves_chunk_peaks  ; @call.xl
    r0 = 1
    b[r4+0] = r0
    {pc, r4} = [sp++]
