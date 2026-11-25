; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 1 function, 0x0200c9a4..0x0200c9c2

; footswitch_events_colour_word: 0x0200c9a4..0x0200c9c2, module footswitch-events (colour_word)
.type footswitch_events_colour_word,@function
footswitch_events_colour_word:
    [--sp] = rets
    r1 = L01c26890
    r2 = h[r1+78] (u)
    r1 = r0
    if (r2 == 0) goto L0200c9be
    r0 = r2
    call command_services_colour_bytes
    r0 = 1
    pc = [sp++]
L0200c9be:
    r0 = 0
    pc = [sp++]
