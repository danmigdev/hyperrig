; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 2 functions, 0x020069fa..0x02006a9e

; link_and_print_other_space: 0x020069fa..0x02006a14, module link-and-print (other_space)
.type link_and_print_other_space,@function
link_and_print_other_space:
    [--sp] = rets
    sp += -4
    r0 = 0
    [sp] = r0
    r2 = sp + 0
    r0 = 9
    r1 = 1
    call L0204c744  ; @call.xl
    r0 = [sp]
    sp += 4
    pc = [sp++]

; link_and_print_other_send: 0x02006a14..0x02006a9e, module link-and-print (other_send)
.type link_and_print_other_send,@function
link_and_print_other_send:
    [--sp] = {rets, r12-r4}
    sp += -8
    r5 = r1
    r8 = r0
    r10 = 0
    r11 = L01c26890
    r4 = 0
L02006a26:
    r9 = r8 + r4
    r12 = r5 - r4
    r7 = 0
L02006a30:
    if (r4 >= r5) goto L02006a8a
    call state_queries_both_set
    if (r0 == 0) goto L02006a7c
    r1 = h[r11+84] (u)
    r0 = 20
    if (r1 >= 24) {  ; @if.ge.ri.s12
    r0 = h[r11+84] (u)
    r0 += -3
    }
    r6 = umin(r12, r0)
    call link_and_print_other_space
    if (r0 < r6) goto L02006a68
    [sp+4] = r10  ; @st.w.sp.l
    r0 = 10
    r1 = 4
    r2 = 8
    r3 = r9  #
    [sp] = r6
    call L0204c744  ; @call.xl
    if (r0 == 0) goto L02006a78
L02006a68:
    if (r7 > 19) goto L02006a7c
    r0 = 1
    call L0203feb8  ; @call.xl
    r7 += 1  ; @add.ri.u5
    goto L02006a30
L02006a78:
    r4 += r6  ; @add.rr
    goto L02006a26
L02006a7c:
    r0 = r11 + 1352
    [r0+0] += r4
    r1 = [++r0=4]
    goto L02006a94
L02006a8a:
    r0 = r11 + 1352
    r12 = [r0+0]
    r1 = r4
L02006a94:
    r1 += r12
    r0 = r4  #
    [r0+0] = r1
    sp += 8
    {pc, r12-r4} = [sp++]
