; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_loader: 1 function, 0x02009dd0..0x02009e14

; preset_loader_report: 0x02009dd0..0x02009e14, module preset-loader (report)
.type preset_loader_report,@function
preset_loader_report:
    [--sp] = {rets, r7-r4}
    r4 = 1023
    r5 = L01c26890
    r7 = [r5+r4<<2]
    r4 = r3
    r5 = r1
    r6 = r0
    r0 = r2
    call preset_loader_elapsed
    r1 = 65535
    r0 = umin(r0, r1)
    r1 = r7 - r4
    r2 = 32767
    r1 = umin(r1, r2)
    r1 = r1 << 16
    r2 = r1 | r0
    r0 = r5 << 8
    r1 = r0 | r6
    r0 = 26
    call storage_coordination_notify
    {pc, r7-r4} = [sp++]
