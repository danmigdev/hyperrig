; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_relocation: 1 function, 0x01c05ffa..0x01c06004

; effect_relocation_rebase: 0x01c05ffa..0x01c06004, module effect-relocation (rebase)
.type effect_relocation_rebase,@function
effect_relocation_rebase:
    r1 = r0 - r1
    r1 = r1 + r2
    if (r0 == 0) goto L01c06002
    r0 = r1
L01c06002:
    rts
