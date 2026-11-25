; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 1 function, 0x02004198..0x020041b8

; flash_helpers_next_page: 0x02004198..0x020041b8, module flash-helpers (next_page)
.type flash_helpers_next_page,@function
flash_helpers_next_page:
    [--sp] = rets
    r3 = r0
    call storage_fault_tag
    r2 = r3 + 4096
    r1 = r3
    if (r0 == 0) goto L020041aa
    r1 = r2
L020041aa:
    r0 = r3 & 0xFF000
    if (r0 != 1044480) {
    r3 = r1
    }
    r0 = r3
    pc = [sp++]
