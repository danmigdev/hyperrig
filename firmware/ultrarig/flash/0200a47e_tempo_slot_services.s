; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tempo_slot_services: 1 function, 0x0200a47e..0x0200a4b2

; tempo_slot_services_tempo_command: 0x0200a47e..0x0200a4b2, module tempo-slot-services (tempo_command)
.type tempo_slot_services_tempo_command,@function
tempo_slot_services_tempo_command:
    [--sp] = {rets, r5, r4}
    r1 = L01c26890
    r1 = [r1+280]
    r4 = r0
    if (r1 != 2) goto L0200a49c
    call tempo_slot_services_set_tempo  ; @call.xl
    r5 = r0
    if (r5 != -6) goto L0200a4ae
L0200a49c:
    call audio_pause_pause_audio
    r0 = r4
    call effect_setup_tempo  ; @call.xl
    r5 = r0
    call audio_pause_resume_audio
L0200a4ae:
    r0 = r5
    {pc, r5, r4} = [sp++]
