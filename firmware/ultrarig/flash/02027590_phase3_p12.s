; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p12: 1 function, 0x02027590..0x02027598

; phase3_p12_att_clear_transaction_queue: 0x02027590..0x02027598, module phase3-p12 (att_clear_transaction_queue)
.type phase3_p12_att_clear_transaction_queue,@function
phase3_p12_att_clear_transaction_queue:
    [--sp] = rets
    r1 = 3
    call L02027536
    pc = [sp++]
