; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 1 function, 0x02025cde..0x02025ce8

; phase3_p11_btctler_nv_memory_free: 0x02025cde..0x02025ce8, module phase3-p11 (btctler_nv_memory_free)
.type phase3_p11_btctler_nv_memory_free,@function
phase3_p11_btctler_nv_memory_free:
    [--sp] = rets
    call L0203d218  ; @call.xl
    pc = [sp++]
