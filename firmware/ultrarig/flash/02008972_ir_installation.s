; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_installation: 5 functions, 0x02008972..0x02008c28

; ir_installation_attach: 0x02008972..0x020089c4, module ir-installation (attach), ir-loader (attach)
.type ir_installation_attach,@function
ir_installation_attach:
    [--sp] = {rets, r9-r4}
    r5 = L01c26928
    r8 = [r5+12]
    r6 = r3
    r7 = r2
    r4 = r1
    r9 = r0
    call audio_pause_pause_audio
    r0 = r9
    r1 = r4
    r2 = r7
    r3 = r6
    call ir_installation_configure  ; @call.xl
    call audio_pause_resume_audio
    [r5+12] = r9
    [r5+] = {r7, r4}
    r0 = 1
    b[r5+8] = r0
    if (r6 != 0) goto L020089ac
    r0 = r6
L020089ac:
    [r5+16] = r0
    [r5+20] = 0x0
    if (r8 == 0) goto L020089c2
    if (r8 != r9) {
    r0 = r8
    call L0203d218  ; @call.xl
    }
L020089c2:
    {pc, r9-r4} = [sp++]

; ir_installation_pending: 0x020089c4..0x020089da, module ir-installation (pending), ir-loader (pending)
.type ir_installation_pending,@function
ir_installation_pending:
    r0 = L01c26930
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L020089d0
    r1 = [r0+12]
L020089d0:
    r2 = [r0+4]
    r0 = 0
    if (r2 != 0) goto L020089d8
    r0 = r1
L020089d8:
    rts

; ir_installation_query: 0x020089da..0x020089f2, module ir-installation (query), ir-loader (query)
.type ir_installation_query,@function
ir_installation_query:
    r2 = L01c26890
    r3 = [++r2=152]
    [r0+0] = r3
    r0 = [r2+4]
    [r1+0] = r0
    r0 = b[r2+8] (u)
    if (r0 == 0) goto L020089f0
    r0 = [r2+12]
L020089f0:
    rts

; ir_installation_refresh: 0x020089f2..0x02008a62, module ir-installation (refresh), ir-loader (refresh)
.type ir_installation_refresh,@function
ir_installation_refresh:
    [--sp] = {rets, r7-r4}
    sp += -8
    r0 = L01c1f180
    r5 = b[r0+10] (u)
    r0 = L01c3441c
    r1 = ir_installation_read
    [r0+0] = r1
    if (r5 == 255) goto L02008a14
    call ir_installation_pending
    if (r0 == 0) goto L02008a18
L02008a14:
    sp += 8
    {pc, r7-r4} = [sp++]
L02008a18:
    r0 = sp + 4
    r1 = sp + 0
    call ir_installation_query
    if (r0 == 0) goto L02008a14
    r7 = L01c26890
    r0 = b[r7+160] (u)
    if (r0 == 0) goto L02008a14
    r0 = [r7+164]
    if (r0 == 0) goto L02008a14
    r4 = [r7+744]
    r5 += 1  ; @add.ri.u5
    call audio_pause_pause_audio
    r0 = r5
    r1 = r4
    call ir_installation_slot  ; @call.xl
    r6 = r0
    call audio_pause_resume_audio
    if (r6 != 0) goto L02008a14
    r0 = [++r7=164]
    call L0203d218  ; @call.xl
    [r7+0] = 0x0
    [r7+8] = r5
    [r7+12] = r4
    goto L02008a14

; ir_installation_load: 0x02008a62..0x02008c28, module ir-installation (load), ir-loader (load)
.type ir_installation_load,@function
ir_installation_load:
    [--sp] = {rets, r15-r4}
    sp += -60
    r9_r8 = r1_r0
    r0 = 1
    call tempo_slot_services_priority_nest
    r1 = sp + 20
    r3 = sp + 16
    r2 = 8152
    r0 = r8
    call preset_application_asset_header
    if (r0 == 0) goto L02008aa0
    r12 = L01c1f180
    r0 = b[r12+10] (u)
    r11 = L01c26890
    if (r0 != r8) goto L02008aaa
    r0 = sp + 20
    r15 = [sp+16]  ; @ld.w.sp.l
    r5 = r0 + 12
    r7 = r0 + 4
    r4 = r0 + 8
    goto L02008ad6
