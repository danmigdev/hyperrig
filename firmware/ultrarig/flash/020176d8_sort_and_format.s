; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sort_and_format: 2 functions, 0x020176d8..0x0201779c

; sort_and_format_normalized_differences: 0x020176d8..0x02017764, module sort-and-format (normalized_differences)
.type sort_and_format_normalized_differences,@function
sort_and_format_normalized_differences:
    [--sp] = {rets, r15-r4}
    r8 = L01c25390
    r9 = L01c24790
    if (r2 != 1) goto L02017700
    [r8+0] = 0x0
    r2 = 289
    r4 = 0x3F800000
    [r9+r2<<2] = r4
    r14 = 0
    r2 = 1
    goto L02017704
L02017700:
    r14 = [r8+0]
L02017704:
    r13 = 0x0 - r2
    r10 = 0x3F800000
    r11 = 0
    r12 = 289
    goto L0201775a
L02017714:
    r15 = 0
    r7 = r13
    r4 = 0
    goto L0201772e
L0201771c:
    r6 = h[r0+r7<<1] (s)
    r5 = h[r0+r4<<1] (s)
    r5 = r5 - r6
    r5 *= r5
    r15 += r5
    r7 += 1  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L0201772e:
    ifs (r4 < r1) goto L0201771c
    r5 = itof(r15)
    r14 = r14 + r5 (f)
    r4 = r10
    iff (r14 > r11) {
    r4 = itof(r2)
    r4 = r4 * r5 (f)
    r4 = r4 / r14 (f)
    }
    r5 = r2 << 2
    r5 += r9
    [r5+r12<<2] = r4
    r13 = r13 + -1
    r2 += 1  ; @add.ri.u5
L0201775a:
    ifs (r2 <= r3) goto L02017714
    [r8+0] = r14
    {pc, r15-r4} = [sp++]

; sort_and_format_dip_estimate: 0x02017764..0x0201779c, module sort-and-format (dip_estimate)
.type sort_and_format_dip_estimate,@function
sort_and_format_dip_estimate:
    [--sp] = {rets, r4}
    r0 = r0 << 2
    r1 = L01c24790
    r0 += r1  ; @add.rr
    r0 = r0 + 1152
    r3 = [r0+0]
    r4 = [r0+8]
    r2 = r4 - r3 (f)
    r1 = r3 - r4 (f)
    iff (r3 u<= r4) {
    r1 = r2
    }
    r2 = 0xBF000000  #
    r0 = [r0+4]
    r1 = r1 * r2 (f)
    r0 = r0 + r1 (f)
    r1 = 0
    r0 = fmax(r0, r1)
    {pc, r4} = [sp++]
