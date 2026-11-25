; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 2 functions, 0x02004c8a..0x02004d36

; phase3_p5_pb0_io_pullup: 0x02004c8a..0x02004c9a, module phase3-p5 (pb0_io_pullup)
.type phase3_p5_pb0_io_pullup,@function
phase3_p5_pb0_io_pullup:
    [--sp] = rets
    r1 = r0 & 0x1
    r0 = 156
    call storage_fault_write_register  ; @call.xl
    pc = [sp++]

; phase3_p5_gpio_set_pull_up: 0x02004c9a..0x02004d36, module phase3-p5 (gpio_set_pull_up)
.type phase3_p5_gpio_set_pull_up,@function
phase3_p5_gpio_set_pull_up:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r2 = r0
    if (r2 < 148) goto L02004ca8
    call L02004c48
    {pc, r5, r4} = [sp++]
L02004ca8:
    if (r2 != 16) goto L02004cb2
    r0 = r4
    call phase3_p5_pb0_io_pullup
    {pc, r5, r4} = [sp++]
L02004cb2:
    if (r2 < 144) goto L02004cee
    r0 = r2 + 112
    r0 = r0.b0 (u)
    if (r0 > 1) goto L02004d34
    r1 = 1
    r5 = r1 << r0
    r0 = 32924
    call storage_fault_read_register  ; @call.xl
    if ((r4 & 0xFF) == 0) {
    r1 = r5 ^ 0xFF
    r0 &= r1
    } else {
    r0 |= r5
    }
    r1 = r0.b0 (u)
    r0 = 32924
    call storage_fault_write_register  ; @call.xl
    {pc, r5, r4} = [sp++]
L02004cee:
    call sdk_gpio2reg
    r3 = r0
    if (r3 == -1) goto L02004d34
    r0 = r2 >> 4
    r1 = L01c25ce0
    r5 = r0 + r1
    call storage_coordination_irq_enter  ; @call.xl
    csync
L02004d0a:
    testset b[r5]
    ifeq goto L02004d0a
    r0 = r2 & 0xF
    r1 = 1
    r0 = r1 << r0
    csync
    if (r4 == 0) {  ; @if.eq.ri.s12
    [r3+16] &= ~r0
    } else {
    [r3+16] |= r0
    }
    csync
    r0 = 0
    b[r5+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
L02004d34:
    {pc, r5, r4} = [sp++]
