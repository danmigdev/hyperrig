; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; record_helpers: 2 functions, 0x02004272..0x020042d2

; record_helpers_copy_record: 0x02004272..0x020042a2, module record-helpers (copy_record)
.type record_helpers_copy_record,@function
record_helpers_copy_record:
    [--sp] = {rets, r4}
    r2 = 1
    b[r1+0] = r2
    r2 = b[r0+4] (u)
    b[r1+1] = r2
    r2 = h[r0+0] (u)
    h[r1+2] = r2
    r2 = h[r0+2] (u)
    h[r1+4] = r2
    r2 = b[r0+6] (u)
    r2 = r2 & 0xFFFFFF0F  #
    r3 = b[r0+5] (u)
    r3 <= insert(r2, p:8, l:4)  #
    r4 = b[r0+7] (u)
    r3 <= insert(r4, p:12, l:20)
    h[r1+6] = r3
    r2 = b[r0+10] (u)
    b[r1+8] = r2
    r0 = b[r0+9] (u)
    b[r1+9] = r0
    {pc, r4} = [sp++]

; record_helpers_copy_name: 0x020042a2..0x020042d2, module record-helpers (copy_name)
.type record_helpers_copy_name,@function
record_helpers_copy_name:
    [--sp] = {rets, r5, r4}
    r0 += 16  ; @add.ri.u5
    r2 = 0
    r3 = r0
    rep 6 {
    [r3++=4] = r2
    }
    goto L020042cc
L020042b0:
    r3 = b[r1+r2] (s)
    if (r3 == 0) goto L020042d0
    r4 = 95
    r5 = 95
    if (r3 != 127) {  ; @if.ne.ri.s12
    r5 = r3
    }
    ifs (r3 >= 32) {  ; @ifs.ge.ri.s12
    r4 = r5
    }
    b[r0+r2] = r4
    r2 += 1  ; @add.ri.u5
L020042cc:
    if (r2 <= 22) goto L020042b0
L020042d0:
    {pc, r5, r4} = [sp++]
