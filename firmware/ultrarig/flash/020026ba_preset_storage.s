; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage: 1 function, 0x020026ba..0x020026d6

; preset_storage_block: 0x020026ba..0x020026d6, module preset-storage (block)
.type preset_storage_block,@function
preset_storage_block:
    r2 = 0xDD000
    if (r0 != 16) {  ; @if.ne.ri.s12
    r2 = 0xDE000
    }
    r1 = r0 << 12
    r1 = r1 + 0xBF000
    if (r0 >= 16) {  ; @if.ge.ri.s12
    r1 = r2
    }
    r0 = r1
    rts
