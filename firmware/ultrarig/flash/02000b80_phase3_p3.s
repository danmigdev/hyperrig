; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 5 functions, 0x02000b80..0x02000ebc

; phase3_p3_nvram_set_boot_state: 0x02000b80..0x02000ba2, module phase3-p3 (nvram_set_boot_state)
.type phase3_p3_nvram_set_boot_state,@function
phase3_p3_nvram_set_boot_state:
    r0 = 29883776
    r1 = L0203a135  ; "usb_update_mode"
    rep 16 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = 160
    r1 = 4
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
L02000ba0:
    goto L02000ba0

; phase3_p3_wdt_tx_con: 0x02000ba2..0x02000bb0, module phase3-p3 (wdt_tx_con)
.type phase3_p3_wdt_tx_con,@function
phase3_p3_wdt_tx_con:
    [--sp] = rets
    r1 = r0
    r0 = 128
    call storage_fault_write_register  ; @call.xl
    pc = [sp++]

; phase3_p3_wdt_init: 0x02000bb0..0x02000be2, module phase3-p3 (wdt_init)
.type phase3_p3_wdt_init,@function
phase3_p3_wdt_init:
    [--sp] = rets
    r0 = 0
    call phase3_p3_wdt_tx_con
    r0 = 12
    call phase3_p3_wdt_tx_con
    r0 = 32
    call phase3_p3_wdt_or_con
    r0 = 64
    call phase3_p3_wdt_or_con
    r0 = 23
    r1 = 64
    call L01c00f72  ; @call.xl
    r0 = 16
    call phase3_p3_wdt_or_con
    r0 = 81412
    [r0+0] |= 0x10
    pc = [sp++]

; phase3_p3_clk_early_init: 0x02000be2..0x02000e06, module phase3-p3 (clk_early_init)
.type phase3_p3_clk_early_init,@function
phase3_p3_clk_early_init:
    [--sp] = {rets, r13-r4}
    r2 = 65544
    r13 = [r2+12]
    r12 = [r2+12]
    r11 = r2 + 6552  #
    r4 = [r2+12]
    r5 = [r11+0]
    r7 = [r11+8]
    r0 = [r11+12]
    r1 = 0x16A00
    r6 = [r1+0]
    r3 = 0
    r9 = 32436464
    [r9+0] = r3
    r5 = r5 & 0xC000000
    [r9+4] = r3
    if (r5 != 134217728) {
    r5 = 24000000
    } else {
    r5 = 40000000
    }
    r3 = uextra(r7, p:2, l:5)
    r3 += 2  ; @add.ri.u5
    r3 = r5 / r3 (u)
    r5 = 4095
    r0 &= r5
    r0 += 2  ; @add.ri.u5
    r7 = r0 * r3
    r8 = L02035810
    r0 = r4 & 0xF
    r3 = uextra(r6, p:18, l:10)
    r10 = r3 + 2
    r6 = L01c373b8
    if (r0 > 4) goto L02000c92
    r3 = uextra(r13, p:4, l:2)
    r3 += r8
    r3 = b[r3+234] (u)
    r4 = uextra(r12, p:6, l:2)
    r4 += r8
    r4 = b[r4+238] (u)
    r0 += -1
    if (r0 <= 3) {  ; @if.le.ri.s12
    r5 = r8 + 2788
    r0 = [r5+r0<<2]
    } else {
    r0 = 192000000
    }
    r0 = r0 / r3 (u)
    r5 = r0 / r4 (u)
    goto L02000cce
L02000c92:
    r3 = r4 + 11
    r3 = r3 & 0xF
    if (r3 >= 3) goto L02000ca8
    r0 = r7 << 1
    r3 = 0x4 - r3
    r5 = r0 / r3 (u)
    goto L02000cce
L02000ca8:
    r5 = 480000000
    r3 = r4 & 0xE  #
    [r6+8] = r5
    if (r3 != 8) goto L02000cd0
    r3 = 1
    if (r0 == 8) {  ; @if.eq.ri.s12
    r3 = 0
    }
    r0 = r10 >> r3
    r3 = 1000000
    r5 = r0 * r3
L02000cce:
    [r6+8] = r5
L02000cd0:
    r0 = [r2+0]
    r0 = [r2+0]
    [r6+24] = r0
    r0 = 262660
    r0 = [r0+0]
    b[r6+2] = r0
    r0 = [r2+0]
    r0 = uextra(r0, p:16, l:2)
    r0 += 1  ; @add.ri.u5
    b[r6+1] = r0
    r3 = [r2+0]
    r3 = uextra(r3, p:8, l:3)
    r3 += 1  ; @add.ri.u5
    r0 = r5 / r0 (u)  #
    b[r6+0] = r3
    r0 = r0 / r3 (u)  #
    [r6+20] = r0
    [r6+16] = r0
    r0 = [r1+8]
    r3 = 263168
    r0 = r0 & 0x18  #
    r3 = [r3+0]
    r3 = r3 & 0x800
    if (r0 != 24) goto L02000d28
    r0 = 0
    if (r3 == 0) goto L02000d2e
    r0 = r10 >> 1
    r3 = 1000000
    r0 *= r3
    goto L02000d2e
