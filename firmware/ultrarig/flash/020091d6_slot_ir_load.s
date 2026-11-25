; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_ir_load: 1 function, 0x020091d6..0x020092e4

; slot_ir_load_load_slot_ir: 0x020091d6..0x020092e4, module slot-ir-load (load_slot_ir)
.type slot_ir_load_load_slot_ir,@function
slot_ir_load_load_slot_ir:
    [--sp] = {rets, r10-r4}
    sp += -56
    r4 = r0
    call preset_application_effect_type  ; @call.xl
    r6 = -1
    if (r0 != 7) goto L020092de
    r1 = 2
    r0 = r4
    call preset_application_parameter  ; @call.xl
    r7 = r0
    ifs (r7 <= 0) goto L020092a6
    ifs (r7 > 8) goto L020092de
    r0 = 1
    call tempo_slot_services_priority_nest
    r5 = r7 + -1
    r1 = sp + 16
    r3 = sp + 12
    r2 = 8152
    r0 = r5
    call preset_application_asset_header
    if (r0 == 0) goto L020092ce
    r0 = [sp+20]
    r9 = sp + 16
    call L0203c15c  ; @call.xl
    r8 = r0
    if (r0 == 0) goto L020092d6
    r10 = [sp+12]  ; @ld.w.sp.l
    r0 = r9 + 4
    [sp] = r8  ; @st.w.sp.l
    if (r10 == 0) {  ; @if.eq.ri.s12
    r1 = 1229409108
    } else {
    r1 = 1246186324
    }
    r0 = r5 << 13
    r0 = r0 + 0xEF000
    r3 = sp + 16
    r2 = 8152
    call preset_storage_record
    r6 = r0
    r0 = 0
    call tempo_slot_services_priority_nest
    if (r6 != 0) goto L02009290
    r0 = L01c3441c
    r1 = ir_installation_read
    [r0+0] = r1
    call audio_pause_pause_audio
    r0 = [r9+4]
    r3 = [sp+28]
    r1 = [sp+24]
    r1 = r8  #
    [sp+8] = r1
    [sp+4] = r7
    r2 = r0 >> 1
    [sp] = r10  ; @st.w.sp.l
    r0 = r4
    call ir_effect_lifecycle_assign  ; @call.xl
    r6 = r0
    call audio_pause_resume_audio
L02009290:
    r0 = r8
    call L0203d218  ; @call.xl
    r1 = r5 | 0x700
    r0 = 20
    r2 = r6
    call storage_coordination_notify
    goto L020092de
L020092a6:
    r0 = r4
    call ir_effect_lifecycle_owns  ; @call.xl
    if (r0 == 0) goto L020092ca
    call audio_pause_pause_audio
    r1_r0 = 0
    r3_r2 = 0  #
    [sp] = r0
    r0 = r4
    call ir_effect_lifecycle_assign_direct  ; @call.xl
    r6 = r0
    call audio_pause_resume_audio
    goto L020092de
L020092ca:
    r6 = 0
    goto L020092de
L020092ce:
    r0 = 0
    call tempo_slot_services_priority_nest
    goto L020092de
L020092d6:
    r0 = 0
    call tempo_slot_services_priority_nest
    r6 += -99
L020092de:
    r0 = r6
    sp += 56
    {pc, r10-r4} = [sp++]
