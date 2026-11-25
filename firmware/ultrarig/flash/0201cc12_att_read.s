; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; att_read: 1 function, 0x0201cc12..0x0201cca2

; att_read_att_read: 0x0201cc12..0x0201cca2, module att-read (att_read)
.type att_read_att_read,@function
att_read_att_read:
    [--sp] = {rets, r7-r4}
    r4 = r3
    r0 = r1 + -3
    r3 = uextra(r0, p:1, l:15)
    r3 <= insert(r0, p:15, l:17)
    r6 = r3.l (u)
    r5 = 0
    if (r6 > 6) goto L0201cc9e
    r0 = [sp+20]
    r3 = L01c26890
    tbb [r6]
att_read_handle_cases:
    .byte (L0201cc3c - att_read_handle_cases) / 2, (L0201cc9e - att_read_handle_cases) / 2, (L0201cc9e - att_read_handle_cases) / 2, (L0201cc74 - att_read_handle_cases) / 2, (L0201cc62 - att_read_handle_cases) / 2, (L0201cc9e - att_read_handle_cases) / 2, (L0201cc88 - att_read_handle_cases) / 2
    .byte 0x00  ; alignment
L0201cc3c:
    r6 = b[r3+56] (u)
    if (r6 <= r2) goto L0201cc9e
    r1 = r6 - r2
    r5 = smin(r1, r0)
    if (r4 == 0) goto L0201cc5c
    r0 = r2 + r3
    r1 = r0 + 2072
    r2 = r5.l (u)
    r0 = r4
    call effect_parameter_support_memmove  ; @call.xl
L0201cc5c:
    if (r4 != 0) goto L0201cc9e
    r5 = r6
    goto L0201cc9e
L0201cc62:
    if (r4 == 0) goto L0201cc6c
    if (r2 != 0) goto L0201cc6c
    if (r0 == 0) goto L0201cc6c
    r0 = 1
    b[r4+0] = r0
L0201cc6c:
    r5 = 1
    if (r2 == 0) goto L0201cc9e
    r5 = 0
    goto L0201cc9e
L0201cc74:
    r5 = 2
    if (r4 == 0) goto L0201cc9e
    r0 = r1
    call L0204d42a  ; @call.xl
    b[r4+0] = r0
    r0 = 0
    b[r4+1] = r0
    goto L0201cc9e
L0201cc88:
    if (r4 == 0) goto L0201cc9a
    if (r2 != 0) goto L0201cc9a
    if (r0 >= 2) {  ; @if.ge.ri.s12
    r0 = b[r3+63] (u)
    b[r4+0] = r0
    r0 = 0
    b[r4+1] = r0
    }
L0201cc9a:
    if (r2 != 0) goto L0201cc9e
    r5 = 2
L0201cc9e:
    r0 = r5.l (u)
    {pc, r7-r4} = [sp++]
