; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; record_helpers: 1 function, 0x020040f8..0x0200410c

; record_helpers_next_serial: 0x020040f8..0x0200410c, module record-helpers (next_serial)
.type record_helpers_next_serial,@function
record_helpers_next_serial:
    r1 = r0 + 1
    r3 = 65535
    r2 = -1
    if (r0 != r3) {
    r2 = r1
    }
    r0 = r2.l (u)
    rts
