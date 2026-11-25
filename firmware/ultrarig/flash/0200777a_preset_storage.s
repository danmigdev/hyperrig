; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage: 1 function, 0x0200777a..0x020077aa

; preset_storage_address: 0x0200777a..0x020077aa, module preset-storage (address)
.type preset_storage_address,@function
preset_storage_address:
    [--sp] = rets
    r3 = r0
    r0 = 0
    if (r3 > 31) goto L020077a8
    r1 = r3 >> 1
    r2 = L01c26890
    r1 += r2  ; @add.rr
    r2 = 3476
    r1 = b[r1+r2] (s)
    ifs (r1 < 0) goto L020077a8
    r0 = r1
    call preset_storage_block
    r1 = r3 << 11
    r1 = r1 & 0x800
    r0 += r1  ; @add.rr
L020077a8:
    pc = [sp++]
