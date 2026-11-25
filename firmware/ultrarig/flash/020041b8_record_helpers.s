; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; record_helpers: 4 functions, 0x020041b8..0x02004250

; record_helpers_id_in_use: 0x020041b8..0x020041e2, module record-helpers (id_in_use)
.type record_helpers_id_in_use,@function
record_helpers_id_in_use:
    r1 = L01c26890
    r3 = [r1+784]
    r1 = 1
    r2 = 1
    if (r3 != r0) {
    r2 = 0
    }
    r3 = L01c1f180
    r3 = [r3+224]
    if (r3 != r0) {
    r1 = 0
    }
    r0 = r1 | r2
    rts

; record_helpers_pack_tag: 0x020041e2..0x02004206, module record-helpers (pack_tag)
.type record_helpers_pack_tag,@function
record_helpers_pack_tag:
    [--sp] = {rets, r5, r4}
    r3_r2 = 0
    r1 = 0
    goto L020041fe
L020041ea:
    r4 = b[r0+r3] (u)
    r5 = r4 | 0x20
    if (r5 == 32) goto L02004202
    r4 <<= r2
    r1 |= r4
    r2 += 8  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L020041fe:
    if (r3 <= 3) goto L020041ea
L02004202:
    r0 = r1
    {pc, r5, r4} = [sp++]

; record_helpers_half_fields: 0x02004206..0x02004238, module record-helpers (half_fields)
.type record_helpers_half_fields,@function
record_helpers_half_fields:
    r1 = L01c26890
    r1 = h[r1+80] (u)
    r3 = 1
    r2 = uextra(r1, p:8, l:4)  #
    b[r0+0] = r3
    if (r2 >= 7) {  ; @if.ge.ri.s12
    r2 = 0
    }
    r3 = r1 >> 12
    b[r0+1] = r2
    if (r1 >= 28672) {
    r3 = 0
    }
    r1 = r1 & 0xF  #
    b[r0+2] = r3
    if (r1 >= 7) {  ; @if.ge.ri.s12
    r1 = 0
    }
    b[r0+3] = r1
    rts

; record_helpers_leading_ones: 0x02004238..0x02004250, module record-helpers (leading_ones)
.type record_helpers_leading_ones,@function
record_helpers_leading_ones:
    [--sp] = {rets, r4}
    r2 = r0 + 1
    r3 = 0
L0200423e:
    r0 = r3
    if (r0 >= r1) goto L0200424e
    r4 = b[r2+r0] (u)
    r3 = r0 + 1
    if (r4 == 1) goto L0200423e
L0200424e:
    {pc, r4} = [sp++]
