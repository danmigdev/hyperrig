; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 1 function, 0x02020648..0x02020664

; phase3_p8_norflash_protect_resume: 0x02020648..0x02020664, module phase3-p8 (norflash_protect_resume)
.type phase3_p8_norflash_protect_resume,@function
phase3_p8_norflash_protect_resume:
    [--sp] = {rets, r4}
    r4 = L01c3743c
    r1_r0 = d[r4+68]
    if (r1 == r0) goto L02020662
    r0 = 13
    call storage_control_control
    [r4+72] = 0x0
L02020662:
    {pc, r4} = [sp++]
