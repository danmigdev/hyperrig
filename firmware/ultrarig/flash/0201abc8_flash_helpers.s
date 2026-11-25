; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 1 function, 0x0201abc8..0x0201ac0a

; flash_helpers_second_task: 0x0201abc8..0x0201ac0a, module flash-helpers (second_task)
.type flash_helpers_second_task,@function
flash_helpers_second_task:
    r5 = L01c26890
    r6 = 1
    r7 = 0
    r4 = capture_async_worker
L0201abd8:
    r0 = [r5+552]
    if (r0 == 0) goto L0201abec
    r1 = r5 + 552
    r0 = r4
    call interrupt_and_stack_calls_aligned_call  ; @call.xl
    goto L0201abd8
L0201abec:
    b[r5+30] = r6
    csync
    r0 = [r5+552]
    if (r0 != 0) goto L0201ac04
    r0 = r5 + 3588
    r1 = 0
    call L02040d34  ; @call.xl
L0201ac04:
    b[r5+30] = r7
    goto L0201abd8
