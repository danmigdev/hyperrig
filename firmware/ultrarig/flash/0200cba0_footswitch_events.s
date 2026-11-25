; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 1 function, 0x0200cba0..0x0200cbac

; footswitch_events_bank_of: 0x0200cba0..0x0200cbac, module footswitch-events (bank_of)
.type footswitch_events_bank_of,@function
footswitch_events_bank_of:
    r1 = r0
; HyperRig MINI, product option: three presets to a bank; the callers give no negative number.
.if MINI_PRODUCT
    r0 = 3
    r0 = r1 / r0 (u)
.else
    r0 = r1 >>> 2
.endif
    if (r1 >= 32) {  ; @if.ge.ri.s12
    r0 = 0
    }
    rts
