; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_control: 2 functions, 0x02002e6a..0x02002f16

; storage_control_program_pages: 0x02002e6a..0x02002ef2, module storage-control (program_pages)
.type storage_control_program_pages,@function
storage_control_program_pages:
    [--sp] = {rets, r10-r4}
    r3 = L01c3743c
    r6 = r2  #
    r3 = [r3+24]
    r10 = r1
    r7 = r0
    r1 += r6  ; @add.rr
    r0 = 0
    if (r1 > r3) goto L02002ef0
    r9 = L01c26890
    r8 = r9 + 3748
    r0 = r8
    call L02040614  ; @call.xl
    r0 = b[r9+67] (u)
    r0 += 1  ; @add.ri.u5
    b[r9+67] = r0
    r0 = r6.b0 (u)
    r0 = 0x100 - r0
    r5 = umin(r0, r10)
    r0 = r7
    r1 = r6
    r2 = r5
    call storage_control_device_program  ; @call.xl
    r6 += r5  ; @add.rr
    r7 += r5  ; @add.rr
    r4 = r10 - r5
    goto L02002eda
L02002ebe:
    r5 = r4
    ifs (r4 >= 256) {  ; @ifs.ge.ri.s12
    r5 = 256
    }
    r0 = r7
    r1 = r6
    r2 = r5
    call storage_control_device_program  ; @call.xl
    r7 += r5  ; @add.rr
    r6 += r5  ; @add.rr
    r4 = r4 - r5
L02002eda:
    if (r4 != 0) goto L02002ebe
    r0 = b[r9+67] (u)
    r0 += -1
    b[r9+67] = r0
    r0 = r8
    call L0204074c  ; @call.xl
    r0 = r10
L02002ef0:
    {pc, r10-r4} = [sp++]

; storage_control_program: 0x02002ef2..0x02002f16, module storage-control (program)
.type storage_control_program,@function
storage_control_program:
    [--sp] = {rets, r5, r4}
    r4 = r2
    r5 = r1
    r0 = r3
    r1 = r4
    call storage_control_range
    if (r0 == 0) goto L02002f0c
    r0 = r5
    r1 = r4
    r2 = r3
    call storage_control_program_pages
    {pc, r5, r4} = [sp++]
L02002f0c:
    r0 = r3
    call storage_control_reject
    r0 = -1
    {pc, r5, r4} = [sp++]
