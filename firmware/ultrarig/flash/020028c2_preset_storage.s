; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage: 1 function, 0x020028c2..0x020028f2

; preset_storage_crc_update: 0x020028c2..0x020028f2, module preset-storage (crc_update)
.type preset_storage_crc_update,@function
preset_storage_crc_update:
    [--sp] = {rets, r6-r4}
    r3 = 0
    r4 = 3988292384
    goto L020028ec
L020028ce:
    r5 = b[r1+r3] (u)
    r0 ^= r5
    r5 = 8
    goto L020028e8
L020028d8:
    r6 = r0 & 0x1
    r6 = 0x0 - r6
    r6 &= r4
    r0 = r0 >> 1
    r0 ^= r6
    r5 += -1
L020028e8:
    if (r5 != 0) goto L020028d8
    r3 += 1  ; @add.ri.u5
L020028ec:
    if (r3 != r2) goto L020028ce
    {pc, r6-r4} = [sp++]
