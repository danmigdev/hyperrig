; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02000ebc..0x02000ed0: vendor code (JieLi SDK or library, not reversed), as instructions
L02000ebc:
    [--sp] = rets
    r2 = L01c00dd0
    r0 = 2
    r1 = 7
    r3 = 0
    call storage_platform_register
    pc = [sp++]
