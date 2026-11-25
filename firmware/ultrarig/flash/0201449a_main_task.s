; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; main_task: 1 function, 0x0201449a..0x02014504

; main_task_shift: 0x0201449a..0x02014504, module main-task (shift)
.type main_task_shift,@function
main_task_shift:
    [--sp] = {rets, r9-r4}
    r4 = 41
L0201449e:
    r2 = r4 + 22
    r7_r6 = r1_r0
    r7_r6 >>= r2
    r2 = r6 | r7
    r4 += -1
    if (r2 == 0) goto L0201449e
    r2 = r4 + 23
    ifs (r2 < 23) {  ; @ifs.lt.ri.s12
    r4 = 0x0 - r4
    r1_r0 <<= r4
    } else {
    r1_r0 >>= r4
    }
    r4 = r0 >> 17
    r4 = r4 & 0x3C
    r5 = L02035810
    r4 += r5  ; @add.rr
    r5 = 2119
    r6 = [r4+r5<<2]
    r5 += 1  ; @add.ri.u5
    r4 = [r4+r5<<2]
    r4 = r4 - r6
    r0 = uextra(r0, p:3, l:16)
    r5_r4 = r4 * r0 (u)
    r5_r4 >>= 16
    r3 = r2 >>> 31
    r3_r2 <<= 16
    r7 = 0
    r8 = r6 + r2
    r9 = r7 + r3 + c
    r0 = r8 + r4
    r1 = r9 + r5 + c
    {pc, r9-r4} = [sp++]
