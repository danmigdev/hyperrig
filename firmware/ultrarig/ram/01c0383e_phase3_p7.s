; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p7: 2 functions, 0x01c0383e..0x01c040a8

; phase3_p7_p33_soft_reset: 0x01c0383e..0x01c0384c, module phase3-p7 (p33_soft_reset)
.type phase3_p7_p33_soft_reset,@function
phase3_p7_p33_soft_reset:
    r0 = 160
    r1 = 4
    r2 = 1
    r3 = 1
    call storage_fault_masked_register
L01c0384a:
    goto L01c0384a

; phase3_p7_low_power_enter_and_exit: 0x01c0384c..0x01c040a8, module phase3-p7 (low_power_enter_and_exit)
.type phase3_p7_low_power_enter_and_exit,@function
phase3_p7_low_power_enter_and_exit:
    [--sp] = {rets, r15-r4}
    sp += -4
    r13 = L01c1fa30
    r1 = [r13+472]
    [sp] = r0
    if (r1 == 0) goto L01c03862
    r0 = 1
    call r1
L01c03862:
    call L0201d3d4  ; @call.xl
    r1 = [r13+472]
    if (r1 == 0) goto L01c03872
    r0 = 2
    call r1
L01c03872:
    csync
    r8 = 32432136
L01c0387a:
    r0 = [r8+0]
    if ((r0 & 16384) == 0) goto L01c0387a
    csync
    r4 = 262656
L01c0388a:
    r0 = [r4+0]
    ifs (r0 < 0) goto L01c0388a
    r9 = L01c3740c
    r0 = b[r9+0] (u)
    r5 = r4 + 516
    if ((r0 & 1) == 0) goto L01c038a8
    [r5+0] |= 0x80
    csync
L01c038a8:
    r0 = 1
    r1 = 8
    call L01c00f72
    r0 = b[r13+103] (u)
    r0 = r0 << 5
    r0 = r0 | 0xD6
    r1 = r0.b0 (u)
    r0 = 117
    call storage_fault_write_register
    r0 = b[r9+0] (u)
    if ((r0 & 4) != 0) goto L01c038d4
    r0 = 2
    r1 = 247
    call L01c0100e
    goto L01c038dc
L01c038d4:
    r0 = 2
    r1 = 8
    call L01c00f72
L01c038dc:
    r0 = 4
    r1 = 254
    call L01c0100e
    r0 = 2
    r1 = 191
    call L01c0100e
    r0 = 23
    r1 = 2
    call L01c00f72
    r0 = b[r9+0] (u)
    if ((r0 & 64) != 0) goto L01c03906
    r0 = 23
    r1 = 251
    call L01c0100e
    goto L01c0390e
L01c03906:
    r0 = 23
    r1 = 4
    call L01c00f72
L01c0390e:
    r0 = 23
    r1 = 32
    call L01c00f72
    r0 = 14
    call storage_fault_read_register
    if ((r0 & 0x3) != 0) {
    r0 = 0
    r1 = 32
    call L01c00f72
    }
    r0 = 32
    call storage_fault_read_register
    if ((r0 & 0x1) != 0) {
    r0 = 117
    r1 = 214
    call storage_fault_write_register
    }
    r0 = 17
    r1 = 254
    call L01c0100e
    r0 = b[r13+92] (u)
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = 0
    r1 = 4
    call L01c00f72
    }
    r0 = 6
    call storage_fault_read_register
    r0 = r0 & 0xFFFFFF07
    b[r9+11] = r0
    r0 = b[r9+0] (u)
    r12 = 327880
    r14 = r12 + 64
    r11 = r12 + 128
    r10 = r11 + 64
    if ((r0 & 1) == 0) goto L01c03a0a
    r0 = [r13+456]
    if (r0 == 0) goto L01c03a0a
    r1 = [r14+0]
    [r0+0] = r1
    r1 = [r14+4]
    [r0+4] = r1
    r1 = [r14+8]
    [r0+8] = r1
    r1 = [r14+12]
    [r0+12] = r1
    r1 = [r11+0]
    [r0+16] = r1
    r1 = [r11+4]
    [r0+20] = r1
    r1 = [r11+8]
    [r0+24] = r1
    r1 = [r11+12]
    [r0+28] = r1
    r1 = [r10+0]
    [r0+32] = r1
    r1 = [r10+4]
    [r0+36] = r1
    r1 = [r10+8]
    [r0+40] = r1
    r1 = [r10+12]
    [r0+44] = r1
    r0 = -5
    [r14+0] = r0
    [r14+4] = 0x4
    r0 = 0
    [r12+56] = r0
    [r14+8] = r0
    [r14+12] = r0
    [r11+8] = r0
    r1 = -1
    [r11+0] = r1
    [r11+12] = r0
    [r11+4] = r0
    [r11+24] = r0
    [r10+8] = r0
    [r10+0] = r1
    [r10+12] = r0
    [r10+4] = r0
    [r10+24] = r0
