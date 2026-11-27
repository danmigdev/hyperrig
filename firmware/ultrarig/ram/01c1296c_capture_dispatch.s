; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_dispatch: 2 functions, 0x01c1296c..0x01c129dc

; capture_dispatch_load_context: 0x01c1296c..0x01c129ce, module capture-dispatch (load_context), capture-live (load_context), capture-native (load_context)
.type capture_dispatch_load_context,@function
capture_dispatch_load_context:
    [--sp] = {rets, r6-r4}
    sp += -12
    r6 = r0
    r4 = -5
    if (r1 == 0) goto L01c129c8
    r0 = r1 + 7
    r0 = r0 & 0xFFFFFFF8
    r1 = r0 - r1
    if (r1 > r2) goto L01c129c8
    r4 = [sp+28]
    [sp] = r0
    r0 = 0
    r0 = r2 - r1  #
    [sp+4] = r0
    r0 = r6  #
    [sp+8] = r0
    r5 = sp + 0
    r1 = r5
    r2 = r3
    r3 = r4
    call capture_live_parse  ; @call.xl
    r4 = r0
    if (r4 != 0) goto L01c129c8
    r0 = [r5+4]
    r1 = [r5+8]
    r4 = -5
    if (r0 > r1) goto L01c129c8
    r1 = native_A2_dot_i16
    r0 = r6 + 108
    r4 = 0
    [r0+0] = r1
    [r0+4] = r4
    r0 = r6  #
    [r0+8] = r4
    b[r6+136] = r4
; HyperRig MINI, product option: audio_task_warmup comes next, and fills what this clears (mini/product/swap.c).
.if MINI_PRODUCT
    r1 = hyperrig_capture_unstopped
    r1 = b[r1+0] (u)
    if (r1 != 0) goto hyperrig_context_unstopped
.endif
    call capture_live_reset
.if MINI_PRODUCT
hyperrig_context_unstopped:
.endif
; HyperRig MINI, product option: a capture is in the engine (mini/product/parametric.c).
.if MINI_PRODUCT
    call hyperrig_capture_loaded  ; @call.xl
.endif
L01c129c8:
    r0 = r4
    sp += 12
    {pc, r6-r4} = [sp++]

; capture_dispatch_select_dot: 0x01c129ce..0x01c129dc, module capture-dispatch (select_dot), capture-live (select_dot), capture-native (select_dot)
.type capture_dispatch_select_dot,@function
capture_dispatch_select_dot:
    if (r1 != 0) goto L01c129d6
    r1 = native_A2_dot_i16
L01c129d6:
    [r0+108] = r1
    rts
