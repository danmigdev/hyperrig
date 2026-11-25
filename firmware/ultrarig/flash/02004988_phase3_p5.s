; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 2 functions, 0x02004988..0x02004a70

; phase3_p5_pb0_io_out: 0x02004988..0x02004998, module phase3-p5 (pb0_io_out)
.type phase3_p5_pb0_io_out,@function
phase3_p5_pb0_io_out:
    [--sp] = rets
    r1 = r0 & 0x1
    r0 = 153
    call storage_fault_write_register  ; @call.xl
    pc = [sp++]

; phase3_p5_gpio_direction_output: 0x02004998..0x02004a70, module phase3-p5 (gpio_direction_output)
.type phase3_p5_gpio_direction_output,@function
phase3_p5_gpio_direction_output:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r3 = r0
    if (r3 < 148) goto L020049ae
    r1 = 0
    call L02004904
    r0 = r3
    r1 = r4
    call L0200492a
    {pc, r6-r4} = [sp++]
L020049ae:
    if (r3 != 16) goto L020049cc
    r0 = 32
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = 154
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    r0 = r4
    call phase3_p5_pb0_io_out
    {pc, r6-r4} = [sp++]
L020049cc:
    if (r3 < 144) goto L02004a20
    r0 = r3 + 112
    r6 = r0.b0 (u)
    if (r6 > 1) goto L02004a6e
    r5 = 32922
    r0 = r5
    call storage_fault_read_register  ; @call.xl
    r1 = r0 & ~(1 << r6)
    r0 = r5
    call storage_fault_write_register  ; @call.xl
    r0 = 1
    r0 <<= r6
    r5 = 0
    if ((r4 & 0xFF) != 0) {
    r5 = r0
    }
    r4 = 32921
    r0 = r4
    call storage_fault_read_register  ; @call.xl
    r0 = r0 & ~(1 << r6)
    r0 |= r5
    r1 = r0.b0 (u)
    r0 = r4
    call storage_fault_write_register  ; @call.xl
    {pc, r6-r4} = [sp++]
L02004a20:
    call sdk_gpio2reg
    r2 = r0
    if (r2 == -1) goto L02004a6e
    r0 = r3 >> 4
    r1 = L01c25ce0
    r5 = r0 + r1
    call storage_coordination_irq_enter  ; @call.xl
    csync
L02004a3c:
    testset b[r5]
    ifeq goto L02004a3c
    r0 = r3 & 0xF
    r1 = 1
    r0 = r1 << r0
    csync
    if (r4 == 0) goto L02004a5a
    if (r4 == 1) {  ; @if.eq.ri.s12
    [r2+0] |= r0
    }
    goto L02004a5e
L02004a5a:
    [r2+0] &= ~r0
L02004a5e:
    [r2+8] &= ~r0
    csync
    r0 = 0
    b[r5+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
L02004a6e:
    {pc, r6-r4} = [sp++]
