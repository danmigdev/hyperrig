; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 2 functions, 0x0201fd16..0x0201fdae

; phase3_p8_syscfg_bin_ptr_read: 0x0201fd16..0x0201fd6c, module phase3-p8 (syscfg_bin_ptr_read)
.type phase3_p8_syscfg_bin_ptr_read,@function
phase3_p8_syscfg_bin_ptr_read:
    [--sp] = {rets, r6-r4}
    sp += -16
    r5 = 0
    r4 = r1  #
    [sp+12] = r5
    r6 = r0  #
    h[r4+0] = r5
    call L0201fb7a
    if (r0 == 0) goto L0201fd48
    r0 = 1
    r1 = sp + 12
    r2 = 65535
    r3 = 0
    r0 = r6  #
    [sp] = r0
    call L0201fc28
    ifs (r0 >= 1) {  ; @ifs.ge.ri.s12
    h[r4+0] = r0
    }
    r5 = [sp+12]
    goto L0201fd66
L0201fd48:
    r0 = 0
    r1 = 0
    d[sp+4] = r1_r0
    h[sp+4] = r6
    r0 = sp + 4
    call L0201fc00
    if (r0 != 0) goto L0201fd66
    r0 = h[sp+6] (u)
    h[r4+0] = r0
    r5 = [sp+8]
    [sp+12] = r5
L0201fd66:
    r0 = r5
    sp += 16
    {pc, r6-r4} = [sp++]

; phase3_p8_btif_get_addr_info: 0x0201fd6c..0x0201fdae, module phase3-p8 (btif_get_addr_info)
.type phase3_p8_btif_get_addr_info,@function
phase3_p8_btif_get_addr_info:
    [--sp] = {rets, r5, r4}
    sp += -36
    r1 = L02035823
    r0 = r1 + 3561
    call phase3_p1_fopen
    r5 = r0
    if (r5 == 0) goto L0201fda4
    r1 = sp + 0
    r4 = 0
    r0 = r1
    rep 9 {
    [r0++=4] = r4
    }
    r0 = r5
    call phase3_p6_fget_attrs
    r0 = [sp+8]
    r1 = L01c2603c
    r0 = r5  #
    [r1+0] = r0
    call phase3_p8_fclose
    goto L0201fda8
L0201fda4:
    r4 = -766
L0201fda8:
    r0 = r4
    sp += 36
    {pc, r5, r4} = [sp++]
