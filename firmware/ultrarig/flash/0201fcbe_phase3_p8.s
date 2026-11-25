; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 1 function, 0x0201fcbe..0x0201fccc

; phase3_p8_syscfg_bin_group_read: 0x0201fcbe..0x0201fccc, module phase3-p8 (syscfg_bin_group_read)
.type phase3_p8_syscfg_bin_group_read,@function
phase3_p8_syscfg_bin_group_read:
    [--sp] = {rets, r4}
    sp += -4
    r4 = 0
    [sp] = r4
    call L0201fc28
    sp += 4
    {pc, r4} = [sp++]
