; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 4 functions, 0x0201fe1c..0x0201ff12

; phase3_p8_btif_item_read: 0x0201fe1c..0x0201fe78, module phase3-p8 (btif_item_read)
.type phase3_p8_btif_item_read,@function
phase3_p8_btif_item_read:
    [--sp] = {rets, r6-r4}
    sp += -4
    r4 = r0
    call L0201fdae
    if (r0 == 0) goto L0201fe6a
    r0 = L01c2603c
    r0 = [r0+0]
    r1 = [r4+4]
    r2 = 0
    r5 = r0 + r1  #
    [sp] = r2
    r0 = sp + 0
    r2 = 4
    r1 = r5
    call phase3_p8_btif_buf_read
    r6 = [sp]
    if (r6 == -1) goto L0201fe70
    r0 = -759  #
    r1 = h[r4+2] (u)
    r2 = r6 >> 20
    if (r1 != r2) goto L0201fe74
    r0 = r5
    r1 = r6
    call L0201fde4
    r1 = r0
    r2 = r6.b0 (u)
    r0 = -763
    if (r1 == r2) {
    r0 = r5 + 4
    [r4+4] = r0
    r0 = 0
    }
    goto L0201fe74
L0201fe6a:
    r0 = -765
    goto L0201fe74
L0201fe70:
    r0 = -768
L0201fe74:
    sp += 4
    {pc, r6-r4} = [sp++]

; phase3_p8_sdfile_cpu_addr2flash_addr: 0x0201fe78..0x0201fe92, module phase3-p8 (sdfile_cpu_addr2flash_addr)
.type phase3_p8_sdfile_cpu_addr2flash_addr,@function
phase3_p8_sdfile_cpu_addr2flash_addr:
    r1 = 558
    r2 = L01c26890
    r3 = r1 + 1
    r3 = [r2+r3<<2]
    r1 = [r2+r1<<2]
    r0 = r0 - r3
    r0 += r1  ; @add.rr
    rts

; phase3_p8_btif_buf_erase: 0x0201fe92..0x0201fea4, module phase3-p8 (btif_buf_erase)
.type phase3_p8_btif_buf_erase,@function
phase3_p8_btif_buf_erase:
    [--sp] = {rets, r4}
    r4 = r1
    call phase3_p8_sdfile_cpu_addr2flash_addr
    r2 = r0
    r0 = 0
    r1 = r4
    call storage_control_ioctl
    {pc, r4} = [sp++]

; phase3_p8_syscfg_btif_init: 0x0201fea4..0x0201ff12, module phase3-p8 (syscfg_btif_init)
.type phase3_p8_syscfg_btif_init,@function
phase3_p8_syscfg_btif_init:
    [--sp] = {rets, r9-r4}
    sp += -8
    r9 = L01c2603c
    r0 = r9 + 4
    call L0203fb92  ; @call.xl
    call phase3_p8_btif_get_addr_info
    if (r0 != 0) goto L0201ff0e
    r0 = 0
    r1 = 0
    d[sp] = r1_r0
    r7 = L02033b40
    r8 = 29883724
    goto L0201ff06
L0201fed4:
    h[sp] = r0
    r0 = sp + 0
    call phase3_p8_btif_item_read
    if (r0 == -768) goto L0201ff06
    if (r0 == 0) goto L0201ff06
    r6 = b[r8+0] (u)
    r4 = 204
    if (r6 != 1) {  ; @if.ne.ri.s12
    r4 = 200
    }
    r5 = [r9+0]
    r0 = r5
    r1 = r4
    call phase3_p8_btif_buf_erase
    if (r6 != 1) goto L0201ff06
    r0 = r5 + 256
    r1 = r4
    call phase3_p8_btif_buf_erase
L0201ff06:
    r0 = h[r7++=4] (u)
    if (r0 != 0) goto L0201fed4
    r0 = 0
L0201ff0e:
    sp += 8
    {pc, r9-r4} = [sp++]
