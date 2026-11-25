; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p7: 5 functions, 0x01c008c4..0x01c009e2

; phase3_p7_norflash_enter_spi_code: 0x01c008c4..0x01c008d8, module phase3-p7 (norflash_enter_spi_code)
.type phase3_p7_norflash_enter_spi_code,@function
phase3_p7_norflash_enter_spi_code:
    [--sp] = rets
    call storage_control_bus_enter
    call storage_control_leave_continuous
    r1 = L01c25cf0
    [r1+0] = r0
    pc = [sp++]

; phase3_p7_norflash_entry_sleep: 0x01c008d8..0x01c00904, module phase3-p7 (norflash_entry_sleep)
.type phase3_p7_norflash_entry_sleep,@function
phase3_p7_norflash_entry_sleep:
    [--sp] = {rets, r4}
    call storage_control_bus_enter
    call storage_control_leave_continuous
    r4 = r0
    r0 = 0
    call storage_control_chip_select
    r0 = 185
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    if (r4 == 0) goto L01c008fc
    call storage_control_restore_read
L01c008fc:
    r0 = 0
    call storage_control_bus_leave
    {pc, r4} = [sp++]

; phase3_p7_norflash_eraser_otp: 0x01c00904..0x01c0099e, module phase3-p7 (norflash_eraser_otp)
.type phase3_p7_norflash_eraser_otp,@function
phase3_p7_norflash_eraser_otp:
    [--sp] = rets
    call storage_control_bus_enter
    call storage_control_write_enable
    r0 = 0
    call storage_control_chip_select
    r0 = 68
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 16
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    call storage_control_busy_wait
    csync
    call storage_control_write_enable
    r0 = 0
    call storage_control_chip_select
    r0 = 68
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 32
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    call storage_control_busy_wait
    csync
    call storage_control_write_enable
    r0 = 0
    call storage_control_chip_select
    r0 = 68
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 48
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    call storage_control_busy_wait
    csync
    r0 = 0
    call storage_control_bus_leave
    r0 = 0
    pc = [sp++]

; phase3_p7_norflash_exit_sleep: 0x01c0099e..0x01c009ca, module phase3-p7 (norflash_exit_sleep)
.type phase3_p7_norflash_exit_sleep,@function
phase3_p7_norflash_exit_sleep:
    [--sp] = {rets, r4}
    call storage_control_bus_enter
    call storage_control_leave_continuous
    r4 = r0
    r0 = 0
    call storage_control_chip_select
    r0 = 171
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    if (r4 == 0) goto L01c009c2
    call storage_control_restore_read
L01c009c2:
    r0 = 0
    call storage_control_bus_leave
    {pc, r4} = [sp++]

; phase3_p7_norflash_exit_spi_code: 0x01c009ca..0x01c009e2, module phase3-p7 (norflash_exit_spi_code)
.type phase3_p7_norflash_exit_spi_code,@function
phase3_p7_norflash_exit_spi_code:
    [--sp] = rets
    r0 = L01c25cf0
    r0 = [r0+0]
    if (r0 == 0) goto L01c009da
    call storage_control_restore_read
L01c009da:
    r0 = 0
    call storage_control_bus_leave
    pc = [sp++]
