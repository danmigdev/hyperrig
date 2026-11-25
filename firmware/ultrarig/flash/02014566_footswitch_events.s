; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 1 function, 0x02014566..0x02014578

; footswitch_events_pedal_read: 0x02014566..0x02014578, module footswitch-events (pedal_read)
.type footswitch_events_pedal_read,@function
footswitch_events_pedal_read:
    [--sp] = rets
    r3 = r0
    r0 = 3
    r1 = 2
    r2 = 20000
    call footswitch_events_adc_read
    pc = [sp++]
