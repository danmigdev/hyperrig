; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; bond_records_and_prints: 1 function, 0x02014504..0x0201453a

; bond_records_and_prints_db_value: 0x02014504..0x0201453a, module bond-records-and-prints (db_value)
.type bond_records_and_prints_db_value,@function
bond_records_and_prints_db_value:
    [--sp] = {rets, r5, r4}
    r2 = 30103
    r4 = r1 * r2
    r3_r2 = r0 * r2 (u)
    r3 += r4  ; @add.rr
    r0 = 0
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r4 = r2 + 0x1F40000
    r5 = r3 + r0 + c
    r0 = 0x3E80000
    } else {
    r4 = 0x1F40000 - r2
    r5 = r0 - r3 - !c
    r0 = 4229431296
    }
    r1_r0 = r5_r4 / r0 (s)
    {pc, r5, r4} = [sp++]
