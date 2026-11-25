; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dispatch_helpers: 6 functions, 0x0200eae6..0x0200ecf6

; dispatch_helpers_effect_number: 0x0200eae6..0x0200eb24, module dispatch-helpers (effect_number)
.type dispatch_helpers_effect_number,@function
dispatch_helpers_effect_number:
    [--sp] = {rets, r5, r4}
    r5 = r0
    r4 = 1
    goto L0200eb04
L0200eaee:
    r0 = r4
    call console_reports_type_name  ; @call.xl
    r1 = r0
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200eb20
    r4 += 1  ; @add.ri.u5
L0200eb04:
; HyperRig MINI, product option: the ids go on after 39.
.if MINI_PRODUCT
    r0 = hyperrig_effect_end  ; @li.u32
    r0 = [r0+0]
    if (r4 < r0) goto L0200eaee
.else
    ifs (r4 <= 39) goto L0200eaee
.endif
    r1 = 0
    r2 = 10
    r0 = r5
    call capture_command_decimal  ; @call.xl
    r4 = r0
    r0 = r4 + -1
.if MINI_PRODUCT
    r1 = hyperrig_effect_end  ; @li.u32
    r1 = [r1+0]
    r1 = r1 + -1
    if (r0 < r1) goto L0200eb20
    r4 = 0
.else
    if (r0 >= 39) {  ; @if.ge.ri.s12
    r4 = 0
    }
.endif
L0200eb20:
    r0 = r4
    {pc, r5, r4} = [sp++]

; dispatch_helpers_path_letter: 0x0200eb24..0x0200eb42, module dispatch-helpers (path_letter)
.type dispatch_helpers_path_letter,@function
dispatch_helpers_path_letter:
    r1 = r0.b0 (u)
    r0 = 0
    if (r1 == 80) goto L0200eb40
    if (r1 == 81) {  ; @if.eq.ri.s12
    r0 = 1
    rts
    }
    if (r1 == 112) goto L0200eb40
    r0 = 1
    if (r1 != 113) {  ; @if.ne.ri.s12
    r0 = -1
    }
L0200eb40:
    rts

; dispatch_helpers_bank_bit_clear: 0x0200eb42..0x0200eb78, module dispatch-helpers (bank_bit_clear)
; HyperRig MINI, product option: eight scenes.
.type dispatch_helpers_bank_bit_clear,@function
dispatch_helpers_bank_bit_clear:
.if MINI_PRODUCT
    [--sp] = rets
    call hyperrig_scene_forget
    pc = [sp++]
.else
    [--sp] = {rets, r5, r4}
    if (r0 > 15) goto L0200eb76
    r1 = 65535
    r0 = r1 ^ (1 << r0)
    r1 = 0
    r2 = L01c26890
    r3 = 5969
    goto L0200eb70
L0200eb60:
    r4 = r1 + r2
    r5 = h[r4+r3<<1] (u)
    r5 &= r0
    h[r4+r3<<1] = r5
    r1 = r1 + 260
L0200eb70:
    if (r1 != 1040) goto L0200eb60
L0200eb76:
    {pc, r5, r4} = [sp++]
.endif

; dispatch_helpers_cpu_line: 0x0200eb78..0x0200ebea, module dispatch-helpers (cpu_line)
.type dispatch_helpers_cpu_line,@function
dispatch_helpers_cpu_line:
    [--sp] = {rets, r7-r4}
    sp += -16
    r4 = r0
    call effect_setup_total_cost  ; @call.xl
    r5 = r0
    call preset_application_services_budget  ; @call.xl
    r6 = r0
    call preset_application_services_budget  ; @call.xl
    if (r0 == 0) goto L0200ebac
    call effect_setup_total_cost  ; @call.xl
    r7 = r0 * 0x64
    call preset_application_services_budget  ; @call.xl
    r7 = r7 / r0 (u)
    goto L0200ebae
L0200ebac:
    r7 = 0
L0200ebae:
    call slot_queries_slots_memory  ; @call.xl
    r0 = 8728  #
    [sp+12] = r0
    d[sp+4] = r7_r6
    r1 = L01c26890
    r6 = r1 + r0  #
    [sp] = r5
    r2 = L02039ff1  ; "%s cpu=%u/%u ticks (%u%%) mem_fx=%u B\x0a"
    r1 = 512
    r0 = r6
    r3 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    sp += 16
    {pc, r7-r4} = [sp++]

; dispatch_helpers_cpu_notify: 0x0200ebea..0x0200ec2a, module dispatch-helpers (cpu_notify)
.type dispatch_helpers_cpu_notify,@function
dispatch_helpers_cpu_notify:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = r1 << 8
    r6 = r0 | r4
    call preset_application_services_budget  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L0200ec10
    call effect_setup_total_cost  ; @call.xl
    r0 = r0 * 0x64
    r0 = r0 / r5 (u)
    r0 = r0 << 16
    goto L0200ec12
L0200ec10:
    r0 = 0
L0200ec12:
    r5 = r6 | r0
    r0 = r4
    call slot_queries_type_cost  ; @call.xl
    r2 = r0
    r0 = 10
    r1 = r5
    call storage_coordination_notify
    {pc, r6-r4} = [sp++]

; dispatch_helpers_parameter_apply: 0x0200ec2a..0x0200ecf6, module dispatch-helpers (parameter_apply)
.type dispatch_helpers_parameter_apply,@function
dispatch_helpers_parameter_apply:
    [--sp] = {rets, r9-r4}
    r8 = r3
    r5 = r2
    r6 = r1
    r4 = r0
    call preset_application_effect_type  ; @call.xl
    r1 = r6
    call preset_application_metadata  ; @call.xl
    r7 = r0
    if (r7 == 0) goto L0200ec58
    r0 = [r7+8]
    if (r0 == 0) goto L0200ec58
    r1 = L0203bc41  ; "os_n"
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200ecd2
L0200ec58:
    r0 = r4
    r1 = r6
    r2 = r5
    call effect_parameter_lifecycle_parameter_probe  ; @call.xl
    r7 = r0
    if (r7 != 0) goto L0200ecf2
    r9 = L01c26890
    r0 = [r9+280]
    if (r0 != 2) goto L0200ec8a
    r0 = r4
    r1 = r6
    r2 = r5
    r3 = r8
    call effect_parameter_lifecycle_parameter_fast_wrapper  ; @call.xl
    r7 = r0
    if (r7 != -6) goto L0200ecf2
L0200ec8a:
    r0 = [r9+280]
    r8 = 0
    if (r0 != 2) goto L0200ecb0
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    if (r6 != 6) goto L0200ecb0
    if (r0 == 37) {  ; @if.eq.ri.s12
    r0 = 1
    r1 = 0
    r8 = 1
    call storage_coordination_gate_core
    }
L0200ecb0:
    call audio_pause_pause_audio
    r0 = r4
    r1 = r6
    r2 = r5
    call effect_parameter_lifecycle_parameter_commit  ; @call.xl
    r7 = r0
    call audio_pause_resume_audio
    if (r8 != 0) {  ; @if.ne.ri.s12
    r1_r0 = 0
    call storage_coordination_gate_core
    }
    goto L0200ecf2
L0200ecd2:
    call audio_pause_pause_audio
    ifs (r5 >= 0) {  ; @ifs.ge.ri.s12
    r0 = h[r7+2] (s)
    r1 = smin(r0, r5)
    } else {
    r1 = 0
    }
    r0 = r4
    call slot_queries_slot_set_mode  ; @call.xl
    r7 = r0
    call audio_pause_resume_audio
L0200ecf2:
    r0 = r7
    {pc, r9-r4} = [sp++]