L02000d28:
    r0 = r7 >> 1
    if (r3 != 0) goto L02000d2e
    r0 = r3
L02000d2e:
    [r6+28] = r0
    [r6+32] = r5
    [r6+36] = r0
    r0 = [r2+8]
    r0 = r0 & 0xFFFFF3FF
    r0 |= 1024
    [r2+8] = r0
    r0 = 48000000
    [r6+12] = r0
    [r2+8] &= 0xFFFEFFFF
    [r11+4] |= 0x20000000
    [r2+8] &= 0xFFFFFFF3
    r0 = [r1+0]
    if ((r0 & 2) != 0) goto L02000dd2
    r0 = 0
    [r1+8] = r0
    r2 = [r1+8]
    r2 = r2 & 0xFFFFFFF8
    r2 |= 4
    [r1+8] = r2
    [r1+0] = r0
    [r1+0] |= 0x1
    r0 = [r1+0]
    r0 = r0 & 0xFFFFFFE7
    r0 |= 16
    [r1+0] = r0
    r0 = [r1+0]
    r0 = r0 & 0xFFFFFF9F
    r0 |= 32
    [r1+0] = r0
    r0 = [r1+0]
    r0 = r0 & 0xFFFFFE7F
    r0 |= 128
    [r1+0] = r0
    r0 = [r1+0]
    r0 = r0 & 0xFFFFF9FF
    r0 |= 1024
    [r1+0] = r0
    [r1+0] |= 0x800
    [r1+0] |= 0x16000
    [r1+0] |= 0x7780000
    [r1+0] |= 0x4
    r0 = -1000
    goto L02000dae
L02000daa:
    nop
    r0 += 1  ; @add.ri.u5
L02000dae:
    if (r0 != 0) goto L02000daa
    [r1+0] |= 0x2
    r0 = -1000
    goto L02000dbe
L02000dba:
    nop
    r0 += 1  ; @add.ri.u5
L02000dbe:
    if (r0 != 0) goto L02000dba
    [r1+0] &= 0xFFFFFFFB
    r0 = 4294867296
    goto L02000dd0
L02000dcc:
    nop
    r0 += 1  ; @add.ri.u5
L02000dd0:
    if (r0 != 0) goto L02000dcc
L02000dd2:
    [r11+4] &= 0xE7FFFFFF
    r0 = 4
    call L01c00fdc  ; @call.xl
    r0 = [r6+8]
    r1 = 100
    r0 = r0 / r1 (u)
    [r9+4] = r0
    r0 = L01c373e4
    r1 = L02033b54
    r1 = 13492  #
    [r0+4] = r1
    [r6+4] = 0x2D
    r1 += r8
    [r0+8] = r1
    {pc, r13-r4} = [sp++]

; phase3_p3_system_reset_reason_get: 0x02000e06..0x02000ebc, module phase3-p3 (system_reset_reason_get)
.type phase3_p3_system_reset_reason_get,@function
phase3_p3_system_reset_reason_get:
    [--sp] = {rets, r9-r4}
    r7 = L01c21cb0
    r4 = [r7+0]
    if (r4 != 0) goto L02000eb8
    r0 = 65728
    r9 = [r0+0]
    r0 = 18
    call storage_fault_read_register  ; @call.xl
    r8 = r0
    r0 = 32936
    call storage_fault_read_register  ; @call.xl
    r6 = r0
    r0 = 147
    call storage_fault_read_register  ; @call.xl
    r5 = r0
    r0 = 49
    call storage_fault_read_register  ; @call.xl
    r0 = 88
    call storage_fault_read_register  ; @call.xl
    r4 = 32
    if ((r6 & 1) != 0) goto L02000eac
    if ((r6 & 8) != 0) goto L02000e9e
    if (r5 == 255) goto L02000e5e
    if (r5 != 0) goto L02000ea6
L02000e5e:
    if ((r9 & 64) != 0) goto L02000e9e
    r4 = 16
    if ((r9 & 32) != 0) goto L02000eac
    if ((r8 & 64) != 0) goto L02000eac
    r4 = 1024
    if ((r0 & 0xA0) != 0) goto L02000eac
    r0 = r8 & 0xFFFFFF08
    r1 = r8
    r1 <= insert(r1, p:8, l:8)
    r1 = r1 & 0x304
    r0 |= r1
    r1 = r8 << 3
    r1 = r1 & 0x80
    r0 |= r1
    r1 = r8 >> 4
    r1 = r1 & 0x2
    r4 = r1 | r0
    goto L02000eac
L02000e9e:
    r4 = 64
    if (r5 == 0) goto L02000eac
    if (r5 == 255) goto L02000eac
L02000ea6:
    r4 = 64
    r4 <= insert(r5, p:16, l:8)
L02000eac:
    r0 = 49
    r1 = 64
    call L01c00f72  ; @call.xl
    [r7+0] = r4
L02000eb8:
    r0 = r4.l (u)
    {pc, r9-r4} = [sp++]
