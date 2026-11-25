; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 4 functions, 0x02020124..0x020201dc

; phase3_p8_sdfile_get_disk_capacity: 0x02020124..0x0202013a, module phase3-p8 (sdfile_get_disk_capacity)
.type phase3_p8_sdfile_get_disk_capacity,@function
phase3_p8_sdfile_get_disk_capacity:
    [--sp] = rets
    sp += -4
    r0 = 0
    [sp] = r0
    r2 = sp + 0
    r1 = 103
    call storage_control_ioctl
    r0 = [sp]
    sp += 4
    pc = [sp++]

; phase3_p8_vm_recover_check: 0x0202013a..0x020201a2, module phase3-p8 (vm_recover_check)
.type phase3_p8_vm_recover_check,@function
phase3_p8_vm_recover_check:
    [--sp] = {rets, r6-r4}
    sp += -32
    r6 = r0
    r5 = r1  #
    r0 = h[r6+2] (u)
    r0 = r0 - 0x5A00
    r0 = r0.l (u)
    r4 = 0
    if (r0 > 11) goto L0202019c
    r1 = 21569  #
    r0 = h[r6+6] (u)
    if (r0 != r1) goto L0202019c
    call phase3_p8_sdfile_get_disk_capacity
    r1 = [r6+72]
    r2 = r1 + -1
    if (r2 >= r0) goto L0202019c
    r6 = sp + 0
    r2 = 32
    r0 = r6
    call L02020116
    r0 = r6 | 0x2
    r1 = 30
    call L02001776
    r1 = h[sp] (u)
    if (r1 != r0) goto L0202019c
    r0 = sp + 0
    r0 += 16  ; @add.ri.u5
    r1 = L0203a17f  ; "LOADER.BIN"
    r2 = 11
    call capture_command_prefix  ; @call.xl
    if (r0 != 0) goto L0202019c
    r0 = [sp+8]
    [r5+0] = r0
    r4 = 1
L0202019c:
    r0 = r4
    sp += 32
    {pc, r6-r4} = [sp++]

; phase3_p8_sfc_erase: 0x020201a2..0x020201ce, module phase3-p8 (sfc_erase)
.type phase3_p8_sfc_erase,@function
phase3_p8_sfc_erase:
    [--sp] = rets
    r2 = r0 + -1
    r0 = 0
    if (r2 > 2) goto L020201cc
    r0 = L02035f74
    r3 = r0 + 12
    r0 = [r0+r2<<2]
    r3 = [r3+r2<<2]
    r2 = r0 & r1
    r0 = 0
    r1 = r3
    call storage_control_ioctl
    r0 = 1
L020201cc:
    pc = [sp++]

; phase3_p8_sfc_write: 0x020201ce..0x020201dc, module phase3-p8 (sfc_write)
.type phase3_p8_sfc_write,@function
phase3_p8_sfc_write:
    [--sp] = rets
    r3 = r1
    r1 = r0
    r0 = 0
    call storage_control_program
    pc = [sp++]
