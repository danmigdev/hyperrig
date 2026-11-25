; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_platform: 2 functions, 0x02000558..0x02000570

; storage_platform_gate_disable: 0x02000558..0x02000564, module storage-platform (gate_disable)
.type storage_platform_gate_disable,@function
storage_platform_gate_disable:
    r0 = icfg
    r0 &= 4294967039
    icfg = r0
    rts

; storage_platform_gate_enable: 0x02000564..0x02000570, module storage-platform (gate_enable)
.type storage_platform_gate_enable,@function
storage_platform_gate_enable:
    r0 = icfg
    r0 |= 256
    icfg = r0
    rts
