; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; command_services: 2 functions, 0x0200ad06..0x0200adaa

; command_services_calibration_running: 0x0200ad06..0x0200ad40, module command-services (calibration_running)
.type command_services_calibration_running,@function
command_services_calibration_running:
    [--sp] = {rets, r5, r4}
    r2 = L01c26890
    if (r0 == 0) goto L0200ad30
    r3 = [r2+280]
    r1 = -1
    if (r3 != 2) goto L0200ad3c
    r1 = 0
    [r2+284] = r1
    [r2+288] = r1
    r1 = r2 + 1600
    r4 = 0
    r5 = 0
    d[r1+0] = r5_r4
L0200ad30:
    r1 = 1
    if (r0 != 0) goto L0200ad36
    r1 = r0
L0200ad36:
    b[r2+17] = r1
    r1 = 0
L0200ad3c:
    r0 = r1
    {pc, r5, r4} = [sp++]

; command_services_calibration_measure: 0x0200ad40..0x0200adaa, module command-services (calibration_measure)
.type command_services_calibration_measure,@function
command_services_calibration_measure:
    [--sp] = {rets, r10-r4}
    r3 = 0
    r8 = 486
    r9 = L01c26890
    goto L0200ad96
L0200ad50:
    r5 = [r9+r8<<2]
    r7 = 4
    if ((r5 & 1) != 0) goto L0200ad84
    r4 = r9 + 1944
    r6 = [r4+4]
    [r0+0] = r6
    r7_r6 = d[r4+12]
    d[r1+0] = r7_r6
    r6 = [r4+8]
    r6 = r6 << 7
    [r2+0] = r6
    r4 = [r4+0]
    r6 = r5 >> 1
    if (r4 != r5) {
    r6 = r10
    }
    r7 = 1
    if (r4 != r5) {
    r7 = 0
    }
    goto L0200ad86
L0200ad84:
    r6 = r10
L0200ad86:
    r4 = r7 | 0x4
    r4 = r4 & 0x7
    if (r4 != 4) goto L0200ad9e
    r3 += 1  ; @add.ri.u5
    r10 = r6
L0200ad96:
    ifs (r3 <= 3) goto L0200ad50
    r7 = 2
    goto L0200ada0
L0200ad9e:
    r10 = r6
L0200ada0:
    r0 = 0
    if (r7 != 2) {  ; @if.ne.ri.s12
    r0 = r10
    }
    {pc, r10-r4} = [sp++]
