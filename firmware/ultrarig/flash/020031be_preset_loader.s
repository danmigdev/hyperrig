; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_loader: 1 function, 0x020031be..0x020031d4

; preset_loader_elapsed: 0x020031be..0x020031d4, module preset-loader (elapsed)
.type preset_loader_elapsed,@function
preset_loader_elapsed:
    [--sp] = {rets, r4}
    r4 = r0
    call storage_platform_clock  ; @call.xl
    r2 = r0 - r4
    call preset_application_rate
    r0 = r2 / r0 (u)
    {pc, r4} = [sp++]
