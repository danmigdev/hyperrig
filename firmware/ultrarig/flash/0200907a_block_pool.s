; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; block_pool: 1 function, 0x0200907a..0x02009082

; block_pool_maintain_wrapper: 0x0200907a..0x02009082, module block-pool (maintain_wrapper)
.type block_pool_maintain_wrapper,@function
block_pool_maintain_wrapper:
    [--sp] = rets
    call block_pool_maintain
    pc = [sp++]