L01c03a0a:
    r0 = b[r13+99] (u)
    r15 = 71936
    r7 = 0x16A00
    if (r0 == 0) goto L01c03a98
    r0 = 22
    r1 = 219
    call L01c0100e
    r0 = 26
    call storage_fault_read_register
    if ((r0 & 1) != 0) goto L01c03a36
    r0 = 32
    call storage_fault_read_register
    if ((r0 & 1) == 0) goto L01c03a3e
L01c03a36:
    r0 = 22
    r1 = 32
    call L01c00f72
L01c03a3e:
    r0 = 22
    r1 = 33
    call L01c00f72
    r0 = b[r9+0] (u)
    if ((r0 & 0x20) == 0) {
    r0 = 22
    r1 = 4
    } else {
    r0 = 22
    r1 = 8
    }
    call L01c00f72
    r6 = b[r9+11] (u)
    r7 = -10
    goto L01c03a7e
L01c03a62:
    r6 += -1
    r3 = r6.b0 (u)
    r0 = 6
    r1 = 0
    r2 = 3
    call storage_fault_masked_register
    r0 = b[r13+97] (u)
    r0 *= r7
    goto L01c03a7c
L01c03a78:
    nop
    r0 += 1  ; @add.ri.u5
L01c03a7c:
    if (r0 != 0) goto L01c03a78
L01c03a7e:
    if ((r6 & 0xFF) != 0) goto L01c03a62
    call L01c0344c
    r0 = b[r13+99] (u)
    if (r0 == 0) goto L01c03abe
    r0 = 2
    r1 = 239
    call L01c0100e
    goto L01c03ac6
L01c03a98:
    r0 = 22
    r1 = 33
    call L01c00f72
    r0 = b[r9+0] (u)
    if ((r0 & 0x20) == 0) {
    r0 = 22
    r1 = 4
    } else {
    r0 = 22
    r1 = 8
    }
    call L01c00f72
    r0 = 1
    r1 = 127
    call L01c0100e
    goto L01c03b60
L01c03abe:
    r0 = 2
    r1 = 16
    call L01c00f72
L01c03ac6:
    r7 = 0x16A00
    r0 = b[r13+99] (u)
    r2 = r15 + 160
    if (r0 != 0) goto L01c03af2
    r0 = [r15+36]
    r1 = -32768
    r0 &= r1
    r1 = 12018
    r0 |= r1
    [r15+36] = r0
    r0 = 839489733
    [r15+32] = r0
