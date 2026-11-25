; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_task: 1 function, 0x01c05d40..0x01c05d4a

; audio_task_set_input: 0x01c05d40..0x01c05d4a, module audio-task (set_input)
.type audio_task_set_input,@function
audio_task_set_input:
    r1 = L01c32db0
    [r1+48] = r0
    rts
