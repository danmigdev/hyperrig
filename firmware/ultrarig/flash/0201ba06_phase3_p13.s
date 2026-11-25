; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 3 functions, 0x0201ba06..0x0201ba8a

; phase3_p13_get_manufacture_str: 0x0201ba06..0x0201ba18, module phase3-p13 (get_manufacture_str)
.type phase3_p13_get_manufacture_str,@function
phase3_p13_get_manufacture_str:
    [--sp] = rets
    r1 = L02035097
    r2 = 34
    call effect_parameter_support_memmove  ; @call.xl
    pc = [sp++]

; phase3_p13_get_product_str: 0x0201ba18..0x0201ba26, module phase3-p13 (get_product_str)
.type phase3_p13_get_product_str,@function
phase3_p13_get_product_str:
    r1 = L0203a264
    rep 32 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    rts

; phase3_p13_get_iserialnumber_str: 0x0201ba26..0x0201ba8a, module phase3-p13 (get_iserialnumber_str)
.type phase3_p13_get_iserialnumber_str,@function
phase3_p13_get_iserialnumber_str:
    [--sp] = {rets, r6-r4}
    sp += -16
    r1 = 34
    b[r0+0] = r1
    r1 = 3
    b[r0+1] = r1
    r2 = r0 + 2
    r1 = 0
    rep 32 {
    b[r2++=1] = r1
    }
    r2 = L01c3743c
    r5_r4 = d[r2+8]
    r3_r2 = d[r2+0]
    d[sp+8] = r5_r4
    d[sp] = r3_r2
    r0 += 4  ; @add.ri.u5
    r2 = sp + 0
    goto L0201ba82
L0201ba56:
    r3 = b[r2+r1] (u)
    r4 = r3 >> 4
    r5 = r4 | 0x30
    r4 += 55
    if (r3 <= 159) {  ; @if.le.ri.s12
    r4 = r5
    }
    r6 = r3 & 0xFFFFFF0F  #
    b[r0+-2] = r4
    r5 = r6 | 0x30
    r3 = r6 + 55
    if (r6 <= 9) {  ; @if.le.ri.s12
    r3 = r5
    }
    b[r0++=4] = r3
    r1 += 1  ; @add.ri.u5
L0201ba82:
    if (r1 != 8) goto L0201ba56
    sp += 16
    {pc, r6-r4} = [sp++]
