; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p7: 2 functions, 0x01c00a02..0x01c00ab2

; phase3_p7_norflash_read_otp: 0x01c00a02..0x01c00a68, module phase3-p7 (norflash_read_otp)
.type phase3_p7_norflash_read_otp,@function
phase3_p7_norflash_read_otp:
    [--sp] = {rets, r8-r4}
    r4 = r2
    r5 = r1
    r8 = r0
    call storage_control_bus_enter
    r7 = 0
    goto L01c00a5a
L01c00a12:
    r6 = 0
    call storage_control_chip_select
    r0 = 72
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = r7 / r4 (s)
    r0 = r0 << 4
    r0 += 16  ; @add.ri.u5
    r0 = r0.b0 (u)
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 255
    call storage_control_send_byte
    r3 = r8 + r7
    goto L01c00a4e
L01c00a44:
    call storage_control_receive_byte
    b[r3+r6] = r0
    r6 += 1  ; @add.ri.u5
L01c00a4e:
    ifs (r6 < r4) goto L01c00a44
    r0 = 1
    call storage_control_chip_select
    r7 += r6  ; @add.rr
L01c00a5a:
    r0 = 0
    ifs (r7 < r5) goto L01c00a12
    call storage_control_bus_leave
    r0 = 0
    {pc, r8-r4} = [sp++]

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; phase3_p7_norflash_read_otp_general: 0x01c00a68..0x01c00ab2, module phase3-p7 (norflash_read_otp_general)
.type phase3_p7_norflash_read_otp_general,@function
phase3_p7_norflash_read_otp_general:
    [--sp] = {rets, r8-r4}
    r4 = r3
    r5 = r2
    r8 = r1
    r7 = r0
    r6 = -22
    if (r5 == 0) goto L01c00aae
    if (r4 == 0) goto L01c00aae
    call storage_control_bus_enter
    r0 = 0
    call storage_control_chip_select
    r0 = r7
    call storage_control_send_byte
    r0 = r8
    call storage_control_send_address
    r0 = 255
    call storage_control_send_byte
    goto L01c00a9e
L01c00a96:
    call storage_control_receive_byte
    b[r5++=1] = r0
    r4 += -1
L01c00a9e:
    if (r4 != 0) goto L01c00a96
    r0 = 1
    call storage_control_chip_select
    r0 = 0
    r6 = 0
    call storage_control_bus_leave
L01c00aae:
    r0 = r6
    {pc, r8-r4} = [sp++]
.endif
