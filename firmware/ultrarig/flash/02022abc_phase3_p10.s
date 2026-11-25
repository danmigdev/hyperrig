; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 2 functions, 0x02022abc..0x02022ad8

; phase3_p10_sdfile_len: 0x02022abc..0x02022aca, module phase3-p10 (sdfile_len)
.type phase3_p10_sdfile_len,@function
phase3_p10_sdfile_len:
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L02022ac8
    r1 = [r1+12]
    if (r1 == 0) goto L02022ac8
    r0 = [r1+12]
L02022ac8:
    rts

; phase3_p10_sdfile_pos: 0x02022aca..0x02022ad8, module phase3-p10 (sdfile_pos)
.type phase3_p10_sdfile_pos,@function
phase3_p10_sdfile_pos:
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L02022ad6
    r1 = [r1+12]
    if (r1 == 0) goto L02022ad6
    r0 = [r1+0]
L02022ad6:
    rts
