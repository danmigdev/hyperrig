; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_dispatch: 1 function, 0x01c1308c..0x01c1308e

; capture_dispatch_noop_d: 0x01c1308c..0x01c1308e, module capture-dispatch (noop_d), capture-live (noop_d), capture-native (noop_d)
.type capture_dispatch_noop_d,@function
capture_dispatch_noop_d:
    rts
