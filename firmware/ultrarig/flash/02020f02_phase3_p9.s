; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 1 function, 0x02020f02..0x02020fac

; phase3_p9_sdfile_open_part_dir: 0x02020f02..0x02020fac, module phase3-p9 (sdfile_open_part_dir)
.type phase3_p9_sdfile_open_part_dir,@function
phase3_p9_sdfile_open_part_dir:
    [--sp] = {rets, r11-r4}
    sp += -32
    r4 = r2
    r11 = r1
    r9 = r0
    r6 = L0203590a  ; "res"
    r1 = r6 + 2140
    r0 = r4
    call L02020e88
    r7 = L01c27150
    if (r0 == 0) goto L02020f40
    r1 = r6 + 1835
    r0 = r4
    call L02020e88
    if (r0 == 0) goto L02020f3e
    r0 = r4
    r1 = r6
    call L02020e88
    r1 = r0
    r0 = -255
    if (r1 != 0) goto L02020fa8
    r7 += 8  ; @add.ri.u5
    goto L02020f40
L02020f3e:
    r7 += 4  ; @add.ri.u5
L02020f40:
    r0 = [r9+8]
    if (r0 == 0) goto L02020f52
    call phase3_p8_sdfile_flash_addr2cpu_addr
    r6 = r0
    r10 = 1
    goto L02020f56
L02020f52:
    r10 = 0  #
    r6 = [r7+0]
L02020f56:
    r8 = r9 + 4
    r5 = sp + 0
    r7 = r5 + 16
    r4 = r5 | 0x2
L02020f62:
    r0 = sp + 0
    r2 = 32
    r1 = r6
    call phase3_p8_memcpy_flash
    r1 = 30
    r0 = r4
    call L02001776
    r1 = h[sp] (u)
    if (r0 != r1) goto L02020f8c
    r0 = r7
    r1 = r11
    call L02020e88
    if (r0 == 0) goto L02020f92
    r1 = h[r5+14] (u)
    r6 += 32
    if (r1 == 0) goto L02020f62
    goto L02020fa8
L02020f8c:
    r0 = -251
    goto L02020fa8
L02020f92:
    r1 = sp + 0
    r2 = 32
    r0 = r8
    call phase3_p8_memcpy_flash
    if (r10 == 0) {  ; @if.eq.ri.s12
    r6 = [sp+4]
    }
    [r9+8] = r6
    r0 = 0
L02020fa8:
    sp += 32
    {pc, r11-r4} = [sp++]
