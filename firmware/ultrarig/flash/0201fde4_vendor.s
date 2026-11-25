; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201fde4..0x0201fe1c: vendor code (JieLi SDK or library, not reversed), as instructions
L0201fde4:
    [--sp] = {rets, r7, r5, r4}
    r7 = sp
    r4 = r1 >> 20
    r1 = r4 + 3
    r2 = 8188
    r1 &= r2
    r2 = sp
    r5 = r2 - r1
    sp = r5
    r1 = r0 + 4
    r0 = r5
    r2 = r4
    call phase3_p8_btif_buf_read
    r0 = r5
    r1 = r4
    call L02001776
    r0 = r0 & 0xFFFF00FF
    sp = r7
    {pc, r7, r5, r4} = [sp++]
