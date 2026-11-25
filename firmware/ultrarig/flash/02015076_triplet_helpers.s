; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; triplet_helpers: 1 function, 0x02015076..0x0201508c

; triplet_helpers_mark_record: 0x02015076..0x0201508c, module triplet-helpers (mark_record)
.type triplet_helpers_mark_record,@function
triplet_helpers_mark_record:
    [--sp] = {rets, r4}
    r4 = 1
    if (r3 != 0) goto L0201507e
    r4 = r3
L0201507e:
    b[r0+0] = r4
    b[r0+1] = r1
    if (r3 != 0) goto L02015086
    r1 = -1
L02015086:
    b[r0+2] = r1
    h[r0+4] = r2
    {pc, r4} = [sp++]