L01c03af2:
    r0 = [r15+48]
    r0 = uextra(r0, p:23, l:5)
    b[r9+6] = r0
    [r2+0] &= 0xFFFFFFFC
    r1 = [r2+8]
    r0 = h[r9+0] (u)
    r0 <= insert(r1, p:9, l:1)
    h[r9+0] = r0
    if ((r1 & 0x1) != 0) {
    [r2+8] &= 0xFFFFFFFC
    r0 = h[r9+0] (u)
    }
    r2 = r2 + -6817  #
    r1 = [r7+0]
    r0 &= r2
    r2 = r1 << 7
    r2 = r2 & 0x100
    r0 |= r2
    r1 = r1 >> 1
    h[r9+0] = r0
    if ((r1 & 0x1) != 0) {
    [r7+0] &= 0xFFFFFFF9
    }
    csync
    [r15+48] &= 0xFFFFFFFE
    csync
    r0 = 1
    r1 = 127
    call L01c0100e
    [r15+0] &= 0xFFFFFFFE
    csync
    r0 = b[r13+97] (u)
    r1 = -10
    r0 *= r1
    goto L01c03b5e
L01c03b5a:
    nop
    r0 += 1  ; @add.ri.u5
L01c03b5e:
    if (r0 != 0) goto L01c03b5a
L01c03b60:
    csync
L01c03b62:
    r0 = [r8+0]
    if ((r0 & 16384) == 0) goto L01c03b62
    csync
L01c03b6c:
    r0 = [r4+0]
    ifs (r0 < 0) goto L01c03b6c
    r0 = 15
    call storage_fault_read_register
    b[r9+9] = r0
    [r4+0] &= 0xFFFFFFFE
    csync
    r0 = [r12+4]
    b[r9+12] = r0
    r0 = [r12+24]
    b[r9+13] = r0
    r0 = [r12+8]
    b[r9+14] = r0
    r0 = [r12+12]
    b[r9+15] = r0
    r0 = [r12+0]
    b[r9+16] = r0
    r0 = b[r9+0] (u)
    if ((r0 & 64) != 0) goto L01c03bd4
    r0 = 15
    r1 = 0
    r6 = 0
    call storage_fault_write_register
    [r12+8] = r6
    [r12+12] = r6
    r0 = r15 + -6401
    [r12+0] = r0
    [r12+4] = r6
    [r12+24] = r6
L01c03bd4:
    r8 = 0x10000
    [r8+0] |= 0x8
    csync
    r0 = b[r9+0] (s)
    ifs (r0 < 0) {  ; @ifs.lt.ri.s12
    r0 = 128
    r1 = 223
    } else {
    r0 = 128
    r1 = 239
    }
    call L01c0100e
    r0 = 0
    call sdk___hw_nv_timer_is_runnig
    if (r0 == 0) goto L01c03c80
    r14 = r11
    r7 = r10
    call L01c03694
    r1 = [r13+460]
    r2 = 1000000
    r3_r2 = r0 * r2 (u)
    r11_r10 = r3_r2 / r1 (u)
    r1 = b[r9+0] (u)
    r0 = [r13+76]
    if ((r1 & 0x1) != 0) {
    r1 = [r9+36]
    r0 += r1  ; @add.rr
    r0 = r0 + 6000
    } else {
    r0 = r0 + 4000
    }
    r0 = r0 + 4000
    if (r10 >= r0) goto L01c03c4c
    r0 = 1
    b[r13+90] = r0
    r6 = 0
    r10 = r7
    r11 = r14
    r14 = r12 + 64
    r7 = 0x16A00
    goto L01c03d06
L01c03c4c:
    call L01c0374a
    r1 = b[r9+0] (u)
    r0 = [r13+76]
    if ((r1 & 0x1) != 0) {
    r1 = [r9+36]
    r0 += r1  ; @add.rr
    r0 = r0 + 6000
    } else {
    r0 = r0 + 4000
    }
    r1 = r10 + -2000
    r0 = r1 - r0
    call L01c03812
    r10 = r7
    r11 = r14
    r14 = r12 + 64
    r7 = 0x16A00
