; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; command_services: 4 functions, 0x02006d14..0x02006f14

; command_services_console_write: 0x02006d14..0x02006e00, module command-services (console_write)
.type command_services_console_write,@function
command_services_console_write:
    [--sp] = {rets, r14-r4}
    r9_r8 = r1_r0
    r11_r10 = 0
    r13 = L01c26890
    r12 = 0
    goto L02006de0
L02006d24:
    r0 = b[r13+148] (u)
    if (r0 != 0) goto L02006d68
    call storage_platform_clock  ; @call.xl
    r14 = r0
    call preset_application_rate
    r4 = r0 << 1
    r7 = 0
    goto L02006d42
L02006d3c:
    call storage_coordination_poll_forward
    r7 += 1  ; @add.ri.u5
L02006d42:
    call L02006a9e
    r5 = r0
    call phase3_p4_cdc_ready
    r6 = r0
    call storage_platform_clock  ; @call.xl
    if (r7 > 1999) goto L02006d68
    if ((r5 & 1) == 0) goto L02006d68
    if (r6 == 0) goto L02006d68
    r0 = r0 - r14
    if (r0 <= r4) goto L02006d3c
L02006d68:
    r5 = 0
    goto L02006d8a
L02006d6c:
    r0 = 1
    if (r5 <= 9) {  ; @if.le.ri.s12
    r0 = 0
    }
    r0 |= r1
    if ((r0 & 1) != 0) goto L02006de6
    call phase3_p4_cdc_ready
    if (r0 == 0) goto L02006dea
    r0 = 1
    call L0203feb8  ; @call.xl
    r5 += 1  ; @add.ri.u5
L02006d8a:
    call L02006a9e
    r1 = b[r13+148] (u)
    if ((r0 & 1) != 0) goto L02006d6c
    if ((r1 & 1) == 0) goto L02006daa
    b[r13+148] = r11
    r2 = [r13+144]
    r0 = 14
    r1 = 3
    call storage_coordination_notify
L02006daa:
    r0 = r8 + r10
    r5 = r9 - r10
    r1 = r5
    call phase3_p4_cdc_write_data
    r0 = umin(r0, r5)
    r10 += r0
    if (r12 > 7) goto L02006dfc
    if (r10 >= r9) goto L02006dfc
    call phase3_p4_cdc_ready
    if (r0 == 0) goto L02006dfc
    r0 = r13 + 140
    [r0+0] += 1  ; @rmw.add.s12
    r0 = 1
    call L0203feb8  ; @call.xl
    r12 = r12 + 1
L02006de0:
    if (r10 < r9) goto L02006d24
    goto L02006dfc
L02006de6:
    if ((r1 & 1) != 0) goto L02006dfc
L02006dea:
    r0 = 1
    b[r13+148] = r0
    r2 = [r13+144]
    r0 = 14
    r1 = 2
    call storage_coordination_notify
L02006dfc:
    r0 = r10
    {pc, r14-r4} = [sp++]

; command_services_counted_write: 0x02006e00..0x02006e24, module command-services (counted_write)
.type command_services_counted_write,@function
command_services_counted_write:
    [--sp] = {rets, r5, r4}
    r4 = L01c26890
    r5 = [r4+140]
    call command_services_console_write
    r2 = [r4+140]
    r4 = r0
    if (r2 != r5) {
    r0 = 14
    r1 = 5
    call storage_coordination_notify
    }
    r0 = r4
    {pc, r5, r4} = [sp++]

; command_services_console_send: 0x02006e24..0x02006ecc, module command-services (console_send)
.type command_services_console_send,@function
command_services_console_send:
    [--sp] = {rets, r8-r4}
    r8 = L01c26890
    r2 = b[r8+136] (u)
    r4 = r1
    r5 = r0
    if (r2 == 0) goto L02006e3c
    call link_and_print_other_send
    {pc, r8-r4} = [sp++]
L02006e3c:
    call phase3_p4_cdc_ready
    if (r0 == 0) goto L02006eb2
    r6 = L01c1f180
    r0 = [r6+24]
    r0 = r0 * 0xA
    [r8+100] = r0
    r0 = L01c26844
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L02006e78
    r1 = 0
    r0 = r6  #
    b[r0+0] = r1
    r1 = 1
    r7 = 1
    call command_services_console_write
    if (r0 == 1) {  ; @if.eq.ri.s12
    r0 = r8 + 1452
    [r0+0] += 1  ; @rmw.add.s12
    b[r6+1] = r7
    }
L02006e78:
    if (r4 == 0) goto L02006e8c
    r0 = b[r6+1] (u)
    if (r0 != 0) goto L02006e8c
    r1 = 1
    r7 = 1
    r0 = r6
    call command_services_counted_write
    if (r0 != 1) goto L02006eb4
    b[r6+1] = r7
L02006e8c:
    if (r4 == 0) goto L02006eb2
L02006e8e:
    r7 = r4
    if (r4 >= 63) {  ; @if.ge.ri.s12
    r7 = 63
    }
    r0 = r5
    r1 = r7
    call command_services_counted_write
    if (r0 != r7) goto L02006ebe
    r5 += r7  ; @add.rr
    r1 = b[r5+-1] (u)
    r0 = 1
    if (r1 != 10) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r4 = r4 - r7  #
    b[r6+1] = r0
    if (r4 != 0) goto L02006e8e
L02006eb2:
    {pc, r8-r4} = [sp++]
L02006eb4:
    r0 = r8 + 144
    [r0+0] += 1  ; @rmw.add.s12
    {pc, r8-r4} = [sp++]
L02006ebe:
    r0 = r8 + 144
    [r0+0] += 1  ; @rmw.add.s12
    r0 = 0
    b[r6+1] = r0
    {pc, r8-r4} = [sp++]

; command_services_decimal_field: 0x02006ecc..0x02006f14, module command-services (decimal_field)
.type command_services_decimal_field,@function
command_services_decimal_field:
    [--sp] = {rets, r7-r4}
    r3 = [r0+0]
    r2 = 0
    r6 = 99999999
    r4 = 0
    goto L02006eea
L02006edc:
    if (r2 > r6) goto L02006f10
    r2 = r2 * 0xA
    r2 += r5  ; @add.rr
    r2 += -48
    r4 += 1  ; @add.ri.u5
L02006eea:
    r5 = b[r3+r4] (s)
    r7 = r5 + -48
    r7 = r7.b0 (u)
    if (r7 <= 9) goto L02006edc
    if (r4 == 0) goto L02006f10
    r3 += r4  ; @add.rr
    goto L02006f02
L02006efe:
    r3 += 1  ; @add.ri.u5
    r5 = b[r3+0] (u)
L02006f02:
    r4 = r5.b0 (u)
    if (r4 == 32) goto L02006efe
    [r0+0] = r3
    [r1+0] = r2
    r0 = 0
    {pc, r7-r4} = [sp++]
L02006f10:
    r0 = -1
    {pc, r7-r4} = [sp++]
