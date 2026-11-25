; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 1 function, 0x01c13088..0x01c1308c

; ram_callbacks_zero_stub: 0x01c13088..0x01c1308c, module ram-callbacks (zero_stub)
.type ram_callbacks_zero_stub,@function
ram_callbacks_zero_stub:
    r0 = 0
    rts
