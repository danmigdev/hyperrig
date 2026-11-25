; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_async: 1 function, 0x01c13080..0x01c13082

; capture_async_command_noop: 0x01c13080..0x01c13082, module capture-async (command_noop)
.type capture_async_command_noop,@function
capture_async_command_noop:
    rts
