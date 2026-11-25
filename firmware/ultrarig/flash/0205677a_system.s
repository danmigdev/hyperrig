; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0205677a..0x02056780: data
    .fill ((26 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0205677a:
    .byte 0x00,0x00,0x00,0x00,0x00,0x00
