; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sample_leaves: 1 function, 0x01c048a4..0x01c048c2

; sample_leaves_capture_idle: 0x01c048a4..0x01c048c2, module sample-leaves (capture_idle)
.type sample_leaves_capture_idle,@function
sample_leaves_capture_idle:
    csync
    r2 = L01c2bff0
    r0 = [r2+8]
    r1 = 0
    if (r0 != 0) goto L01c048be
    r3 = [r2+24]
    r0 = [r2+20]
    r1 = 1
    if (r3 != r0) {
    r1 = 0
    }
L01c048be:
    r0 = r1
    rts
