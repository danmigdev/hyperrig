; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_pause: 1 function, 0x020307ea..0x02030838

; audio_pause_drop_idle_queued: 0x020307ea..0x02030838, module audio-pause (drop_idle_queued)
.type audio_pause_drop_idle_queued,@function
audio_pause_drop_idle_queued:
    [--sp] = {rets, r8-r4}
    r4 = L01c32db0
    r1 = b[r4+8] (u)
    if (r1 == 0) goto L02030832
    r8 = 0
    r7 = L01c2c220
    r5 = 0
    r6 = 0
    goto L02030810
L02030804:
    b[r2+3] = r8
    call effect_ownership_remove
    r1 = b[r4+8] (u)
    goto L02030828
L02030810:
    r0 = r6 + r4
    r0 = b[r0+88] (u)
    r2 = r0 * 0x1E0
    r2 = r2 + r7
    r3 = h[r2+8] (u)
    if (r3 == 0) goto L02030804
    r2 = r5 + r4
    b[r2+88] = r0
    r5 = r5 + 1
L02030828:
    r6 = r6 + 1
    r0 = r1.b0 (u)
    ifs (r6 < r0) goto L02030810
    goto L02030834
L02030832:
    r5 = 0
L02030834:
    b[r4+8] = r5
    {pc, r8-r4} = [sp++]