L01c03c80:
    r0 = 52
    r1 = 5
    call storage_fault_write_register
    r6 = 0x13E00
    r0 = [r6+0]
    if ((r0 & 64) != 0) goto L01c03cfe
    r0 = [r6+0]
    if ((r0 & 128) != 0) goto L01c03cfe
    r3 = b[r9+18] (u)
    if (r3 != 0) goto L01c03ca0
    r3 = 9
L01c03ca0:
    r0 = 9
    r1 = 0
    r2 = 4
    call storage_fault_masked_register
    [r6+0] |= 0x10
    [r8+0] |= 0x4
    csync
L01c03cb4:
    csync
    r0 = [r6+0]
    if ((r0 & 0xC0) != 0) goto L01c03cc6
    r0 = [r6+4]
    if ((r0 & 0xE1) == 0) goto L01c03cb4
L01c03cc6:
    r0 = b[r9+7] (u)
    r6 = 0
    if (r0 == 0) goto L01c03d06
    r0 = 147
    call storage_fault_read_register
    r1 = b[r9+7] (u)
    if ((r1 & r0) == 0) goto L01c03d06
    r0 = 147
    call storage_fault_read_register
    r1 = b[r9+7] (u)
    r0 &= r1
    b[r9+7] = r0
    r0 = 148
    call storage_fault_read_register
    if ((r0 & 1) == 0) goto L01c03d0a
    r0 = b[r9+7] (u)
    r6 = r0 >> 1
    goto L01c03d06
L01c03cfe:
    r0 = 1
    b[r13+90] = r0
    r6 = 0
L01c03d06:
    b[r9+7] = r6
L01c03d0a:
    csync
    rep 20 {
    nop
    }
    [r8+0] &= 0xFFFFFFFB
    csync
    r3 = b[r9+17] (u)
    r0 = 9
    r1 = 0
    r2 = 4
    call storage_fault_masked_register
    r1 = b[r9+10] (u)
    r0 = 128
    call storage_fault_write_register
    r3 = b[r9+11] (u)
    r0 = 6
    r1 = 0
    r2 = 3
    call storage_fault_masked_register
    r0 = b[r13+97] (u)
    r1 = -10
    r0 *= r1
    goto L01c03d4a
L01c03d46:
    nop
    r0 += 1  ; @add.ri.u5
L01c03d4a:
    if (r0 != 0) goto L01c03d46
    r0 = b[r9+16] (u)
    [r12+0] = r0
    r0 = b[r9+14] (u)
    [r12+8] = r0
    r0 = b[r9+15] (u)
    [r12+12] = r0
    r0 = b[r9+12] (u)
    [r12+4] = r0
    r0 = b[r9+13] (u)
    [r12+24] = r0
    csync
    r0 = b[r9+0] (u)
    if ((r0 & 0x40) == 0) {
    r1 = b[r9+9] (u)
    r0 = 15
    call storage_fault_write_register
    }
    csync
    rep 20 {
    nop
    }
    [r4+0] |= 0x1
    csync
    rep 20 {
    nop
    }
    [r15+0] |= 0x1
    r0 = 131200
    [r15+48] |= r0
    r0 = [r15+48]
    r0 = r0 & 0xF07FFFFF
    r0 = r0 | 0x9800000
    [r15+48] = r0
    [r15+48] |= 0x1
    csync
    csync
    rep 20 {
    nop
    }
    r0 = 1
    r1 = 127
    call L01c0100e
    r0 = 23
    r1 = 251
    call L01c0100e
    csync
    rep 20 {
    nop
    }
    r0 = 1
    r1 = 247
    call L01c0100e
    r0 = b[r9+0] (u)
    if ((r0 & 4) != 0) goto L01c03df2
    r0 = 2
    r1 = 247
    call L01c0100e
    goto L01c03dfa
L01c03df2:
    r0 = 2
    r1 = 8
    call L01c00f72
