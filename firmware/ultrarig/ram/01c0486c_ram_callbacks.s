; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 1 function, 0x01c0486c..0x01c04882

; ram_callbacks_job_busy: 0x01c0486c..0x01c04882, module ram-callbacks (job_busy)
.type ram_callbacks_job_busy,@function
ram_callbacks_job_busy:
    csync
    r0 = L01c2bff0
    r2 = [r0+24]
    r1 = [r0+20]
    r0 = 1
    if (r2 == r1) {
    r0 = 0
    }
    rts
