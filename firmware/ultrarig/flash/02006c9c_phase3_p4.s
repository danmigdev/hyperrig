; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 1 function, 0x02006c9c..0x02006d14

; phase3_p4_cdc_write_data: 0x02006c9c..0x02006d14, module phase3-p4 (cdc_write_data)
.type phase3_p4_cdc_write_data,@function
phase3_p4_cdc_write_data:
    [--sp] = {rets, r8-r4}
    r2 = 412
    r8 = L01c26890
    r2 = [r8+r2<<2]
    r5 = r1
    r6 = r0
    r4 = 0
    if (r2 == 0) goto L02006d10
    r0 = b[r2+104] (u)
    r0 = r0 & 0xFFFFFF12
    if (r0 != 18) goto L02006d10
    r0 = r2 + 24
    call L02040614  ; @call.xl
    r0 = 0
    r7 = 412
L02006cce:
    r4 = r0
    if (r4 >= r5) goto L02006cf6
    r0 = r6 + r4
    r1 = r5 - r4
    if (r1 >= 64) {  ; @if.ge.ri.s12
    r1 = 64
    }
    call L02006bca
    if (r0 == 0) goto L02006cf6
    r1 = [r8+r7<<2]
    r1 = b[r1+104] (u)
    r1 = r1 & 0xFFFFFF12
    r0 += r4  ; @add.rr
    if (r1 == 18) goto L02006cce
L02006cf6:
    if (r4 == 0) goto L02006d02
    if ((r4 & 0x3F) == 0) {
    r1_r0 = 0
    call L02006bca
    }
L02006d02:
    r0 = r7
    r0 = [r8+r0<<2]
    r0 += 24  ; @add.ri.u5
    call L0204074c  ; @call.xl
L02006d10:
    r0 = r4
    {pc, r8-r4} = [sp++]