L01c03dfa:
    r0 = 4
    r1 = 1
    call L01c00f72
    r0 = 2
    r1 = 191
    call L01c0100e
    r0 = 17
    r1 = 64
    call L01c00f72
    r0 = b[r9+0] (u)
    if ((r0 & 2) != 0) goto L01c03e24
    r0 = 17
    r1 = 254
    call L01c0100e
    goto L01c03e2c
L01c03e24:
    r0 = 17
    r1 = 1
    call L01c00f72
L01c03e2c:
    r0 = 23
    r1 = 223
    call L01c0100e
    r0 = b[r13+102] (u)
    if (r0 == 0) goto L01c03e44
    r0 = 2
    r1 = 239
    call L01c0100e
    goto L01c03e4c
L01c03e44:
    r0 = 2
    r1 = 16
    call L01c00f72
L01c03e4c:
    r0 = b[r13+92] (u)
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = 0
    r1 = 251
    call L01c0100e
    }
    r0 = b[r13+99] (u)
    r3 = 0x10400
    r1 = r3 + 5536
    if (r0 == 0) goto L01c03ee0
    [r1+0] |= 0x1
    r0 = h[r9+0] (u)
    if ((r0 & 0x200) != 0) {
    [r1+8] |= 0x1
    r0 = h[r9+0] (u)
    }
    if ((r0 & 0x100) != 0) {
    [r7+0] |= 0x2
    }
    csync
    [r3+0] = 0x4000
    [r3+4] = 0x0
    [r3+8] = 0x4B00
    [r3+0] = 0x1
L01c03e98:
    r0 = [r3+0]
    if ((r0 & 32768) == 0) goto L01c03e98
    [r3+0] = 0x4000
    [r1+0] |= 0x2
    r0 = h[r9+0] (u)
    if ((r0 & 0x200) != 0) {
    [r1+8] |= 0x2
    r0 = h[r9+0] (u)
    }
    if ((r0 & 0x100) != 0) {
    [r7+0] |= 0x4
    }
    csync
    [r3+0] = 0x4000
    [r3+4] = 0x0
    [r3+8] = 0x4B0
    [r3+0] = 0x1
L01c03ed0:
    r0 = [r3+0]
    if ((r0 & 32768) == 0) goto L01c03ed0
    [r3+0] = 0x4000
    csync
    call sdk_sys_clk_source_rc_clk_off
L01c03ee0:
    [r3+0] = 0x4000
    [r3+4] = 0x0
    [r3+8] = 0x3C
    [r3+0] = 0x1
L01c03ef0:
    r0 = [r3+0]
    if ((r0 & 32768) == 0) goto L01c03ef0
    [r3+0] = 0x4000
    r0 = 4294836095
    [r15+48] &= r0
    r0 = [r15+48]
    r1 = b[r9+6] (u)
    r0 = r0 & 0xF07FFFFF
    r1 = r1 & 0xFFFFFF1F
    r0 <= insert(r1, p:23, l:5)
    [r15+48] = r0
    r0 = b[r9+0] (u)
    if ((r0 & 1) == 0) goto L01c03fba
    r0 = [r13+456]
    if (r0 == 0) goto L01c03f7a
    r1 = [r0+0]
    r1 &= 4294967291
    [r14+0] = r1
    r1 = [r0+4]
    r1 &= 4294967291
    [r14+4] = r1
    r1 = [r0+8]
    r1 &= 4294967291
    [r14+8] = r1
    r1 = [r0+12]
    r1 &= 4294967291
    [r14+12] = r1
    r1 = [r0+16]
    [r11+0] = r1
    r1 = [r0+20]
    [r11+4] = r1
    r1 = [r0+24]
    [r11+8] = r1
    r1 = [r0+28]
    [r11+12] = r1
    r1 = [r0+32]
    [r10+0] = r1
    r1 = [r0+36]
    [r10+4] = r1
    r1 = [r0+40]
    [r10+8] = r1
    r0 = [r0+44]
    [r10+12] = r0
