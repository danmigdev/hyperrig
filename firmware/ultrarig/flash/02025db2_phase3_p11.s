; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 1 function, 0x02025db2..0x02025db8

; phase3_p11_thread_run: 0x02025db2..0x02025db8, module phase3-p11 (thread_run)
.type phase3_p11_thread_run,@function
phase3_p11_thread_run:
    [--sp] = rets
    call L02025d66
    pc = [sp++]
