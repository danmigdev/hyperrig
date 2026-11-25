; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p2: 3 functions, 0x02024c52..0x02024d10

; phase3_p2_get_pll_vc_res: 0x02024c52..0x02024c68, module phase3-p2 (get_pll_vc_res)
.type phase3_p2_get_pll_vc_res,@function
phase3_p2_get_pll_vc_res:
    [--sp] = rets
    call L02055c0e  ; @call.xl
    r1 = uextra(r0, p:18, l:1)
    r0 = r0 >> 16
    r0 = r0 & 0x2
    r0 |= r1
    pc = [sp++]

; phase3_p2_get_wfa_pll_bank: 0x02024c68..0x02024c9a, module phase3-p2 (get_wfa_pll_bank)
.type phase3_p2_get_wfa_pll_bank,@function
phase3_p2_get_wfa_pll_bank:
    [--sp] = {rets, r4}
    r1 = 0
    r3 = 2769
    r2 = L01c26890
L02024c76:
    r4 = b[r3+r2] (u)
    if (r4 > r0) goto L02024c8c
    r4 = r3 + -2767
    r3 += 1  ; @add.ri.u5
    r1 += 1  ; @add.ri.u5
    ifs (r4 < 48) goto L02024c76
    r1 = 47
L02024c8c:
    r0 = 2815
    r0 = b[r2+r0] (u)
    r0 = r0 - r1
    r0 = r0.b0 (u)
    {pc, r4} = [sp++]

; phase3_p2_wifi_get_pa_trim_data: 0x02024c9a..0x02024d10, module phase3-p2 (wifi_get_pa_trim_data)
.type phase3_p2_wifi_get_pa_trim_data,@function
phase3_p2_wifi_get_pa_trim_data:
    [--sp] = {rets, r5, r4}
    sp += -8
    r4 = L01c1f180
    r5 = r4 + 156
    r0 = L02035106
    r1 = r5
    rep 7 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r1 = sp + 1
    r0 = 107
    r2 = 7
    call L02024a78
    r1 = L01c26890
    if (r0 != 7) goto L02024cdc
    r0 = sp + 1
    rep 7 {
    r2 = b[r0++=1] (u)
    b[r5++=1] = r2
    }
    r0 = b[r1+57] (u)
    r0 |= 2
    b[r1+57] = r0
L02024cdc:
    r0 = 302
    r0 = [r1+r0<<2]
    if (r0 == 0) goto L02024d0c
    r2 = 1216
    r2 = b[r1+r2] (u)
    if ((r2 & 1) != 0) goto L02024d0c
    r2 = 1216
    r3 = 1
    b[r1+r2] = r3
    r1 = [r4+24]
    r0 = r1 - r0
    r2 = r0 * 0xA
    r0 = 32
    r1 = -4
    call storage_coordination_notify
L02024d0c:
    sp += 8
    {pc, r5, r4} = [sp++]
