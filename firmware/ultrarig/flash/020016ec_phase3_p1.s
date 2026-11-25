; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p1: 2 functions, 0x020016ec..0x02001720

; phase3_p1_app_version_check: 0x020016ec..0x02001710, module phase3-p1 (app_version_check)
.type phase3_p1_app_version_check,@function
phase3_p1_app_version_check:
    [--sp] = {rets, r5, r4}
    r4 = L0203bec0  ; "INCLUDE_BTCTRLER-$65564b0"
    r5 = L0203c017
    goto L02001708
L020016fc:
    r0 = r4
    call L020283a8  ; @call.xl
    r0 += r4  ; @add.rr
    r4 = r0 + 1
L02001708:
    if (r4 < r5) goto L020016fc
    r0 = 0
    {pc, r5, r4} = [sp++]

; phase3_p1_ota_idle_query: 0x02001710..0x02001720, module phase3-p1 (ota_idle_query)
.type phase3_p1_ota_idle_query,@function
phase3_p1_ota_idle_query:
    r0 = L01c26890
    r1 = b[r0+0] (u)
    r0 = 1
    if (r1 == 0) goto L0200171e
    r0 = 0
L0200171e:
    rts
