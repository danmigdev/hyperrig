; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dispatch_helpers: 4 functions, 0x0200e18e..0x0200e32e

; dispatch_helpers_error_text: 0x0200e18e..0x0200e200, module dispatch-helpers (error_text)
.type dispatch_helpers_error_text,@function
dispatch_helpers_error_text:
    [--sp] = {rets, r4}
    r1 = L02035d95  ; "bank full"
    if (r0 == -4) goto L0200e1c4
    if (r0 == -2) goto L0200e1ca
    if (r0 != -3) goto L0200e1ce
    r0 = L01c26890
    r3 = [r0+468]
    r2 = L01c3448b
    r2 = b[r2+0] (u)
    if (r2 == 0) goto L0200e1de
    r4 = r0 + 2992
    r2 = r1 + 5452
    r1 = 64
    r3 = 4
    goto L0200e1f0
L0200e1c4:
    r4 = r1 + 1081
    goto L0200e1f6
L0200e1ca:
    r4 = r1
    goto L0200e1f6
L0200e1ce:
    r2 = r1 + 581
    r4 = r1 + 4862
    if (r0 != -5) {
    r4 = r2
    }
    goto L0200e1f6
L0200e1de:
    if (r3 == 0) goto L0200e1fa
    r4 = r0 + 2992
    r2 = r1 + 2965
    r0 = r3 + 1023
    r3 = r0 >> 10
    r1 = 64
L0200e1f0:
    r0 = r4
    call L0200691e
L0200e1f6:
    r0 = r4
    {pc, r4} = [sp++]
L0200e1fa:
    r4 = r1 + 795
    goto L0200e1f6

; dispatch_helpers_mix_list: 0x0200e200..0x0200e278, module dispatch-helpers (mix_list)
.type dispatch_helpers_mix_list,@function
dispatch_helpers_mix_list:
    [--sp] = {rets, r9-r4}
    sp += -12
    r4 = 0
    r0 = 8728
    r1 = L01c26890
    r5 = r1 + r0
    r8 = L020364fb  ; "FXMIX %c %d %d %d\x0a"
    goto L0200e270
L0200e21a:
    r9 = 81
    if (r4 != 0) goto L0200e224
    r9 = 80
L0200e224:
    r6 = 0
    goto L0200e262
L0200e228:
    r2 = 0
    r0 = r4
    r1 = r6
    call preset_band_controls_band_level  ; @call.xl
    r7 = r0
    r2 = 1
    r0 = r4
    r1 = r6
    call preset_band_controls_band_level  ; @call.xl
    r1 = 512  #
    [sp+8] = r0
    d[sp] = r7_r6
    r0 = r5
    r3_r2 = r9_r8
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r6 += 1  ; @add.ri.u5
L0200e262:
    r0 = r4
    call slot_queries_group_count  ; @call.xl
    ifs (r6 < r0) goto L0200e228
    r4 += 1  ; @add.ri.u5
L0200e270:
    if (r4 != 2) goto L0200e21a
    sp += 12
    {pc, r9-r4} = [sp++]

; dispatch_helpers_crossover_list: 0x0200e278..0x0200e2ec, module dispatch-helpers (crossover_list)
.type dispatch_helpers_crossover_list,@function
dispatch_helpers_crossover_list:
    [--sp] = {rets, r9-r4}
    sp += -12
    r4 = 0
    r0 = 8728
    r1 = L01c26890
    r5 = r1 + r0
    r8 = L02036421  ; "FXXO %c %d %d %d\x0a"
    goto L0200e2e4
L0200e292:
    r9 = 81
    if (r4 != 0) goto L0200e29c
    r9 = 80
L0200e29c:
    r6 = 0
    goto L0200e2d6
L0200e2a0:
    r0 = r4
    r1 = r6
    call slot_queries_group_value  ; @call.xl
    r7 = r0
    r0 = r4
    r1 = r6
    call preset_band_controls_band_flag  ; @call.xl
    r1 = 512  #
    [sp+8] = r0
    d[sp] = r7_r6
    r0 = r5
    r3_r2 = r9_r8
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    r6 += 1  ; @add.ri.u5
L0200e2d6:
    r0 = r4
    call slot_queries_group_count  ; @call.xl
    ifs (r6 < r0) goto L0200e2a0
    r4 += 1  ; @add.ri.u5
L0200e2e4:
    if (r4 != 2) goto L0200e292
    sp += 12
    {pc, r9-r4} = [sp++]

; dispatch_helpers_buffer_release: 0x0200e2ec..0x0200e32e, module dispatch-helpers (buffer_release)
.type dispatch_helpers_buffer_release,@function
dispatch_helpers_buffer_release:
    [--sp] = {rets, r5, r4}
    r4 = L01c26890
    r5 = 0
    b[r4+25] = r5
    r0 = 2
    call L0203feb8  ; @call.xl
    r0 = r4
    r1 = [++r0=456]
    [r0+0] = r5
    [r0+4] = r5
    [r0+8] = r5
    if (r1 == 0) goto L0200e32c
    r4 = r4 + 2452
    r0 = r4
    call block_pool_contains
    if (r0 == 0) goto L0200e324
    r0 = r4
    call block_pool_release
    {pc, r5, r4} = [sp++]
L0200e324:
    r0 = r1
    call L0203d218  ; @call.xl
L0200e32c:
    {pc, r5, r4} = [sp++]
