; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 1 function, 0x02022bd4..0x02022bde

; phase3_p10_sdf_opendir: 0x02022bd4..0x02022bde, module phase3-p10 (sdf_opendir)
.type phase3_p10_sdf_opendir,@function
phase3_p10_sdf_opendir:
    r1 = [r0+0]
    [r0+4] = r1
    [r0+8] = 0x0
    rts
