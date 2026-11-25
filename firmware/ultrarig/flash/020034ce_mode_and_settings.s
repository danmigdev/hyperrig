; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; mode_and_settings: 1 function, 0x020034ce..0x020034da

; mode_and_settings_record_read: 0x020034ce..0x020034da, module mode-and-settings (record_read)
.type mode_and_settings_record_read,@function
mode_and_settings_record_read:
    [--sp] = rets
    r0 = r0 + 0xFE000
    call storage_control_read
    pc = [sp++]
