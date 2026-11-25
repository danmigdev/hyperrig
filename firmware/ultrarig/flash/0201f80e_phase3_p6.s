; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 2 functions, 0x0201f80e..0x0201f834

; phase3_p6_syscfg_file_open: 0x0201f80e..0x0201f81c, module phase3-p6 (syscfg_file_open)
.type phase3_p6_syscfg_file_open,@function
phase3_p6_syscfg_file_open:
    [--sp] = rets
    r1 = L02035823
    call phase3_p1_fopen
    pc = [sp++]

; phase3_p6_fget_attrs: 0x0201f81c..0x0201f834, module phase3-p6 (fget_attrs)
.type phase3_p6_fget_attrs,@function
phase3_p6_fget_attrs:
    [--sp] = rets
    if (r0 == 0) goto L0201f832
    r2 = [r0+0]
    if (r2 == 0) goto L0201f832
    r3 = 0
    b[r1+0] = r3
    r2 = [r2+8]
    r2 = [r2+100]
    if (r2 == 0) goto L0201f832
    call r2
L0201f832:
    pc = [sp++]
