; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 3 functions, 0x02021d9e..0x02021dd8

; phase3_p10_sdf_seach_total_new: 0x02021d9e..0x02021daa, module phase3-p10 (sdf_seach_total_new)
.type phase3_p10_sdf_seach_total_new,@function
phase3_p10_sdf_seach_total_new:
    r1 = r0
    r0 = h[r1+8] (u)
    r2 = r0 + 1
    r0 = 0
    h[r1+8] = r2
    rts

; phase3_p10_sdf_store_number_new: 0x02021daa..0x02021db6, module phase3-p10 (sdf_store_number_new)
.type phase3_p10_sdf_store_number_new,@function
phase3_p10_sdf_store_number_new:
    r1 = r0
    r0 = h[r1+8] (u)
    r2 = r0 + 1
    r0 = 0
    h[r1+8] = r2
    rts

; phase3_p10_nor_sdfile_mount: 0x02021db6..0x02021dd8, module phase3-p10 (nor_sdfile_mount)
.type phase3_p10_nor_sdfile_mount,@function
phase3_p10_nor_sdfile_mount:
    r1 = r0
    r0 = [r1+12]
    r2 = L01c26350
    [r2+0] = r0
    r0 = 0
    [r1+36] = r0
    r2 = 67
    b[r1+50] = r2
    b[r1+51] = r0
    r2 = 1
    b[r1+165] = r2
    rts
