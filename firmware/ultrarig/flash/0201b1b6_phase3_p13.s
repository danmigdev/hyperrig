; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 2 functions, 0x0201b1b6..0x0201b2ce

; phase3_p13_gpio_set_hd_0: 0x0201b1b6..0x0201b23a, module phase3-p13 (gpio_set_hd_0)
.type phase3_p13_gpio_set_hd_0,@function
phase3_p13_gpio_set_hd_0:
    [--sp] = {rets, r5, r4}
    r2 = r0
    if (r2 <= 147) goto L0201b1c0
L0201b1be:
    {pc, r5, r4} = [sp++]
L0201b1c0:
    if (r2 != 16) goto L0201b1d0
    r0 = 158
    r1 = 0
    call storage_fault_write_register  ; @call.xl
    {pc, r5, r4} = [sp++]
L0201b1d0:
    if (r2 < 144) goto L0201b200
    r0 = r2 + 112
    r0 = r0.b0 (u)
    if (r0 > 1) goto L0201b1be
    r1 = 255
    r5 = r1 ^ (1 << r0)
    r4 = 32926
    r0 = r4
    call storage_fault_read_register  ; @call.xl
    r1 = r0 & r5
    r0 = r4
    call storage_fault_write_register  ; @call.xl
    {pc, r5, r4} = [sp++]
L0201b200:
    call sdk_gpio2reg
    r3 = r0
    if (r3 == -1) goto L0201b1be
    r0 = r2 >> 4
    r1 = L01c25ce0
    r4 = r0 + r1
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201b21c:
    testset b[r4]
    ifeq goto L0201b21c
    csync
    r0 = r2 & 0xF
    [r3+24] &= ~(1 << r0)
    csync
    r0 = 0
    b[r4+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]

; phase3_p13_iic_open: 0x0201b23a..0x0201b2ce, module phase3-p13 (iic_open)
.type phase3_p13_iic_open,@function
phase3_p13_iic_open:
    [--sp] = {rets, r6-r4}
    r4 = [r0+12]
    r0 = r4
    call L0201b18a
    r5 = r0
    if (r5 == 0) goto L0201b2c8
    r0 = [r4+8]
    r1 = [r0+0]
    r2 = [r4+12]
    r1 &= r2  #
    r3 = [r5+4]
    r1 |= r3
    [r0+0] = r1
    r0 = b[r5+0] (u)
    if (r0 != 148) goto L0201b26a
    r1 = b[r5+1] (u)
    r0 = 148
    if (r1 == 149) {  ; @if.eq.ri.s12
    r1 = 0x51000
    [r1+0] |= 0x900
    }
L0201b26a:
    r1 = 1
    call phase3_p5_gpio_direction_output
    r0 = b[r5+1] (u)
    r1 = 1
    call phase3_p5_gpio_direction_output
    r0 = b[r5+0] (u)
    r1 = 1
    call phase3_p5_gpio_set_pull_up
    r0 = b[r5+1] (u)
    r1 = 1
    call phase3_p5_gpio_set_pull_up
    r0 = b[r5+0] (u)
    r1 = 0
    r6 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r5+1] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r5+0] (u)
    call phase3_p13_gpio_set_hd_0
    r0 = b[r5+1] (u)
    call phase3_p13_gpio_set_hd_0
    r0 = b[r5+0] (u)
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = b[r5+1] (u)
    r1 = 1
    call phase3_p5_gpio_set_die
    r0 = [r4+20]
    r1 = [r4+4]
    r1 = 513  #
    b[r0+8] = r1
    h[r0+0] = r1
    r1 = h[r0+0] (u)
    r1 = r1 | 0x5000
    h[r0+0] = r1
    goto L0201b2ca
L0201b2c8:
    r6 = -22
L0201b2ca:
    r0 = r6
    {pc, r6-r4} = [sp++]