L02008aa0:
    r0 = 0
    call tempo_slot_services_priority_nest
    r6 = -1
    goto L02008b10
L02008aaa:
    r6 = [sp+24]
    r1 = [sp+28]
    r15 = [sp+16]  ; @ld.w.sp.l
    r2 = uextra(r15, p:0, l:8)  #
    r3 = [sp+32]
    r0 = r11 + 1796  #
    [sp] = r2
    r2 = r6
    call preset_application_asset_matches
    r13 = sp + 20
    if (r0 == 0) goto L02008b16
    r5 = r13 + 12
    r7 = r13 + 4
    r4 = r13 + 8
L02008ad6:
    r0 = 0
    r6 = 0
    call tempo_slot_services_priority_nest
    r4 = r11 + 1796  #
    r0 = [r4+0]
    b[r12+10] = r8
    [r11+744] = r0
    r1 = 255
    b[r12+19] = r1
    r1 = [r5+0]
    r2 = [r7+0]
    r3 = 1
    b[r4+0] = r3
    [r4+4] = r0
    [r4+8] = r2
    r1 = r8 | 0x600  #
    [r4+12] = r1
    b[r4+1] = r15
    r0 = 20
    r2 = 0
    call storage_coordination_notify
L02008b10:
    r0 = r6
    sp += 60
    {pc, r15-r4} = [sp++]
L02008b16:
    r0 = r6
    call L0203c15c  ; @call.xl
    r10 = r0
    if (r0 == 0) goto L02008b72
    r0 = 6
    call storage_control_activity
    [sp] = r10  ; @st.w.sp.l
    if (r15 == 0) {  ; @if.eq.ri.s12
    r1 = 1229409108
    } else {
    r1 = 1246186324
    }
    r0 = r8 << 13
    r0 = r0 + 0xEF000
    r3 = sp + 20
    r2 = 8152
    call preset_storage_record
    r6 = r0
    r0 = 0
    r7 = 0
    call tempo_slot_services_priority_nest
    if (r6 == 0) goto L02008b7e
    r0 = r10
    call L0203d218  ; @call.xl
    r1 = r8 | 0x100
    r0 = 20
    r2 = r6
    call storage_coordination_notify
    r0 = 0
    goto L02008c22
L02008b72:
    r0 = 0
    call tempo_slot_services_priority_nest
    r6 = -100
    goto L02008b10
L02008b7e:
    r1 = r8 | 0x100
    r0 = 20
    r2 = 0
    call storage_coordination_notify
    r4 = [r13+12]
    r14 = [r13+4]
    r1 = r14 >> 1
    r0 = r10
    r2 = r4
    r3 = r15
    call ir_installation_attach
    call audio_pause_pause_audio
    goto L02008be8
L02008ba6:
    r1 = sp + 6
    r0 = r7
    call preset_application_chain_read  ; @call.xl
    r6 = r0
    r5 = 0
    goto L02008be2
L02008bb6:
    r0 = sp + 6
    r0 = b[r0+r5] (u)
    call preset_application_effect_type  ; @call.xl
    if (r0 != 7) goto L02008be0
    r0 = sp + 6
    r0 = b[r0+r5] (u)
    call ir_effect_lifecycle_owns  ; @call.xl
    if (r0 != 0) goto L02008be0
    r0 = sp + 6
    r0 = b[r0+r5] (u)
    call ir_effect_lifecycle_refresh  ; @call.xl
L02008be0:
    r5 += 1  ; @add.ri.u5
L02008be2:
    ifs (r5 < r6) goto L02008bb6
    r7 += 1  ; @add.ri.u5
L02008be8:
    if (r7 != 2) goto L02008ba6
    call audio_pause_resume_audio
    r0 = [r13+8]
    b[r12+10] = r8
    [r11+744] = r0
    r1 = 255
    b[r12+19] = r1
    r1 = 1
    r2 = r11 + 1796
    b[r2+0] = r1
    [r2+4] = r0
    [r2+8] = r14
    [r2+12] = r4
    b[r2+1] = r15
    if (r9 != 0) {  ; @if.ne.ri.s12
    call ir_installation_refresh
    }
    r0 = 0
    r6 = 0
L02008c22:
    call storage_control_activity
    goto L02008b10
