; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_reports: 1 function, 0x0200ecf6..0x0200eeba

; console_reports_effect_table: 0x0200ecf6..0x0200eeba, module console-reports (effect_table)
.type console_reports_effect_table,@function
console_reports_effect_table:
    [--sp] = {rets, r13-r4}
    sp += -64
    r5 = 1
    r12 = L01c26890
    r4 = L02035d07  ; "FXT end\x0a"
    r13 = 8728
    goto L0200ee94
L0200ed0e:
    r0 = r5
    call preset_preflight_needs_conversion  ; @call.xl
    if (r0 != 0) goto L0200ee92
    r1 = sp + 60
    r0 = r5
    call slot_queries_type_demand  ; @call.xl
    r8 = r0
    r0 = r5
    call slot_queries_type_partition  ; @call.xl
    r7 = r0
    r0 = sp + 20
    r1 = 0
    r2 = 40
    r6 = 0
    call effect_enable_memset  ; @call.xl
    r3 = [sp+60]
    if (r3 <= r8) goto L0200ed52
    r2 = r4 + 278
    r0 = sp + 20
    r1 = 40
    call L0200691e
    r6 = r0
L0200ed52:
    if (r7 == 0) goto L0200ed66
    r0 = sp + 20
    r0 += r6  ; @add.rr
    r1 = 0x28 - r6
    r2 = r4 + 132
    r3 = r7
    call L0200691e
L0200ed66:
    r0 = r5
    call console_reports_type_name  ; @call.xl
    r7 = r0
    r0 = r5
    call slot_queries_type_cost  ; @call.xl
    r6 = r0
    r0 = r5
    call slot_queries_type_name  ; @call.xl
    r1 = sp + 20
    r1 = 512  #
    [sp+16] = r1
    [sp+12] = r8  ; @st.w.sp.l
    r3 = r5  #
    [sp+8] = r0
    r6 = r12 + r13  #
    [sp+4] = r6
    r2 = r4 + 4274  #
    [sp] = r7
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
    r7 = 0
    goto L0200edf4
L0200edb4:
    r0 = r5
    r1 = r7
    call preset_application_metadata  ; @call.xl
    if (r0 == 0) goto L0200edf2
    r3 = [r0+8]
    r1 = h[r0+0] (s)
    r2 = h[r0+2] (s)
    r0 = h[r0+4] (s)
    r0 = r6  #
    [sp+12] = r0
    r2 = r4 + 2837  #
    [sp+8] = r2
    r1 = 512  #
    [sp+4] = r1
    r3 = r7  #
    [sp] = r3
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
L0200edf2:
    r7 += 1  ; @add.ri.u5
L0200edf4:
    if (r7 != 7) goto L0200edb4
    r1 = 0
    r0 = r5
    call slot_queries_mode_code  ; @call.xl
    ifs (r0 <= -1) goto L0200ee74
    r1 = 0
    r0 = r5
    call slot_queries_mode_code  ; @call.xl
    r8 = r0
    r1 = 1
    r0 = r5
    call slot_queries_mode_code  ; @call.xl
    r9 = r0
    r1 = 2
    r0 = r5
    call slot_queries_mode_code  ; @call.xl
    r7 = r0
    r0 = r5
    r1 = r8
    call slot_queries_mode_cost  ; @call.xl
    r10 = r0
    r0 = r5
    r1 = r9
    call slot_queries_mode_cost  ; @call.xl
    r11 = r0
    r0 = r5
    r1 = r7
    call slot_queries_mode_cost  ; @call.xl
    r2 = r4 + 4599  #
    [sp+16] = r0
    d[sp+8] = r11_r10
    r1 = 512  #
    [sp+4] = r7
    [sp] = r9  ; @st.w.sp.l
    r0 = r6
    r3 = r8
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
L0200ee74:
    if (r5 != 29) goto L0200ee92
    r2 = r4 + 2093
    r1 = 512
    r0 = r6
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r6
    call command_services_console_send
L0200ee92:
    r5 += 1  ; @add.ri.u5
L0200ee94:
; HyperRig MINI, product option: the ids go on after 39.
.if MINI_PRODUCT
    r0 = hyperrig_effect_end  ; @li.u32
    r0 = [r0+0]
    if (r5 != r0) goto L0200ed0e
.else
    if (r5 != 40) goto L0200ed0e
.endif
    r0 = r13
    r5 = r12 + r0
    r1 = 512
    r0 = r5
    r2 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    sp += 64
    {pc, r13-r4} = [sp++]
