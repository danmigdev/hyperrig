; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; status_snapshot: 1 function, 0x02007324..0x0200733e

; status_snapshot_override_byte: 0x02007324..0x0200733e, module status-snapshot (override_byte)
.type status_snapshot_override_byte,@function
status_snapshot_override_byte:
    ifs (r2 < 0) goto L0200733a
    if (r0 == 255) goto L0200733a
    r3 = L01c1f180
    r3 = b[r3+20] (s)
    if (r3 == r2) goto L0200733c
L0200733a:
    r0 = r1
L0200733c:
    rts
