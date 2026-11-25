; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 6 functions, 0x0201f834..0x0201fa72

; phase3_p8_fclose: 0x0201f834..0x0201f936, module phase3-p8 (fclose)
.type phase3_p8_fclose,@function
phase3_p8_fclose:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r5 = -1
    if (r4 == 0) goto L0201f932
    r0 = [r4+0]
    if (r0 == 0) goto L0201f932
    r0 += 84
    call L02040614  ; @call.xl
    r5 = r0  #
    r1 = [r4+0]
    r2 = b[r1+164] (u)
    if (r2 != 0) goto L0201f860
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    r1 = [r4+0]
    r5 = -22
L0201f860:
    r0 = [r1+8]
    r2 = [r0+68]
    if (r2 == 0) goto L0201f86e
    r0 = r4
    call r2
    r1 = [r4+0]
L0201f86e:
    r0 = [r1+12]
    if (r0 == 0) goto L0201f87e
    r1 = [r0+8]
    r3 = [r1+24]
    if (r3 == 0) goto L0201f87e
    r1 = 16
    r2 = 0
    call r3
L0201f87e:
    if (r5 != 0) goto L0201f88a
    r0 = [r4+0]
    r0 += 84
    call L0204074c  ; @call.xl
L0201f88a:
    r6 = [r4+0]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0201f8aa
    lockset
L0201f8aa:
    csync
    r3 = r6 + 72
    r1 = [r3+8]
    r7 = r1 + -1
    [r3+8] = r7
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0201f8cc
    lockclr
L0201f8cc:
    call storage_coordination_irq_leave  ; @call.xl
    if (r7 != 0) goto L0201f92c
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = L01c26890
    r1 = r0 + 72
L0201f8e6:
    testset b[r1]
    ifeq goto L0201f8e6
    csync
    {r2, r1} = [r3+]
    [r1+4] = r2
    [r2+0] = r1
    [r3+0] = r3
    [r3+4] = r3
    csync
    r1 = 0
    b[r0+72] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r6+8]
    r1 = [r0+8]
    if (r1 == 0) goto L0201f912
    r0 = r6
    call r1
L0201f912:
    r0 = r6 + 84
    call L0204175a  ; @call.xl
    r0 = [r6+4]
    call L0203d218  ; @call.xl
    r0 = r6
    call L0203d218  ; @call.xl
L0201f92c:
    r0 = r4
    call L0201f2da
L0201f932:
    r0 = r5
    {pc, r7-r4} = [sp++]

; phase3_p8_syscfg_file_close: 0x0201f936..0x0201f940, module phase3-p8 (syscfg_file_close)
.type phase3_p8_syscfg_file_close,@function
phase3_p8_syscfg_file_close:
    [--sp] = rets
    if (r0 == 0) goto L0201f93e
    call phase3_p8_fclose  ; @call.l
L0201f93e:
    pc = [sp++]

; phase3_p8_get_system_enc_key: 0x0201f940..0x0201f94a, module phase3-p8 (get_system_enc_key)
.type phase3_p8_get_system_enc_key,@function
phase3_p8_get_system_enc_key:
    r0 = 29883724
    r0 = h[r0+28] (u)
    rts

; phase3_p8_norflash_read: 0x0201f94a..0x0201f9e0, module phase3-p8 (norflash_read)
.type phase3_p8_norflash_read,@function
phase3_p8_norflash_read:
    [--sp] = {rets, r10-r4}
    r8 = L01c3743c
    r3 = [r8+48]
    r7 = r2
    r4 = r1
    r9 = r0
    r5 = r7 + r4
    if (r3 > r7) goto L0201f976
    r0 = 16773121
    if (r5 < r0) goto L0201f9c8
    r0 = [r8+24]
    if (r0 <= 16777216) goto L0201f9c8
L0201f976:
    r10 = L01c26890
    r6 = r10 + 3748
    r0 = r6
    call L02040614  ; @call.xl
    r0 = b[r10+67] (u)
    r0 += 1  ; @add.ri.u5
    b[r10+67] = r0
    r0 = r9
    r1 = r7
    r2 = r4
    call storage_control_device_read  ; @call.xl
    r0 = [r8+36]
    if (r5 > r0) goto L0201f9b4
    call phase3_p8_get_system_enc_key
    r0 = r0.l (u)
    r3 = 0
    r1 = r9
    r2 = r4
    call L0201eec0
L0201f9b4:
    r0 = b[r10+67] (u)
    r0 += -1
    b[r10+67] = r0
    r0 = r6
    call L0204074c  ; @call.xl
    goto L0201f9dc
L0201f9c8:
    r0 = r7
    call storage_control_translate  ; @call.xl
    r1 = r0
    r0 = r9
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
L0201f9dc:
    r0 = r4
    {pc, r10-r4} = [sp++]

; phase3_p8_memcpy_flash: 0x0201f9e0..0x0201fa6c, module phase3-p8 (memcpy_flash)
.type phase3_p8_memcpy_flash,@function
phase3_p8_memcpy_flash:
    [--sp] = {rets, r8-r4}
    r4 = r2
    r6 = r1
    r5 = r0
    r0 = r6 + r4
    call L01c008b4  ; @call.xl
    r0 = r0 >> 24
    if (r0 != 0) goto L0201fa02
    r0 = r5
    r1 = r6
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    {pc, r8-r4} = [sp++]
L0201fa02:
    if (r6 < 33554432) goto L0201fa1e
    r0 = r6 >> 26
    if (r0 != 0) goto L0201fa1e
    r0 = r6
    call L01c008b4  ; @call.xl
    r2 = r0
    r0 = r5
    r1 = r4
    call phase3_p8_norflash_read
    {pc, r8-r4} = [sp++]
L0201fa1e:
    r8 = L01c3743c
    r0 = b[r8+16] (u)
    r7 = L01c26890
    if (r0 == 0) goto L0201fa44
    r0 = r7 + 3748
    call L02040614  ; @call.xl
    r0 = b[r7+67] (u)
    r0 += 1  ; @add.ri.u5
    b[r7+67] = r0
L0201fa44:
    r0 = r5
    r1 = r6
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r0 = b[r8+16] (u)
    if (r0 == 0) goto L0201fa6a
    r0 = b[r7+67] (u)
    r0 += -1
    b[r7+67] = r0
    r0 = r7 + 3748
    call L0204074c  ; @call.xl
L0201fa6a:
    {pc, r8-r4} = [sp++]

; phase3_p8_bin_buf_read: 0x0201fa6c..0x0201fa72, module phase3-p8 (bin_buf_read)
.type phase3_p8_bin_buf_read,@function
phase3_p8_bin_buf_read:
    [--sp] = rets
    call phase3_p8_memcpy_flash
    pc = [sp++]
