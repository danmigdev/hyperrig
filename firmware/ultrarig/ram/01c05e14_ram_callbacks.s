; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 3 functions, 0x01c05e14..0x01c05e7e

; ram_callbacks_mode_class: 0x01c05e14..0x01c05e24, module ram-callbacks (mode_class)
.type ram_callbacks_mode_class,@function
ram_callbacks_mode_class:
    ifs (r0 < 1) {
    r0 = 0
    rts
    }
    if (r0 != 1) {
    r0 = 3
    }
    rts

; ram_callbacks_mode_value: 0x01c05e24..0x01c05e5e, module ram-callbacks (mode_value)
.type ram_callbacks_mode_value,@function
ram_callbacks_mode_value:
    r1 = r0
    r2 = r1 + -3
    r0 = -1
    if (r2 > 20) goto L01c05e5c
    r3 = 2089153
    r3 >>= r2
    if ((r3 & 1) == 0) goto L01c05e5c
    r0 = effect_support_selector
    r0 = [r0+r2<<2]
    r0 = r0 * 0xC
    r1 = r1 * 0x54
    r0 = r0 + r1
    r1 = effect_parameter_metadata
    r0 = r0 + r1
    r0 = h[r0+2] (s)
L01c05e5c:
    rts

; ram_callbacks_mode_width: 0x01c05e5e..0x01c05e7e, module ram-callbacks (mode_width)
.type ram_callbacks_mode_width,@function
ram_callbacks_mode_width:
    r1 = r0
    ifs (r1 < 1) {
    r0 = 0
    rts
    }
    r3 = r1 | 0x1
    r0 = 9
    r2 = 9
    if (r3 != 3) {
    r2 = 12
    }
    if (r1 != 1) {
    r0 = r2
    }
    rts
