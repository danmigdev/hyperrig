; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 1 function, 0x0201453a..0x02014566

; panel_inputs_pedal_pins: 0x0201453a..0x02014566, module panel-inputs (pedal_pins)
.type panel_inputs_pedal_pins,@function
panel_inputs_pedal_pins:
    r0 = 327752
    [r0+72] &= 0xFFFFFE3F
    [r0+76] &= 0xFFFFFE3F
    [r0+56] &= 0xFFFFFE3F
    [r0+68] |= 0x1C0
    [r0+64] &= 0xFFFFFE3F
    [r0+8] &= 0xFFFFFFFD
    [r0+12] &= 0xFFFFFFFD
    [r0+4] &= 0xFFFFFFFD
    [r0+0] |= 0x2
    rts
