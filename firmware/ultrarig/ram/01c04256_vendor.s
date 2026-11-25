; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c04256..0x01c042b0: vendor code (JieLi SDK or library, not reversed), as instructions
L01c04256:
    [--sp] = rets
    call L02055c34  ; @call.xl
    r0 = 2
    call L02055a96  ; @call.xl
    r0 = 1
    call L02055d38  ; @call.xl
    call L02056148  ; @call.xl
    call L020563de  ; @call.xl
    r0 = 0
    call L02055a96  ; @call.xl
    r0 = 71940
    [r0+0] &= 0xFFFF7FFF
    call L0205645e  ; @call.xl
    call L020565dc  ; @call.xl
    r0 = 3
    call L02055a96  ; @call.xl
    r0 = 0
    call L02055d38  ; @call.xl
    call L02056626  ; @call.xl
    pc = [sp++]
