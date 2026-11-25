; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_journal: 1 function, 0x0200294e..0x02002994

; capture_journal_invalidate: 0x0200294e..0x02002994, module capture-journal (invalidate)
.type capture_journal_invalidate,@function
capture_journal_invalidate:
    [--sp] = {rets, r8-r4}
    r1 += r0  ; @add.rr
    r8 = 0
    r3 = 16
    r4 = 524280
    r5 = L01c2422c
    r6 = 0
    goto L0200298e
L02002966:
    r7 = 0xDF000
    r2 = r6
    ifs (r6 >= 8) {  ; @ifs.ge.ri.s12
    r2 = r6 + r4
    r7 = 0xCF000
    }
    r2 = r2 << 13
    r2 += r7  ; @add.rr
    if (r1 <= r2) goto L0200298a
    r2 = r2 + 0x2000
    if (r2 > r0) {
    b[r3+r5] = r8
    }
L0200298a:
    r3 += 20  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L0200298e:
    if (r3 != 316) goto L02002966
    {pc, r8-r4} = [sp++]
