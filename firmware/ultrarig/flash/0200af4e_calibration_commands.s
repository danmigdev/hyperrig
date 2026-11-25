; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; calibration_commands: 1 function, 0x0200af4e..0x0200b052

; calibration_commands_calibration_command: 0x0200af4e..0x0200b052, module calibration-commands (calibration_command)
.type calibration_commands_calibration_command,@function
calibration_commands_calibration_command:
    [--sp] = {rets, r7-r4}
    sp += -32
    r5 = r0
    r4 = L020359dc  ; "stop"
    r1 = r4 + 313
    call L02028308  ; @call.xl
    r7 = L01c26890
    r6 = L01c1f180
    if (r0 == 0) goto L0200afa4
    r0 = r5
    r1 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200afb8
    r1 = r4 + 461
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200aff0
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0200aff0
    r1 = r4 + 5
    r2 = 4
    r0 = r5
    call capture_command_prefix  ; @call.xl
    if (r0 == 0) goto L0200aff8
L0200af9e:
    r0 = r4 + 2476
    goto L0200afb2
L0200afa4:
    r0 = 1
    r5 = 1
    call command_services_calibration_running
    if (r0 == 0) goto L0200afc8
    r0 = r4 + 7195
L0200afb2:
    call link_and_print_print
    goto L0200aff4
L0200afb8:
    r0 = 0
    b[r7+17] = r0
    r1 = 748
    b[r7+r1] = r0
    goto L0200aff0
L0200afc8:
    r0 = sp + 28
    r1 = sp + 16
    r2 = sp + 24
    call command_services_calibration_measure
    r1 = r7 + 748
    [r1+8] = r0
    b[r1+0] = r5
    r0 = [r6+24]
    r0 = r0 * 0xA
    r0 = -999  #
    [r1+4] = r0
    [r1+12] = 0x0
    [r1+24] = r0
    [r1+20] = r0
    [r1+16] = r0
L0200aff0:
    call command_services_calibration_status
L0200aff4:
    sp += 32
    {pc, r7-r4} = [sp++]
L0200aff8:
    r0 = b[++r5=4] (u)
    r1 = r0 | 0x20
    if (r1 == 32) goto L0200b00a
    goto L0200af9e
L0200b006:
    r5 += 1  ; @add.ri.u5
    r0 = b[r5+0] (u)
L0200b00a:
    if (r0 == 32) goto L0200b006
    if (r0 == 0) goto L0200b02a
    r1 = sp + 0
    r0 = r5
    call capture_command_tenths
    if (r0 == 0) goto L0200b044
    r1 = [sp]
    r0 = r1 + 100
    if (r0 > 400) goto L0200b044
    [r6+96] = r1
    goto L0200b02e
L0200b02a:
    r1 = [r6+96]
L0200b02e:
    r5 = sp + 4
    r2 = 0
    r0 = r5
    call link_and_print_tenths
    r0 = r4 + 6078
    r1 = r5
    call link_and_print_print
    goto L0200aff4
L0200b044:
    r0 = r4 + 5120
    r1 = -10
    r2 = 30
    call link_and_print_print
    goto L0200aff4
