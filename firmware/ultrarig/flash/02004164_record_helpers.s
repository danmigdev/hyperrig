; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; record_helpers: 1 function, 0x02004164..0x02004198

; record_helpers_checksum: 0x02004164..0x02004198, module record-helpers (checksum)
.type record_helpers_checksum,@function
record_helpers_checksum:
    [--sp] = {rets, r6-r4}
    r2 = 0
    r3 = -1
    r4 = 3988292384
    goto L02004190
L02004172:
    r5 = b[r0+r2] (u)
    r3 ^= r5
    r5 = 8
    goto L0200418c
L0200417c:
    r6 = r3 & 0x1
    r6 = 0x0 - r6
    r6 &= r4
    r3 = r3 >> 1
    r3 ^= r6
    r5 += -1
L0200418c:
    if (r5 != 0) goto L0200417c
    r2 += 1  ; @add.ri.u5
L02004190:
    if (r2 != r1) goto L02004172
    r0 = ~r3
    {pc, r6-r4} = [sp++]
