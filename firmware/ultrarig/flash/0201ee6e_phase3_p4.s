; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 1 function, 0x0201ee6e..0x0201ee98

; phase3_p4_app_core_event_handler: 0x0201ee6e..0x0201ee98, module phase3-p4 (app_core_event_handler)
.type phase3_p4_app_core_event_handler,@function
phase3_p4_app_core_event_handler:
    [--sp] = {rets, r4}
    r4 = r0
    call phase3_p3_list_empty
    if (r0 == 0) goto L0201ee7e
L0201ee78:
    r0 = r4
    call boundary_hooks_default_event
L0201ee7c:
    {pc, r4} = [sp++]
L0201ee7e:
    r0 = L01c1f180
    r0 = [r0+164]
    r1 = [r0+12]
    r2 = [r1+4]
    if (r2 == 0) goto L0201ee78
    r0 += -16
    r1 = r4
    call r2
    if (r0 != 0) goto L0201ee7c
    goto L0201ee78
