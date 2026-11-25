; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 3 functions, 0x0201ff7c..0x02020100

; phase3_p8_fwrite: 0x0201ff7c..0x0201ffd2, module phase3-p8 (fwrite)
.type phase3_p8_fwrite,@function
phase3_p8_fwrite:
    [--sp] = {rets, r8-r4}
    r4 = r3
    r7 = r2
    r6 = r1
    r8 = r0
    r5 = -1
    if (r4 == 0) goto L0201ffce
    r0 = [r4+0]
    if (r0 == 0) goto L0201ffce
    r0 += 84
    call L02040614  ; @call.xl
    r1 = [r4+0]
    r2 = b[r1+164] (u)
    if (r2 == 0) goto L0201ffc2
    r5 = 0
    if (r0 != 0) goto L0201ffce
    r0 = [r1+8]
    r3 = [r0+36]
    if (r3 == 0) goto L0201ffb6
    r2 = r7 * r6
    r0 = r4
    r1 = r8
    call r3
    r5 = r0  #
    r1 = [r4+0]
L0201ffb6:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    goto L0201ffce
L0201ffc2:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    r5 = 0
L0201ffce:
    r0 = r5
    {pc, r8-r4} = [sp++]

; phase3_p8_btif_area_write: 0x0201ffd2..0x020200ea, module phase3-p8 (btif_area_write)
.type phase3_p8_btif_area_write,@function
phase3_p8_btif_area_write:
    [--sp] = {rets, r14-r4}
    sp += -8
    r5 = r2
    r9 = r1
    r4 = r0
    r0 = 0
    r1 = 0
    d[sp] = r1_r0
    r8 = L01c26040
    r0 = r8
    call L02040614  ; @call.xl
    h[sp] = r4
    r0 = sp + 0
    call phase3_p8_btif_item_read
    if (r0 != -768) goto L020200bc
    r0 = sp + 0
    call L0201fdae
    r6 = h[sp+2] (u)
    r11 = r6 + 4
    r0 = r11
    call L0203c15c  ; @call.xl
    r7 = r0
    if (r7 == 0) goto L020200ca
    r1 = L02035823
    r0 = r1 + 3561
    call phase3_p1_fopen
    r10 = r0
    if (r0 == 0) goto L020200d0
    r5 = umin(r5, r6)
    r1 = 0
    r0 = r7
    r2 = r11
    call effect_enable_memset  ; @call.xl
    r0 = h[sp] (u)
    r1 = r6 << 20
    r0 = r0 & 0xFFFF0FFF
    r1 <= insert(r0, p:8, l:12)
    r12 = r1 >> 24  #
    b[r7+0] = r1
    b[r7+3] = r12
    r13 = r1 >> 16
    b[r7+2] = r13
    r14 = r1 >> 8
    b[r7+1] = r14
    r4 = r7 + 4
    r0 = r4
    r1 = r9
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r1 = r6 & 0xFFFF0FFF
    r0 = r4
    call L02001776
    b[r7+3] = r12
    b[r7+2] = r13
    b[r7+1] = r14
    r0 = r10  #
    b[r7+0] = r0
    r1 = [sp+4]
    r2 = 0
    call phase3_p13_fseek
    r2 = 1
    r0 = r7
    r1 = r11
    r3 = r10
    call phase3_p8_fwrite
    r4 = r0
    r0 = r7
    call L0203d218  ; @call.xl
    r0 = r10
    call phase3_p8_fclose
    if (r4 != r11) {
    r5 = -762
    }
    goto L020200dc
L020200bc:
    r0 = r8
    call L0204074c  ; @call.xl
    r5 = -767
    goto L020200e4
L020200ca:
    r5 = -760
    goto L020200dc
L020200d0:
    r0 = r7
    call L0203d218  ; @call.xl
    r5 = -766
L020200dc:
    r0 = r8
    call L0204074c  ; @call.xl
L020200e4:
    r0 = r5
    sp += 8
    {pc, r14-r4} = [sp++]

; phase3_p8_vm_idle_query: 0x020200ea..0x02020100, module phase3-p8 (vm_idle_query)
.type phase3_p8_vm_idle_query,@function
phase3_p8_vm_idle_query:
    r0 = 621
    r1 = L01c26090
    r1 = b[r1+r0] (u)
    r0 = 1
    if (r1 == 0) goto L020200fe
    r0 = 0
L020200fe:
    rts
