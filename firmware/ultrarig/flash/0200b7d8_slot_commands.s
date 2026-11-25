; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_commands: 1 function, 0x0200b7d8..0x0200b834

; slot_commands_choose_slot_ir: 0x0200b7d8..0x0200b834, module slot-commands (choose_slot_ir)
.type slot_commands_choose_slot_ir,@function
slot_commands_choose_slot_ir:
    [--sp] = {rets, r7-r4}
    r5_r4 = r1_r0
    call preset_application_effect_type  ; @call.xl
    r7 = r5 + 1
    r5 = -1
    if (r7 > 8) goto L0200b830
    if (r0 != 7) goto L0200b830
    r1 = 2
    r0 = r4
    call preset_application_parameter  ; @call.xl
    r6 = r0
    call audio_pause_pause_audio
    r1 = 2
    r0 = r4
    r2 = r7
    call effect_parameter_lifecycle_parameter_commit  ; @call.xl
    call audio_pause_resume_audio
    r0 = r4
    call slot_ir_load_load_slot_ir
    r5 = r0
    if (r5 == 0) goto L0200b82e
    call audio_pause_pause_audio
    r1 = 2
    r0 = r4
    r2 = r6
    call effect_parameter_lifecycle_parameter_commit  ; @call.xl
    call audio_pause_resume_audio
    goto L0200b830
L0200b82e:
    r5 = 0
L0200b830:
    r0 = r5
    {pc, r7-r4} = [sp++]
