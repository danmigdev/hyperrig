; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sort_and_format: 1 function, 0x0201792a..0x02017988

; sort_and_format_median_word: 0x0201792a..0x02017988, module sort-and-format (median_word)
.type sort_and_format_median_word,@function
sort_and_format_median_word:
    [--sp] = {rets, r8-r4}
    sp += -20
    r2 = 0
    r3 = L01c27064
    r8 = sp + 0
    goto L02017946
L0201793c:
    r1 = [r3+r2<<2]
    [r8+r2<<2] = r1
    r2 += 1  ; @add.ri.u5
L02017946:
    ifs (r2 < r0) goto L0201793c
    r2 = 1
    r3 = 0
    r4 = r8
    goto L02017974
L02017952:
    r5 = [r8+r2<<2]
    r7 = r3
    r6 = r4
    goto L02017962
L0201795c:
    [r6+4] = r1
    r7 += -1
    r6 += -4
L02017962:
    ifs (r7 < 0) goto L0201796c
    r1 = [r6+0]
    iff (r1 > r5) goto L0201795c
L0201796c:
    [r6+4] = r5
    r3 += 1  ; @add.ri.u5
    r4 += 4  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L02017974:
    ifs (r2 < r0) goto L02017952
    r1 = 2
    r0 = r0 / r1 (s)
    r1 = sp + 0
    r0 = [r1+r0<<2]
    sp += 20
    {pc, r8-r4} = [sp++]
