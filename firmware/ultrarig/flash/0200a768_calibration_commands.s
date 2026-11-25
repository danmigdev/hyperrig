; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; calibration_commands: 1 function, 0x0200a768..0x0200a7de

; calibration_commands_trim_report: 0x0200a768..0x0200a7de, module calibration-commands (trim_report)
.type calibration_commands_trim_report,@function
calibration_commands_trim_report:
    [--sp] = {rets, r8-r4}
    sp += -80
    r6 = r3
    r8 = r1
    r5 = r0
    r1 = r2 * 0x5
    r0 = sp + 68
    r2 = 0
    r4 = 0
    call link_and_print_tenths
    r1 = [sp+104]
    r0 = sp + 56
    r2 = 0
    call link_and_print_tenths
    r0 = [sp+112]
    b[sp+16] = r4
    r4 = L02035810
    if (r0 == 0) goto L0200a7b2
    r7 = r4 + 1604  #
    r0 = [sp+124]
    r1 = [sp+120]
    r3 = [sp+116]
    [sp] = r1
    if (r0 != 0) goto L0200a7a4
    r7 = r4
L0200a7a4:
    r2 = r4 + 2599  #
    [sp+4] = r7
    r0 = sp + 16
    r1 = 40
    call L0200691e
L0200a7b2:
    r0 = [sp+108]
    r2 = sp + 56
    if (r6 == 0) {  ; @if.eq.ri.s12
    r1 = r4
    r2 = r4
    } else {
    r1 = r4 + 415
    }
    r3 = sp + 16
    [sp+12] = r3
    r0 = r4 + 6067  #
    [sp+8] = r0
    r2 = r8  #
    [sp+4] = r2
    r3 = sp + 68
    r1 = r5  #
    [sp] = r1
    call link_and_print_print
    sp += 80
    {pc, r8-r4} = [sp++]
