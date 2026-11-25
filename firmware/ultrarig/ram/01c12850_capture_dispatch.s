; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_dispatch: 1 function, 0x01c12850..0x01c12878

; capture_dispatch_size: 0x01c12850..0x01c12878, module capture-dispatch (size), capture-live (size), capture-native (size)
.type capture_dispatch_size,@function
capture_dispatch_size:
    [--sp] = {rets, r4}
    sp += -240
    r4 = 0
    r3_r2 = r1_r0  #
    [sp+8] = r4
    r0 = 0
    r1 = 0
    [sp] = r0
    [sp+4] = r1
    r0 = sp + 12
    r1 = sp + 0
    call capture_live_parse  ; @call.xl
    if (r0 != 0) goto L01c12872
    r0 = [sp+4]
    r4 = r0 + 8
L01c12872:
    r0 = r4
    sp += 240
    {pc, r4} = [sp++]
