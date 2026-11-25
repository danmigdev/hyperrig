; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_measurement: 1 function, 0x02030838..0x0203086a

; audio_measurement_queued_idle: 0x02030838..0x0203086a, module audio-measurement (queued_idle)
.type audio_measurement_queued_idle,@function
audio_measurement_queued_idle:
    [--sp] = {rets, r4}
    r0 = L01c32db0
    r1 = b[r0+8] (u)
    if (r1 == 0) goto L02030862
    r2 = 0
    r3 = L01c2c220
L0203084c:
    r4 = r2 + r0
    r4 = b[r4+88] (u)
    r4 = r4 * 0x1E0
    r4 = r4 + r3
    r4 = h[r4+8] (u)
    if (r4 == 0) goto L02030866
    r2 = r2 + 1
    ifs (r2 < r1) goto L0203084c
L02030862:
    r0 = 0
    {pc, r4} = [sp++]
L02030866:
    r0 = 1
    {pc, r4} = [sp++]
