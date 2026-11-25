; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_pause: 1 function, 0x01c04882..0x01c048a4

; audio_pause_queue_drained: 0x01c04882..0x01c048a4, module audio-pause (queue_drained)
.type audio_pause_queue_drained,@function
audio_pause_queue_drained:
    csync
    r2 = L01c2bff0
    r1 = [r2+16]
    r0 = [r2+24]
    if (r1 == r0) goto L01c04896
    [r2+32] = r1
    csync
L01c04896:
    r3 = [r2+24]
    r1 = [r2+20]
    r0 = 1
    if (r3 != r1) {
    r0 = 0
    }
    rts
