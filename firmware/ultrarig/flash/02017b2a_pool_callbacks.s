; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; pool_callbacks: 1 function, 0x02017b2a..0x02017b74

; pool_callbacks_digits_text: 0x02017b2a..0x02017b74, module pool-callbacks (digits_text)
.type pool_callbacks_digits_text,@function
pool_callbacks_digits_text:
    [--sp] = {rets, r6-r4}
    sp += -12
    ifs (r1 <= -1) {  ; @ifs.le.ri.s12
    r2 = 45
    b[r0++=1] = r2
    r1 = 0x0 - r1
    }
    r2 = 0
    r4 = 10
    r3 = sp + 0
L02017b40:
    r5 = r1
    r1 = r5 / r4 (u)
    r6 = r1 * 0xA
    r6 = r5 - r6
    r6 = r6 | 0x30
    b[r3+r2] = r6
    r2 += 1  ; @add.ri.u5
    if (r5 > 9) goto L02017b40
    r1 = r3 + r2
    r1 += -1
    r3 = 0
    goto L02017b6a
L02017b62:
    r4 = b[r1++=-1] (u)
    b[r0+r3] = r4
    r3 += 1  ; @add.ri.u5
L02017b6a:
    if (r3 != r2) goto L02017b62
    r0 += r2  ; @add.rr
    sp += 12
    {pc, r6-r4} = [sp++]
