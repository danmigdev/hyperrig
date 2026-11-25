; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 1 function, 0x0201fddc..0x0201fde4

; phase3_p8_btif_buf_read: 0x0201fddc..0x0201fde4, module phase3-p8 (btif_buf_read)
.type phase3_p8_btif_buf_read,@function
phase3_p8_btif_buf_read:
    [--sp] = rets
    call phase3_p8_memcpy_flash
    pc = [sp++]