L01c03f7a:
    r0 = [r9+36]
    [r3+0] = 0x4000
    [r3+4] = 0x0
    r0 = r0 * 0xC
    [r3+8] = r0
    [r3+0] = 0x1
L01c03f90:
    r0 = [r3+0]
    if ((r0 & 32768) == 0) goto L01c03f90
    r0 = 16384
    [r3+0] = r0
    [r5+0] |= 0x20
    csync
    [r3+0] = r0
    [r3+4] = 0x0
    [r3+8] = 0x4B0
    [r3+0] = 0x1
L01c03fb0:
    r0 = [r3+0]
    if ((r0 & 32768) == 0) goto L01c03fb0
    [r3+0] = 0x4000
L01c03fba:
    call L01c00bb2  ; @call.xl
    r4 = 0
    r5 = L02035340  ; "flash_powerup_ok"
    r6 = L01c1fc20  ; "flash_powerup_ok"
    r7 = 100
L01c03fd0:
    r1 = 32
    r0 = r5
    call storage_control_cache_forward  ; @call.xl
    r0 = 0
L01c03fdc:
    if (r0 > 31) goto L01c03ff2
    r1 = b[r0+r6] (u)
    r2 = b[r0+r5] (u)
    r0 += 1  ; @add.ri.u5
    if (r1 == r2) goto L01c03fdc
    r0 = 1
    goto L01c03ff4
L01c03ff2:
    r0 = 0
L01c03ff4:
    r4 += 1  ; @add.ri.u5
    r1 = r4.b0 (u)
    r2 = r1 / r7 (u)
    r2 = r2 * 0x64
    r1 = r1 - r2
    if (r1 == 0) goto L01c04068
    if (r0 != 0) goto L01c03fd0
    r0 = b[r9+0] (u)
    if ((r0 & 1) == 0) goto L01c04054
    r4 = L01c1f0a0  ; "sdram_powerup_ok"
    if (r4 < 67108864) goto L01c04054
    r5 = 100
L01c0401c:
    r5 += -1
    if (r5 == 0) goto L01c040a2
    r1_r0 = 0
    goto L01c0402c
L01c04024:
    b[r1+r4] = r0
    r0 += 1  ; @add.ri.u5
    r1 += 1  ; @add.ri.u5
L01c0402c:
    if (r1 != 32) goto L01c04024
    call L01c00c8c  ; @call.xl
    r1_r0 = 0
    goto L01c04040
L01c0403a:
    r1 = r1 + 0x1000000
    r0 += 1  ; @add.ri.u5
L01c04040:
    if (r0 > 31) goto L01c04050
    r2 = b[r0+r4] (s)
    r3 = r1 >>> 24
    if (r2 == r3) goto L01c0403a
    goto L01c0401c
L01c04050:
    if (r0 != 32) goto L01c0401c
L01c04054:
    call L0201d94c  ; @call.xl
    r1 = [r13+476]
    if (r1 == 0) goto L01c04064
    r0 = [sp]
    call r1
L01c04064:
    sp += 4
    {pc, r15-r4} = [sp++]
L01c04068:
    r0 = b[r9+0] (u)
    if ((r0 & 64) != 0) goto L01c040a2
    r0 = 15
    r1 = 0
    call storage_fault_write_register
    r0 = b[r13+97] (u)
    r1 = -10
    r0 *= r1
    goto L01c04086
L01c04082:
    nop
    r0 += 1  ; @add.ri.u5
L01c04086:
    if (r0 != 0) goto L01c04082
    r1 = b[r9+9] (u)
    r0 = 15
    call storage_fault_write_register
    r0 = b[r13+97] (u)
    r1 = -10
    r0 *= r1
    goto L01c040a0
L01c0409c:
    nop
    r0 += 1  ; @add.ri.u5
L01c040a0:
    if (r0 != 0) goto L01c0409c
L01c040a2:
    call phase3_p7_p33_soft_reset
L01c040a6:
    goto L01c040a6
