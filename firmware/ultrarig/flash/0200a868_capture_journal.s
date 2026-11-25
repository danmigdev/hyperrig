; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_journal: 1 function, 0x0200a868..0x0200a878

; capture_journal_write_offset: 0x0200a868..0x0200a878, module capture-journal (write_offset)
.type capture_journal_write_offset,@function
capture_journal_write_offset:
    [--sp] = rets
    r0 = [r0+0]
    r0 += r1  ; @add.rr
    r1 = r2
    r2 = r3
    call capture_journal_write
    pc = [sp++]
