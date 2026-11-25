; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_dispatch: 3 functions, 0x01c13082..0x01c13088

; capture_dispatch_noop_a: 0x01c13082..0x01c13084, module capture-dispatch (noop_a), capture-live (noop_a), capture-native (noop_a)
.type capture_dispatch_noop_a,@function
capture_dispatch_noop_a:
    rts

; capture_dispatch_noop_b: 0x01c13084..0x01c13086, module capture-dispatch (noop_b), capture-live (noop_b), capture-native (noop_b)
.type capture_dispatch_noop_b,@function
capture_dispatch_noop_b:
    rts

; capture_dispatch_noop_c: 0x01c13086..0x01c13088, module capture-dispatch (noop_c), capture-live (noop_c), capture-native (noop_c)
.type capture_dispatch_noop_c,@function
capture_dispatch_noop_c:
    rts
