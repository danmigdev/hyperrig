; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_transition: 1 function, 0x02028936..0x02028968

; dsp_transition_clamp: 0x02028936..0x02028968, module dsp-transition (clamp), dsp-transition-notification (transition_clamp)
.type dsp_transition_clamp,@function
dsp_transition_clamp:
    r2 = r0
    r0 = -240
    if (r2 == 0) goto L02028940
    r0 += 120
L02028940:
    r3 = r1
    ifs (r1 >= 120) {
    r3 = 120
    }
    ifs (r0 <= r1) {
    r0 = r3
    }
    if (r2 != 5) goto L02028966
    r1 = r0 >>> 31
    r1 = r1 & 0xFFFFFFFC
    r1 |= 2
    r0 = r0 + r1
    r1 = 5
    r0 = r0 / r1 (s)
    r0 = r0 * 0x5
L02028966:
    rts
