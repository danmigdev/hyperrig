; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_commands: 1 function, 0x0200d060..0x0200d0c0

; slot_commands_enable_command: 0x0200d060..0x0200d0c0, module slot-commands (enable_command)
.type slot_commands_enable_command,@function
slot_commands_enable_command:
    [--sp] = {rets, r7-r4}
    r7 = L01c26890
    r2 = [r7+280]
    r4 = r1
    r5 = r0
    if (r2 != 2) goto L0200d080
    call effect_enable_fast  ; @call.xl
    r6 = r0
    if (r6 != -6) goto L0200d0bc
L0200d080:
    r0 = [r7+280]
    r7 = 0
    if (r4 == 0) goto L0200d0a0
    if (r0 != 2) goto L0200d0a0
    r0 = r5
    call preset_application_services_needs_resource  ; @call.xl
    if (r0 == 0) goto L0200d0a0
    r0 = 1
    r1 = 0
    r7 = 1
    call storage_coordination_gate_core
L0200d0a0:
    call audio_pause_pause_audio
    r0 = r5
    r1 = r4
    call effect_enable_commit  ; @call.xl
    r6 = r0
    call audio_pause_resume_audio
    if (r7 == 0) goto L0200d0bc
    r1_r0 = 0
    call storage_coordination_gate_core
L0200d0bc:
    r0 = r6
    {pc, r7-r4} = [sp++]
