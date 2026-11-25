; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; mode_and_settings: 2 functions, 0x02004a70..0x02004aac

; mode_and_settings_first_callbacks: 0x02004a70..0x02004a8e, module mode-and-settings (first_callbacks)
.type mode_and_settings_first_callbacks,@function
mode_and_settings_first_callbacks:
    r0 = 1046
    r1 = L01c26890
    r2 = 0
    [r1+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
    r2 = ram_callbacks_input_block
    [r1+r0<<2] = r2
    rts

; mode_and_settings_second_callbacks: 0x02004a8e..0x02004aac, module mode-and-settings (second_callbacks)
.type mode_and_settings_second_callbacks,@function
mode_and_settings_second_callbacks:
    r0 = 1048
    r1 = L01c26890
    r2 = 0
    [r1+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
    r2 = ram_callbacks_output_block
    [r1+r0<<2] = r2
    rts
