; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 2 functions, 0x02020210..0x02020376

; phase3_p8_vm_update_recover: 0x02020210..0x02020354, module phase3-p8 (vm_update_recover)
.type phase3_p8_vm_update_recover,@function
phase3_p8_vm_update_recover:
    [--sp] = {rets, r12-r4}
    sp += -104
    call L02020100
    if (r0 == 0) goto L02020350
    r0 = 0
    r1 = 0
    d[sp+96] = r1_r0
    d[sp+88] = r1_r0
    r2 = sp + 88
    r1 = 206
    r4 = 0
    call storage_control_ioctl
    r0 = [sp+100]
    r1 = [sp+92]
    r5 = r0 + r1  #
    [sp+84] = r4
    r8 = r5 + -256  #
    [sp+80] = r4
    r4 = sp + 0
    r2 = 80
    r0 = r4
    r1 = r8
    call L02020116
    r1 = sp + 80
    r0 = r4
    call phase3_p8_vm_recover_check
    if (r0 != 0) goto L02020290
    r1 = b[sp+88] (u)
    r0 = r1 << 8
    r1 += -1
    r1 = r1.b0 (u)
    r6 = 4096
    if (r1 <= 15) {  ; @if.le.ri.s12
    r6 = r0
    }
    call phase3_p8_sdfile_get_disk_capacity
    r7 = r0 - r6
L02020270:
    if (r7 <= 4096) goto L02020350
    r1 = r7 + -256
    r4 = sp + 0
    r2 = 80
    r0 = r4
    call L02020116
    r1 = sp + 80
    r0 = r4
    call phase3_p8_vm_recover_check
    r7 = r7 - r6
    if (r0 == 0) goto L02020270
L02020290:
    r10 = [sp+72]  ; @ld.w.sp.l
    r1 = -4096  #
    r0 = [sp+80]
    r0 += r10
    r0 = r0 + 4095
    r12 = r0 & r1
    r0 = sp + 84
    r2 = 4
    r1 = r12
    call L02020116
    r0 = [sp+84]
    r1 = 1437248085
    r9 = sp + 0
    if (r0 != r1) goto L02020350
    r11 = L01c26090
    r0 = [r11+4]
    r7 = [r11+0]
    r1 = r5 - r12
    r5 = umin(r1, r0)
    r6 = 0
    goto L02020314
L020202d8:
    r0 = b[sp+88] (u)
    if (r0 != 1) goto L020202ee
    r0 = 3
    r1 = r7
    call phase3_p8_sfc_erase
    r0 = 256
    goto L020202fa
L020202ee:
    r0 = 2
    r1 = r7
    call phase3_p8_sfc_erase
    r0 = 4096
L020202fa:
    r4 = r5 - r6
    r1 = r0 + r6
    if (r1 <= r5) {
    r4 = r0
    }
    r0 = r7
    r1 = r12
    r2 = r4
    call L020201dc
    r7 += r4  ; @add.rr
    r12 += r4
    r6 += r4  ; @add.rr
L02020314:
    if (r5 > r6) goto L020202d8
    r0 = 512
    call L0203c15c  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L0202033a
    r1 = [r11+0]
    r2 = 512
    call L02020116
    r0 = r6
    call L0203d218  ; @call.xl
L0202033a:
    r0 = 2
    r1 = r10
    call phase3_p8_sfc_erase
    [r9+72] = 0x0
    r0 = sp + 0
    r2 = 80
    r1 = r8
    call phase3_p8_sfc_write
L02020350:
    sp += 104
    {pc, r12-r4} = [sp++]

; phase3_p8_norflash_protect_suspend: 0x02020354..0x02020376, module phase3-p8 (norflash_protect_suspend)
.type phase3_p8_norflash_protect_suspend,@function
phase3_p8_norflash_protect_suspend:
    [--sp] = rets
    r0 = L01c3743c
    r1 = [r0+68]
    r2 = [r0+72]
    if (r2 != r1) {
    [r0+72] = r1
    r0 = 13
    r1 = 0
    call storage_control_control
    }
    pc = [sp++]
