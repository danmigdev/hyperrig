; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_transition_notification: 1 function, 0x0201a9ea..0x0201aa08

; dsp_transition_notification_notify: 0x0201a9ea..0x0201aa08, module dsp-transition-notification (notify)
.type dsp_transition_notification_notify,@function
dsp_transition_notification_notify:
    [--sp] = rets
    r1 = 5
    r0 = r0 / r1 (s)
    call capture_loader_clamp
    r1 = L01c26890
    [r1+268] = r0
    r0 = 0
    call capture_loader_mix
    pc = [sp++]
