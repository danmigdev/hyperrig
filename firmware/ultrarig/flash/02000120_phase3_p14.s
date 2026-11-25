; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p14: 6 functions, 0x02000120..0x02000238

; phase3_p14_start: 0x02000120..0x02000122, module phase3-p14 (start)
.type phase3_p14_start,@function
phase3_p14_start:
    goto phase3_p14_chip_entry

; phase3_p14_wait_if_breakpoint: 0x02000122..0x02000124, module phase3-p14 (wait_if_breakpoint)
.type phase3_p14_wait_if_breakpoint,@function
phase3_p14_wait_if_breakpoint:
    rts

; phase3_p14_check_key_trampoline: 0x02000124..0x0200012e, module phase3-p14 (check_key_trampoline)
.type phase3_p14_check_key_trampoline,@function
phase3_p14_check_key_trampoline:
    csync
L02000126:
    reti = L02041656
    rti

; phase3_p14_check_key_request: 0x0200012e..0x0200018a, module phase3-p14 (check_key_request)
.type phase3_p14_check_key_request,@function
phase3_p14_check_key_request:
    [--sp] = {rets, r4}
    sp += -4
    [sp] = r0
    r0 = [sp]
    r1 = 29884168
    [r1+8] = 0x0
    [r1+0] = r0
    r2 = [r1+228]
    r0 = L02000126 + 2
    r3 = [r0+0]
    r0 = 0
    if (r3 != r2) goto L02000186
    [r1+4] &= 0x7FFFFFFF
    r0 = cnum
    r2 = r0 << 9
    r0 = 32436540
    r0 = r0 + r2
    [r0+0] |= 0x1000
    csync
    r3 = 8109160
    r4 = 8
    [r2+r3<<2] = r4
L02000178:
    csync
    r2 = [r1+4]
    ifs (r2 > -1) goto L02000178
    [r0+0] &= 0xFFFFEFFF
    r0 = [r1+8]
L02000186:
    sp += 4
    {pc, r4} = [sp++]

; phase3_p14_chip_entry: 0x0200018a..0x02000224, module phase3-p14 (chip_entry)
.type phase3_p14_chip_entry,@function
phase3_p14_chip_entry:
; HyperRig MINI v4, patch mini_entry_footswitch_recovery_v2: Branch before G startup to an application guard: preserve context, force PA10/PA0/PA3 input, check the chord, then reset with stock ROM marker or resume the original G entry.
.if TARGET_MINI
    goto hyperrig_mini_entry_guard_v2  ; @goto.l
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
    nop  ; @nop
.else
    sp = L01c350b8
    ssp = L01c360b8
.endif
    call L0200042e  ; @call.xl
    r3 = L01c2030c
    r1 = 0
    r2 = ultrarig_bss_size
    r2 = r2 >> 2
L020001ac:
    rep r2 {
    [r3++=4] = r1
    }
    if (r2 != 0) goto L020001ac
    r4 = ultrarig_ram_start
    r1 = ultrarig_ram_image_load
    r2 = ultrarig_ram_image_size
    r2 = r2 >> 2
L020001c6:
    rep r2 {
    r3 = [r1++=4]
    [r4++=4] = r3
    }
    if (r2 != 0) goto L020001c6
    call L02000484  ; @call.xl
    r3 = r0
    r0 = 67109152
    r1 = ultrarig_ram_image_load
    r2 = 0  ; @li.u32
    if (r0 == r1) goto L020001f4
    call L02000486  ; @call.xl
    r0 = r3
L020001f4:
    r3 = 67109152
    r1 = 0
    r2 = 0  ; @li.u32
    r2 = r2 >> 2
L02000204:
    rep r2 {
    [r3++=4] = r1
    }
    if (r2 != 0) goto L02000204
    call L01c00cc0  ; @call.xl
    call L0203e358  ; @call.xl
    call L020017f6  ; @call.xl
    r6 = phase3_p3_main
    goto r6

; phase3_p14_cpu1_start: 0x02000224..0x02000238, module phase3-p14 (cpu1_start)
.type phase3_p14_cpu1_start,@function
phase3_p14_cpu1_start:
    usp = L01c363b8
    sp = L01c373b8
    reti = L02000ad0
    rti
