; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 1 function, 0x02025930..0x02025936

; phase3_p11_hw_dma_free: 0x02025930..0x02025936, module phase3-p11 (hw_dma_free)
.type phase3_p11_hw_dma_free,@function
phase3_p11_hw_dma_free:
    [--sp] = rets
    call L02025902
    pc = [sp++]
