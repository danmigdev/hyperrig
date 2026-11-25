; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 1 function, 0x02001854..0x02001864

; phase3_p5_pb0_io_set_die: 0x02001854..0x02001864, module phase3-p5 (pb0_io_set_die)
.type phase3_p5_pb0_io_set_die,@function
phase3_p5_pb0_io_set_die:
    [--sp] = rets
    r1 = r0 & 0x1
    r0 = 155
    call storage_fault_write_register  ; @call.xl
    pc = [sp++]
