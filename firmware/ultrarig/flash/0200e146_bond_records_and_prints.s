; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; bond_records_and_prints: 2 functions, 0x0200e146..0x0200e18e

; bond_records_and_prints_boot_clear: 0x0200e146..0x0200e15c, module bond-records-and-prints (boot_clear)
.type bond_records_and_prints_boot_clear,@function
bond_records_and_prints_boot_clear:
    r0 = L01c26890
    r1 = 1
    b[r0+13] = r1
    r0 = 29883888
    [r0+0] = 0x0
    rts

; bond_records_and_prints_hex_value: 0x0200e15c..0x0200e18e, module bond-records-and-prints (hex_value)
.type bond_records_and_prints_hex_value,@function
bond_records_and_prints_hex_value:
    r1 = r0 + -48
    r2 = r1.b0 (u)
    r1 = -48
    if (r2 < 10) goto L0200e178
    r1 = r0 + -97
    r2 = r1.b0 (u)
    r1 = -87
    if (r2 >= 6) goto L0200e17c
L0200e178:
    r0 += r1  ; @add.rr
    rts
L0200e17c:
    r1 = r0 + -55
    r0 += -65
    r0 = r0.b0 (u)
    if (r0 >= 6) {  ; @if.ge.ri.s12
    r1 = -1
    }
    r0 = r1
    rts
