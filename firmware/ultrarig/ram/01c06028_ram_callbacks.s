; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 1 function, 0x01c06028..0x01c06038

; ram_callbacks_aligned_size: 0x01c06028..0x01c06038, module ram-callbacks (aligned_size)
.type ram_callbacks_aligned_size,@function
ram_callbacks_aligned_size:
    if (r0 != 0) {
    r0 = r0 << 1
    r0 = r0 + 18
    r0 = r0 & 0xFFFFFFFC
    } else {
    r0 = 0
    }
    rts
