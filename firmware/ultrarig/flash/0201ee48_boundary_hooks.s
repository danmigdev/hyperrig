; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; boundary_hooks: 1 function, 0x0201ee48..0x0201ee6e

; boundary_hooks_default_event: 0x0201ee48..0x0201ee6e, module boundary-hooks (default_event)
.type boundary_hooks_default_event,@function
boundary_hooks_default_event:
    [--sp] = rets
    r1 = h[r0+0] (u)
    if (r1 != 16) goto L0201ee6c
    r1 = b[r0+2] (u)
    if (r1 != 3) goto L0201ee6c
    r0 = b[r0+4] (u)
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = L01c26890
    r1 = 1
    b[r0+60] = r1
    call console_helpers_ble_advertise
    }
L0201ee6c:
    pc = [sp++]
