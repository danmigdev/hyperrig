; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 1 function, 0x0200cb3c..0x0200cb60

; footswitch_events_reload_preset: 0x0200cb3c..0x0200cb60, module footswitch-events (reload_preset)
.type footswitch_events_reload_preset,@function
footswitch_events_reload_preset:
    [--sp] = rets
    r0 = L01c1f180
    r0 = [r0+92]
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    call preset_loader_load
    }
    r0 = 836
    r1 = L01c26890
    r2 = 1
    b[r1+r0] = r2
    pc = [sp++]
