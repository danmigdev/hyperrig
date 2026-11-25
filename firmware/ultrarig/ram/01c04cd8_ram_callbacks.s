; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 1 function, 0x01c04cd8..0x01c04cda

; ram_callbacks_empty_hook: 0x01c04cd8..0x01c04cda, module ram-callbacks (empty_hook)
.type ram_callbacks_empty_hook,@function
ram_callbacks_empty_hook:
    rts
