; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x01c065a4..0x01c065b4

; effect_setup_buffer_selector: 0x01c065a4..0x01c065b4, module effect-setup (buffer_selector)
.type effect_setup_buffer_selector,@function
effect_setup_buffer_selector:
    r2 = r1 << 2
    r2 = r2 + r0
    r2 += 88
    r0 += 84
    if (r1 == 0) goto L01c065b0
    r0 = r2
L01c065b0:
    r0 = [r0+0]
    rts
