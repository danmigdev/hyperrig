; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_relocation: 2 functions, 0x01c05eec..0x01c05f1c

; effect_relocation_rebase_within: 0x01c05eec..0x01c05f12, module effect-relocation (rebase_within)
.type effect_relocation_rebase_within,@function
effect_relocation_rebase_within:
    [--sp] = {rets, r4}
    r2 = r2 + r1
    r4 = r0 - r1
    r4 = r4 + r3
    r3 = r0
    if (r0 == 0) goto L01c05efa
    r3 = r4
L01c05efa:
    r4 = r0
    if (r0 >= r1) {
    r4 = r3
    }
    r1 = r0
    if (r0 == 0) goto L01c05f08
    r1 = r4
L01c05f08:
    if (r2 <= r0) {
    r1 = r0
    }
    r0 = r1
    {pc, r4} = [sp++]

; effect_relocation_has_layout: 0x01c05f12..0x01c05f1c, module effect-relocation (has_layout)
.type effect_relocation_has_layout,@function
effect_relocation_has_layout:
    r1 = [r0+40]
    r0 = 1
    if (r1 != 0) goto L01c05f1a
    r0 = r1
L01c05f1a:
    rts
