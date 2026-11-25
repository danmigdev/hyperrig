; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_metadata: 2 functions, 0x020034da..0x02003502

; capture_metadata_erased: 0x020034da..0x020034f2, module capture-metadata (erased)
.type capture_metadata_erased,@function
capture_metadata_erased:
    r2 = 0
L020034dc:
    if (r2 >= r1) goto L020034ee
    r3 = b[r0+r2] (u)
    r2 += 1  ; @add.ri.u5
    if (r3 == 255) goto L020034dc
    r0 = 0
    rts
L020034ee:
    r0 = 1
    rts

; capture_metadata_crc: 0x020034f2..0x02003502, module capture-metadata (crc)
.type capture_metadata_crc,@function
capture_metadata_crc:
    [--sp] = rets
    r2 = r1
    r1 = r0
    r0 = -1
    call preset_storage_crc_update
    r0 = ~r0
    pc = [sp++]
