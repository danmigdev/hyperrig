; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p7: 5 functions, 0x01c00af8..0x01c00b80

; phase3_p7_norflash_wait_busy: 0x01c00af8..0x01c00b00, module phase3-p7 (norflash_wait_busy)
.type phase3_p7_norflash_wait_busy,@function
phase3_p7_norflash_wait_busy:
    [--sp] = rets
    call storage_control_busy_wait
    pc = [sp++]

; phase3_p7_norflash_write_otp: 0x01c00b00..0x01c00b70, module phase3-p7 (norflash_write_otp)
.type phase3_p7_norflash_write_otp,@function
phase3_p7_norflash_write_otp:
    [--sp] = {rets, r8-r4}
    r4 = r2
    r5 = r1
    r8 = r0
    call storage_control_bus_enter
    r7 = 0
    goto L01c00b62
L01c00b10:
    call storage_control_write_enable
    r0 = 0
    r6 = 0
    call storage_control_chip_select
    r0 = 66
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = r7 / r4 (s)
    r0 = r0 << 4
    r0 += 16  ; @add.ri.u5
    r1 = r7 >> 8
    r0 |= r1
    r0 = r0.b0 (u)
    call storage_control_send_byte
    r0 = r7.b0 (u)
    call storage_control_send_byte
    r3 = r8 + r7
    goto L01c00b50
L01c00b46:
    r0 = b[r3+r6] (u)
    call storage_control_send_byte
    r6 += 1  ; @add.ri.u5
L01c00b50:
    ifs (r6 < r4) goto L01c00b46
    r0 = 1
    call storage_control_chip_select
    r7 += r6  ; @add.rr
    call storage_control_busy_wait
    csync
L01c00b62:
    ifs (r7 < r5) goto L01c00b10
    r0 = 0
    call storage_control_bus_leave
    r0 = 0
    {pc, r8-r4} = [sp++]

; phase3_p7_sfc_protect: 0x01c00b70..0x01c00b7c, module phase3-p7 (sfc_protect)
.type phase3_p7_sfc_protect,@function
phase3_p7_sfc_protect:
    r1 = L01c26890
    b[r1+66] = r0
    rts

; phase3_p7_sfc_suspend: 0x01c00b7c..0x01c00b7e, module phase3-p7 (sfc_suspend)
.type phase3_p7_sfc_suspend,@function
phase3_p7_sfc_suspend:
    rts

; phase3_p7_sfc_resume: 0x01c00b7e..0x01c00b80, module phase3-p7 (sfc_resume)
.type phase3_p7_sfc_resume,@function
phase3_p7_sfc_resume:
    rts
