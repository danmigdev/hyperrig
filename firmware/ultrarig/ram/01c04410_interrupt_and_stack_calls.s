; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; interrupt_and_stack_calls: 2 functions, 0x01c04410..0x01c0444e

; interrupt_and_stack_calls_aligned_call: 0x01c04410..0x01c0442e, module interrupt-and-stack-calls (aligned_call)
.type interrupt_and_stack_calls_aligned_call,@function
interrupt_and_stack_calls_aligned_call:
    [--sp] = {rets, r5, r4}
    r4 = sp
    r5 = r0
    r0 = r1
    r2 = sp
    r2 = r2 >> 3
    r2 = r2 << 3
    sp = r2
    call r5
    sp = r4
    {pc, r5, r4} = [sp++]

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; interrupt_and_stack_calls_aligned_call_low: 0x01c0442e..0x01c0444e, module interrupt-and-stack-calls (aligned_call_low)
.type interrupt_and_stack_calls_aligned_call_low,@function
interrupt_and_stack_calls_aligned_call_low:
    [--sp] = {rets, r5, r4}
    r4 = sp
    r5 = r0
    r0 = r1
    r2 = sp
    r2 = r2 >> 3
    r2 = r2 << 3
    r2 += -4
    sp = r2
    call r5
    sp = r4
    {pc, r5, r4} = [sp++]
.endif
